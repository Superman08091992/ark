#!/usr/bin/env node
/**
 * ARK Code Lattice CLI Tool
 * Command-line interface for the capability-based knowledge graph
 */

const { program } = require('commander');
const path = require('path');
const fs = require('fs');
const http = require('http');

// Paths
const LATTICE_DIR = __dirname;
const MANAGER_PATH = path.join(LATTICE_DIR, 'lattice-manager.js');

// Check if manager exists
if (!fs.existsSync(MANAGER_PATH)) {
    console.error('❌ Error: Lattice manager not found at', MANAGER_PATH);
    process.exit(1);
}

const LatticeManager = require(MANAGER_PATH);

// Initialize manager
const manager = new LatticeManager(path.join(LATTICE_DIR, 'lattice.db'));

// Helper function to make API requests to backend
async function apiRequest(method, path, body = null) {
    const backendUrl = process.env.ARK_BACKEND_URL || 'http://localhost:8000';
    return new Promise((resolve, reject) => {
        const url = new URL(path, backendUrl);
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const req = http.request(url, options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    resolve(data);
                }
            });
        });
        
        req.on('error', reject);
        
        if (body) {
            req.write(JSON.stringify(body));
        }
        req.end();
    });
}

program
    .name('ark-lattice')
    .description('ARK Code Lattice - Capability-based knowledge graph for code generation')
    .version('1.0.0');

// Query command
program
    .command('query')
    .description('Query nodes by criteria')
    .option('-l, --language <lang>', 'Filter by programming language')
    .option('-t, --type <type>', 'Filter by node type')
    .option('-c, --capability <cap>', 'Search by capability keyword')
    .option('--limit <n>', 'Limit results', '10')
    .action(async (options) => {
        try {
            const filters = {};
            if (options.language) filters.language = options.language;
            if (options.type) filters.type = options.type;
            if (options.capability) filters.capability = options.capability;
            
            const results = await manager.queryNodes(filters, parseInt(options.limit));
            
            console.log(`\n🔍 Found ${results.length} node(s):\n`);
            results.forEach(node => {
                console.log(`📦 ${node.id}`);
                console.log(`   Type: ${node.type}`);
                console.log(`   Language: ${node.language || 'N/A'}`);
                console.log(`   Value: ${node.value}`);
                if (node.capabilities) {
                    const caps = JSON.parse(node.capabilities);
                    console.log(`   Capabilities: ${caps.join(', ')}`);
                }
                console.log('');
            });
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Generate command
program
    .command('generate')
    .description('Generate code from capability requirements')
    .requiredOption('-r, --requirements <reqs...>', 'Capability requirements')
    .option('-l, --language <lang>', 'Target language', 'javascript')
    .option('-o, --output <file>', 'Output file (optional)')
    .action(async (options) => {
        try {
            console.log(`\n🔧 Generating code for: ${options.requirements.join(', ')}`);
            console.log(`   Target language: ${options.language}\n`);
            
            const result = await manager.generateCode(options.requirements, {
                language: options.language
            });
            
            console.log('✅ Generated code:\n');
            console.log('─'.repeat(60));
            console.log(result.code);
            console.log('─'.repeat(60));
            console.log(`\n📊 Used ${result.nodes.length} node(s):`);
            result.nodes.forEach(node => {
                console.log(`   - ${node.id} (${node.type})`);
            });
            
            if (options.output) {
                fs.writeFileSync(options.output, result.code);
                console.log(`\n💾 Saved to: ${options.output}`);
            }
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Add node command
program
    .command('add')
    .description('Add a new node to the lattice')
    .requiredOption('-i, --id <id>', 'Node ID')
    .requiredOption('-t, --type <type>', 'Node type')
    .requiredOption('-v, --value <value>', 'Node value')
    .option('-l, --language <lang>', 'Programming language')
    .option('-c, --capabilities <caps...>', 'Capabilities')
    .option('--content <content>', 'Node content (code/template)')
    .action(async (options) => {
        try {
            const node = {
                id: options.id,
                type: options.type,
                value: options.value,
                language: options.language,
                capabilities: options.capabilities ? JSON.stringify(options.capabilities) : null,
                content: options.content
            };
            
            await manager.addNode(node);
            console.log(`✅ Node '${options.id}' added successfully`);
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Import command
program
    .command('import')
    .description('Import nodes from JSON file')
    .argument('<file>', 'JSON file path')
    .action(async (file) => {
        try {
            const absolutePath = path.resolve(file);
            
            if (!fs.existsSync(absolutePath)) {
                throw new Error(`File not found: ${absolutePath}`);
            }
            
            const data = JSON.parse(fs.readFileSync(absolutePath, 'utf8'));
            
            console.log(`\n📥 Importing from: ${file}`);
            console.log(`   Schema version: ${data.meta?.schema_version || 'unknown'}`);
            console.log(`   Total nodes: ${data.meta?.total_nodes || 'unknown'}\n`);
            
            let imported = 0;
            let skipped = 0;
            
            if (data.topics && Array.isArray(data.topics)) {
                for (const topic of data.topics) {
                    console.log(`📂 Processing topic: ${topic.name} (${topic.nodes?.length || 0} nodes)`);
                    
                    if (topic.nodes && Array.isArray(topic.nodes)) {
                        for (const node of topic.nodes) {
                            try {
                                // Add topic/category to node
                                node.category = topic.name;
                                await manager.addNode(node);
                                imported++;
                            } catch (error) {
                                if (error.message.includes('UNIQUE constraint failed')) {
                                    skipped++;
                                } else {
                                    console.error(`   ⚠️  Failed to import ${node.id}: ${error.message}`);
                                }
                            }
                        }
                    }
                }
            }
            
            console.log(`\n✅ Import complete:`);
            console.log(`   Imported: ${imported} nodes`);
            console.log(`   Skipped: ${skipped} nodes (already exist)`);
            process.exit(0);
            
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Stats command
program
    .command('stats')
    .description('Show lattice statistics')
    .action(async () => {
        try {
            const stats = await manager.getStats();
            
            console.log('\n📊 Code Lattice Statistics:\n');
            console.log(`   Total nodes: ${stats.total_nodes}`);
            console.log(`   Languages: ${stats.languages.length}`);
            console.log(`   Node types: ${stats.node_types.length}`);
            console.log(`   Categories: ${stats.categories.length}\n`);
            
            console.log('🔤 Languages:');
            stats.languages.forEach(lang => {
                console.log(`   - ${lang.language || 'Generic'}: ${lang.count} nodes`);
            });
            
            console.log('\n📦 Node Types:');
            stats.node_types.forEach(type => {
                console.log(`   - ${type.type}: ${type.count} nodes`);
            });
            
            if (stats.categories.length > 0) {
                console.log('\n📂 Categories:');
                stats.categories.forEach(cat => {
                    console.log(`   - ${cat.category || 'Uncategorized'}: ${cat.count} nodes`);
                });
            }
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// List command
program
    .command('list')
    .description('List all nodes')
    .option('-l, --language <lang>', 'Filter by language')
    .option('-t, --type <type>', 'Filter by type')
    .option('--limit <n>', 'Limit results', '50')
    .action(async (options) => {
        try {
            const filters = {};
            if (options.language) filters.language = options.language;
            if (options.type) filters.type = options.type;
            
            const nodes = await manager.queryNodes(filters, parseInt(options.limit));
            
            console.log(`\n📋 Listing ${nodes.length} node(s):\n`);
            nodes.forEach((node, i) => {
                console.log(`${i + 1}. ${node.id}`);
                console.log(`   ${node.type} | ${node.language || 'Generic'} | ${node.category || 'Uncategorized'}`);
                console.log(`   ${node.value}`);
                console.log('');
            });
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Delete command
program
    .command('delete')
    .description('Delete a node by ID')
    .argument('<id>', 'Node ID')
    .action(async (id) => {
        try {
            await manager.deleteNode(id);
            console.log(`✅ Node '${id}' deleted successfully`);
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Export command
program
    .command('export')
    .description('Export all nodes to JSON file')
    .argument('<file>', 'Output JSON file path')
    .action(async (file) => {
        try {
            const nodes = await manager.queryNodes({}, 10000);
            
            // Group by category
            const topics = {};
            nodes.forEach(node => {
                const category = node.category || 'Uncategorized';
                if (!topics[category]) {
                    topics[category] = [];
                }
                topics[category].push(node);
            });
            
            const exportData = {
                meta: {
                    schema_version: '1.0.0',
                    export_date: new Date().toISOString(),
                    total_nodes: nodes.length
                },
                topics: Object.entries(topics).map(([name, nodes]) => ({
                    name,
                    nodes
                }))
            };
            
            fs.writeFileSync(file, JSON.stringify(exportData, null, 2));
            console.log(`✅ Exported ${nodes.length} nodes to: ${file}`);
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// ===== FEDERATION COMMANDS =====

// Federation command group
const federation = program
    .command('federation')
    .description('Manage Code Lattice federation for distributed ARK instances');

// Federation status
federation
    .command('status')
    .description('Show federation status and info')
    .action(async () => {
        try {
            const result = await apiRequest('GET', '/api/federation/status');
            
            console.log('\n🌐 Federation Status:\n');
            console.log(`   Status: ${result.status}`);
            console.log(`   Running: ${result.isRunning ? '✅ Yes' : '❌ No'}`);
            console.log(`   Instance ID: ${result.info.instanceId}`);
            console.log(`   Instance Name: ${result.info.instanceName}`);
            console.log(`   Instance Type: ${result.info.instanceType}`);
            console.log(`   Mode: ${result.info.federationMode}`);
            console.log(`   Port: ${result.info.listenPort}`);
            console.log(`   Auto-sync: ${result.info.autoSync ? '✅ Enabled' : '❌ Disabled'}`);
            console.log(`   Sync Interval: ${result.info.syncInterval / 1000}s`);
            console.log(`\n📊 Statistics:`);
            console.log(`   Total Syncs: ${result.stats.totalSyncs}`);
            console.log(`   Nodes Sent: ${result.stats.nodesSent}`);
            console.log(`   Nodes Received: ${result.stats.nodesReceived}`);
            console.log(`   Conflicts Resolved: ${result.stats.conflictsResolved}`);
            console.log(`\n🔗 Peers:`);
            console.log(`   Total: ${result.info.peers.length}`);
            console.log(`   Active: ${result.activePeers.length}`);
            
            if (result.info.peers.length > 0) {
                console.log('\n   Configured Peers:');
                result.info.peers.forEach(peer => {
                    const isActive = result.activePeers.includes(peer);
                    console.log(`   ${isActive ? '✅' : '⚪'} ${peer}`);
                });
            }
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Start federation server
federation
    .command('start')
    .description('Start federation server')
    .action(async () => {
        try {
            const result = await apiRequest('POST', '/api/federation/start');
            
            console.log(`\n✅ Federation server started`);
            console.log(`   Instance: ${result.instanceName}`);
            console.log(`   Port: ${result.port}`);
            console.log(`   Instance ID: ${result.instanceId}\n`);
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Stop federation server
federation
    .command('stop')
    .description('Stop federation server')
    .action(async () => {
        try {
            const result = await apiRequest('POST', '/api/federation/stop');
            console.log(`\n✅ Federation server stopped\n`);
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Add peer
federation
    .command('add-peer <url>')
    .description('Add a peer to the federation')
    .action(async (url) => {
        try {
            const result = await apiRequest('POST', '/api/federation/peers/add', { peerUrl: url });
            
            console.log(`\n✅ Peer added: ${result.peerUrl}`);
            console.log(`   Total peers: ${result.totalPeers}\n`);
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Remove peer
federation
    .command('remove-peer <url>')
    .description('Remove a peer from the federation')
    .action(async (url) => {
        try {
            const result = await apiRequest('DELETE', `/api/federation/peers/${encodeURIComponent(url)}`);
            
            console.log(`\n✅ Peer removed: ${result.peerUrl}`);
            console.log(`   Total peers: ${result.totalPeers}\n`);
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// List peers
federation
    .command('list-peers')
    .description('List all configured peers')
    .action(async () => {
        try {
            const result = await apiRequest('GET', '/api/federation/peers');
            
            console.log(`\n🔗 Configured Peers (${result.totalPeers}):\n`);
            
            if (result.peers.length === 0) {
                console.log('   No peers configured\n');
            } else {
                result.peers.forEach((peer, i) => {
                    const isActive = result.activePeers.includes(peer);
                    console.log(`   ${i + 1}. ${isActive ? '✅' : '⚪'} ${peer}`);
                });
                console.log('');
            }
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Sync with peers
federation
    .command('sync')
    .description('Synchronize with all peers')
    .option('-p, --peer <url>', 'Sync with specific peer only')
    .action(async (options) => {
        try {
            const body = options.peer ? { peerUrl: options.peer } : {};
            const result = await apiRequest('POST', '/api/federation/sync', body);
            
            console.log(`\n✅ Synchronization complete`);
            console.log(`   Status: ${result.status}\n`);
            
            if (result.result) {
                console.log('📊 Sync Results:');
                if (Array.isArray(result.result)) {
                    result.result.forEach(r => {
                        console.log(`\n   Peer: ${r.peer}`);
                        console.log(`   Success: ${r.success ? '✅' : '❌'}`);
                        if (r.nodesSent !== undefined) console.log(`   Nodes Sent: ${r.nodesSent}`);
                        if (r.nodesReceived !== undefined) console.log(`   Nodes Received: ${r.nodesReceived}`);
                        if (r.error) console.log(`   Error: ${r.error}`);
                    });
                } else {
                    console.log(`   ${JSON.stringify(result.result, null, 2)}`);
                }
                console.log('');
            }
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Discover peers
federation
    .command('discover')
    .description('Discover peers on local network')
    .action(async () => {
        try {
            console.log('\n🔍 Discovering peers on local network...\n');
            
            const result = await apiRequest('POST', '/api/federation/discover');
            
            console.log(`✅ Discovery complete`);
            console.log(`   Found: ${result.peers.length} peer(s)`);
            console.log(`   Total peers: ${result.totalPeers}\n`);
            
            if (result.peers.length > 0) {
                console.log('Discovered Peers:');
                result.peers.forEach((peer, i) => {
                    console.log(`   ${i + 1}. ${peer}`);
                });
                console.log('');
            }
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

// Start auto-sync
federation
    .command('auto-sync')
    .description('Control automatic synchronization')
    .option('--start', 'Start auto-sync')
    .option('--stop', 'Stop auto-sync')
    .action(async (options) => {
        try {
            if (options.start) {
                const result = await apiRequest('POST', '/api/federation/auto-sync/start');
                console.log(`\n✅ Auto-sync started`);
                console.log(`   Interval: ${result.interval / 1000}s\n`);
            } else if (options.stop) {
                const result = await apiRequest('POST', '/api/federation/auto-sync/stop');
                console.log(`\n✅ Auto-sync stopped\n`);
            } else {
                console.log('\n⚠️  Please specify --start or --stop\n');
            }
            
            process.exit(0);
        } catch (error) {
            console.error('❌ Error:', error.message);
            process.exit(1);
        }
    });

program.parse(process.argv);
