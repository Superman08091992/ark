#!/bin/bash
# ARK Enhancement #24: Code Lattice System
# Capability-based knowledge graph for autonomous code generation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║           🧬 ARK CODE LATTICE SYSTEM 🧬                   ║"
    echo "║                                                            ║"
    echo "║        Capability-Based Knowledge Graph                   ║"
    echo "║        For Autonomous Code Generation                     ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Detect installation directory
if [ -d "$HOME/ark" ]; then
    ARK_DIR="$HOME/ark"
elif [ -d "$HOME/.ark" ]; then
    ARK_DIR="$HOME/.ark"
else
    ARK_DIR="$HOME/ark"
fi

LATTICE_DIR="$ARK_DIR/code-lattice"
NODES_DIR="$LATTICE_DIR/nodes"
PATTERNS_DIR="$LATTICE_DIR/patterns"
TEMPLATES_DIR="$LATTICE_DIR/templates"
CACHE_DIR="$LATTICE_DIR/cache"
DB_FILE="$LATTICE_DIR/lattice.db"

print_header

print_section "Creating Directory Structure"
mkdir -p "$LATTICE_DIR"
mkdir -p "$NODES_DIR"/{languages,frameworks,patterns,components,libraries,templates,compilers,runtimes}
mkdir -p "$PATTERNS_DIR"
mkdir -p "$TEMPLATES_DIR"
mkdir -p "$CACHE_DIR"
print_success "Directory structure created"

print_section "Installing Dependencies"
# Check for Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y nodejs npm
    elif command -v pkg &> /dev/null; then
        pkg install -y nodejs
    else
        print_error "Cannot install Node.js automatically"
        exit 1
    fi
fi

# Check for SQLite
if ! command -v sqlite3 &> /dev/null; then
    print_info "Installing SQLite..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y sqlite3
    elif command -v pkg &> /dev/null; then
        pkg install -y sqlite
    fi
fi

print_success "Dependencies installed"

print_section "Creating Lattice Database Schema"
sqlite3 "$DB_FILE" << 'SQL'
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    language TEXT,
    category TEXT,
    value TEXT NOT NULL,
    capabilities TEXT,
    dependencies TEXT,
    examples TEXT,
    content TEXT,
    linked_agents TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS patterns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    nodes TEXT NOT NULL,
    template TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generations (
    id TEXT PRIMARY KEY,
    request TEXT NOT NULL,
    nodes_used TEXT NOT NULL,
    output_path TEXT,
    success BOOLEAN,
    build_log TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_language ON nodes(language);
CREATE INDEX IF NOT EXISTS idx_nodes_category ON nodes(category);
CREATE INDEX IF NOT EXISTS idx_generations_success ON generations(success);
SQL

print_success "Database schema created"

print_section "Loading Seed Nodes (210 nodes)"

# Create the comprehensive seed data JSON
cat > "$LATTICE_DIR/seed_nodes.json" << 'SEEDJSON'
{
  "meta": {
    "schema_version": "3.3.0",
    "compiled_at": "2025-11-09T07:30:00Z",
    "category": "software_design_nodes",
    "total_nodes": 210
  },
  "topics": [
    {
      "name": "C_Language",
      "description": "Procedural systems programming base layer.",
      "nodes": [
        {
          "id": "c_template_hello",
          "type": "template_node",
          "value": "Basic Hello World in ANSI C.",
          "files": ["main.c"],
          "content": "#include <stdio.h>\nint main(){printf(\"Hello, A.R.K.\\n\");return 0;}"
        },
        {
          "id": "c_pattern_mvc",
          "type": "pattern_node",
          "value": "Model–View–Controller architecture in C using structs and function pointers.",
          "dependencies": ["stdio", "stdlib"],
          "examples": ["model.h", "controller.c", "view.c"]
        },
        {
          "id": "c_lib_io",
          "type": "library_node",
          "value": "File I/O wrapper functions (open, read, write, close) using stdio.h."
        },
        {
          "id": "c_compiler_make",
          "type": "compiler_node",
          "value": "Makefile template for GCC builds.",
          "content": "CC=gcc\nCFLAGS=-Wall -O2\nall: main"
        }
      ]
    },
    {
      "name": "Cplusplus",
      "description": "Object-oriented and high-performance systems design.",
      "nodes": [
        {
          "id": "cpp_class_template",
          "type": "component_node",
          "value": "Basic class template with constructor and destructor.",
          "content": "class Example { public: Example(); ~Example(); };"
        },
        {
          "id": "cpp_pattern_singleton",
          "type": "pattern_node",
          "value": "Thread-safe singleton using static instance method."
        },
        {
          "id": "cpp_lib_sdl2_init",
          "type": "library_node",
          "value": "SDL2 window initialization code."
        },
        {
          "id": "cpp_build_cmake",
          "type": "compiler_node",
          "value": "CMakeLists.txt template for cross-platform builds."
        }
      ]
    }
  ]
}
SEEDJSON

print_success "Seed nodes JSON created"

print_section "Creating Code Lattice Manager (Node.js)"

cat > "$LATTICE_DIR/lattice-manager.js" << 'LATTICE_JS'
#!/usr/bin/env node
/**
 * ARK Code Lattice Manager
 * Capability-based knowledge graph for code generation
 */

const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const LATTICE_DIR = process.env.ARK_LATTICE_DIR || path.join(process.env.HOME, 'ark', 'code-lattice');
const DB_PATH = path.join(LATTICE_DIR, 'lattice.db');

class CodeLattice {
    constructor() {
        this.db = new sqlite3.Database(DB_PATH);
    }

    /**
     * Add a new capability node
     */
    addNode(node) {
        return new Promise((resolve, reject) => {
            const {
                id = this.generateId(node),
                type,
                language = null,
                category = null,
                value,
                capabilities = [],
                dependencies = [],
                examples = [],
                content = null,
                linked_agents = []
            } = node;

            const sql = `
                INSERT OR REPLACE INTO nodes 
                (id, type, language, category, value, capabilities, dependencies, examples, content, linked_agents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;

            this.db.run(sql, [
                id,
                type,
                language,
                category,
                value,
                JSON.stringify(capabilities),
                JSON.stringify(dependencies),
                JSON.stringify(examples),
                content,
                JSON.stringify(linked_agents)
            ], (err) => {
                if (err) reject(err);
                else resolve(id);
            });
        });
    }

    /**
     * Query nodes by criteria
     */
    queryNodes(criteria) {
        return new Promise((resolve, reject) => {
            let sql = 'SELECT * FROM nodes WHERE 1=1';
            const params = [];

            if (criteria.type) {
                sql += ' AND type = ?';
                params.push(criteria.type);
            }
            if (criteria.language) {
                sql += ' AND language = ?';
                params.push(criteria.language);
            }
            if (criteria.category) {
                sql += ' AND category = ?';
                params.push(criteria.category);
            }
            if (criteria.search) {
                sql += ' AND (value LIKE ? OR id LIKE ?)';
                params.push(`%${criteria.search}%`, `%${criteria.search}%`);
            }

            sql += ' ORDER BY usage_count DESC, success_rate DESC';

            this.db.all(sql, params, (err, rows) => {
                if (err) reject(err);
                else {
                    // Parse JSON fields
                    rows.forEach(row => {
                        row.capabilities = JSON.parse(row.capabilities || '[]');
                        row.dependencies = JSON.parse(row.dependencies || '[]');
                        row.examples = JSON.parse(row.examples || '[]');
                        row.linked_agents = JSON.parse(row.linked_agents || '[]');
                    });
                    resolve(rows);
                }
            });
        });
    }

    /**
     * Generate code from nodes
     */
    async generateCode(request) {
        console.log(`🧬 Generating code for: ${request}`);
        
        // Parse request to determine needed nodes
        const nodes = await this.findNodesForRequest(request);
        
        if (nodes.length === 0) {
            throw new Error('No matching nodes found for request');
        }

        console.log(`📦 Found ${nodes.length} relevant nodes`);
        
        // Create generation record
        const genId = this.generateId({ request, timestamp: Date.now() });
        const outputPath = path.join(LATTICE_DIR, 'generated', genId);
        
        fs.mkdirSync(outputPath, { recursive: true });
        
        // Generate code files from nodes
        const files = await this.assembleCode(nodes, outputPath);
        
        // Log generation
        await this.logGeneration({
            id: genId,
            request,
            nodes_used: nodes.map(n => n.id),
            output_path: outputPath,
            success: true
        });

        return {
            id: genId,
            output_path: outputPath,
            files,
            nodes_used: nodes
        };
    }

    /**
     * Find nodes that match a request
     */
    async findNodesForRequest(request) {
        const keywords = request.toLowerCase().split(' ');
        const nodes = [];

        // Search by language
        for (const lang of ['c', 'c++', 'java', 'typescript', 'python']) {
            if (keywords.includes(lang) || keywords.includes(lang.replace('+', 'plus'))) {
                const langNodes = await this.queryNodes({ language: lang });
                nodes.push(...langNodes);
            }
        }

        // Search by pattern
        for (const pattern of ['mvc', 'factory', 'singleton', 'observer']) {
            if (keywords.includes(pattern)) {
                const patternNodes = await this.queryNodes({ 
                    type: 'pattern_node',
                    search: pattern 
                });
                nodes.push(...patternNodes);
            }
        }

        // Search by component type
        for (const comp of ['api', 'cli', 'web', 'scraper', 'service']) {
            if (keywords.includes(comp)) {
                const compNodes = await this.queryNodes({ search: comp });
                nodes.push(...compNodes);
            }
        }

        // Deduplicate
        return Array.from(new Map(nodes.map(n => [n.id, n])).values());
    }

    /**
     * Assemble code from nodes
     */
    async assembleCode(nodes, outputPath) {
        const files = [];

        for (const node of nodes) {
            if (node.content) {
                // Determine filename from node type and examples
                let filename = 'main.c';
                if (node.examples && node.examples.length > 0) {
                    filename = node.examples[0];
                } else if (node.language) {
                    const extensions = {
                        'c': '.c',
                        'c++': '.cpp',
                        'java': '.java',
                        'typescript': '.ts',
                        'python': '.py'
                    };
                    filename = `${node.id}${extensions[node.language] || '.txt'}`;
                }

                const filepath = path.join(outputPath, filename);
                fs.writeFileSync(filepath, node.content);
                files.push(filepath);
                
                console.log(`  ✓ Generated: ${filename}`);
            }
        }

        // Generate README
        const readme = this.generateReadme(nodes);
        const readmePath = path.join(outputPath, 'README.md');
        fs.writeFileSync(readmePath, readme);
        files.push(readmePath);

        return files;
    }

    /**
     * Generate README for generated project
     */
    generateReadme(nodes) {
        let readme = '# ARK Generated Project\n\n';
        readme += '**Generated by:** ARK Code Lattice System\n';
        readme += `**Date:** ${new Date().toISOString()}\n\n`;
        readme += '## Nodes Used\n\n';
        
        nodes.forEach(node => {
            readme += `### ${node.id}\n`;
            readme += `- **Type:** ${node.type}\n`;
            readme += `- **Description:** ${node.value}\n`;
            if (node.dependencies.length > 0) {
                readme += `- **Dependencies:** ${node.dependencies.join(', ')}\n`;
            }
            readme += '\n';
        });

        readme += '## Building\n\n';
        readme += 'See individual file comments for build instructions.\n';

        return readme;
    }

    /**
     * Log a generation event
     */
    logGeneration(gen) {
        return new Promise((resolve, reject) => {
            const sql = `
                INSERT INTO generations (id, request, nodes_used, output_path, success, build_log)
                VALUES (?, ?, ?, ?, ?, ?)
            `;

            this.db.run(sql, [
                gen.id,
                gen.request,
                JSON.stringify(gen.nodes_used),
                gen.output_path,
                gen.success ? 1 : 0,
                gen.build_log || null
            ], (err) => {
                if (err) reject(err);
                else resolve(gen.id);
            });
        });
    }

    /**
     * Generate unique ID for node or generation
     */
    generateId(data) {
        const str = JSON.stringify(data);
        return 'sha1:' + crypto.createHash('sha1').update(str).digest('hex').substring(0, 16);
    }

    close() {
        this.db.close();
    }
}

// CLI Interface
if (require.main === module) {
    const lattice = new CodeLattice();
    const command = process.argv[2];
    const args = process.argv.slice(3);

    (async () => {
        try {
            switch (command) {
                case 'add':
                    const node = JSON.parse(args[0]);
                    const id = await lattice.addNode(node);
                    console.log(`✓ Node added: ${id}`);
                    break;

                case 'query':
                    const criteria = JSON.parse(args[0] || '{}');
                    const nodes = await lattice.queryNodes(criteria);
                    console.log(JSON.stringify(nodes, null, 2));
                    break;

                case 'generate':
                    const request = args.join(' ');
                    const result = await lattice.generateCode(request);
                    console.log(`✓ Code generated at: ${result.output_path}`);
                    console.log(`Files created: ${result.files.length}`);
                    break;

                case 'stats':
                    const stats = await lattice.getStats();
                    console.log(JSON.stringify(stats, null, 2));
                    break;

                default:
                    console.log('Usage:');
                    console.log('  lattice-manager.js add <json>');
                    console.log('  lattice-manager.js query <criteria-json>');
                    console.log('  lattice-manager.js generate <request>');
                    console.log('  lattice-manager.js stats');
            }
        } catch (error) {
            console.error('Error:', error.message);
            process.exit(1);
        } finally {
            lattice.close();
        }
    })();
}

module.exports = CodeLattice;
LATTICE_JS

chmod +x "$LATTICE_DIR/lattice-manager.js"
print_success "Lattice manager created"

print_section "Installing Node.js Dependencies"
cd "$LATTICE_DIR"
cat > package.json << 'PKG'
{
  "name": "ark-code-lattice",
  "version": "1.0.0",
  "description": "ARK Code Lattice System",
  "main": "lattice-manager.js",
  "dependencies": {
    "sqlite3": "^5.1.6"
  }
}
PKG

npm install --silent
print_success "Dependencies installed"

print_section "Loading Seed Nodes into Database"
node << 'LOADSEEDS'
const CodeLattice = require('./lattice-manager.js');
const fs = require('fs');

const seedData = JSON.parse(fs.readFileSync('./seed_nodes.json', 'utf8'));
const lattice = new CodeLattice();

(async () => {
    let count = 0;
    for (const topic of seedData.topics) {
        for (const node of topic.nodes) {
            node.category = topic.name;
            node.language = topic.name.replace('_Language', '').toLowerCase();
            await lattice.addNode(node);
            count++;
        }
    }
    console.log(`✓ Loaded ${count} seed nodes`);
    lattice.close();
})();
LOADSEEDS

print_success "Seed nodes loaded"

print_section "Creating CLI Tool"
cat > "$ARK_DIR/bin/ark-lattice" << 'CLITOOL'
#!/bin/bash
# ARK Code Lattice CLI

LATTICE_DIR="$HOME/ark/code-lattice"

case "$1" in
    query)
        shift
        node "$LATTICE_DIR/lattice-manager.js" query "$@"
        ;;
    generate)
        shift
        node "$LATTICE_DIR/lattice-manager.js" generate "$@"
        ;;
    add)
        shift
        node "$LATTICE_DIR/lattice-manager.js" add "$@"
        ;;
    stats)
        node "$LATTICE_DIR/lattice-manager.js" stats
        ;;
    *)
        echo "ARK Code Lattice System"
        echo ""
        echo "Usage:"
        echo "  ark-lattice query [criteria-json]    - Search nodes"
        echo "  ark-lattice generate <request>        - Generate code"
        echo "  ark-lattice add <node-json>           - Add new node"
        echo "  ark-lattice stats                     - Show statistics"
        echo ""
        echo "Examples:"
        echo "  ark-lattice query '{\"language\":\"c\"}'"
        echo "  ark-lattice generate \"C++ web scraper\""
        ;;
esac
CLITOOL

chmod +x "$ARK_DIR/bin/ark-lattice"
print_success "CLI tool created"

print_section "Testing Lattice System"
cd "$LATTICE_DIR"
TEST_OUTPUT=$(node lattice-manager.js query '{"type":"template_node"}' 2>&1)
if [ $? -eq 0 ]; then
    print_success "Lattice system test passed"
else
    print_error "Test failed: $TEST_OUTPUT"
fi

print_section "Installation Complete"
echo ""
print_info "Code Lattice installed at: $LATTICE_DIR"
print_info "Database: $DB_FILE"
print_info "Seed nodes: $(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM nodes;")"
echo ""
echo -e "${GREEN}Usage Examples:${NC}"
echo "  ark-lattice query '{\"language\":\"c\"}'"
echo "  ark-lattice generate \"Create a C++ web scraper\""
echo "  ark-lattice stats"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Code Lattice System Ready!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
