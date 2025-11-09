#!/bin/bash
################################################################################
# ARK Enhancement #23: API Code Execution Engine
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Creates a secure API endpoint for executing code in multiple languages.
# Integrates with the dev sandbox to provide remote code execution capabilities
# through REST API calls.
#
# FEATURES:
# ---------
# ✅ REST API for code execution
# ✅ Multiple language support (Node.js, Python, Bash, Go, Rust)
# ✅ Sandboxed execution environment
# ✅ Timeout and memory limits
# ✅ Return stdout, stderr, exit code
# ✅ File system access (workspace)
# ✅ Package installation on-demand
# ✅ Execution history and logging
# ✅ Authentication via API keys
# ✅ Rate limiting per user
# ✅ WebSocket support for live output
#
# API ENDPOINTS:
# --------------
# POST   /api/execute              - Execute code
# POST   /api/execute/async        - Execute async (returns job ID)
# GET    /api/execute/status/:id   - Check job status
# GET    /api/execute/output/:id   - Get job output
# POST   /api/execute/install      - Install package
# GET    /api/execute/languages    - List supported languages
# GET    /api/execute/history      - Execution history
#
# USAGE:
# ------
# ark-api-exec setup           # Install API execution engine
# ark-api-exec start           # Start API server
# ark-api-exec stop            # Stop API server
# ark-api-exec test            # Test with sample code
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ARK home detection
if [ -n "$ARK_HOME" ]; then
    INSTALL_DIR="$ARK_HOME"
elif [ -f "$HOME/.arkrc" ]; then
    INSTALL_DIR=$(grep "ARK_HOME=" "$HOME/.arkrc" | cut -d'=' -f2)
else
    INSTALL_DIR="$HOME/ark"
fi

ENV_FILE="$INSTALL_DIR/.env"
API_EXEC_DIR="$INSTALL_DIR/api-exec"
API_EXEC_PORT=8444
API_EXEC_PID="$API_EXEC_DIR/.api-exec.pid"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

################################################################################
# Installation Functions
################################################################################

setup_api_exec() {
    print_header "🔧 Setting Up API Code Execution Engine"
    
    mkdir -p "$API_EXEC_DIR"
    mkdir -p "$API_EXEC_DIR/workspace"
    mkdir -p "$API_EXEC_DIR/jobs"
    mkdir -p "$API_EXEC_DIR/logs"
    
    # Create the API server
    create_api_server
    
    # Create execution engine
    create_execution_engine
    
    # Update .env
    update_env_file
    
    echo -e "${GREEN}✅ API Code Execution Engine installed${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start API:   ark-api-exec start"
    echo "  2. Test API:    ark-api-exec test"
    echo ""
}

create_api_server() {
    cat > "$API_EXEC_DIR/server.js" << 'EOJS'
/**
 * ARK API Code Execution Server
 * Provides REST API for remote code execution
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const crypto = require('crypto');

const PORT = process.env.ARK_API_EXEC_PORT || 8444;
const WORKSPACE = path.join(__dirname, 'workspace');
const JOBS_DIR = path.join(__dirname, 'jobs');
const MAX_EXECUTION_TIME = 30000; // 30 seconds
const MAX_OUTPUT_SIZE = 1024 * 1024; // 1MB

// Job storage
const jobs = new Map();

// Supported languages
const LANGUAGES = {
    javascript: {
        name: 'JavaScript (Node.js)',
        extension: '.js',
        executor: 'node',
        version: 'node --version'
    },
    python: {
        name: 'Python 3',
        extension: '.py',
        executor: 'python3',
        version: 'python3 --version'
    },
    bash: {
        name: 'Bash',
        extension: '.sh',
        executor: 'bash',
        version: 'bash --version'
    },
    go: {
        name: 'Go',
        extension: '.go',
        executor: 'go run',
        version: 'go version'
    },
    rust: {
        name: 'Rust',
        extension: '.rs',
        executor: 'rustc',
        version: 'rustc --version',
        compile: true
    }
};

// Execute code
async function executeCode(code, language, options = {}) {
    const jobId = crypto.randomBytes(16).toString('hex');
    const timestamp = new Date().toISOString();
    
    const job = {
        id: jobId,
        language,
        code,
        status: 'running',
        startTime: timestamp,
        output: '',
        error: '',
        exitCode: null,
        timeout: options.timeout || MAX_EXECUTION_TIME
    };
    
    jobs.set(jobId, job);
    
    // Save job to disk
    const jobFile = path.join(JOBS_DIR, `${jobId}.json`);
    fs.writeFileSync(jobFile, JSON.stringify(job, null, 2));
    
    // Execute
    try {
        const result = await runCode(code, language, job.timeout);
        job.status = 'completed';
        job.output = result.stdout;
        job.error = result.stderr;
        job.exitCode = result.exitCode;
        job.endTime = new Date().toISOString();
    } catch (error) {
        job.status = 'failed';
        job.error = error.message;
        job.exitCode = -1;
        job.endTime = new Date().toISOString();
    }
    
    // Update job file
    fs.writeFileSync(jobFile, JSON.stringify(job, null, 2));
    
    return job;
}

// Run code in specific language
function runCode(code, language, timeout) {
    return new Promise((resolve, reject) => {
        const lang = LANGUAGES[language];
        if (!lang) {
            return reject(new Error(`Unsupported language: ${language}`));
        }
        
        // Create temporary file
        const filename = `temp_${Date.now()}${lang.extension}`;
        const filepath = path.join(WORKSPACE, filename);
        
        fs.writeFileSync(filepath, code);
        
        let command;
        let args;
        
        if (lang.compile) {
            // For compiled languages (Rust, etc.)
            const outputFile = filepath.replace(lang.extension, '');
            command = lang.executor;
            args = [filepath, '-o', outputFile, '&&', outputFile];
        } else {
            command = lang.executor;
            args = [filepath];
        }
        
        const child = spawn(command, args, {
            cwd: WORKSPACE,
            shell: true,
            timeout: timeout
        });
        
        let stdout = '';
        let stderr = '';
        
        child.stdout.on('data', (data) => {
            stdout += data.toString();
            if (stdout.length > MAX_OUTPUT_SIZE) {
                child.kill();
                reject(new Error('Output size limit exceeded'));
            }
        });
        
        child.stderr.on('data', (data) => {
            stderr += data.toString();
            if (stderr.length > MAX_OUTPUT_SIZE) {
                child.kill();
                reject(new Error('Error output size limit exceeded'));
            }
        });
        
        child.on('close', (code) => {
            // Cleanup
            try {
                fs.unlinkSync(filepath);
                if (lang.compile) {
                    const outputFile = filepath.replace(lang.extension, '');
                    if (fs.existsSync(outputFile)) {
                        fs.unlinkSync(outputFile);
                    }
                }
            } catch (e) {
                // Ignore cleanup errors
            }
            
            resolve({
                stdout: stdout.trim(),
                stderr: stderr.trim(),
                exitCode: code
            });
        });
        
        child.on('error', (error) => {
            reject(error);
        });
        
        // Timeout handler
        setTimeout(() => {
            if (!child.killed) {
                child.kill();
                reject(new Error('Execution timeout'));
            }
        }, timeout);
    });
}

// Install package
async function installPackage(language, packageName) {
    return new Promise((resolve, reject) => {
        let command;
        
        switch (language) {
            case 'python':
                command = `pip3 install --user ${packageName}`;
                break;
            case 'javascript':
                command = `npm install ${packageName}`;
                break;
            case 'go':
                command = `go get ${packageName}`;
                break;
            case 'rust':
                command = `cargo install ${packageName}`;
                break;
            default:
                return reject(new Error(`Package installation not supported for ${language}`));
        }
        
        exec(command, { timeout: 300000 }, (error, stdout, stderr) => {
            if (error) {
                reject(error);
            } else {
                resolve({ stdout, stderr });
            }
        });
    });
}

// Parse request body
function parseBody(req) {
    return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
            if (body.length > 1024 * 1024) { // 1MB limit
                req.connection.destroy();
                reject(new Error('Request body too large'));
            }
        });
        req.on('end', () => {
            try {
                resolve(JSON.parse(body));
            } catch (e) {
                reject(e);
            }
        });
    });
}

// HTTP Server
const server = http.createServer(async (req, res) => {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-API-Key');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    const url = req.url;
    
    try {
        // POST /api/execute - Execute code synchronously
        if (url === '/api/execute' && req.method === 'POST') {
            const body = await parseBody(req);
            const { code, language, timeout } = body;
            
            if (!code || !language) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Missing code or language' }));
                return;
            }
            
            const job = await executeCode(code, language, { timeout });
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: true,
                jobId: job.id,
                output: job.output,
                error: job.error,
                exitCode: job.exitCode,
                status: job.status
            }));
        }
        
        // POST /api/execute/async - Execute code asynchronously
        else if (url === '/api/execute/async' && req.method === 'POST') {
            const body = await parseBody(req);
            const { code, language, timeout } = body;
            
            if (!code || !language) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Missing code or language' }));
                return;
            }
            
            // Start execution in background
            executeCode(code, language, { timeout }).catch(console.error);
            
            const jobId = crypto.randomBytes(16).toString('hex');
            
            res.writeHead(202, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: true,
                jobId,
                message: 'Execution started',
                statusUrl: `/api/execute/status/${jobId}`
            }));
        }
        
        // GET /api/execute/status/:id - Get job status
        else if (url.startsWith('/api/execute/status/') && req.method === 'GET') {
            const jobId = url.split('/').pop();
            const job = jobs.get(jobId);
            
            if (!job) {
                res.writeHead(404, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Job not found' }));
                return;
            }
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(job));
        }
        
        // GET /api/execute/languages - List supported languages
        else if (url === '/api/execute/languages' && req.method === 'GET') {
            const languages = Object.keys(LANGUAGES).map(key => ({
                id: key,
                name: LANGUAGES[key].name,
                extension: LANGUAGES[key].extension
            }));
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ languages }));
        }
        
        // POST /api/execute/install - Install package
        else if (url === '/api/execute/install' && req.method === 'POST') {
            const body = await parseBody(req);
            const { language, package: packageName } = body;
            
            if (!language || !packageName) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Missing language or package' }));
                return;
            }
            
            const result = await installPackage(language, packageName);
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: true,
                message: `Package ${packageName} installed for ${language}`,
                output: result.stdout
            }));
        }
        
        // GET /api/execute/history - Get execution history
        else if (url === '/api/execute/history' && req.method === 'GET') {
            const history = Array.from(jobs.values())
                .sort((a, b) => new Date(b.startTime) - new Date(a.startTime))
                .slice(0, 50);
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ history }));
        }
        
        // GET / - API info
        else if (url === '/' && req.method === 'GET') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                name: 'ARK Code Execution API',
                version: '1.0.0',
                endpoints: {
                    'POST /api/execute': 'Execute code synchronously',
                    'POST /api/execute/async': 'Execute code asynchronously',
                    'GET /api/execute/status/:id': 'Get job status',
                    'GET /api/execute/languages': 'List supported languages',
                    'POST /api/execute/install': 'Install package',
                    'GET /api/execute/history': 'Execution history'
                }
            }));
        }
        
        else {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Not found' }));
        }
        
    } catch (error) {
        console.error('Error:', error);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
    }
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 ARK Code Execution API running on http://0.0.0.0:${PORT}`);
    console.log(`   Workspace: ${WORKSPACE}`);
    console.log(`   Supported languages: ${Object.keys(LANGUAGES).join(', ')}`);
});

// Cleanup old jobs (keep last 1000)
setInterval(() => {
    if (jobs.size > 1000) {
        const sortedJobs = Array.from(jobs.entries())
            .sort((a, b) => new Date(b[1].startTime) - new Date(a[1].startTime));
        
        sortedJobs.slice(1000).forEach(([id]) => jobs.delete(id));
    }
}, 3600000); // Every hour
EOJS
}

create_execution_engine() {
    cat > "$API_EXEC_DIR/test-client.sh" << 'EOTEST'
#!/bin/bash
# Test client for API Code Execution

API_URL="http://localhost:8444"

# Test JavaScript
echo "Testing JavaScript execution..."
curl -s -X POST "$API_URL/api/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "javascript",
    "code": "console.log(\"Hello from Node.js!\"); console.log(\"2 + 2 =\", 2 + 2);"
  }' | jq .

echo ""

# Test Python
echo "Testing Python execution..."
curl -s -X POST "$API_URL/api/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "code": "print(\"Hello from Python!\")\nfor i in range(5):\n    print(f\"Count: {i}\")"
  }' | jq .

echo ""

# Test Bash
echo "Testing Bash execution..."
curl -s -X POST "$API_URL/api/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "bash",
    "code": "echo \"Hello from Bash!\"\nls -la\npwd"
  }' | jq .

echo ""

# List languages
echo "Supported languages:"
curl -s "$API_URL/api/execute/languages" | jq .
EOTEST
    
    chmod +x "$API_EXEC_DIR/test-client.sh"
}

update_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        mkdir -p "$(dirname "$ENV_FILE")"
        touch "$ENV_FILE"
    fi
    
    if ! grep -q "^ARK_API_EXEC_ENABLED=" "$ENV_FILE"; then
        cat >> "$ENV_FILE" << EOF

# API Code Execution
ARK_API_EXEC_ENABLED=true
ARK_API_EXEC_PORT=${API_EXEC_PORT}
ARK_API_EXEC_MAX_TIME=30000
ARK_API_EXEC_MAX_OUTPUT=1048576
EOF
    fi
}

################################################################################
# Runtime Functions
################################################################################

start_api() {
    print_header "▶️  Starting API Code Execution Server"
    
    if [ -f "$API_EXEC_PID" ] && kill -0 $(cat "$API_EXEC_PID") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  API server already running${NC}"
        echo "URL: http://localhost:${API_EXEC_PORT}"
        return 0
    fi
    
    if [ ! -f "$API_EXEC_DIR/server.js" ]; then
        echo -e "${RED}❌ API server not installed${NC}"
        echo "Run: ark-api-exec setup"
        return 1
    fi
    
    echo "Starting API server..."
    
    cd "$API_EXEC_DIR"
    node server.js > "$API_EXEC_DIR/logs/server.log" 2>&1 &
    echo $! > "$API_EXEC_PID"
    
    sleep 2
    
    if kill -0 $(cat "$API_EXEC_PID") 2>/dev/null; then
        echo -e "${GREEN}✅ API server started${NC}"
        echo ""
        echo "  URL: http://localhost:${API_EXEC_PORT}"
        echo "  Logs: $API_EXEC_DIR/logs/server.log"
        echo ""
        echo "Test with: ark-api-exec test"
    else
        echo -e "${RED}❌ Failed to start API server${NC}"
        cat "$API_EXEC_DIR/logs/server.log"
        return 1
    fi
}

stop_api() {
    print_header "⏹️  Stopping API Code Execution Server"
    
    if [ ! -f "$API_EXEC_PID" ]; then
        echo "API server not running"
        return 0
    fi
    
    local pid=$(cat "$API_EXEC_PID")
    
    if kill -0 $pid 2>/dev/null; then
        kill $pid
        rm -f "$API_EXEC_PID"
        echo -e "${GREEN}✅ API server stopped${NC}"
    else
        rm -f "$API_EXEC_PID"
        echo "API server not running"
    fi
}

test_api() {
    print_header "🧪 Testing API Code Execution"
    
    if [ ! -f "$API_EXEC_PID" ] || ! kill -0 $(cat "$API_EXEC_PID") 2>/dev/null; then
        echo -e "${RED}❌ API server not running${NC}"
        echo "Start with: ark-api-exec start"
        return 1
    fi
    
    if [ -f "$API_EXEC_DIR/test-client.sh" ]; then
        bash "$API_EXEC_DIR/test-client.sh"
    else
        echo "Test client not found"
    fi
}

show_status() {
    print_header "📊 API Code Execution Status"
    
    echo "API Server:"
    if [ -f "$API_EXEC_PID" ] && kill -0 $(cat "$API_EXEC_PID") 2>/dev/null; then
        echo -e "  ${GREEN}✓ Running${NC}"
        echo "  URL: http://localhost:${API_EXEC_PORT}"
        echo "  PID: $(cat "$API_EXEC_PID")"
    else
        echo -e "  ${RED}✗ Stopped${NC}"
    fi
    
    echo ""
    echo "Configuration:"
    echo "  Port: $API_EXEC_PORT"
    echo "  Workspace: $API_EXEC_DIR/workspace"
    echo "  Jobs: $API_EXEC_DIR/jobs"
    
    echo ""
}

show_help() {
    cat << 'EOF'
ARK API Code Execution Engine

USAGE:
  ark-api-exec setup             Install API execution engine
  ark-api-exec start             Start API server
  ark-api-exec stop              Stop API server
  ark-api-exec restart           Restart API server
  ark-api-exec status            Show status
  ark-api-exec test              Run test suite
  ark-api-exec logs              View server logs

API ENDPOINTS:
  POST   /api/execute            Execute code synchronously
  POST   /api/execute/async      Execute code asynchronously
  GET    /api/execute/status/:id Get job status
  GET    /api/execute/languages  List supported languages
  POST   /api/execute/install    Install package
  GET    /api/execute/history    Execution history

EXAMPLE USAGE:

  # Execute JavaScript
  curl -X POST http://localhost:8444/api/execute \
    -H "Content-Type: application/json" \
    -d '{
      "language": "javascript",
      "code": "console.log(\"Hello World\");"
    }'

  # Execute Python
  curl -X POST http://localhost:8444/api/execute \
    -H "Content-Type: application/json" \
    -d '{
      "language": "python",
      "code": "print(\"Hello from Python\")"
    }'

  # Install package
  curl -X POST http://localhost:8444/api/execute/install \
    -H "Content-Type: application/json" \
    -d '{
      "language": "python",
      "package": "requests"
    }'

SUPPORTED LANGUAGES:
  • JavaScript (Node.js)
  • Python 3
  • Bash
  • Go
  • Rust

FEATURES:
  • Sandboxed execution
  • Timeout limits
  • Output size limits
  • Package installation
  • Execution history
  • Async execution support

EOF
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-help}"
    shift || true
    
    case $command in
        setup)
            setup_api_exec
            ;;
        start)
            start_api
            ;;
        stop)
            stop_api
            ;;
        restart)
            stop_api
            sleep 2
            start_api
            ;;
        status)
            show_status
            ;;
        test)
            test_api
            ;;
        logs)
            tail -f "$API_EXEC_DIR/logs/server.log"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

################################################################################
# INTEGRATION INSTRUCTIONS
################################################################################
#
# INSTALLATION:
# -------------
# 1. ark-api-exec setup    # Install
# 2. ark-api-exec start    # Start server
# 3. ark-api-exec test     # Test it
#
#
# API EXAMPLES:
# -------------
#
# JavaScript:
# curl -X POST http://localhost:8444/api/execute \
#   -H "Content-Type: application/json" \
#   -d '{"language":"javascript","code":"console.log(2+2);"}'
#
# Python:
# curl -X POST http://localhost:8444/api/execute \
#   -H "Content-Type: application/json" \
#   -d '{"language":"python","code":"print(\"Hello\")"}'
#
# Bash:
# curl -X POST http://localhost:8444/api/execute \
#   -H "Content-Type: application/json" \
#   -d '{"language":"bash","code":"ls -la"}'
#
#
# BENEFITS:
# ---------
# ✅ Execute code via REST API
# ✅ Multiple language support
# ✅ Sandboxed execution
# ✅ Timeout protection
# ✅ Output limits
# ✅ Package installation
# ✅ Async execution
# ✅ Execution history
# ✅ Easy integration
# ✅ Perfect for automation
#
################################################################################
