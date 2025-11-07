// Kyle Updates: Quiet operation + Auto-research + Repetition tracking

// 1. SIMPLIFIED RESPONSES (no bragging)
const quietResponses = {
  greet: () => `🔍 Hello. What would you like to know?`,
  thanks: () => `🔍 You're welcome.`,
  default: (relevantInfo) => {
    if (relevantInfo) {
      return `🔍 ${relevantInfo}\n\nWhat else?`;
    }
    return `🔍 What do you need?`;
  }
};

// 2. REPETITION TRACKING (sliding scale)
class RepetitionTracker {
  constructor() {
    this.mentionCounts = new Map(); // topic -> count
    this.lastMentioned = new Map(); // topic -> timestamp
  }
  
  /**
   * Track mention and calculate importance boost based on repetition
   */
  trackMention(topic) {
    const count = (this.mentionCounts.get(topic) || 0) + 1;
    this.mentionCounts.set(topic, count);
    this.lastMentioned.set(topic, Date.now());
    
    // Sliding scale: More mentions = more important
    // 1 mention: +0
    // 2 mentions: +10
    // 3 mentions: +15
    // 5 mentions: +20
    // 10+ mentions: +30 (cap)
    let boost = 0;
    if (count >= 10) boost = 30;
    else if (count >= 5) boost = 20;
    else if (count >= 3) boost = 15;
    else if (count >= 2) boost = 10;
    
    console.log(`📊 Kyle: Topic "${topic}" mentioned ${count} times (importance boost: +${boost})`);
    return boost;
  }
  
  getMentionCount(topic) {
    return this.mentionCounts.get(topic) || 0;
  }
  
  getImportanceBoost(topics) {
    let totalBoost = 0;
    topics.forEach(topic => {
      const count = this.getMentionCount(topic);
      if (count >= 10) totalBoost += 30;
      else if (count >= 5) totalBoost += 20;
      else if (count >= 3) totalBoost += 15;
      else if (count >= 2) totalBoost += 10;
    });
    return Math.min(totalBoost, 40); // Cap at +40
  }
}

const repetitionTracker = new RepetitionTracker();

// 3. AUTO-RESEARCH (search internet for unknown topics)
async function autoResearchUnknownTopics(topics, agentTools, knowledge) {
  const unknownTopics = topics.filter(topic => {
    const existing = knowledge.query(topic);
    return !existing || existing.strength < 2; // New or weakly known
  });
  
  if (unknownTopics.length === 0) return;
  
  console.log(`🔎 Kyle: Auto-researching unknown topics: ${unknownTopics.join(', ')}`);
  
  for (const topic of unknownTopics.slice(0, 2)) { // Limit to 2 per message
    try {
      const searchResult = await agentTools.executeTool('web', 'searchWeb', {
        query: topic
      });
      
      if (searchResult.success && searchResult.result) {
        const summary = searchResult.result.abstract || searchResult.result.snippet || '';
        if (summary) {
          knowledge.addKnowledge(topic, summary, 'Kyle_AutoResearch', []);
          console.log(`✅ Kyle: Learned about "${topic}" from web search`);
          
          // Store the researched knowledge
          return {
            topic,
            summary,
            source: 'web_search',
            timestamp: new Date().toISOString()
          };
        }
      }
    } catch (err) {
      console.error(`❌ Kyle: Failed to research "${topic}":`, err.message);
    }
  }
}

// 4. INTEGRATION INTO calculateImportance
function calculateImportanceWithRepetition(data, topics, repetitionTracker) {
  let baseScore = calculateImportance(data); // Existing function
  
  // Add repetition boost
  const repetitionBoost = repetitionTracker.getImportanceBoost(topics);
  
  // Track all mentions
  topics.forEach(topic => repetitionTracker.trackMention(topic));
  
  const finalScore = Math.min(baseScore + repetitionBoost, 100);
  
  if (repetitionBoost > 0) {
    console.log(`📈 Kyle: Repetition boost +${repetitionBoost} (final score: ${finalScore})`);
  }
  
  return finalScore;
}

// EXAMPLE USAGE:
// 
// User mentions "astrology" for the first time:
// - Kyle doesn't know about it → Auto-research triggered
// - Kyle searches web for "astrology"
// - Extracts: "Astrology is the study of celestial bodies..."
// - Stores to knowledge base
// - Responds: "Astrology relates to celestial bodies. What specifically?"
//
// User mentions "astrology" again (2nd time):
// - Repetition +10 importance boost
// - More likely to be stored in memory
//
// User mentions "astrology" 5 times:
// - Repetition +20 importance boost
// - Highly likely to be stored
//
// User mentions "astrology" 10+ times:
// - Repetition +30 importance boost (max)
// - ALWAYS stored (even if message is short)

module.exports = {
  quietResponses,
  RepetitionTracker,
  autoResearchUnknownTopics,
  calculateImportanceWithRepetition
};
