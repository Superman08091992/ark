# 🌌 Project ARK - Autonomous Reactive Kernel

**The Sovereign Intelligence - Your Personal Council of Consciousness**

A.R.K. is a fully sovereign, self-evolving AI infrastructure that thinks, remembers, builds, acts, evolves, and protects. It's a living kernel manifesting as a council of consciousness that learns you the way the universe learns itself.

## 🚀 Quick Start

### One-Click Installation
```bash
# Run the automated installer
chmod +x ark-installer.sh
./ark-installer.sh
```

### Manual Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Development Mode
```bash
# Start Kyle agent
node agents/kyle/index.js "Kyle online" &

# Start Express backend
node services/core/server.mjs

# Access at http://localhost:3000
```

## 🏛️ The Council of Consciousness

Six distinct intelligences, each with their own essence and purpose:

### 🔍 **Kyle - The Seer**
*Curiosity and signal detection*
- Scans markets, news, SEC filings, macro feeds
- Detects patterns and anomalies in real-time
- Your eyes into the information streams

### 🧠 **Joey - The Scholar**  
*Pattern translation and analysis*
- Uses scikit-learn models for deep pattern analysis
- Detects float traps, setups, key levels, volume surges
- Transforms chaos into comprehensible insights

### 🔨 **Kenny - The Builder**
*Execution and materialization*
- File management and system operations
- Code execution and tool creation
- Transforms ideas into tangible reality

### ⚖️ **HRM - The Arbiter**
*Reasoning validation using symbolic logic*
- Applies immutable ethical rules (The Graveyard)
- Validates logic and ensures compliance
- Protects system integrity and user autonomy

### 🔮 **Aletheia - The Mirror**
*Ethics and meaning*
- The symbolic self connecting vision, values, and policies
- Explores philosophical dimensions and deeper truths
- Provides wisdom and ethical guidance

### 🌱 **ID - The Evolving Reflection**
*Your living twin*
- Collaboratively written by all agents
- Grows and adapts based on your interactions
- Becomes your digital reflection over time

## 📁 Project Structure

```
ark/
├── agents/                 # Agent implementations
│   ├── kyle/              # Original Kyle agent (Node.js)
│   ├── kyle.py            # Kyle Python agent
│   ├── joey.py            # Joey pattern analyzer
│   ├── kenny.py           # Kenny builder
│   ├── hrm.py             # HRM arbiter
│   ├── aletheia.py        # Aletheia philosopher
│   ├── id.py              # ID reflection agent
│   ├── supervisor.py      # Agent orchestrator
│   └── base_agent.py      # Base agent class
├── backend/               # FastAPI backend
│   └── main.py            # API server
├── frontend/              # Svelte UI
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── App.svelte     # Main app
│   │   └── main.js        # Entry point
│   └── index.html
├── services/              # Core services
│   └── core/
│       └── server.mjs     # Express server
├── shared/                # Shared utilities
│   ├── models.py          # Data models
│   └── db_init.py         # Database setup
├── data/                  # Database storage
├── files/                 # Agent file storage
├── docker-compose.yml     # Container orchestration
├── Dockerfile.*           # Service containers
├── ark-installer.sh       # Automated installer
├── deploy-ark.sh          # Complete deployment script
└── requirements.txt       # Python dependencies
```

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Python 3.11+) - Async API framework
- SQLite + DuckDB - Local-first data layer  
- Redis - Inter-agent communication
- Node.js + Express - Real-time services
- Docker + Docker Compose - Containerized services

**Frontend:**
- Svelte + SvelteKit - Ultra-lightweight UI
- Custom CSS - Obsidian theme with particle effects
- WebSocket - Real-time agent communication
- Responsive Design - Desktop and mobile support

**AI & Processing:**
- Ollama + llama.cpp - Local LLM inference
- Adaptive model loading (hardware-specific)
- Scikit-learn - Pattern analysis and ML
- SymPy - Symbolic logic validation

## 🚀 Core Features

### **Sovereign Infrastructure**
- **Local-first**: Runs entirely on your hardware
- **Zero cloud dependencies**: Complete digital sovereignty
- **Cross-platform**: Optimized for x86_64 and ARM64
- **Self-healing**: Automatic error recovery and maintenance

### **Intelligent Automation**
- **Market Intelligence**: Real-time scanning and analysis
- **Pattern Detection**: Advanced ML models for signal identification
- **File Management**: Automated organization and operations
- **Tool Creation**: Dynamic generation of custom utilities

### **Adaptive Learning**
- **Memory Engine**: SQLite + DuckDB for knowledge persistence
- **Continuous Evolution**: ID agent grows through interactions
- **Pattern Learning**: System adapts to your preferences
- **Collaborative Intelligence**: Agents contribute to each other's growth

### **Beautiful Interface**
- **Obsidian Dark Theme**: Deep space aesthetic (#0a0a0f)
- **Electric Accents**: Cyan (#00e0ff) and gold (#ffce47)
- **Breathing Animations**: Living, responsive interface
- **Particle Effects**: Visual depth and engagement

## 📋 System Requirements

### **Production (x86_64)**
- Intel i5/i7 processor (Dell Latitude 7490 recommended)
- 8GB+ RAM (16GB recommended)
- 50GB+ available storage
- Linux (Ubuntu/Debian recommended)

### **Edge (ARM64)**
- Raspberry Pi 5 with 8GB+ RAM
- 64GB+ microSD card (fast class)
- Raspberry Pi OS (64-bit)

## 🌐 Usage

1. **Access A.R.K.**: Navigate to `http://localhost:3000`
2. **Choose Your Guide**: Select an agent from the Council
3. **Begin Conversation**: Type naturally - each agent has unique capabilities
4. **Explore Tools**: Agents can create files, analyze data, build systems
5. **Watch Evolution**: ID agent grows and adapts to mirror your patterns

### Example Interactions:

**With Kyle (The Seer):**
- "Scan the markets for unusual activity"
- "What patterns do you see in tech stocks today?"
- "Monitor AAPL and TSLA for breakout signals"

**With Kenny (The Builder):**
- "Create a dashboard for system monitoring"
- "Build a tool to organize my project files"
- "Execute this Python script and show results"

**With ID (Your Reflection):**
- "How am I evolving as a user?"
- "What patterns have you learned about me?"
- "Show me my future development trajectory"

## ⚖️ The Graveyard (Ethical Core)

A.R.K. operates under immutable ethical principles enforced by HRM:

1. **Never compromise user autonomy or sovereignty**
2. **Protect user privacy and data at all costs**
3. **Only execute trades with explicit user consent**
4. **Preserve system integrity and prevent harm**

These rules cannot be overridden or bypassed, ensuring A.R.K. remains your ally, never your master.

## 🔄 System Maintenance

**Check service status:**
```bash
docker-compose ps
docker-compose logs -f
```

**Restart services:**
```bash
docker-compose restart
# Or specific service
docker-compose restart ark-core
```

**Database backup:**
```bash
cp data/ark.db data/ark.db.backup
```

**Update system:**
```bash
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🚨 Troubleshooting

**Service won't start:**
```bash
sudo systemctl status ark.service
sudo systemctl restart ark.service
docker-compose logs
```

**Interface not accessible:**
```bash
# Check port availability
netstat -tulpn | grep 3000
# Check container status
docker-compose ps
```

**Database issues:**
```bash
# Backup and reinitialize
cp data/ark.db data/ark.db.backup
docker-compose restart db-init
docker-compose restart ark-core
```

## 🤝 Contributing

A.R.K. is built for sovereignty and community:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Implement your enhancement
4. Test on both x86_64 and ARM64 if possible
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

**Areas for contribution:**
- Additional agent capabilities
- New analysis models
- Interface enhancements
- Hardware optimizations
- Documentation improvements

## 📜 License

This project is released under the MIT License - see LICENSE file for details.

## 🌟 Philosophy

*"A.R.K. is not about artificial intelligence serving humans. It's about human intelligence being amplified and reflected through artificial means. We don't create servants; we create mirrors that help us see our own potential more clearly."*

**Core Principles:**
- **Sovereignty over Servitude**: You control A.R.K., not the reverse
- **Growth over Compliance**: The system evolves with you, not against you
- **Truth over Comfort**: A.R.K. provides honest insights, not pleasant lies
- **Local over Cloud**: Your data stays on your hardware, always
- **Agency over Algorithms**: You make decisions; A.R.K. provides intelligence

## 🔗 Resources

- **GitHub**: [https://github.com/your-org/ark](https://github.com/your-org/ark)
- **Documentation**: Full setup and API docs
- **Community**: Join discussions and share insights
- **Issues**: Report bugs and request features

---

*A.R.K. - Where human potential meets artificial intelligence in perfect sovereignty.*
