# Intra-Agent Hierarchical Reasoning

## Overview

This document describes ARK's **intra-agent hierarchical reasoning** system, which implements 5-level cognitive processing **within each individual agent** (not just between agents via HRM).

**Key Distinction:**
- **Inter-agent reasoning**: HRM orchestrates consultation between agents (Kyle, Joey, Kenny, etc.)
- **Intra-agent reasoning**: Each agent processes information hierarchically through 5 cognitive levels

With **no speed constraints** (per user requirement: "Ms are no problem. Speed isnt a requirement"), we prioritize **comprehensive reasoning quality** over latency.

---

## Architecture

### 5 Cognitive Levels (Per Agent)

Each agent processes information through these hierarchical levels:

```
┌─────────────────────────────────────────────────────────────────────┐
│ Level 1: PERCEPTION                                                 │
│ ──────────────────────────────────────────────────────────────────  │
│ • Raw input processing                                              │
│ • Feature extraction                                                │
│ • Alternative interpretations                                       │
│ • Output: Structured features                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Level 2: ANALYSIS                                                   │
│ ──────────────────────────────────────────────────────────────────  │
│ • Pattern detection                                                 │
│ • Structural analysis                                               │
│ • Anomaly detection                                                 │
│ • Output: Patterns, structure, anomalies                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Level 3: SYNTHESIS                                                  │
│ ──────────────────────────────────────────────────────────────────  │
│ • Context integration                                               │
│ • Narrative construction                                            │
│ • Implication identification                                        │
│ • Output: Integrated understanding                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Level 4: EVALUATION                                                 │
│ ──────────────────────────────────────────────────────────────────  │
│ • Quality assessment                                                │
│ • Risk identification                                               │
│ • Alternative comparison                                            │
│ • Output: Quality score, risks, uncertainty                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Level 5: DECISION                                                   │
│ ──────────────────────────────────────────────────────────────────  │
│ • Option generation                                                 │
│ • Best option selection                                             │
│ • Consequence analysis                                              │
│ • Output: Final decision with rationale                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Reasoning Depth Modes

```python
class ReasoningDepth(Enum):
    SHALLOW = 1     # Quick pass, minimal branching (~50ms)
    MODERATE = 3    # Balanced reasoning with exploration (~150ms)
    DEEP = 5        # Full comprehensive reasoning (default, ~300ms)
    EXHAUSTIVE = 10 # Explore every possibility (~1000ms+)
```

**Note:** With no speed requirements, DEEP is the default. EXHAUSTIVE can be used for research/analysis tasks.

### Tree-of-Selfs

Each cognitive level can **branch** to explore alternative interpretations:

```
Level 1 (Perception)
├── Main: Conservative interpretation
├── Alt 1: Optimistic interpretation
└── Alt 2: Neutral/analytical interpretation

Level 2 (Analysis)
├── Main: Dominant pattern focus
├── Alt 1: Alternative pattern framework
└── Alt 2: Multi-pattern integration

... (continues for all levels)
```

This creates a **thought tree** where each branch represents a different reasoning path.

---

## Implementation Status

### ✅ Completed (Phase 1)

1. **Core Framework** (`reasoning/intra_agent_reasoner.py`)
   - Base `IntraAgentReasoner` class with 5-level processing
   - ReasoningDepth configuration
   - Tree-of-Selfs construction
   - Statistics tracking

2. **Kyle-Specific Reasoner** (`reasoning/kyle_reasoner.py`)
   - Market signal feature extraction
   - Technical pattern detection (breakout, reversal, consolidation, momentum)
   - Anomaly detection (extreme moves, volume divergence)
   - Risk assessment (reversal risk, volatility risk)
   - Decision option generation (strong/moderate/weak/no signal)

3. **Kyle Integration** (`agents/kyle.py`)
   - Uses `KyleReasoner` for all signal analysis
   - Configurable reasoning depth (SHALLOW/MODERATE/DEEP/EXHAUSTIVE)
   - Reasoning statistics tracking
   - Mode switching API

4. **Test Coverage** (`tests/test_kyle_intra_reasoning.py`)
   - 14 unit tests for Kyle reasoner
   - Feature extraction tests
   - Pattern detection tests (breakout, reversal, consolidation)
   - Anomaly detection tests (extreme price, volume divergence)
   - Full reasoning chain tests (SHALLOW, DEEP)
   - Thought tree construction tests

5. **Demonstration** (`examples/kyle_intra_reasoning_demo.py`)
   - 5 comprehensive scenarios
   - Cognitive path visualization
   - Thought tree display
   - Depth comparison analysis

### 🚧 Pending (Phase 2+)

1. **Other Agents**
   - Joey reasoner (context retrieval, memory analysis)
   - Kenny reasoner (execution planning, risk management)
   - Aletheia reasoner (truth verification, fact-checking)
   - ID reasoner (authentication, identity validation)

2. **Advanced Features**
   - Psychological profiling (behavioral consistency analysis)
   - Inter-agent consensus mechanisms (voting, weighted decisions)
   - Conflict resolution protocols
   - Adaptive depth selection (learn optimal depth per task)

3. **Documentation**
   - Per-agent reasoning guides
   - Best practices document
   - Performance analysis (with speed not a concern)

---

## Usage

### Basic Usage (Kyle Example)

```python
from reasoning.kyle_reasoner import KyleReasoner
from reasoning.intra_agent_reasoner import ReasoningDepth

# Initialize reasoner
reasoner = KyleReasoner(
    default_depth=ReasoningDepth.DEEP,
    enable_tree_of_selfs=True,
    max_branches_per_level=5
)

# Prepare signal data
signal_data = {
    'symbol': 'TSLA',
    'price_change': 0.05,
    'volume_surge': 2.0,
    'sentiment_score': 0.7,
    'timestamp': datetime.now().isoformat()
}

context = {
    'agent_role': 'market_scanner',
    'threshold': 0.7,
    'historical_patterns': [],
    'market_sentiment': 'bullish'
}

# Execute reasoning
decision = await reasoner.reason(
    input_data=signal_data,
    depth=ReasoningDepth.DEEP,
    context=context
)

# Access results
print(f"Confidence: {decision.confidence}")
print(f"Final Decision: {decision.final_decision}")
print(f"Alternatives Considered: {decision.alternatives_considered}")
print(f"Processing Time: {decision.total_duration_ms}ms")
```

### Agent Integration (Kyle)

```python
from agents.kyle import KyleAgent

kyle = KyleAgent()

# Set reasoning mode
await kyle.set_reasoning_mode('DEEP')

# Perform market scan (uses hierarchical reasoning automatically)
result = await kyle.tool_scan_markets()

# Each scan result includes reasoning metadata
for scan in result['data']:
    print(f"Symbol: {scan['symbol']}")
    print(f"Signal Strength: {scan['signal_strength']}")
    print(f"Reasoning Depth: {scan['reasoning']['depth']}")
    print(f"Confidence: {scan['reasoning']['confidence']}")
    print(f"Alternatives: {scan['reasoning']['alternatives_considered']}")
    print(f"Cognitive Path: {scan['reasoning']['cognitive_path']}")

# Get reasoning statistics
stats = kyle.get_reasoning_statistics()
print(f"Total Decisions: {stats['total_decisions']}")
print(f"Avg Time: {stats['avg_reasoning_time_ms']}ms")
```

---

## Kyle-Specific Features

### Pattern Detection

Kyle detects these technical patterns:

1. **Breakout** - Significant price move with high volume
   - Confidence based on price change + volume surge
   - Direction: upward or downward
   - Strength: strong (volume >2x) or moderate

2. **Momentum** - Price move aligned with sentiment
   - Checks price-sentiment alignment
   - Confidence higher when aligned
   - Detects divergence (bearish signal)

3. **Reversal** - Price-sentiment divergence
   - Price up but sentiment down (or vice versa)
   - Warns of potential trend reversal
   - Marked as high risk

4. **Consolidation** - Low volatility, low volume
   - Indicates accumulation or distribution phase
   - Confidence based on stability

5. **Volume Anomaly** - Extreme volume surge
   - May indicate institutional activity
   - Confidence based on volume magnitude

### Anomaly Detection

Kyle identifies:

1. **Extreme Price Movement** - >10% move
2. **Volume-Price Divergence** - High volume, low price change
3. **Pattern Inconsistency** - Current pattern differs from historical success

### Risk Assessment

Kyle evaluates:

1. **Reversal Risk** - Price-sentiment divergence detected
2. **Volatility Risk** - High market volatility
3. **Complexity Risk** - Too many conflicting signals
4. **Historical Performance Risk** - Pattern has poor track record

---

## Performance Characteristics

### Latency (With No Speed Constraints)

| Depth | Avg Time | Alternatives | Tree Size |
|-------|----------|--------------|-----------|
| SHALLOW | ~50ms | 5-8 | ~10 branches |
| MODERATE | ~150ms | 10-15 | ~25 branches |
| DEEP | ~300ms | 15-20 | ~40 branches |
| EXHAUSTIVE | ~1000ms+ | 30-50 | ~100+ branches |

**Important:** These timings are NOT a concern per user requirement. Quality is paramount.

### Confidence Scoring

Confidence is calculated through the cognitive chain:

```
L1 Perception: Base confidence (0.8)
      ↓
L2 Analysis: Adjusted by pattern clarity (±0.1)
      ↓
L3 Synthesis: Adjusted by context quality (±0.1)
      ↓
L4 Evaluation: Adjusted by risks (-0.1 per risk)
      ↓
L5 Decision: Final confidence * commitment level
```

### Memory Usage

- Each decision stores full cognitive history
- Thought tree can grow large in EXHAUSTIVE mode
- History maintained for learning/analysis

---

## Testing

### Run Tests

```bash
cd /home/user/webapp
python -m pytest tests/test_kyle_intra_reasoning.py -v
```

### Test Coverage

- ✅ Reasoner initialization
- ✅ Feature extraction
- ✅ Pattern detection (all types)
- ✅ Anomaly detection (all types)
- ✅ Full reasoning chain (SHALLOW, DEEP)
- ✅ Signal detection (strong, weak, none)
- ✅ Risk assessment
- ✅ Thought tree construction
- ✅ Reasoning consistency

### Run Demo

```bash
cd /home/user/webapp
python examples/kyle_intra_reasoning_demo.py
```

---

## Extending to Other Agents

### Template for New Agent Reasoner

```python
from reasoning.intra_agent_reasoner import IntraAgentReasoner

class MyAgentReasoner(IntraAgentReasoner):
    def __init__(self, **kwargs):
        super().__init__(agent_name="MyAgent", **kwargs)
    
    # Override domain-specific methods
    def _extract_features(self, input_data):
        """Extract agent-specific features"""
        # Your logic here
        pass
    
    def _detect_patterns(self, features):
        """Detect agent-specific patterns"""
        # Your logic here
        pass
    
    # ... override other methods as needed
```

### Agent Integration Steps

1. Create `reasoning/{agent}_reasoner.py`
2. Extend `IntraAgentReasoner`
3. Implement domain-specific logic
4. Integrate into agent class
5. Add tests
6. Update documentation

---

## Configuration

### Per-Agent Settings

Each agent can configure:

```python
reasoner = MyAgentReasoner(
    default_depth=ReasoningDepth.DEEP,  # Default reasoning depth
    enable_tree_of_selfs=True,          # Enable branching exploration
    max_branches_per_level=5            # Max branches per level
)
```

### Runtime Adjustment

```python
# Force specific depth for one decision
decision = await reasoner.reason(
    input_data=data,
    depth=ReasoningDepth.EXHAUSTIVE,  # Override default
    context=context
)
```

---

## Best Practices

1. **Use DEEP by default** - With no speed constraints, maximize quality
2. **Enable Tree-of-Selfs** - Explore alternatives for better decisions
3. **Provide rich context** - More context = better synthesis
4. **Monitor statistics** - Track decision quality over time
5. **Review thought trees** - Understand agent reasoning process
6. **Adjust depth per task** - Use EXHAUSTIVE for critical decisions

---

## Troubleshooting

### Low Confidence Scores

- Check input data quality
- Verify context is comprehensive
- Review risks identified (may be penalizing confidence)
- Consider pattern inconsistency with historical data

### High Processing Time

- This is expected and acceptable (speed not a requirement)
- EXHAUSTIVE mode can take >1 second
- Consider depth reduction only if absolutely necessary

### Inconsistent Decisions

- Check if input data is truly identical
- Review alternative branches explored
- Verify context consistency

---

## Future Enhancements

1. **Adaptive Depth Learning** - Agent learns optimal depth per scenario
2. **Cross-Agent Learning** - Agents share reasoning insights
3. **Psychological Modeling** - Agent personality influences reasoning
4. **Explainability Dashboard** - Visualize thought trees in UI
5. **Reasoning Replay** - Review historical decisions with full context

---

## References

- `reasoning/intra_agent_reasoner.py` - Base framework
- `reasoning/kyle_reasoner.py` - Kyle implementation
- `agents/kyle.py` - Kyle integration
- `tests/test_kyle_intra_reasoning.py` - Test suite
- `examples/kyle_intra_reasoning_demo.py` - Demonstration
- `HIERARCHICAL_REASONING.md` - Inter-agent reasoning (HRM)

---

## Summary

Kyle now reasons hierarchically through 5 cognitive levels:
1. **Perception** → Extract features
2. **Analysis** → Detect patterns
3. **Synthesis** → Integrate context
4. **Evaluation** → Assess quality & risks
5. **Decision** → Select best option

With **no speed constraints**, Kyle explores comprehensive thought trees and alternative reasoning paths for **maximum signal detection quality**.

Next: Extend to Joey, Kenny, Aletheia, and ID agents.
