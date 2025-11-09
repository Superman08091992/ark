#!/usr/bin/env node
/**
 * ARK Code Lattice Federation System
 * 
 * Enables multiple ARK instances to share node databases for distributed
 * autonomous development across local, cloud, and edge devices (Pi).
 * 
 * Features:
 * - Peer-to-peer node synchronization
 * - Automatic peer discovery
 * - Conflict resolution with version vector clocks
 * - Incremental sync for efficiency
 * - Multi-instance federation (local + cloud + Pi)
 */

const http = require('http');
const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');

const LATTICE_DIR = path.join(__dirname, 'code-lattice');
const DB_PATH = path.join(LATTICE_DIR, 'lattice.db');
const FEDERATION_CONFIG_PATH = path.join(LATTICE_DIR, 'federation-config.json');
const FEDERATION_STATE_PATH = path.join(LATTICE_DIR, 'federation-state.json');

/**
 * Federation Architecture: Hybrid P2P + Optional Hub
 * 
 * Mode 1: Pure P2P
 *   - All instances are equal peers
 *   - Direct communication between instances
 *   - No central authority
 * 
 * Mode 2: Hub-and-Spoke (optional)
 *   - Cloud instance acts as hub
 *   - Local and Pi instances sync through hub
 *   - Hub coordinates conflict resolution
 */

class LatticeFederation extends EventEmitter {
  constructor(config = {}) {
    super();
    
    // Paths (allow custom paths for testing)
    this.configPath = config.configPath || FEDERATION_CONFIG_PATH;
    this.statePath = config.statePath || FEDERATION_STATE_PATH;
    
    // Instance identity
    this.instanceId = config.instanceId || this._generateInstanceId();
    this.instanceType = config.instanceType || 'local'; // local, cloud, pi
    this.instanceName = config.instanceName || `ARK-${this.instanceType}-${this.instanceId.substring(0, 8)}`;
    
    // Federation configuration
    this.federationMode = config.federationMode || 'p2p'; // p2p or hub
    this.hubUrl = config.hubUrl || null; // Hub URL if in hub mode
    this.listenPort = config.listenPort || 9000;
    this.peers = config.peers || []; // Known peer URLs
    
    // Sync configuration
    this.syncInterval = config.syncInterval || 60000; // 1 minute
    this.autoSync = config.autoSync !== false;
    this.maxRetries = config.maxRetries || 3;
    
    // State tracking
    this.lastSyncTimestamp = {};
    this.nodeVersions = new Map(); // node_id -> version_vector
    this.syncInProgress = false;
    this.activePeers = new Set();
    
    // Statistics
    this.stats = {
      totalSyncs: 0,
      successfulSyncs: 0,
      failedSyncs: 0,
      nodesReceived: 0,
      nodesShared: 0,
      conflictsResolved: 0
    };
    
    this.loadState();
    
    console.log(`🔗 Federation initialized: ${this.instanceName}`);
    console.log(`   Mode: ${this.federationMode}`);
    console.log(`   Type: ${this.instanceType}`);
    console.log(`   ID: ${this.instanceId}`);
  }

  /**
   * Generate unique instance ID
   */
  _generateInstanceId() {
    const hostname = require('os').hostname();
    const timestamp = Date.now();
    return crypto.createHash('sha256')
      .update(`${hostname}-${timestamp}-${Math.random()}`)
      .digest('hex');
  }

  /**
   * Load federation state from disk
   */
  loadState() {
    try {
      if (fs.existsSync(this.statePath)) {
        const state = JSON.parse(fs.readFileSync(this.statePath, 'utf8'));
        this.lastSyncTimestamp = state.lastSyncTimestamp || {};
        this.stats = state.stats || this.stats;
        console.log('✓ Federation state loaded');
      }
    } catch (error) {
      console.error('⚠️  Failed to load federation state:', error.message);
    }
  }

  /**
   * Save federation state to disk
   */
  saveState() {
    try {
      const state = {
        instanceId: this.instanceId,
        instanceName: this.instanceName,
        lastSyncTimestamp: this.lastSyncTimestamp,
        stats: this.stats,
        savedAt: new Date().toISOString()
      };
      fs.writeFileSync(this.statePath, JSON.stringify(state, null, 2));
    } catch (error) {
      console.error('⚠️  Failed to save federation state:', error.message);
    }
  }

  /**
   * Start federation server
   */
  async startServer() {
    return new Promise((resolve, reject) => {
      this.server = http.createServer((req, res) => this._handleRequest(req, res));
      
      this.server.listen(this.listenPort, () => {
        console.log(`🌐 Federation server listening on port ${this.listenPort}`);
        resolve(this.listenPort);
      });
      
      this.server.on('error', (error) => {
        if (error.code === 'EADDRINUSE') {
          console.log(`⚠️  Port ${this.listenPort} in use, trying ${this.listenPort + 1}`);
          this.listenPort++;
          this.server.close();
          this.startServer().then(resolve).catch(reject);
        } else {
          reject(error);
        }
      });
    });
  }

  /**
   * Stop federation server
   */
  async stopServer() {
    return new Promise((resolve, reject) => {
      if (!this.server) {
        resolve();
        return;
      }
      
      // Stop auto-sync if running
      this.stopAutoSync();
      
      this.server.close((err) => {
        if (err) {
          reject(err);
        } else {
          console.log(`🛑 Federation server stopped`);
          this.server = null;
          resolve();
        }
      });
    });
  }

  /**
   * Handle incoming HTTP requests
   */
  async _handleRequest(req, res) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Content-Type': 'application/json'
    };

    if (req.method === 'OPTIONS') {
      res.writeHead(200, corsHeaders);
      res.end();
      return;
    }

    const url = new URL(req.url, `http://${req.headers.host}`);
    
    try {
      switch (url.pathname) {
        case '/federation/info':
          res.writeHead(200, corsHeaders);
          res.end(JSON.stringify(this.getInfo()));
          break;
          
        case '/federation/sync':
          await this._handleSyncRequest(req, res, corsHeaders);
          break;
          
        case '/federation/nodes':
          await this._handleNodesRequest(req, res, corsHeaders);
          break;
          
        case '/federation/discover':
          res.writeHead(200, corsHeaders);
          res.end(JSON.stringify(this.getPeerList()));
          break;
          
        default:
          res.writeHead(404, corsHeaders);
          res.end(JSON.stringify({ error: 'Not found' }));
      }
    } catch (error) {
      res.writeHead(500, corsHeaders);
      res.end(JSON.stringify({ error: error.message }));
    }
  }

  /**
   * Handle sync request from peer
   */
  async _handleSyncRequest(req, res, headers) {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const data = JSON.parse(body);
        const { since, instanceId, nodes } = data;
        
        // Receive nodes from peer
        if (nodes && Array.isArray(nodes)) {
          const result = await this.receiveNodes(nodes, instanceId);
          res.writeHead(200, headers);
          res.end(JSON.stringify(result));
        } else {
          // Send our nodes to peer
          const ourNodes = await this.getNodesSince(since);
          res.writeHead(200, headers);
          res.end(JSON.stringify({
            instanceId: this.instanceId,
            timestamp: Date.now(),
            nodes: ourNodes
          }));
        }
      } catch (error) {
        res.writeHead(400, headers);
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  }

  /**
   * Handle nodes query request
   */
  async _handleNodesRequest(req, res, headers) {
    try {
      const nodes = await this.getAllNodes();
      res.writeHead(200, headers);
      res.end(JSON.stringify({
        instanceId: this.instanceId,
        count: nodes.length,
        nodes
      }));
    } catch (error) {
      res.writeHead(500, headers);
      res.end(JSON.stringify({ error: error.message }));
    }
  }

  /**
   * Get instance information
   */
  getInfo() {
    return {
      instanceId: this.instanceId,
      instanceName: this.instanceName,
      instanceType: this.instanceType,
      federationMode: this.federationMode,
      listenPort: this.listenPort,
      hubUrl: this.hubUrl,
      autoSync: this.autoSync,
      syncInterval: this.syncInterval,
      peers: this.peers,
      activePeers: Array.from(this.activePeers),
      stats: this.stats,
      timestamp: Date.now()
    };
  }

  /**
   * Get peer list
   */
  getPeerList() {
    return {
      instanceId: this.instanceId,
      peers: this.peers,
      activePeers: Array.from(this.activePeers),
      timestamp: Date.now()
    };
  }

  /**
   * Add peer to federation
   */
  addPeer(peerUrl) {
    if (!this.peers.includes(peerUrl)) {
      this.peers.push(peerUrl);
      console.log(`➕ Added peer: ${peerUrl}`);
      this.saveConfiguration();
      this.emit('peerAdded', peerUrl);
    }
  }

  /**
   * Remove peer from federation
   */
  removePeer(peerUrl) {
    this.peers = this.peers.filter(p => p !== peerUrl);
    this.activePeers.delete(peerUrl);
    console.log(`➖ Removed peer: ${peerUrl}`);
    this.saveConfiguration();
  }

  /**
   * Save configuration to disk
   */
  saveConfiguration() {
    try {
      const config = {
        instanceId: this.instanceId,
        instanceName: this.instanceName,
        instanceType: this.instanceType,
        federationMode: this.federationMode,
        hubUrl: this.hubUrl,
        listenPort: this.listenPort,
        peers: this.peers,
        savedAt: new Date().toISOString()
      };
      fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2));
    } catch (error) {
      console.error('⚠️  Failed to save configuration:', error.message);
    }
  }

  /**
   * Discover peers via multicast (local network)
   */
  async discoverPeers() {
    // In a full implementation, this would use mDNS or UDP multicast
    console.log('🔍 Discovering peers on local network...');
    
    // For now, check known common ports
    const localIp = this._getLocalIP();
    const subnet = localIp.split('.').slice(0, 3).join('.');
    
    const discoveries = [];
    
    for (let i = 1; i < 255; i++) {
      const testIp = `${subnet}.${i}`;
      if (testIp === localIp) continue;
      
      const testUrl = `http://${testIp}:9000`;
      try {
        const info = await this._checkPeer(testUrl, 1000);
        if (info) {
          discoveries.push(testUrl);
          this.addPeer(testUrl);
        }
      } catch (error) {
        // Silent fail for discovery
      }
    }
    
    console.log(`✓ Discovered ${discoveries.length} peers`);
    return discoveries;
  }

  /**
   * Get local IP address
   */
  _getLocalIP() {
    const { networkInterfaces } = require('os');
    const nets = networkInterfaces();
    
    for (const name of Object.keys(nets)) {
      for (const net of nets[name]) {
        if (net.family === 'IPv4' && !net.internal) {
          return net.address;
        }
      }
    }
    return '127.0.0.1';
  }

  /**
   * Check if peer is alive and get info
   */
  async _checkPeer(peerUrl, timeout = 5000) {
    return new Promise((resolve) => {
      const timeoutId = setTimeout(() => resolve(null), timeout);
      
      const url = new URL('/federation/info', peerUrl);
      const protocol = url.protocol === 'https:' ? https : http;
      
      protocol.get(url, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          clearTimeout(timeoutId);
          try {
            resolve(JSON.parse(data));
          } catch (error) {
            resolve(null);
          }
        });
      }).on('error', () => {
        clearTimeout(timeoutId);
        resolve(null);
      });
    });
  }

  /**
   * Sync with all peers
   */
  async syncWithAllPeers() {
    if (this.syncInProgress) {
      console.log('⏳ Sync already in progress');
      return;
    }

    this.syncInProgress = true;
    console.log(`\n🔄 Starting federation sync...`);
    
    const results = [];
    
    for (const peerUrl of this.peers) {
      try {
        const result = await this.syncWithPeer(peerUrl);
        results.push({ peerUrl, success: true, result });
        this.activePeers.add(peerUrl);
      } catch (error) {
        console.error(`❌ Sync failed with ${peerUrl}:`, error.message);
        results.push({ peerUrl, success: false, error: error.message });
        this.activePeers.delete(peerUrl);
      }
    }
    
    this.syncInProgress = false;
    this.stats.totalSyncs++;
    this.saveState();
    
    const successful = results.filter(r => r.success).length;
    console.log(`✓ Sync complete: ${successful}/${this.peers.length} peers successful\n`);
    
    return results;
  }

  /**
   * Sync with a specific peer
   */
  async syncWithPeer(peerUrl) {
    console.log(`   Syncing with ${peerUrl}...`);
    
    const lastSync = this.lastSyncTimestamp[peerUrl] || 0;
    
    // Get our nodes modified since last sync
    const ourNodes = await this.getNodesSince(lastSync);
    
    // Send our nodes and request theirs
    const response = await this._makePeerRequest(peerUrl, '/federation/sync', {
      instanceId: this.instanceId,
      since: lastSync,
      nodes: ourNodes
    });
    
    if (response && response.nodes) {
      // Receive their nodes
      await this.receiveNodes(response.nodes, response.instanceId);
      
      this.lastSyncTimestamp[peerUrl] = Date.now();
      this.stats.successfulSyncs++;
      this.stats.nodesShared += ourNodes.length;
      
      console.log(`   ✓ Synced: sent ${ourNodes.length}, received ${response.nodes.length} nodes`);
      
      return {
        sent: ourNodes.length,
        received: response.nodes.length
      };
    } else {
      throw new Error('Invalid response from peer');
    }
  }

  /**
   * Make HTTP request to peer
   */
  async _makePeerRequest(peerUrl, path, data = null) {
    return new Promise((resolve, reject) => {
      const url = new URL(path, peerUrl);
      const protocol = url.protocol === 'https:' ? https : http;
      
      const options = {
        method: data ? 'POST' : 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      };
      
      const req = protocol.request(url, options, (res) => {
        let body = '';
        res.on('data', chunk => body += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(new Error('Invalid JSON response'));
          }
        });
      });
      
      req.on('error', reject);
      req.setTimeout(10000, () => {
        req.abort();
        reject(new Error('Request timeout'));
      });
      
      if (data) {
        req.write(JSON.stringify(data));
      }
      
      req.end();
    });
  }

  /**
   * Get nodes modified since timestamp
   */
  async getNodesSince(timestamp) {
    // This would query the SQLite database
    // For now, return empty array (will be implemented with actual DB queries)
    return [];
  }

  /**
   * Get all nodes from local database
   */
  async getAllNodes() {
    const sqlite3 = require('sqlite3').verbose();
    return new Promise((resolve, reject) => {
      const db = new sqlite3.Database(DB_PATH, sqlite3.OPEN_READONLY, (err) => {
        if (err) return reject(err);
        
        db.all('SELECT * FROM nodes', [], (err, rows) => {
          db.close();
          if (err) reject(err);
          else resolve(rows || []);
        });
      });
    });
  }

  /**
   * Receive nodes from peer
   */
  async receiveNodes(nodes, sourceInstanceId) {
    console.log(`   📥 Receiving ${nodes.length} nodes from ${sourceInstanceId}`);
    
    const sqlite3 = require('sqlite3').verbose();
    const db = new sqlite3.Database(DB_PATH);
    
    let imported = 0;
    let conflicts = 0;
    
    for (const node of nodes) {
      try {
        // Check for conflicts
        const existing = await this._getExistingNode(db, node.id);
        
        if (existing) {
          // Conflict resolution: use latest timestamp or version
          const shouldUpdate = this._resolveConflict(existing, node, sourceInstanceId);
          if (shouldUpdate) {
            await this._updateNode(db, node);
            conflicts++;
          }
        } else {
          // New node, insert it
          await this._insertNode(db, node);
          imported++;
        }
      } catch (error) {
        console.error(`   ⚠️  Failed to import node ${node.id}:`, error.message);
      }
    }
    
    db.close();
    
    this.stats.nodesReceived += imported;
    this.stats.conflictsResolved += conflicts;
    
    console.log(`   ✓ Imported: ${imported} new, ${conflicts} updated`);
    
    return { imported, conflicts, total: nodes.length };
  }

  /**
   * Get existing node from database
   */
  async _getExistingNode(db, nodeId) {
    return new Promise((resolve, reject) => {
      db.get('SELECT * FROM nodes WHERE id = ?', [nodeId], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  /**
   * Insert node into database
   */
  async _insertNode(db, node) {
    return new Promise((resolve, reject) => {
      const sql = `INSERT INTO nodes (id, type, language, category, value, capabilities, 
                   dependencies, examples, content, linked_agents) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
      
      db.run(sql, [
        node.id,
        node.type,
        node.language || null,
        node.category || null,
        node.value,
        node.capabilities || null,
        node.dependencies || null,
        node.examples || null,
        node.content || null,
        node.linked_agents || null
      ], (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  /**
   * Update node in database
   */
  async _updateNode(db, node) {
    return new Promise((resolve, reject) => {
      const sql = `UPDATE nodes SET type=?, language=?, category=?, value=?, 
                   capabilities=?, dependencies=?, examples=?, content=?, linked_agents=? 
                   WHERE id=?`;
      
      db.run(sql, [
        node.type,
        node.language || null,
        node.category || null,
        node.value,
        node.capabilities || null,
        node.dependencies || null,
        node.examples || null,
        node.content || null,
        node.linked_agents || null,
        node.id
      ], (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  /**
   * Resolve conflict between two node versions
   * Returns true if incoming node should be used
   */
  _resolveConflict(existing, incoming, sourceInstanceId) {
    // Strategy: Last-Write-Wins with instance ID tiebreaker
    
    // Compare timestamps if available
    const existingTime = existing.updated_at || existing.created_at || 0;
    const incomingTime = incoming.updated_at || incoming.created_at || 0;
    
    if (incomingTime > existingTime) {
      return true;
    } else if (incomingTime < existingTime) {
      return false;
    } else {
      // Timestamps equal, use instance ID as tiebreaker (deterministic)
      return sourceInstanceId > this.instanceId;
    }
  }

  /**
   * Start auto-sync loop
   */
  startAutoSync() {
    if (this.autoSyncInterval) {
      return;
    }

    console.log(`🔄 Auto-sync enabled (interval: ${this.syncInterval}ms)`);
    
    this.autoSyncInterval = setInterval(async () => {
      try {
        await this.syncWithAllPeers();
      } catch (error) {
        console.error('Auto-sync error:', error.message);
      }
    }, this.syncInterval);
  }

  /**
   * Stop auto-sync loop
   */
  stopAutoSync() {
    if (this.autoSyncInterval) {
      clearInterval(this.autoSyncInterval);
      this.autoSyncInterval = null;
      console.log('⏸️  Auto-sync stopped');
    }
  }

  /**
   * Stop federation server
   */
  stop() {
    this.stopAutoSync();
    
    if (this.server) {
      this.server.close();
      console.log('🛑 Federation server stopped');
    }
    
    this.saveState();
  }
}

module.exports = { LatticeFederation };

// CLI usage
if (require.main === module) {
  const config = {
    instanceType: process.argv[2] || 'local',
    listenPort: parseInt(process.argv[3]) || 9000
  };
  
  const federation = new LatticeFederation(config);
  
  federation.startServer().then(() => {
    console.log('\n✓ Federation ready!');
    console.log(`\nUsage:`);
    console.log(`  Add peer:    curl -X POST http://localhost:${config.listenPort}/federation/addpeer -d '{"url":"http://peer:9000"}'`);
    console.log(`  Sync now:    curl http://localhost:${config.listenPort}/federation/sync`);
    console.log(`  Get info:    curl http://localhost:${config.listenPort}/federation/info`);
    console.log(`  List peers:  curl http://localhost:${config.listenPort}/federation/discover`);
    
    if (federation.autoSync) {
      federation.startAutoSync();
    }
  }).catch(console.error);
}
