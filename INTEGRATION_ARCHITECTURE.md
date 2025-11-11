# ARK Integration Architecture

## Overview

This document describes the **Layered Cognitive Architecture** that integrates the Node.js intelligent-backend.cjs with Python agent reasoning chains through clean async interfaces.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Node.js Layer                             │
│         intelligent-backend.cjs (Event Bus & Policy Gateway) │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Layer                               │
│              reasoning_api.py (Port 8101)                    │
│  • REST endpoints for agent reasoning                        │
│  • WebSocket for streaming traces                            │
│  • Memory sync orchestration                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ↓                       ↓
┌──────────────────┐    ┌──────────────────┐
│ ReasoningEngine  │    │  MemorySyncManager│
│  5-Stage Pipeline│    │  SQLite + Redis   │
│  • Perceive      │    │  • Persistence    │
│  • Analyze       │    │  • Pub/Sub        │
│  • Hypothesize   │    │  • Query API      │
│  • Validate      │    └──────────────────┘
│  • Reflect       │
└────────┬─────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│            Agent Reasoners (Specialized)                     │
│  • KyleReasoner   - Market signal analysis                   │
│  • JoeyReasoner   - Statistical patterns                     │
│  • KennyReasoner  - Execution planning                       │
│  • AletheiaReasoner - Truth verification                     │
│  • IDReasoner     - Identity authentication                  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. ReasoningEngine Base Class

**Location**: `reasoning/reasoning_engine.py`

**Purpose**: Provides a clean 5-stage cognitive pipeline that wraps the IntraAgentReasoner.

**5-Stage Pipeline**:
1. **Perceive** - Raw input processing and feature extraction
2. **Analyze** - Pattern detection and structural analysis  
3. **Hypothesize** - Generate alternative solutions/interpretations
4. **Validate** - Test hypotheses against evidence and constraints
5. **Reflect** - Meta-cognitive assessment and confidence scoring

**Usage**:
```python
engine = AgentReasoningEngine(
    agent_name="kyle",
    intra_reasoner=kyle.intra_reasoner,
    agent_instance=kyle,
    default_depth=ReasoningDepth.DEEP
)

result: ReasoningResult = await engine.reason(
    query="Analyze market conditions",
    context={"market": "crypto"},
    depth=ReasoningDepth.DEEP
)
```

### 2. Memory Synchronization Layer

**Location**: `reasoning/memory_sync.py`

**Components**:
- **ReasoningMemoryDB** - SQLite-based persistent storage for reasoning traces
- **ReasoningPubSub** - Redis-based pub/sub for live reasoning updates
- **MemorySyncManager** - Unified interface combining both

**Features**:
- Persistent logging of all reasoning sessions
- Real-time pub/sub for reasoning events (start, stage_complete, complete)
- Query API for historical reasoning analysis
- Agent performance statistics

**Database Schema**:
```sql
-- Main reasoning sessions
CREATE TABLE reasoning_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    agent_name TEXT,
    query TEXT,
    final_output TEXT,
    overall_confidence REAL,
    total_duration_ms REAL,
    timestamp TEXT,
    metadata TEXT
);

-- Reasoning stages (one-to-many with sessions)
CREATE TABLE reasoning_stages (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    stage_name TEXT,
    stage_order INTEGER,
    input_data TEXT,
    output_data TEXT,
    confidence REAL,
    duration_ms REAL,
    traces TEXT,
    metadata TEXT
);
```

### 3. FastAPI Reasoning API

**Location**: `reasoning_api.py`

**Port**: 8101

**Key Endpoints**:

#### Agent Reasoning
```http
POST /agent/{agent_name}/reason
{
  "query": "string",
  "context": {},
  "depth": "DEEP",
  "stream": false
}

Response: {
  "agent": "kyle",
  "query": "...",
  "final_output": {},
  "overall_confidence": 0.85,
  "stages": [...],
  "total_duration_ms": 1234.5,
  "timestamp": "2025-11-11T...",
  "session_id": "kyle_2025-11-11T..."
}
```

#### Memory Query
```http
GET /reasoning/sessions?agent_name=kyle&min_confidence=0.7&limit=100

Response: {
  "sessions": [...],
  "count": 42,
  "filters": {...}
}

GET /reasoning/session/{session_id}
```

#### Statistics
```http
GET /statistics
GET /agent/{agent_name}/statistics

Response: {
  "agent": "kyle",
  "runtime": {
    "total_inferences": 123,
    "avg_confidence": 0.82,
    ...
  },
  "historical": {
    "total_sessions": 500,
    "avg_confidence": 0.81,
    "avg_duration_ms": 1250.3,
    ...
  }
}
```

#### HRM Orchestration
```http
POST /orchestrate
{
  "query": "Complex task requiring multiple agents",
  "agents": ["kyle", "joey", "kenny"],
  "mode": "parallel"
}
```

#### WebSocket Streaming
```
ws://localhost:8101/ws/reasoning/{agent_name}

Send: {"query": "..."}

Receive: 
  {"type": "ack", "agent": "kyle", ...}
  {"type": "processing", "stage": "perceive", ...}
  {"type": "processing", "stage": "analyze", ...}
  {"type": "result", "final_output": {...}, ...}
```

### 4. Agent Integration

Each agent now has:
1. **IntraAgentReasoner** - Specialized reasoner (e.g., KyleReasoner)
2. **ReasoningEngine** - Wraps the reasoner with 5-stage pipeline
3. **Reasoning Methods** - Updated to use hierarchical reasoning

**Example** (`agents/kyle.py`):
```python
class KyleAgent:
    def __init__(self):
        self.intra_reasoner = KyleReasoner(
            default_depth=ReasoningDepth.DEEP,
            enable_tree_of_selfs=True,
            max_branches_per_level=5
        )
    
    async def tool_scan_markets(self):
        decision = await self.intra_reasoner.reason(
            input_data=raw_signal_data,
            depth=self.reasoning_depth,
            context=reasoning_context
        )
        return self._build_output(decision)
```

## Node.js Integration

### intelligent-backend.cjs Updates Needed

**1. Add HTTP Client for Python API**:
```javascript
const axios = require('axios');

const REASONING_API_URL = 'http://localhost:8101';

async function callAgentReasoning(agentName, query, context = {}, depth = 'DEEP') {
  const response = await axios.post(`${REASONING_API_URL}/agent/${agentName}/reason`, {
    query: query,
    context: context,
    depth: depth
  });
  return response.data;
}
```

**2. Add Agent Routing Logic**:
```javascript
async function routeToAgent(userMessage, intentClassification) {
  // Intent classification determines which agent(s) to call
  const agentName = determineAgent(intentClassification);
  
  // Call Python reasoning API
  const reasoningResult = await callAgentReasoning(
    agentName,
    userMessage,
    { intent: intentClassification },
    'DEEP'
  );
  
  // Extract final output and return to user
  return formatResponseForUser(reasoningResult);
}
```

**3. Add WebSocket Client for Streaming**:
```javascript
const WebSocket = require('ws');

function streamAgentReasoning(agentName, query, onStageCallback) {
  const ws = new WebSocket(`ws://localhost:8101/ws/reasoning/${agentName}`);
  
  ws.on('open', () => {
    ws.send(JSON.stringify({ query: query }));
  });
  
  ws.on('message', (data) => {
    const message = JSON.parse(data);
    onStageCallback(message);
  });
}
```

**4. Add Memory Query Functions**:
```javascript
async function getReasoningHistory(agentName, minConfidence = 0.5, limit = 100) {
  const response = await axios.get(`${REASONING_API_URL}/reasoning/sessions`, {
    params: {
      agent_name: agentName,
      min_confidence: minConfidence,
      limit: limit
    }
  });
  return response.data.sessions;
}

async function getAgentStatistics(agentName) {
  const response = await axios.get(`${REASONING_API_URL}/agent/${agentName}/statistics`);
  return response.data;
}
```

## Deployment

### Development Mode

**Terminal 1 - Python Reasoning API**:
```bash
cd /home/user/webapp
python reasoning_api.py
# Runs on http://0.0.0.0:8101
```

**Terminal 2 - Node.js Backend** (after updates):
```bash
cd /home/user/webapp
node intelligent-backend.cjs
# Calls Python API at http://localhost:8101
```

**Terminal 3 - Redis (for pub/sub)**:
```bash
redis-server
# Optional - pub/sub features disabled if not available
```

### Production Mode (Docker Compose)

```yaml
version: '3.8'

services:
  reasoning-api:
    build: .
    ports:
      - "8101:8101"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./data:/app/data
  
  intelligent-backend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - REASONING_API_URL=http://reasoning-api:8101
    depends_on:
      - reasoning-api
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## Testing

### Test Agent Reasoning
```bash
curl -X POST http://localhost:8101/agent/kyle/reason \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze current market conditions",
    "context": {"market": "crypto"},
    "depth": "DEEP"
  }'
```

### Test Memory Query
```bash
curl http://localhost:8101/reasoning/sessions?agent_name=kyle&limit=10
```

### Test Statistics
```bash
curl http://localhost:8101/agent/kyle/statistics
```

### Test WebSocket (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8101/ws/reasoning/kyle');

ws.onopen = () => {
  ws.send(JSON.stringify({ query: "Analyze market" }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Reasoning stage:', data);
};
```

## Benefits

1. **Clean Separation of Concerns**
   - Node.js: Event bus, policy gateway, user interaction
   - Python: Complex reasoning, ML/AI processing, cognitive pipeline

2. **Scalability**
   - Python reasoning API can scale independently
   - Multiple reasoning workers behind load balancer
   - Redis pub/sub for distributed events

3. **Observability**
   - All reasoning traces logged to SQLite
   - Real-time monitoring via Redis pub/sub
   - Historical analysis and performance tracking

4. **Flexibility**
   - Easy to add new agents
   - Reasoning depth adjustable per request
   - Context and metadata fully customizable

5. **Maintainability**
   - Clear interfaces between layers
   - Comprehensive logging and error handling
   - Well-documented API endpoints

## Next Steps

1. ✅ **ReasoningEngine Base Class** - COMPLETE
2. ✅ **Memory Synchronization (SQLite + Redis)** - COMPLETE
3. ✅ **FastAPI Reasoning API** - COMPLETE
4. ⏳ **Modify intelligent-backend.cjs** - TODO
5. ⏳ **WebSocket Enhancement** - TODO (currently simplified)
6. ⏳ **Integration Testing** - TODO
7. ⏳ **Docker Compose Setup** - TODO
8. ⏳ **Token Authentication** - TODO (security layer)

## Files Modified/Created

### New Files
- `reasoning/reasoning_engine.py` - ReasoningEngine base class
- `reasoning/memory_sync.py` - Memory synchronization layer
- `reasoning_api.py` - FastAPI server (enhanced)
- `INTEGRATION_ARCHITECTURE.md` - This document

### Existing Files Enhanced
- All agent reasoners already implemented:
  - `reasoning/kyle_reasoner.py`
  - `reasoning/joey_reasoner.py`
  - `reasoning/kenny_reasoner.py`
  - `reasoning/aletheia_reasoner.py`
  - `reasoning/id_reasoner.py`
- All agents already integrated:
  - `agents/kyle.py`
  - `agents/joey.py`
  - `agents/kenny.py`
  - `agents/aletheia.py`
  - `agents/id.py`

## Questions?

See also:
- `INTRA_AGENT_REASONING.md` - Detailed intra-agent reasoning documentation
- `examples/kyle_intra_reasoning_demo.py` - Interactive demonstration
- `tests/test_kyle_intra_reasoning.py` - Test suite
