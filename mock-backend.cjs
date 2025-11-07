#!/usr/bin/env node
/**
 * ARK Mock Backend Server
 * Provides mock API endpoints for frontend demonstration
 */

const http = require('http');
const url = require('url');

const PORT = 8000;

// Mock data
const mockAgents = [
  {
    name: 'Kyle',
    status: 'active',
    last_active: new Date().toISOString(),
    essence: 'The Seer'
  },
  {
    name: 'Joey',
    status: 'active',
    last_active: new Date().toISOString(),
    essence: 'The Scholar'
  },
  {
    name: 'Kenny',
    status: 'active',
    last_active: new Date().toISOString(),
    essence: 'The Builder'
  },
  {
    name: 'HRM',
    status: 'active',
    last_active: new Date().toISOString(),
    essence: 'The Arbiter'
  },
  {
    name: 'Aletheia',
    status: 'active',
    last_active: new Date().toISOString(),
    essence: 'The Mirror'
  },
  {
    name: 'ID',
    status: 'active',
    last_active: new Date().toISOString(),
    essence: 'The Evolving Reflection'
  }
];

const mockFiles = [
  {
    name: 'agent_logs.txt',
    path: 'projects/ark/agent_logs.txt',
    size: 2345,
    modified: new Date().toISOString()
  },
  {
    name: 'market_data.json',
    path: 'projects/ark/market_data.json',
    size: 15678,
    modified: new Date().toISOString()
  },
  {
    name: 'patterns.csv',
    path: 'analysis/patterns.csv',
    size: 45234,
    modified: new Date().toISOString()
  }
];

const mockConversations = [
  {
    id: '1',
    user_message: 'Hello Kyle, what do you see?',
    agent_response: '🔍 Scanning the markets... I detect unusual patterns in tech sector.',
    timestamp: new Date().toISOString(),
    tools_used: ['market_scanner', 'pattern_detector']
  }
];

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Content-Type': 'application/json'
};

// Request handler
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  const method = req.method;

  // Handle CORS preflight
  if (method === 'OPTIONS') {
    res.writeHead(200, corsHeaders);
    res.end();
    return;
  }

  console.log(`${method} ${pathname}`);

  // Health check
  if (pathname === '/api/health' && method === 'GET') {
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({
      status: 'healthy',
      service: 'ARK Mock Backend',
      timestamp: new Date().toISOString()
    }));
    return;
  }

  // Get agents
  if (pathname === '/api/agents' && method === 'GET') {
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({ agents: mockAgents }));
    return;
  }

  // Chat with agent
  if (pathname === '/api/chat' && method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const agentName = data.agent_name || 'Kyle';
        const userMessage = data.message || '';
        
        // Generate mock response based on agent
        let response = '';
        switch(agentName) {
          case 'Kyle':
            response = '🔍 Analyzing patterns... I see interesting signals in the market today.';
            break;
          case 'Joey':
            response = '🧠 Processing data... Statistical analysis shows correlation patterns emerging.';
            break;
          case 'Kenny':
            response = '🔨 Building solution... I can create files and execute code for you.';
            break;
          case 'HRM':
            response = '⚖️ Validating logic... This request aligns with ethical principles.';
            break;
          case 'Aletheia':
            response = '🔮 Contemplating meaning... Let me explore the philosophical dimensions.';
            break;
          case 'ID':
            response = '🌱 Learning from you... Your patterns reveal interesting insights.';
            break;
          default:
            response = 'Hello! I am processing your request.';
        }
        
        res.writeHead(200, corsHeaders);
        res.end(JSON.stringify({
          response: response,
          agent: agentName,
          timestamp: new Date().toISOString(),
          tools_used: ['analysis_engine'],
          files_created: []
        }));
      } catch (err) {
        res.writeHead(400, corsHeaders);
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
    return;
  }

  // Get conversations
  if (pathname.startsWith('/api/conversations/') && method === 'GET') {
    const agentName = pathname.split('/')[3];
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({ conversations: mockConversations }));
    return;
  }

  // List files
  if (pathname === '/api/files' && method === 'GET') {
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({ files: mockFiles }));
    return;
  }

  // Create file
  if (pathname === '/api/files' && method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        res.writeHead(200, corsHeaders);
        res.end(JSON.stringify({
          success: true,
          path: data.path,
          message: 'File created successfully (mock)'
        }));
      } catch (err) {
        res.writeHead(400, corsHeaders);
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
    return;
  }

  // Read file
  if (pathname.startsWith('/api/files/') && method === 'GET') {
    const filePath = pathname.substring(11); // Remove '/api/files/'
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({
      content: `Mock content for file: ${filePath}\n\nThis is a demonstration of the ARK file system.`,
      path: filePath
    }));
    return;
  }

  // Delete file
  if (pathname.startsWith('/api/files/') && method === 'DELETE') {
    const filePath = pathname.substring(11);
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({
      success: true,
      message: `File ${filePath} deleted (mock)`
    }));
    return;
  }

  // 404 Not Found
  res.writeHead(404, corsHeaders);
  res.end(JSON.stringify({
    error: 'Not Found',
    path: pathname,
    message: 'This endpoint is not available in the mock backend'
  }));
});

server.listen(PORT, () => {
  console.log(`🌌 ARK Mock Backend running on http://localhost:${PORT}`);
  console.log(`📡 CORS enabled - accepting requests from all origins`);
  console.log(`🔧 Endpoints:`);
  console.log(`   GET  /api/health`);
  console.log(`   GET  /api/agents`);
  console.log(`   POST /api/chat`);
  console.log(`   GET  /api/conversations/:agent`);
  console.log(`   GET  /api/files`);
  console.log(`   POST /api/files`);
  console.log(`   GET  /api/files/:path`);
  console.log(`   DELETE /api/files/:path`);
});

// Handle shutdown gracefully
process.on('SIGTERM', () => {
  console.log('🛑 Shutting down ARK Mock Backend...');
  server.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});
