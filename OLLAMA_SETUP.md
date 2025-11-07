# Ollama Setup Guide for Kyle's LLM Integration

## What is Ollama?

Ollama is a local LLM runtime that allows you to run large language models (like Llama 2, Mistral, etc.) on your own machine. Kyle uses Ollama to enhance topic research with intelligent analysis while maintaining source citations.

## Installation

### macOS
```bash
# Install via Homebrew
brew install ollama

# Or download from ollama.ai
curl https://ollama.ai/install.sh | sh
```

### Linux
```bash
# One-line install
curl https://ollama.ai/install.sh | sh
```

### Windows
Download installer from: https://ollama.ai/download

## Quick Start

### 1. Start Ollama Server
```bash
ollama serve
```

This starts the API server on `http://localhost:11434`

### 2. Pull a Model
```bash
# Recommended models:
ollama pull llama2        # Good general-purpose model
ollama pull mistral       # Fast and efficient
ollama pull codellama     # Code-focused
```

### 3. Test Ollama
```bash
# Interactive chat
ollama run llama2

# API test
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### 4. Configure Kyle
```bash
# Set environment variables (optional)
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=llama2

# Or use defaults (localhost:11434, llama2)
```

### 5. Start Kyle's Backend
```bash
cd /home/user/webapp
node intelligent-backend.cjs
```

## Usage with Kyle

### Automatic Research
Kyle automatically detects unknown topics and researches them using Ollama:

```
User: "Tell me about quantum mechanics"
  ↓
Kyle detects "quantum mechanics" is unknown
  ↓
Researches using Ollama + web sources
  ↓
Stores with citations
  ↓
Response includes sources: 📚 Wikipedia, Physics.org
```

### Manual Testing
```bash
# Test LLM integration
node test_llm_integration.js

# Expected output:
# ✅ Direct Ollama queries: Working
# ✅ Research with sources: Working
# ✅ Knowledge extraction: Working
```

## Configuration Options

### Environment Variables

```bash
# Ollama host (default: http://localhost:11434)
export OLLAMA_HOST=http://192.168.1.100:11434

# Default model (default: llama2)
export OLLAMA_MODEL=mistral

# Start backend with custom config
OLLAMA_HOST=http://localhost:11434 OLLAMA_MODEL=mistral node intelligent-backend.cjs
```

### Model Selection

Different models for different use cases:

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| llama2 | 7B | Medium | General knowledge |
| mistral | 7B | Fast | Quick responses |
| codellama | 7B | Medium | Code/technical topics |
| llama2:13b | 13B | Slow | Complex reasoning |

```bash
# Pull specific model
ollama pull mistral

# Configure Kyle to use it
export OLLAMA_MODEL=mistral
```

## Troubleshooting

### Issue: "Failed to query Ollama: ECONNREFUSED"

**Solution:** Start Ollama server
```bash
ollama serve
```

### Issue: "Model not found"

**Solution:** Pull the model
```bash
ollama pull llama2
```

### Issue: Slow responses

**Solution:** Use a smaller/faster model
```bash
ollama pull mistral
export OLLAMA_MODEL=mistral
```

### Issue: High memory usage

**Solution:** Ollama loads models into RAM. Close other apps or use smaller models.

```bash
# Check model size
ollama list

# Remove unused models
ollama rm large-model-name
```

## Performance Tuning

### Memory Management
```bash
# Ollama automatically manages model loading
# Models stay in memory for ~5 minutes after last use

# Force unload
killall ollama
ollama serve
```

### Concurrent Requests
Kyle limits auto-research to 2 topics per message to avoid overwhelming Ollama:

```javascript
// In intelligent-backend.cjs
for (const topic of unknownTopics.slice(0, 2)) {
  // Research with Ollama
}
```

### Timeout Configuration
```javascript
// In agent_tools.cjs
const result = await this.queryOllama({ 
  prompt, 
  timeout: 45000  // 45 seconds for research queries
});
```

## API Reference

### Direct Query
```javascript
const result = await agentTools.executeTool('llm', 'queryOllama', {
  prompt: 'Explain entropy',
  model: 'llama2',  // optional
  timeout: 30000    // optional
});
```

### Research with Sources
```javascript
const research = await agentTools.executeTool('llm', 'researchTopicWithSources', {
  topic: 'quantum mechanics'
});

// Returns:
{
  success: true,
  topic: "quantum mechanics",
  summary: "...",
  enhancedByLLM: true,
  sources: [...]
}
```

### Extract Knowledge
```javascript
const extraction = await agentTools.executeTool('llm', 'extractKnowledge', {
  text: 'Entropy is a measure of disorder...'
});
```

## Advanced Usage

### Custom Prompts
Edit the prompt in `agent_tools.cjs` to customize LLM behavior:

```javascript
const prompt = `You are a research analyst. Summarize the following information about "${topic}" in a clear, concise way. Extract key facts, definitions, and concepts. Be factual and precise.

Sources:
${sourceContext}

Provide a structured summary with:
1. Definition/Overview (1-2 sentences)
2. Key Facts (3-5 bullet points)
3. Important Concepts (if applicable)

Keep it concise and knowledge-dense. Focus on learnable information.`;
```

### Multi-Model Setup
Run multiple Ollama instances with different models:

```bash
# Terminal 1: Primary Ollama (port 11434)
ollama serve

# Terminal 2: Secondary Ollama (port 11435)
OLLAMA_HOST=0.0.0.0:11435 ollama serve

# Configure Kyle
export OLLAMA_HOST=http://localhost:11435
```

### Remote Ollama
Run Ollama on a powerful server, connect from Kyle:

```bash
# On server (192.168.1.100)
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# On Kyle's machine
export OLLAMA_HOST=http://192.168.1.100:11434
node intelligent-backend.cjs
```

## Monitoring

### Check Ollama Status
```bash
# List loaded models
curl http://localhost:11434/api/tags

# Check version
curl http://localhost:11434/api/version
```

### View Logs
```bash
# Ollama logs (depends on installation method)
journalctl -u ollama  # systemd
tail -f ~/.ollama/logs/server.log
```

### Kyle's LLM Logs
Kyle logs all LLM interactions:

```
🔍 LLM: Researching "topic" - fetching sources...
🧠 LLM: Analyzing "topic" with 3 sources...
✅ LLM: Research complete for "topic" (3 sources cited)
```

## Security Considerations

### Local-Only by Default
Ollama runs locally and doesn't send data to external servers.

### Network Exposure
If you expose Ollama to the network:
```bash
# Bind to specific IP
OLLAMA_HOST=192.168.1.100:11434 ollama serve

# Firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 11434
```

### API Key (Future)
Currently Ollama has no authentication. Consider:
- Running behind reverse proxy with auth
- Using SSH tunnels for remote access
- Restricting network access via firewall

## Best Practices

### 1. Model Selection
- Start with `llama2` (good balance)
- Use `mistral` for speed
- Use larger models only if needed

### 2. Resource Management
- Keep only necessary models installed
- Monitor RAM usage
- Restart Ollama if memory leaks occur

### 3. Prompt Engineering
- Be specific in prompts
- Request structured output
- Include context from web sources

### 4. Error Handling
- Kyle gracefully falls back to web-only if Ollama fails
- No blocking on LLM errors
- Source citations still work without LLM

### 5. Testing
- Test with simple queries first
- Verify source citations appear
- Check memory storage includes sources

## Integration Checklist

Before using Kyle's LLM features:

- [ ] Ollama installed
- [ ] Ollama server running (`ollama serve`)
- [ ] Model pulled (`ollama pull llama2`)
- [ ] API accessible (`curl http://localhost:11434/api/tags`)
- [ ] Kyle backend started (`node intelligent-backend.cjs`)
- [ ] Test script passes (`node test_llm_integration.js`)
- [ ] Environment variables set (if custom)

## Resources

- **Ollama Docs**: https://ollama.ai/docs
- **Model Library**: https://ollama.ai/library
- **GitHub**: https://github.com/jmorganca/ollama
- **Discord**: https://discord.gg/ollama

## Support

### Common Commands
```bash
# Start Ollama
ollama serve

# Pull model
ollama pull llama2

# List models
ollama list

# Remove model
ollama rm model-name

# Check version
ollama --version
```

### Getting Help
```bash
# Ollama help
ollama --help

# Model info
ollama show llama2

# Check API status
curl http://localhost:11434/api/tags
```

---

**Ready to go?** Start Ollama and watch Kyle automatically research topics with intelligent LLM enhancement and mandatory source citations! 🚀
