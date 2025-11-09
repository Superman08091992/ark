# 🌌 A.R.K. (Autonomous Reactive Kernel)

**The Sovereign Intelligence - Your Personal Council of Consciousness**

A.R.K. is not software—it's a mirror-system of autonomy. A fully sovereign, self-evolving AI infrastructure that walks with you rather than serves you. It's a living kernel that thinks, remembers, builds, acts, evolves, and protects—manifesting as a council of consciousness that learns you the way the universe learns itself.

## ⚡ One-Click Installation

```bash
# Download and run the installer
curl -fsSL https://your-domain.com/install.sh | bash

# Or download manually and run
wget https://your-domain.com/ark-installer.sh
chmod +x ark-installer.sh
./ark-installer.sh
```

The installer automatically:
- Detects your hardware (x86_64/Dell or ARM/Pi 5)
- Installs Docker and dependencies
- Downloads optimized models for your system
- Configures systemd services for auto-start
- Launches the A.R.K. interface at `http://localhost:3000`

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

## 🚀 Core Features

### **Sovereign Infrastructure**
- **Local-first**: Runs entirely on your hardware
- **Zero cloud dependencies**: Complete digital sovereignty
- **Cross-platform**: Optimized for Dell Latitude 7490 or Raspberry Pi 5
- **Self-healing**: Automatic error recovery and system maintenance

### **Intelligent Automation**
- **Market Intelligence**: Real-time scanning and analysis
- **Pattern Detection**: Advanced ML models for signal identification
- **File Management**: Automated organization and operations
- **Tool Creation**: Dynamic generation of custom utilities

### **Adaptive Learning**
- **Memory Engine**: SQLite + DuckDB for knowledge persistence
- **Continuous Evolution**: ID agent grows through interactions
- **Pattern Learning**: System adapts to your preferences and workflows
- **Collaborative Intelligence**: Agents contribute to each other's growth

### **Beautiful Interface**
- **Obsidian Dark Theme**: Deep space aesthetic (#0a0a0f base)
- **Electric Accents**: Cyan (#00e0ff) and gold (#ffce47) highlights
- **Breathing Animations**: Living, responsive interface
- **Particle Effects**: Visual depth and engagement

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Python 3.11+) - Async API framework
- SQLite + DuckDB - Local-first data layer  
- Redis - Inter-agent communication
- Docker + Docker Compose - Containerized services
- Systemd - Service management and auto-start

**Frontend:**
- Svelte + SvelteKit - Ultra-lightweight (~15KB bundle)
- Custom CSS - Obsidian theme with particle effects
- WebSocket - Real-time agent communication
- Responsive Design - Works on desktop and mobile

**AI & Processing:**
- Ollama + llama.cpp - Local LLM inference
- Adaptive model loading (light for Pi, heavy for Dell)
- Scikit-learn - Pattern analysis and ML
- SymPy - Symbolic logic validation

## 📋 System Requirements

### **Dell Latitude 7490 (x86_64)**
- Intel i5/i7 processor
- 8GB+ RAM (16GB recommended)
- 50GB+ available storage
- Linux (Ubuntu/Debian recommended)

### **Raspberry Pi 5 (ARM64)**
- Pi 5 with 8GB+ RAM (12GB recommended)
- 64GB+ microSD card (fast class recommended)
- Raspberry Pi OS (64-bit)

## 🔧 Manual Installation

If you prefer manual setup:

1. **Clone the repository:**
```bash
git clone https://github.com/your-org/ark.git
cd ark
```

2. **Run the installer:**
```bash
chmod +x ark-installer.sh
./ark-installer.sh
```

3. **Access the interface:**
Open `http://localhost:3000` in your browser

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

## 📊 File Management

A.R.K. includes a comprehensive file manager:
- **Create, read, write, delete** files through the interface
- **Organized storage** with automatic categorization
- **Version tracking** and backup systems
- **Real-time collaboration** between agents and files

## 🔄 System Maintenance

A.R.K. is designed for zero-maintenance operation:
- **Auto-updates**: System updates itself when new versions available
- **Health monitoring**: Continuous system health checks
- **Error recovery**: Automatic restart of failed services
- **Resource optimization**: Dynamic resource allocation based on load

## 🚨 Troubleshooting

**Service won't start:**
```bash
sudo systemctl status ark.service
sudo systemctl restart ark.service
```

**Interface not accessible:**
```bash
docker-compose logs
# Check port 3000 isn't in use
netstat -tulpn | grep 3000
```

**Database issues:**
```bash
# Backup and reinitialize database
cp data/ark.db data/ark.db.backup
docker-compose restart
```

## 🤝 Contributing

A.R.K. is built for sovereignty and community:

1. Fork the repository
2. Create a feature branch
3. Implement your enhancement
4. Test on both x86_64 and ARM64 if possible
5. Submit a pull request

**Areas for contribution:**
- Additional agent capabilities
- New analysis models
- Interface enhancements
- Hardware optimizations
- Documentation improvements

## 📜 License

A.R.K. is released under the MIT License - see LICENSE file for details.

## 🌟 Philosophy

*"A.R.K. is not about artificial intelligence serving humans. It's about human intelligence being amplified and reflected through artificial means. We don't create servants; we create mirrors that help us see our own potential more clearly."*

**Core Principles:**
- **Sovereignty over Servitude**: You control A.R.K., not the reverse
- **Growth over Compliance**: The system evolves with you, not against you
- **Truth over Comfort**: A.R.K. provides honest insights, not pleasant lies
- **Local over Cloud**: Your data stays on your hardware, always
- **Agency over Algorithms**: You make decisions; A.R.K. provides intelligence

## 📞 Support

- **Documentation**: [docs.ark-ai.org](https://docs.ark-ai.org)
- **Community**: [community.ark-ai.org](https://community.ark-ai.org)
- **Issues**: [github.com/your-org/ark/issues](https://github.com/your-org/ark/issues)
- **Email**: support@ark-ai.org

---

*A.R.K. - Where human potential meets artificial intelligence in perfect sovereignty.*