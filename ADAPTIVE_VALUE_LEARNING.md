# Adaptive Value Learning System

## 🎯 Problem Solved

**You said**: _"He seems to be working but who determines meaningful and valuable though. There isnt a real base value to value"_

**Solution**: Kyle now learns what YOU value based on YOUR behavior, not hardcoded assumptions.

## 🧠 How Kyle Learns Value

### 1. USER-DRIVEN SIGNALS (Highest Priority)

Kyle prioritizes **your explicit signals**:

| Signal | Importance Boost | Examples |
|--------|-----------------|----------|
| "Remember this" | +35 | "Remember this: server runs on port 8000" |
| "Important/Critical" | +35 | "This is critical for deployment" |
| "Don't forget" | +35 | "Don't forget to backup database" |
| User asks to recall | +25 | "What do you remember about X?" |
| Questions | +20 | "How do I configure Twilio?" |

**Test Result**:
```bash
Message: "Remember this: The production server runs on AWS..."
Importance Score: 100/100 ✅ STORED
```

### 2. CONTENT SIGNALS (Medium Priority)

Kyle analyzes message content for value indicators:

| Feature | Score | Why It Matters |
|---------|-------|----------------|
| Contains numbers | +8 | Data points are usually important |
| Contains dates | +10 | Temporal information is valuable |
| Contains URLs | +12 | References are actionable |
| Has proper names | +8 | People, products, companies matter |
| Has instructions | +15 | Actionable procedures = high value |
| Multiple topics | +6 each | Cross-references = interconnected knowledge |
| Length > 100 chars | +10 | More context = more useful |
| Entities (capitalized words) | +3 each | Named things are usually significant |

**Example**:
```
Message: "Deploy to AWS EC2 using https://docs.aws.com on January 15th"
Score: 30 (base) + 35 (explicit "deploy") + 8 (numbers) + 10 (date) + 12 (URL) = 95 ✅
```

### 3. BEHAVIORAL LEARNING (Adaptive)

Kyle tracks YOUR actual usage patterns:

#### Auto-Boost from Retrievals
- Every time you recall a memory → +1 retrieval count
- After **3 retrievals** → Auto-boost +10 importance
- After **6 retrievals** → Auto-boost +10 more (total +20)
- **Max boost**: +30 from frequent use

**Test Result**:
```bash
User asks about AWS (retrieval 1) → 📖 Count: 1
User asks about AWS (retrieval 2) → 📖 Count: 2  
User asks about AWS (retrieval 3) → ⬆️ Auto-boosted +10! (reason: frequent_retrieval)
```

#### Manual Feedback API
You can explicitly tell Kyle what matters:

```bash
# Boost importance (you value this)
POST /api/memory/boost
{
  "memoryId": "kyle_1762542172421_ktvj7tr0j",
  "reason": "user_values_this"
}
Response: Importance 100 → 110 (capped at 100, but tracked)

# Demote importance (you don't care about this)
POST /api/memory/demote
{
  "memoryId": "kyle_xyz",
  "reason": "user_ignores_this"
}
Response: Importance 75 → 65
```

### 4. QUALITY FILTERS (Penalties)

Kyle penalizes low-value patterns:

| Pattern | Penalty | Examples |
|---------|---------|----------|
| Pure greeting | -30 | "hi", "hello" |
| Pure thanks | -30 | "thanks", "thx" |
| Pure goodbye | -30 | "bye", "cya" |
| Too short (< 15 chars) | -20 | "ok", "sure" |
| Generic commands | -15 | "show me your status" |

**Test Result**:
```bash
Message: "The weather is nice today"
Importance Score: 33/100 ❌ FILTERED (< 55 threshold)
```

## 📊 Scoring Comparison

### Old System (Hardcoded)
```javascript
// Financial terms = valuable? Not for everyone!
if (message.includes('stock' || 'portfolio')) score += 20;
if (message.includes('algorithm' || 'pattern')) score += 15;
```

**Problem**: Assumes domain (finance/tech), ignores user intent

### New System (Adaptive)
```javascript
// USER SIGNALS (what you explicitly say matters)
if (message.includes('remember' || 'important')) score += 35;

// USER BEHAVIOR (what you actually use)
if (retrievalCount > 3) boostImportance(memoryId, +10);

// CONTENT (universal indicators)
if (hasNumbers || hasDates || hasUrls) score += points;
```

**Benefit**: Works for ANY domain, learns from YOUR usage

## 🔄 Learning Loop

```
User sends message
      ↓
Kyle calculates importance
  - Explicit signals (+35)
  - Content analysis (+variable)
  - Current behavior data
      ↓
IF important enough (≥55):
  ✅ Store to memory
      ↓
User recalls memory
      ↓
Kyle tracks retrieval (+1 count)
      ↓
After 3 retrievals:
  ⬆️ Auto-boost importance (+10)
      ↓
Future similar messages 
score higher automatically
```

## 🧪 Test Results

### Test 1: Explicit Signal ✅
```
Input: "Remember this: AWS EC2 i-1234567890"
Importance: 100/100
Result: ✅ STORED
Reason: User said "remember this" (+35 explicit signal)
```

### Test 2: Casual Chat ❌
```
Input: "The weather is nice today"
Importance: 33/100
Result: ❌ FILTERED
Reason: No value signals, generic content
```

### Test 3: User Feedback ✅
```
Action: POST /api/memory/boost with memory ID
Result: ⬆️ Importance 100 → 110 (capped at 100)
Log: "Kyle: Boosted memory kyle_xyz importance to 100 (reason: user_values_this)"
```

### Test 4: Auto-Learning from Retrievals ✅
```
Retrieval 1: 📖 Memory retrieved (count: 1)
Retrieval 2: 📖 Memory retrieved (count: 2)
Retrieval 3: 📖 Memory retrieved (count: 3)
            ⬆️ Auto-boosted +10 (reason: frequent_retrieval)
```

## 🚀 Benefits

| Feature | Old System | New System |
|---------|-----------|------------|
| **Domain Agnostic** | ❌ Biased toward finance/tech | ✅ Works for any topic |
| **User Intent** | ❌ Ignores what user says | ✅ Prioritizes explicit signals |
| **Learns from Behavior** | ❌ Static scoring | ✅ Tracks retrievals, auto-boosts |
| **User Feedback** | ❌ No control | ✅ Manual boost/demote API |
| **Transparency** | ❌ Black box | ✅ Logs every decision |

## 📝 API Endpoints

### 1. Boost Memory Importance
```http
POST /api/memory/boost
Content-Type: application/json

{
  "memoryId": "kyle_1762542172421_ktvj7tr0j",
  "reason": "user_values_this"
}

Response:
{
  "success": true,
  "message": "Memory importance boosted",
  "memoryId": "kyle_1762542172421_ktvj7tr0j"
}
```

### 2. Demote Memory Importance
```http
POST /api/memory/demote
Content-Type: application/json

{
  "memoryId": "kyle_xyz",
  "reason": "user_ignores_this"
}

Response:
{
  "success": true,
  "message": "Memory importance demoted",
  "memoryId": "kyle_xyz"
}
```

### 3. Get Memory Details
```http
GET /api/memory/kyle_1762542172421_ktvj7tr0j

Response:
{
  "id": "kyle_1762542172421_ktvj7tr0j",
  "importance": 100,
  "userMessage": "Remember this: AWS EC2...",
  "topics": ["server", "stock_AWS"],
  "userFeedback": {
    "retrievalCount": 3,
    "boostCount": 1,
    "userImportanceAdjustment": +10,
    "lastAccessed": "2025-11-07T17:42:15.123Z"
  }
}
```

## 🎯 Usage Examples

### Example 1: Teaching Kyle Domain Knowledge
```javascript
User: "Remember this: Our database password is stored in AWS Secrets Manager under prod/db/pass"
Kyle: [Calculates importance: 30 + 35 (remember) + 12 (URLs/refs) + 8 (proper names) = 85]
      ✅ STORED with importance 85

Later...
User: "How do I access the database password?"
Kyle: [Retrieves memory, tracks retrieval]
      📖 "Retrieval count: 1"
      Returns: "Your database password is in AWS Secrets Manager at prod/db/pass"

After 3 similar questions...
Kyle: ⬆️ Auto-boosted memory importance to 95 (frequent_retrieval)
```

### Example 2: Filtering Noise
```javascript
User: "The weather is nice"
Kyle: [Calculates importance: 30 - 20 (too short) + 0 (no signals) = 10]
      ❌ FILTERED (below 55 threshold)
      
User: "hi"
Kyle: [Calculates importance: 30 - 30 (pure greeting) = 0]
      ❌ FILTERED (below 55 threshold)
```

### Example 3: Manual Curation
```javascript
// You realize a memory is important
fetch('/api/memory/boost', {
  method: 'POST',
  body: JSON.stringify({
    memoryId: 'kyle_xyz',
    reason: 'critical_for_deployment'
  })
});
// Kyle: ⬆️ Boosted importance +10

// You realize a memory is irrelevant
fetch('/api/memory/demote', {
  method: 'POST',
  body: JSON.stringify({
    memoryId: 'kyle_abc',
    reason: 'outdated_info'
  })
});
// Kyle: ⬇️ Demoted importance -10
```

## 🔮 Future Enhancements (Planned)

1. **Topic-Specific Learning**: Learn per-domain importance patterns
   - Example: "When discussing deployment, X terms are valuable"

2. **Time-Decay with Exceptions**: Older memories fade UNLESS frequently accessed
   - Frequently retrieved → resist decay
   - Never retrieved → gentle fade

3. **Cross-User Learning** (Optional): Aggregate patterns across users
   - "95% of users who retrieve X also value Y"

4. **Context-Aware Scoring**: Importance varies by conversation context
   - Same message in different contexts = different scores

5. **Negative Feedback Loop**: Auto-demote if user never recalls
   - Memory stored but never retrieved after 30 days → -5 importance

## ✅ Status

**FULLY IMPLEMENTED**

- ✅ User-driven signals (explicit keywords)
- ✅ Content analysis (domain-agnostic)
- ✅ Behavioral learning (retrieval tracking)
- ✅ Auto-boost after 3 retrievals
- ✅ Manual boost/demote API endpoints
- ✅ Get memory details endpoint
- ✅ Transparent logging
- ✅ Test coverage: 4/4 scenarios passed

**Kyle now learns value from YOUR behavior, not arbitrary assumptions!** 🎓✨
