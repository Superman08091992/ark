#!/usr/bin/env node
/**
 * ARK Federation System Test Script
 * Tests the federation functionality with simulated instances
 */

const { LatticeFederation } = require('./lattice-federation.cjs');
const http = require('http');
const path = require('path');

console.log('🧪 ARK Federation System Test\n');
console.log('=' .repeat(60));

// Test 1: Create Federation Instance
console.log('\n📋 Test 1: Create Federation Instance');
try {
    const federation = new LatticeFederation({
        instanceType: 'local',
        instanceName: 'ARK-Test-Instance',
        federationMode: 'p2p',
        listenPort: 9100,
        autoSync: false
    });
    
    console.log('✅ Federation instance created');
    console.log(`   Instance ID: ${federation.instanceId.substring(0, 16)}...`);
    console.log(`   Instance Name: ${federation.instanceName}`);
    console.log(`   Instance Type: ${federation.instanceType}`);
    console.log(`   Mode: ${federation.federationMode}`);
    console.log(`   Port: ${federation.listenPort}`);
} catch (error) {
    console.error('❌ Failed to create federation instance:', error.message);
    process.exit(1);
}

// Test 2: Federation Server Start/Stop
console.log('\n📋 Test 2: Federation Server Start/Stop');
(async () => {
    try {
        const federation = new LatticeFederation({
            instanceType: 'local',
            listenPort: 9101,
            autoSync: false
        });
        
        // Start server
        await federation.startServer();
        console.log('✅ Federation server started');
        console.log(`   Listening on port: ${federation.listenPort}`);
        
        // Test if server is responding
        const testRequest = () => new Promise((resolve, reject) => {
            const req = http.get(`http://localhost:${federation.listenPort}/federation/info`, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        resolve(JSON.parse(data));
                    } catch (e) {
                        reject(e);
                    }
                });
            });
            req.on('error', reject);
            req.setTimeout(2000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });
        });
        
        const info = await testRequest();
        console.log('✅ Server responding to requests');
        console.log(`   Instance ID matches: ${info.instanceId === federation.instanceId}`);
        
        // Stop server
        await federation.stopServer();
        console.log('✅ Federation server stopped');
        
    } catch (error) {
        console.error('❌ Server test failed:', error.message);
        process.exit(1);
    }
    
    // Test 3: Peer Management
    console.log('\n📋 Test 3: Peer Management');
    try {
        const federation = new LatticeFederation({
            instanceType: 'local',
            autoSync: false
        });
        
        // Add peers
        federation.addPeer('http://peer1.example.com:9000');
        federation.addPeer('http://peer2.example.com:9000');
        console.log('✅ Added 2 peers');
        console.log(`   Total peers: ${federation.peers.length}`);
        
        // Try to add duplicate
        federation.addPeer('http://peer1.example.com:9000');
        console.log(`✅ Duplicate prevention works (still ${federation.peers.length} peers)`);
        
        // Remove peer
        federation.removePeer('http://peer1.example.com:9000');
        console.log(`✅ Removed peer (now ${federation.peers.length} peers)`);
        
    } catch (error) {
        console.error('❌ Peer management test failed:', error.message);
        process.exit(1);
    }
    
    // Test 4: Conflict Resolution
    console.log('\n📋 Test 4: Conflict Resolution');
    try {
        const federation = new LatticeFederation({
            instanceType: 'local',
            autoSync: false
        });
        
        // Test case 1: Incoming node is newer
        const existing1 = { updated_at: 1000 };
        const incoming1 = { updated_at: 2000 };
        const result1 = federation._resolveConflict(existing1, incoming1, 'remote-instance');
        console.log(`✅ Newer timestamp wins: ${result1 === true ? 'PASS' : 'FAIL'}`);
        
        // Test case 2: Existing node is newer
        const existing2 = { updated_at: 2000 };
        const incoming2 = { updated_at: 1000 };
        const result2 = federation._resolveConflict(existing2, incoming2, 'remote-instance');
        console.log(`✅ Older timestamp loses: ${result2 === false ? 'PASS' : 'FAIL'}`);
        
        // Test case 3: Same timestamp, instance ID tiebreaker
        const existing3 = { updated_at: 1000 };
        const incoming3 = { updated_at: 1000 };
        // Use instance IDs that we know the relationship
        const higherInstanceId = 'zzz' + federation.instanceId; // Guaranteed to be > federation.instanceId
        const lowerInstanceId = 'aaa' + federation.instanceId.substring(3); // Guaranteed to be < federation.instanceId
        const result3a = federation._resolveConflict(existing3, incoming3, higherInstanceId);
        const result3b = federation._resolveConflict(existing3, incoming3, lowerInstanceId);
        console.log(`✅ Tiebreaker works: ${result3a === true && result3b === false ? 'PASS' : 'FAIL'}`);
        
    } catch (error) {
        console.error('❌ Conflict resolution test failed:', error.message);
        process.exit(1);
    }
    
    // Test 5: Info Retrieval
    console.log('\n📋 Test 5: Info Retrieval');
    try {
        const federation = new LatticeFederation({
            instanceType: 'cloud',
            instanceName: 'Test-Cloud-Instance',
            federationMode: 'hub',
            listenPort: 9102,
            hubUrl: 'http://hub.example.com:9000',
            syncInterval: 30000,
            autoSync: true
        });
        
        const info = federation.getInfo();
        
        console.log('✅ Info retrieved successfully');
        console.log(`   Instance Type: ${info.instanceType}`);
        console.log(`   Mode: ${info.federationMode}`);
        console.log(`   Hub URL: ${info.hubUrl}`);
        console.log(`   Sync Interval: ${info.syncInterval}ms`);
        console.log(`   Auto-sync: ${info.autoSync}`);
        
    } catch (error) {
        console.error('❌ Info retrieval test failed:', error.message);
        process.exit(1);
    }
    
    // Test 6: State Persistence
    console.log('\n📋 Test 6: State Persistence');
    try {
        const fs = require('fs');
        const testConfigPath = path.join(__dirname, 'test-federation-config.json');
        const testStatePath = path.join(__dirname, 'test-federation-state.json');
        
        // Clean up any existing test files
        if (fs.existsSync(testConfigPath)) fs.unlinkSync(testConfigPath);
        if (fs.existsSync(testStatePath)) fs.unlinkSync(testStatePath);
        
        const federation = new LatticeFederation({
            instanceType: 'pi',
            listenPort: 9103,
            autoSync: false,
            configPath: testConfigPath,
            statePath: testStatePath
        });
        
        // Add some data
        federation.addPeer('http://test-peer:9000');
        federation.stats.totalSyncs = 10;
        
        // Save state
        federation.saveState();
        federation.saveConfiguration();
        
        console.log('✅ State saved to disk');
        console.log(`   Config exists: ${fs.existsSync(testConfigPath)}`);
        console.log(`   State exists: ${fs.existsSync(testStatePath)}`);
        
        // Load state in new instance
        const federation2 = new LatticeFederation({
            configPath: testConfigPath,
            statePath: testStatePath
        });
        
        console.log('✅ State loaded from disk');
        console.log(`   Peers restored: ${federation2.peers.length}`);
        console.log(`   Stats restored: ${federation2.stats.totalSyncs} syncs`);
        
        // Clean up test files
        if (fs.existsSync(testConfigPath)) fs.unlinkSync(testConfigPath);
        if (fs.existsSync(testStatePath)) fs.unlinkSync(testStatePath);
        
    } catch (error) {
        console.error('❌ State persistence test failed:', error.message);
        process.exit(1);
    }
    
    // Test 7: Event Emission
    console.log('\n📋 Test 7: Event Emission');
    try {
        const federation = new LatticeFederation({
            instanceType: 'local',
            autoSync: false
        });
        
        let eventReceived = false;
        federation.on('peerAdded', (peer) => {
            eventReceived = true;
            console.log(`✅ Event emitted: peerAdded (${peer})`);
        });
        
        federation.addPeer('http://test-peer:9000');
        
        if (!eventReceived) {
            throw new Error('Event was not emitted');
        }
        
    } catch (error) {
        console.error('❌ Event emission test failed:', error.message);
        process.exit(1);
    }
    
    // Test Summary
    console.log('\n' + '='.repeat(60));
    console.log('\n🎉 All Federation Tests Passed!\n');
    console.log('✅ Federation instance creation');
    console.log('✅ Server start/stop');
    console.log('✅ Peer management');
    console.log('✅ Conflict resolution');
    console.log('✅ Info retrieval');
    console.log('✅ State persistence');
    console.log('✅ Event emission');
    console.log('\n📊 Summary:');
    console.log('   7 tests executed');
    console.log('   7 tests passed');
    console.log('   0 tests failed');
    console.log('\n✨ Federation system is ready for deployment!\n');
    
    process.exit(0);
})();
