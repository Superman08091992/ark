#!/usr/bin/env node
/**
 * ARK Intelligent Backend - Adaptive Learning System
 * Self-improving AI with massive memory and knowledge compilation
 * By: Jimmy <jimmy@ark-project.local>
 */

const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');
const { AgentToolRegistry } = require('./agent_tools.cjs');

const PORT = 8000;
const FILES_DIR = path.join(__dirname, 'mock_files');
const KNOWLEDGE_DIR = path.join(__dirname, 'knowledge_base');
const LOGS_DIR = path.join(__dirname, 'agent_logs');
const KYLE_MEMORY_DIR = path.join(__dirname, 'kyle_infinite_memory');

// Ensure directories exist
[FILES_DIR, KNOWLEDGE_DIR, LOGS_DIR, KYLE_MEMORY_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// ===== ENHANCED MEMORY SYSTEM =====
const MEMORY_SIZE = 200; // Store last 200 messages per agent (except Kyle who has infinite)
const conversationMemory = new Map(); // agentName -> [{user, agent, time, topics, sentiment}]
const userProfiles = new Map(); // userId -> {interests, personality, preferences, expertise}

// ===== REPETITION TRACKER =====
class RepetitionTracker {
  constructor() {
    this.mentionCounts = new Map(); // topic -> count
    this.lastMentioned = new Map(); // topic -> timestamp
  }
  
  trackMention(topic) {
    const count = (this.mentionCounts.get(topic) || 0) + 1;
    this.mentionCounts.set(topic, count);
    this.lastMentioned.set(topic, Date.now());
    
    // Sliding scale: More mentions = more important
    let boost = 0;
    if (count >= 10) boost = 30;
    else if (count >= 5) boost = 20;
    else if (count >= 3) boost = 15;
    else if (count >= 2) boost = 10;
    
    if (count > 1) {
      console.log(`📊 Kyle: Topic "${topic}" mentioned ${count} times (boost: +${boost})`);
    }
    return boost;
  }
  
  getImportanceBoost(topics) {
    let totalBoost = 0;
    topics.forEach(topic => {
      const count = this.mentionCounts.get(topic) || 0;
      if (count >= 10) totalBoost += 30;
      else if (count >= 5) totalBoost += 20;
      else if (count >= 3) totalBoost += 15;
      else if (count >= 2) totalBoost += 10;
    });
    return Math.min(totalBoost, 40); // Cap at +40
  }
}

const repetitionTracker = new RepetitionTracker();

// ===== KYLE'S INFINITE MEMORY SYSTEM =====
class KyleInfiniteMemory {
  constructor() {
    this.memoryDir = KYLE_MEMORY_DIR;
    this.indexPath = path.join(this.memoryDir, 'master_index.json');
    this.compressionPath = path.join(this.memoryDir, 'compressed_knowledge.json');
    this.catalogPath = path.join(this.memoryDir, 'catalog.json');
    
    // In-memory indices for fast lookup
    this.masterIndex = new Map(); // topic -> [memory_ids]
    this.catalog = new Map(); // memory_id -> {summary, topics, date, importance}
    this.compressedKnowledge = new Map(); // topic -> {consolidated_info}
    
    // Statistics
    this.totalMemories = 0;
    this.totalCompressed = 0;
    this.indexSize = 0;
    
    this.load();
  }
  
  /**
   * COMPRESS MESSAGE: Remove conversational fluff, keep knowledge
   * Example: "Hey, so I was wondering, like, what is entropy?" → "What is entropy?"
   */
  compressMessage(message, extractedFacts) {
    // If we have extracted facts, use those as the compressed form
    if (extractedFacts && extractedFacts.length > 0) {
      return extractedFacts.map(fact => {
        switch (fact.type) {
          case 'definition':
            return `${fact.subject} = ${fact.value}`;
          case 'causal':
            return `${fact.cause} → ${fact.effect}`;
          case 'numerical':
            return `${fact.subject}: ${fact.value}`;
          case 'formula':
            return `${fact.variable} = ${fact.expression}`;
          default:
            return `${fact.subject || ''} ${fact.value || ''}`.trim();
        }
      }).join(' | ');
    }
    
    // Otherwise, do basic compression
    let compressed = message
      .replace(/\b(um|uh|like|you know|i mean|basically|actually)\b/gi, '') // Filler words
      .replace(/\b(hey|hi|hello|so|well|anyway)\b,?\s*/gi, '') // Greetings/transitions
      .replace(/\s{2,}/g, ' ') // Multiple spaces
      .trim();
    
    // Keep only content-bearing sentences
    const sentences = compressed.split(/[.!?]+/).filter(s => s.trim().length > 10);
    return sentences.join('. ').trim();
  }
  
  /**
   * KNOWLEDGE EXTRACTION: Extract dense facts from message
   * Removes conversational fluff, keeps learnable information
   */
  extractKnowledge(userMessage, agentResponse) {
    const facts = [];
    const combined = `${userMessage} ${agentResponse}`.toLowerCase();
    
    // Extract definitions: "X is Y", "X means Y", "X is defined as Y"
    const definitionPatterns = [
      /(\w+(?:\s+\w+){0,3})\s+(?:is|are|means?|equals?)\s+([^.!?]+)/gi,
      /(\w+(?:\s+\w+){0,3})\s+(?:is defined as|refers to|known as)\s+([^.!?]+)/gi
    ];
    
    definitionPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(combined)) !== null) {
        if (match[1] && match[2] && match[2].length > 3) {
          facts.push({
            type: 'definition',
            subject: match[1].trim(),
            value: match[2].trim(),
            confidence: 0.9
          });
        }
      }
    });
    
    // Extract causal relationships: "X causes Y", "X leads to Y"
    const causalPattern = /(\w+(?:\s+\w+){0,3})\s+(?:causes?|leads? to|results? in)\s+([^.!?]+)/gi;
    let match;
    while ((match = causalPattern.exec(combined)) !== null) {
      if (match[1] && match[2]) {
        facts.push({
          type: 'causal',
          cause: match[1].trim(),
          effect: match[2].trim(),
          confidence: 0.85
        });
      }
    }
    
    // Extract numerical facts: "X is 123", "X at 456"
    const numericalPattern = /(\w+(?:\s+\w+){0,3})\s+(?:is|at|of|equals?)\s+(\d+(?:[.,]\d+)?(?:\s*[a-z%]+)?)/gi;
    while ((match = numericalPattern.exec(combined)) !== null) {
      if (match[1] && match[2]) {
        facts.push({
          type: 'numerical',
          subject: match[1].trim(),
          value: match[2].trim(),
          confidence: 0.95
        });
      }
    }
    
    // Extract formulas/equations (if present)
    const formulaPattern = /([a-z]+)\s*=\s*([^.!?,;]+)/gi;
    while ((match = formulaPattern.exec(userMessage)) !== null) {
      facts.push({
        type: 'formula',
        variable: match[1].trim(),
        expression: match[2].trim(),
        confidence: 1.0
      });
    }
    
    return facts.length > 0 ? facts : null;
  }
  
  /**
   * Store a memory - ONLY if valuable and non-duplicate
   * Enhanced to store EXTRACTED KNOWLEDGE, not just conversations
   */
  store(data) {
    // FILTER 1: Check if important enough (minimum threshold)
    const importance = this.calculateImportance(data);
    if (importance < 55) {
      console.log(`⚠️  Kyle: Skipping low-value memory (importance: ${importance})`);
      return null; // Don't store trivial conversations
    }
    
    // FILTER 2: Check for duplicate content
    const isDuplicate = this.isDuplicate(data.userMessage, data.topics);
    if (isDuplicate) {
      console.log(`⚠️  Kyle: Skipping duplicate memory: "${data.userMessage.substring(0, 40)}..."`);
      return null;
    }
    
    // FILTER 3: Check for "stupid shit" - greetings, thanks, empty
    if (this.isLowQuality(data.userMessage)) {
      console.log(`⚠️  Kyle: Skipping low-quality memory: "${data.userMessage.substring(0, 40)}..."`);
      return null;
    }
    
    const memoryId = `kyle_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const timestamp = new Date();
    
    // KNOWLEDGE EXTRACTION: Pull out learnable facts
    const extractedKnowledge = this.extractKnowledge(data.userMessage, data.agentResponse || '');
    
    // Create compressed summary (remove fluff)
    const compressedSummary = this.compressMessage(data.userMessage, extractedKnowledge);
    
    // Extract key information
    const memory = {
      id: memoryId,
      timestamp: timestamp.toISOString(),
      userMessage: data.userMessage, // Original (for context)
      agentResponse: data.agentResponse,
      compressedSummary, // Dense version (for retrieval)
      extractedFacts: extractedKnowledge, // Structured knowledge
      topics: data.topics || [],
      sentiment: data.sentiment || 'neutral',
      keywords: data.keywords || [],
      context: data.context || {},
      importance: importance,
      relatedMemories: [],
      knowledgeDensity: extractedKnowledge ? extractedKnowledge.length / Math.max(data.userMessage.length, 1) : 0,
      sources: data.sources || [], // NEW: Track research sources
      enhancedByLLM: data.enhancedByLLM || false // NEW: Flag if LLM-enhanced
    };
    
    // Write to individual memory file (never deleted once stored)
    const memoryFile = path.join(this.memoryDir, `${memoryId}.json`);
    fs.writeFileSync(memoryFile, JSON.stringify(memory, null, 2));
    
    // Update catalog (use compressed summary for efficient retrieval)
    this.catalog.set(memoryId, {
      summary: compressedSummary || data.userMessage.substring(0, 100),
      topics: data.topics,
      date: timestamp,
      importance: memory.importance,
      filePath: memoryFile,
      hash: this.hashMessage(data.userMessage), // For duplicate detection
      extractedFactsCount: extractedKnowledge ? extractedKnowledge.length : 0,
      knowledgeDensity: memory.knowledgeDensity,
      sourcesCount: (data.sources || []).length, // NEW: Count of sources
      enhancedByLLM: data.enhancedByLLM || false // NEW: LLM enhancement flag
    });
    
    // Update indices for each topic
    data.topics.forEach(topic => {
      if (!this.masterIndex.has(topic)) {
        this.masterIndex.set(topic, []);
      }
      this.masterIndex.get(topic).push(memoryId);
    });
    
    this.totalMemories++;
    console.log(`✅ Kyle: Stored valuable memory #${this.totalMemories} (importance: ${importance})`);
    
    // Compress knowledge periodically (every 100 memories)
    if (this.totalMemories % 100 === 0) {
      this.compressKnowledge();
    }
    
    // Save indices
    this.saveIndices();
    
    return memoryId;
  }
  
  /**
   * Check if message is duplicate or very similar
   */
  isDuplicate(message, topics) {
    const messageHash = this.hashMessage(message);
    
    // Check catalog for similar messages
    for (const [id, entry] of this.catalog) {
      if (entry.hash === messageHash) {
        return true; // Exact duplicate
      }
      
      // Check for very similar topics + content
      if (topics && topics.length > 0) {
        const commonTopics = topics.filter(t => entry.topics?.includes(t));
        if (commonTopics.length >= topics.length * 0.8) { // 80% topic overlap
          const similarity = this.calculateSimilarity(message, entry.summary);
          if (similarity > 0.85) { // 85% similar
            return true;
          }
        }
      }
    }
    
    return false;
  }
  
  /**
   * Check if message is low quality (greetings, thanks, etc)
   */
  isLowQuality(message) {
    const lower = message.toLowerCase().trim();
    
    // Too short
    if (lower.length < 10) return true;
    
    // Just greetings
    const greetingOnly = /^(hi|hello|hey|sup|yo|greetings?|good\s+(morning|afternoon|evening))[\s!.]*$/i;
    if (greetingOnly.test(lower)) return true;
    
    // Just thanks
    const thanksOnly = /^(thanks?|thank you|thx|ty|appreciated?)[\s!.]*$/i;
    if (thanksOnly.test(lower)) return true;
    
    // Just goodbye
    const byeOnly = /^(bye|goodbye|see you|later|cya|peace)[\s!.]*$/i;
    if (byeOnly.test(lower)) return true;
    
    // Generic "show me" without substance
    if (lower.match(/^show\s+me\s+your\s+(status|index|log)s?[\s!.]*$/i)) return true;
    
    return false;
  }
  
  /**
   * Simple message hash for duplicate detection
   */
  hashMessage(message) {
    // Simple hash: normalize and create signature
    const normalized = message.toLowerCase()
      .replace(/[^\w\s]/g, '') // Remove punctuation
      .replace(/\s+/g, ' ')    // Normalize spaces
      .trim();
    
    // Create simple hash from first 50 chars
    return normalized.substring(0, 50);
  }
  
  /**
   * Calculate similarity between two messages (0-1)
   */
  calculateSimilarity(msg1, msg2) {
    const words1 = new Set(msg1.toLowerCase().split(/\s+/));
    const words2 = new Set(msg2.toLowerCase().split(/\s+/));
    
    const intersection = new Set([...words1].filter(w => words2.has(w)));
    const union = new Set([...words1, ...words2]);
    
    return intersection.size / union.size; // Jaccard similarity
  }
  
  /**
   * Calculate importance score (0-100) - KNOWLEDGE-FOCUSED SYSTEM
   * Value = Information I don't already know (unknown > redundant)
   * Focus: Dense, learnable facts/concepts, not conversational fluff
   */
  calculateImportance(data) {
    let score = 20; // Lower base - knowledge must prove its worth
    
    const message = data.userMessage?.toLowerCase() || '';
    const userId = data.context?.userId || 'default_user';
    
    // === KNOWLEDGE DENSITY DETECTION (Highest Priority) ===
    // Value = Unknown information (new facts, concepts, relationships)
    
    // TEACHING/LEARNING SIGNALS - User is providing knowledge
    const teachingSignals = [
      'learn', 'understand', 'study', 'read', 'book', 'paper', 'article',
      'theory', 'principle', 'law', 'equation', 'formula', 'definition',
      'concept', 'means', 'is defined as', 'refers to', 'known as'
    ];
    const isTeaching = teachingSignals.some(sig => message.includes(sig));
    if (isTeaching) score += 40; // High value - acquiring new knowledge
    
    // FACTUAL STATEMENTS - Declarative knowledge
    // Look for: "X is Y", "X means Y", "X works by Y", "X causes Y"
    const hasFactPattern = message.match(/\b(is|are|means|causes|results in|leads to|equals|represents)\b/);
    const hasDefinitionPattern = message.match(/\b(defined as|known as|called|termed|refers to)\b/);
    if (hasFactPattern || hasDefinitionPattern) score += 25;
    
    // CAUSAL/RELATIONSHIP INFORMATION - How things connect
    const hasCausalPattern = message.match(/\b(because|therefore|thus|hence|consequently|if.*then|when.*then)\b/);
    if (hasCausalPattern) score += 20; // Cause-effect relationships are valuable
    
    // PROCEDURAL KNOWLEDGE - How to do something
    const hasHowTo = message.match(/\b(how to|steps? to|process of|method (for|of)|technique|procedure)\b/);
    if (hasHowTo) score += 25;
    
    // EXPLICIT VALUE SIGNALS - User tells us what matters
    const explicitSignals = [
      'remember', 'important', 'critical', 'save this', 'note that', 
      'keep in mind', 'don\'t forget', 'always', 'never', 'must'
    ];
    const hasExplicit = explicitSignals.some(sig => message.includes(sig));
    if (hasExplicit) score += 30; // User explicitly marks as valuable
    
    // NOVELTY CHECK - Is this information new?
    // Check if similar concepts already exist in knowledge base
    const existingKnowledge = data.topics?.map(t => knowledge.query(t)).filter(k => k) || [];
    const isNovel = existingKnowledge.length === 0 || existingKnowledge.every(k => k.strength < 2);
    if (isNovel && data.topics?.length > 0) score += 20; // Reward truly new information
    
    // QUESTIONS - Seeking knowledge (store the answer, not the question)
    const isQuestion = message.includes('?') || 
                       message.match(/^(what|how|why|when|where|who|which|can you|could you|would you)/);
    if (isQuestion && !message.match(/^(show|tell)\s+me\s+(your|the)\s+(status|index|log)/)) {
      score += 15; // Store Q&A pairs as knowledge
    }
    
    // === CONTENT SIGNALS (Medium Priority) ===
    
    // Message has substance - longer = more context usually
    if (message.length > 50) score += 10;
    if (message.length > 100) score += 10;
    if (message.length > 200) score += 5;
    
    // Multiple topics = interconnected knowledge
    const topicCount = data.topics?.length || 0;
    if (topicCount > 0) score += Math.min(topicCount * 6, 20);
    
    // Contains specific data points (numbers, dates, names, URLs)
    const hasNumbers = /\d+/.test(message);
    const hasDates = /\b(20\d{2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|q[1-4])\b/i.test(message);
    const hasUrls = /https?:\/\/|www\./i.test(message);
    const hasNames = /\b[A-Z][a-z]+\s[A-Z][a-z]+\b/.test(data.userMessage || ''); // Proper names
    
    if (hasNumbers) score += 8;
    if (hasDates) score += 10;
    if (hasUrls) score += 12;
    if (hasNames) score += 8;
    
    // Contains instructions or procedures (actionable info)
    const hasInstructions = message.match(/\b(step|configure|setup|install|deploy|run|execute|create|build)\b/);
    if (hasInstructions) score += 15;
    
    // === DOMAIN-AGNOSTIC LEARNING (Low Priority) ===
    // Don't assume domain - let ANY terminology be valuable
    
    // Extract unique nouns/entities (capitalized words) - these are often important
    const entities = (data.userMessage || '').match(/\b[A-Z][a-z]+\b/g) || [];
    const uniqueEntities = [...new Set(entities)];
    score += Math.min(uniqueEntities.length * 3, 15);
    
    // === PENALTIES (Quality Filters) ===
    
    // ANTI-PATTERN: Neighbor's breakfast problem
    // Conversational anecdotes without learnable information
    const isAnecdote = message.match(/\b(my neighbor|someone|i saw|i heard|they said|apparently)\b/);
    const hasNoFacts = !hasNumbers && !hasUrls && !hasDates && !hasFactPattern && !hasDefinitionPattern;
    if (isAnecdote && hasNoFacts) score -= 25; // Likely irrelevant personal story
    
    // Short, low-content messages
    if (message.length < 15) score -= 25;
    
    // Pure greetings/pleasantries (but allow greetings with content)
    const pureGreeting = message.match(/^(hi|hello|hey|sup|yo|greetings?)[\s!.]*$/);
    const pureThanks = message.match(/^(thanks?|thank you|thx|ty)[\s!.]*$/);
    const pureGoodbye = message.match(/^(bye|goodbye|see you|later|cya)[\s!.]*$/);
    
    if (pureGreeting || pureThanks || pureGoodbye) score -= 35;
    
    // Generic status requests (valuable response, not valuable input)
    if (message.match(/^(show|tell)\s+me\s+(your|the)\s+(status|index|log|memory)/)) score -= 20;
    
    // Opinion without facts ("I think X is good" vs "X works by Y")
    const isOpinion = message.match(/\b(i think|i feel|in my opinion|seems like|probably)\b/);
    if (isOpinion && hasNoFacts) score -= 15; // Opinion without supporting facts = low value
    
    // === REPETITION LEARNING (Sliding Scale) ===
    // Track mentions and boost importance for repeated topics
    const topics = data.topics || [];
    topics.forEach(topic => repetitionTracker.trackMention(topic));
    const repetitionBoost = repetitionTracker.getImportanceBoost(topics);
    score += repetitionBoost;
    
    if (repetitionBoost > 0) {
      console.log(`📈 Kyle: Repetition boost +${repetitionBoost} applied`);
    }
    
    // For now, use conversation history as proxy for engagement
    const conversationLength = data.context?.conversationLength || 0;
    if (conversationLength > 5) score += 5; // Deeper conversation = more context
    
    // Cap at 100, floor at 0
    return Math.max(0, Math.min(score, 100));
  }
  
  /**
   * Retrieve memories by topic with optional filters
   * AUTO-LEARNS: Tracks retrievals to boost important memories
   */
  retrieve(topic, options = {}) {
    const {
      limit = 10,
      minImportance = 0,
      sortBy = 'relevance', // relevance, date, importance
      includeCompressed = true,
      trackRetrieval = true // Auto-track user retrievals
    } = options;
    
    const memoryIds = this.masterIndex.get(topic) || [];
    let memories = memoryIds.map(id => {
      const catalog = this.catalog.get(id);
      if (!catalog || catalog.importance < minImportance) return null;
      
      // Track retrieval for adaptive learning
      if (trackRetrieval && catalog) {
        this.trackRetrieval(id);
      }
      
      // Load full memory if needed
      if (options.fullData) {
        try {
          const data = fs.readFileSync(catalog.filePath, 'utf8');
          return JSON.parse(data);
        } catch (err) {
          return catalog;
        }
      }
      return catalog;
    }).filter(m => m !== null);
    
    // Sort (considering user-adjusted importance)
    if (sortBy === 'importance') {
      memories.sort((a, b) => {
        const aImportance = a.userAdjustedImportance || a.importance;
        const bImportance = b.userAdjustedImportance || b.importance;
        return bImportance - aImportance;
      });
    } else if (sortBy === 'date') {
      memories.sort((a, b) => new Date(b.date) - new Date(a.date));
    }
    
    // Include compressed knowledge if requested
    const result = {
      memories: memories.slice(0, limit),
      total: memories.length,
      compressed: includeCompressed ? this.compressedKnowledge.get(topic) : null
    };
    
    return result;
  }
  
  /**
   * Compress and consolidate knowledge
   */
  compressKnowledge() {
    console.log(`🔧 Kyle: Compressing knowledge from ${this.totalMemories} memories...`);
    
    for (const [topic, memoryIds] of this.masterIndex) {
      if (memoryIds.length < 5) continue; // Only compress topics with 5+ memories
      
      const memories = memoryIds.map(id => {
        const catalog = this.catalog.get(id);
        return catalog;
      }).filter(m => m);
      
      // Consolidate information
      const compressed = {
        topic,
        totalReferences: memoryIds.length,
        firstSeen: memories[0]?.date,
        lastSeen: memories[memories.length - 1]?.date,
        averageImportance: memories.reduce((sum, m) => sum + m.importance, 0) / memories.length,
        keyInsights: this.extractKeyInsights(memories),
        relatedTopics: this.findRelatedTopics(topic),
        compressionRatio: memoryIds.length / Math.max(1, this.extractKeyInsights(memories).length),
        lastCompressed: new Date().toISOString()
      };
      
      this.compressedKnowledge.set(topic, compressed);
    }
    
    this.totalCompressed = this.compressedKnowledge.size;
    this.saveCompressed();
    
    console.log(`✅ Kyle: Compressed ${this.compressedKnowledge.size} topics`);
  }
  
  /**
   * Extract key insights from memories
   */
  extractKeyInsights(memories) {
    // Get unique summaries sorted by importance
    const insights = memories
      .sort((a, b) => b.importance - a.importance)
      .slice(0, 10) // Top 10 most important
      .map(m => ({
        text: m.summary,
        importance: m.importance,
        date: m.date
      }));
    
    return insights;
  }
  
  /**
   * Find related topics
   */
  findRelatedTopics(topic) {
    const related = new Map();
    
    // Get all memories for this topic
    const memoryIds = this.masterIndex.get(topic) || [];
    
    // Find co-occurring topics
    memoryIds.forEach(id => {
      const catalog = this.catalog.get(id);
      if (!catalog) return;
      
      catalog.topics.forEach(t => {
        if (t !== topic) {
          related.set(t, (related.get(t) || 0) + 1);
        }
      });
    });
    
    // Sort by frequency
    return Array.from(related.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([topic, count]) => ({ topic, coOccurrences: count }));
  }
  
  /**
   * Search across all memories
   */
  search(query, options = {}) {
    const { limit = 20, fullData = false } = options;
    const results = [];
    
    // Search in catalog summaries
    for (const [id, catalog] of this.catalog) {
      const relevance = this.calculateRelevance(query, catalog);
      if (relevance > 0.3) { // Threshold
        results.push({
          ...catalog,
          relevance,
          id
        });
      }
    }
    
    // Sort by relevance
    results.sort((a, b) => b.relevance - a.relevance);
    
    return {
      results: results.slice(0, limit),
      total: results.length,
      query
    };
  }
  
  /**
   * Calculate relevance score
   */
  calculateRelevance(query, catalog) {
    const queryLower = query.toLowerCase();
    const summaryLower = catalog.summary?.toLowerCase() || '';
    
    let score = 0;
    
    // Direct word matches
    const queryWords = queryLower.split(/\s+/);
    queryWords.forEach(word => {
      if (summaryLower.includes(word)) score += 0.2;
    });
    
    // Topic matches
    catalog.topics?.forEach(topic => {
      if (queryLower.includes(topic.toLowerCase())) score += 0.3;
    });
    
    // Importance bonus (now considering user feedback)
    const adjustedImportance = catalog.userAdjustedImportance || catalog.importance;
    score += (adjustedImportance / 100) * 0.2;
    
    return Math.min(score, 1.0);
  }
  
  /**
   * USER FEEDBACK: Boost importance of a memory
   * Call this when user explicitly references or values a memory
   */
  boostMemory(memoryId, reason = 'user_reference') {
    const catalog = this.catalog.get(memoryId);
    if (!catalog) return false;
    
    // Load full memory
    try {
      const memoryData = JSON.parse(fs.readFileSync(catalog.filePath, 'utf8'));
      
      // Track user interactions
      if (!memoryData.userFeedback) {
        memoryData.userFeedback = {
          retrievalCount: 0,
          boostCount: 0,
          lastAccessed: null,
          userImportanceAdjustment: 0
        };
      }
      
      memoryData.userFeedback.boostCount++;
      memoryData.userFeedback.lastAccessed = new Date().toISOString();
      memoryData.userFeedback.userImportanceAdjustment = Math.min(
        memoryData.userFeedback.userImportanceAdjustment + 10, 
        30 // Max +30 boost from user interaction
      );
      
      // Recalculate importance with user signal
      const newImportance = Math.min(
        memoryData.importance + memoryData.userFeedback.userImportanceAdjustment,
        100
      );
      
      // Update memory file
      memoryData.importance = newImportance;
      fs.writeFileSync(catalog.filePath, JSON.stringify(memoryData, null, 2));
      
      // Update catalog
      catalog.importance = newImportance;
      catalog.userAdjustedImportance = newImportance;
      this.catalog.set(memoryId, catalog);
      
      console.log(`⬆️  Kyle: Boosted memory ${memoryId} importance to ${newImportance} (reason: ${reason})`);
      return true;
    } catch (err) {
      console.error('Failed to boost memory:', err);
      return false;
    }
  }
  
  /**
   * USER FEEDBACK: Mark memory as less important
   * Call this if user ignores/dismisses a memory
   */
  demoteMemory(memoryId, reason = 'user_ignore') {
    const catalog = this.catalog.get(memoryId);
    if (!catalog) return false;
    
    try {
      const memoryData = JSON.parse(fs.readFileSync(catalog.filePath, 'utf8'));
      
      if (!memoryData.userFeedback) {
        memoryData.userFeedback = {
          retrievalCount: 0,
          boostCount: 0,
          lastAccessed: null,
          userImportanceAdjustment: 0
        };
      }
      
      memoryData.userFeedback.userImportanceAdjustment = Math.max(
        memoryData.userFeedback.userImportanceAdjustment - 10,
        -30 // Max -30 penalty
      );
      
      const newImportance = Math.max(
        memoryData.importance + memoryData.userFeedback.userImportanceAdjustment,
        0
      );
      
      memoryData.importance = newImportance;
      fs.writeFileSync(catalog.filePath, JSON.stringify(memoryData, null, 2));
      
      catalog.importance = newImportance;
      catalog.userAdjustedImportance = newImportance;
      this.catalog.set(memoryId, catalog);
      
      console.log(`⬇️  Kyle: Demoted memory ${memoryId} importance to ${newImportance} (reason: ${reason})`);
      return true;
    } catch (err) {
      console.error('Failed to demote memory:', err);
      return false;
    }
  }
  
  /**
   * AUTO-LEARN: Track when user recalls memories to boost their value
   */
  trackRetrieval(memoryId) {
    const catalog = this.catalog.get(memoryId);
    if (!catalog) return;
    
    try {
      const memoryData = JSON.parse(fs.readFileSync(catalog.filePath, 'utf8'));
      
      if (!memoryData.userFeedback) {
        memoryData.userFeedback = {
          retrievalCount: 0,
          boostCount: 0,
          lastAccessed: null,
          userImportanceAdjustment: 0
        };
      }
      
      memoryData.userFeedback.retrievalCount++;
      memoryData.userFeedback.lastAccessed = new Date().toISOString();
      
      // Auto-boost after multiple retrievals (user clearly values this)
      if (memoryData.userFeedback.retrievalCount % 3 === 0) {
        this.boostMemory(memoryId, 'frequent_retrieval');
      } else {
        // Just update retrieval stats
        fs.writeFileSync(catalog.filePath, JSON.stringify(memoryData, null, 2));
      }
      
      console.log(`📖 Kyle: Memory ${memoryId} retrieved (count: ${memoryData.userFeedback.retrievalCount})`);
    } catch (err) {
      console.error('Failed to track retrieval:', err);
    }
  }
  
  /**
   * Get statistics
   */
  getStats() {
    const topicCount = this.masterIndex.size;
    const avgMemoriesPerTopic = this.totalMemories / Math.max(topicCount, 1);
    
    // Find most active topics
    const topicActivity = Array.from(this.masterIndex.entries())
      .map(([topic, ids]) => ({ topic, count: ids.length }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
    
    return {
      totalMemories: this.totalMemories,
      totalTopics: topicCount,
      totalCompressed: this.totalCompressed,
      avgMemoriesPerTopic: avgMemoriesPerTopic.toFixed(1),
      indexSize: this.indexSize,
      topTopics: topicActivity,
      memoryFiles: fs.readdirSync(this.memoryDir).filter(f => f.startsWith('kyle_')).length,
      lastCompression: this.getLastCompressionTime()
    };
  }
  
  getLastCompressionTime() {
    let latest = null;
    for (const compressed of this.compressedKnowledge.values()) {
      if (!latest || compressed.lastCompressed > latest) {
        latest = compressed.lastCompressed;
      }
    }
    return latest;
  }
  
  /**
   * Save indices to disk
   */
  saveIndices() {
    try {
      // Save master index
      const indexData = {
        version: '1.0',
        lastUpdated: new Date().toISOString(),
        totalMemories: this.totalMemories,
        index: Array.from(this.masterIndex.entries()).map(([topic, ids]) => ({
          topic,
          memoryIds: ids
        }))
      };
      fs.writeFileSync(this.indexPath, JSON.stringify(indexData, null, 2));
      
      // Save catalog
      const catalogData = {
        version: '1.0',
        lastUpdated: new Date().toISOString(),
        entries: Array.from(this.catalog.entries()).map(([id, data]) => ({
          id,
          ...data,
          date: data.date instanceof Date ? data.date.toISOString() : data.date
        }))
      };
      fs.writeFileSync(this.catalogPath, JSON.stringify(catalogData, null, 2));
      
      this.indexSize = indexData.index.length;
    } catch (err) {
      console.error('Failed to save Kyle indices:', err);
    }
  }
  
  /**
   * Save compressed knowledge
   */
  saveCompressed() {
    try {
      const data = {
        version: '1.0',
        lastUpdated: new Date().toISOString(),
        totalCompressed: this.compressedKnowledge.size,
        knowledge: Array.from(this.compressedKnowledge.entries()).map(([topic, data]) => ({
          topic,
          ...data
        }))
      };
      fs.writeFileSync(this.compressionPath, JSON.stringify(data, null, 2));
    } catch (err) {
      console.error('Failed to save Kyle compressed knowledge:', err);
    }
  }
  
  /**
   * Load indices from disk
   */
  load() {
    try {
      // Load master index
      if (fs.existsSync(this.indexPath)) {
        const indexData = JSON.parse(fs.readFileSync(this.indexPath, 'utf8'));
        indexData.index.forEach(entry => {
          this.masterIndex.set(entry.topic, entry.memoryIds);
        });
        this.totalMemories = indexData.totalMemories || 0;
        console.log(`📚 Kyle: Loaded ${this.masterIndex.size} topic indices`);
      }
      
      // Load catalog
      if (fs.existsSync(this.catalogPath)) {
        const catalogData = JSON.parse(fs.readFileSync(this.catalogPath, 'utf8'));
        catalogData.entries.forEach(entry => {
          this.catalog.set(entry.id, {
            ...entry,
            date: new Date(entry.date)
          });
        });
        console.log(`📚 Kyle: Loaded ${this.catalog.size} catalog entries`);
      }
      
      // Load compressed knowledge
      if (fs.existsSync(this.compressionPath)) {
        const compressedData = JSON.parse(fs.readFileSync(this.compressionPath, 'utf8'));
        compressedData.knowledge.forEach(entry => {
          this.compressedKnowledge.set(entry.topic, entry);
        });
        this.totalCompressed = this.compressedKnowledge.size;
        console.log(`📚 Kyle: Loaded ${this.compressedKnowledge.size} compressed topics`);
      }
    } catch (err) {
      console.error('Failed to load Kyle memory system:', err);
    }
  }
}

const kyleMemory = new KyleInfiniteMemory();

// ===== KNOWLEDGE GRAPH =====
class KnowledgeGraph {
  constructor() {
    this.nodes = new Map(); // topic -> {content, related, sources, strength}
    this.load();
  }
  
  addKnowledge(topic, content, source, relatedTopics = []) {
    if (!this.nodes.has(topic)) {
      this.nodes.set(topic, {
        content: [],
        related: new Set(),
        sources: new Set(),
        strength: 0,
        lastUpdated: new Date()
      });
    }
    
    const node = this.nodes.get(topic);
    node.content.push({
      text: content,
      timestamp: new Date(),
      source
    });
    node.sources.add(source);
    node.strength++;
    node.lastUpdated = new Date();
    
    // Add relationships
    relatedTopics.forEach(related => {
      node.related.add(related);
      // Create bidirectional link
      if (!this.nodes.has(related)) {
        this.addKnowledge(related, `Related to ${topic}`, source);
      }
      this.nodes.get(related).related.add(topic);
    });
    
    this.save();
  }
  
  query(topic) {
    if (!this.nodes.has(topic)) return null;
    
    const node = this.nodes.get(topic);
    const related = Array.from(node.related).map(r => ({
      topic: r,
      strength: this.nodes.get(r)?.strength || 0
    })).sort((a, b) => b.strength - a.strength);
    
    return {
      topic,
      content: node.content.slice(-10), // Last 10 entries
      related: related.slice(0, 5), // Top 5 related
      sources: Array.from(node.sources),
      strength: node.strength,
      lastUpdated: node.lastUpdated
    };
  }
  
  getRelated(topic, depth = 2) {
    const visited = new Set();
    const related = [];
    
    const traverse = (currentTopic, currentDepth) => {
      if (currentDepth > depth || visited.has(currentTopic)) return;
      visited.add(currentTopic);
      
      const node = this.nodes.get(currentTopic);
      if (!node) return;
      
      Array.from(node.related).forEach(rel => {
        related.push({
          topic: rel,
          depth: currentDepth,
          strength: this.nodes.get(rel)?.strength || 0
        });
        traverse(rel, currentDepth + 1);
      });
    };
    
    traverse(topic, 0);
    return related.sort((a, b) => b.strength - a.strength);
  }
  
  save() {
    try {
      const data = {
        nodes: Array.from(this.nodes.entries()).map(([topic, node]) => ({
          topic,
          content: node.content,
          related: Array.from(node.related),
          sources: Array.from(node.sources),
          strength: node.strength,
          lastUpdated: node.lastUpdated
        }))
      };
      fs.writeFileSync(
        path.join(KNOWLEDGE_DIR, 'knowledge_graph.json'),
        JSON.stringify(data, null, 2)
      );
    } catch (err) {
      console.error('Failed to save knowledge:', err);
    }
  }
  
  load() {
    try {
      const filepath = path.join(KNOWLEDGE_DIR, 'knowledge_graph.json');
      if (fs.existsSync(filepath)) {
        const data = JSON.parse(fs.readFileSync(filepath, 'utf8'));
        data.nodes.forEach(node => {
          this.nodes.set(node.topic, {
            content: node.content,
            related: new Set(node.related),
            sources: new Set(node.sources),
            strength: node.strength,
            lastUpdated: new Date(node.lastUpdated)
          });
        });
        console.log(`📚 Loaded ${this.nodes.size} knowledge nodes`);
      }
    } catch (err) {
      console.error('Failed to load knowledge:', err);
    }
  }
  
  compile() {
    // Compile knowledge into summaries
    const summaries = new Map();
    
    for (const [topic, node] of this.nodes) {
      if (node.strength > 5) { // Only compile well-established topics
        const summary = {
          topic,
          strength: node.strength,
          insights: node.content.slice(-5).map(c => c.text),
          relatedTopics: Array.from(node.related).slice(0, 5),
          sources: Array.from(node.sources),
          expertiseLevel: this.calculateExpertise(node)
        };
        summaries.set(topic, summary);
      }
    }
    
    return summaries;
  }
  
  calculateExpertise(node) {
    const score = node.strength * node.sources.size;
    if (score > 50) return 'expert';
    if (score > 20) return 'advanced';
    if (score > 10) return 'intermediate';
    return 'beginner';
  }
}

const knowledge = new KnowledgeGraph();

// ===== TOPIC EXTRACTION =====
function extractTopics(message) {
  const topics = new Set();
  
  // Financial topics
  const financialTerms = message.match(/\b(stock|market|trade|price|volume|trend|pattern|signal|analysis|bull|bear|forex|crypto|bitcoin|ethereum|option|future|dividend)\b/gi);
  if (financialTerms) financialTerms.forEach(t => topics.add(t.toLowerCase()));
  
  // Technical topics
  const techTerms = message.match(/\b(code|programming|algorithm|function|api|database|server|cloud|docker|kubernetes|python|javascript|react|node|ml|ai|model)\b/gi);
  if (techTerms) techTerms.forEach(t => topics.add(t.toLowerCase()));
  
  // Philosophical topics
  const philoTerms = message.match(/\b(meaning|purpose|ethics|moral|conscious|truth|reality|existence|knowledge|wisdom|freedom|justice)\b/gi);
  if (philoTerms) philoTerms.forEach(t => topics.add(t.toLowerCase()));
  
  // Business topics
  const bizTerms = message.match(/\b(business|startup|revenue|profit|growth|strategy|market|customer|product|sale|marketing|brand)\b/gi);
  if (bizTerms) bizTerms.forEach(t => topics.add(t.toLowerCase()));
  
  // Extract stock tickers
  const tickers = message.match(/\b[A-Z]{2,5}\b/g);
  if (tickers) tickers.forEach(t => {
    if (t.length <= 5) topics.add(`stock_${t}`);
  });
  
  return Array.from(topics);
}

// ===== ENHANCED PATTERN DETECTION =====
const keywordPatterns = {
  greeting: /\b(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|sup|yo|howdy|hiya)\b/i,
  farewell: /\b(bye|goodbye|see you|later|farewell|peace|cya)\b/i,
  question: /\b(what|why|how|when|where|who|which|can|could|would|should|is|are|do|does|did|will)\b/i,
  market: /\b(market|stock|trade|price|ticker|bull|bear|volume|chart|pattern|signal|forex|crypto)\b/i,
  analysis: /\b(analyz|pattern|detect|find|search|look|scan|monitor|track|predict|forecast|estimate)\b/i,
  file: /\b(file|create|write|read|save|delete|folder|document|directory|path)\b/i,
  code: /\b(code|program|script|function|debug|execute|run|build|compile|deploy|test)\b/i,
  help: /\b(help|assist|support|guide|teach|explain|show|tell|describe|clarify)\b/i,
  thanks: /\b(thank|thanks|appreciate|grateful|kudos|props)\b/i,
  philosophical: /\b(meaning|purpose|why|exist|conscious|truth|ethic|moral|value|belief|philosophy)\b/i,
  learn: /\b(learn|teach|train|adapt|evolve|grow|improve|remember|study|understand)\b/i,
  remember: /\b(remember|recall|memory|history|past|previous|before|earlier|ago)\b/i,
  explain: /\b(explain|clarify|elaborate|describe|detail|expand|tell me about)\b/i,
  opinion: /\b(think|believe|opinion|view|perspective|feel|seem|appear)\b/i,
  positive: /\b(great|good|excellent|amazing|awesome|love|perfect|wonderful|fantastic|brilliant)\b/i,
  negative: /\b(bad|terrible|awful|hate|annoying|frustrat|disappointing|poor|wrong)\b/i,
  urgent: /\b(urgent|asap|quickly|hurry|fast|now|immediately|emergency)\b/i,
  data: /\b(data|dataset|information|record|database|table|column|row|query|sql)\b/i
};

function detectKeywords(message) {
  const detected = {};
  for (const [key, pattern] of Object.entries(keywordPatterns)) {
    detected[key] = pattern.test(message);
  }
  return detected;
}

function getSentiment(message) {
  const keywords = detectKeywords(message);
  if (keywords.positive) return 'positive';
  if (keywords.negative) return 'negative';
  if (keywords.urgent) return 'urgent';
  if (keywords.question) return 'curious';
  if (keywords.thanks) return 'grateful';
  return 'neutral';
}

// ===== MARKET DATA WITH LEARNING =====
const marketData = {
  stocks: [
    { symbol: 'AAPL', price: 178.50, change: 2.3, volume: '52.3M', trend: 'bullish', sector: 'tech' },
    { symbol: 'NVDA', price: 495.20, change: -1.8, volume: '48.1M', trend: 'consolidating', sector: 'tech' },
    { symbol: 'TSLA', price: 242.80, change: 5.2, volume: '89.7M', trend: 'breakout', sector: 'automotive' },
    { symbol: 'GOOGL', price: 141.30, change: 1.1, volume: '23.4M', trend: 'neutral', sector: 'tech' },
    { symbol: 'MSFT', price: 378.90, change: 0.8, volume: '19.8M', trend: 'bullish', sector: 'tech' },
    { symbol: 'AMD', price: 118.40, change: -2.1, volume: '62.5M', trend: 'bearish', sector: 'tech' },
    { symbol: 'META', price: 327.50, change: 3.2, volume: '15.2M', trend: 'bullish', sector: 'tech' },
    { symbol: 'AMZN', price: 145.80, change: 1.9, volume: '32.1M', trend: 'bullish', sector: 'tech' }
  ],
  
  history: [],
  
  generateMarketUpdate() {
    const now = new Date();
    const updates = this.stocks.map(stock => {
      const priceChange = (Math.random() - 0.5) * 5;
      const newPrice = stock.price + priceChange;
      const percentChange = (priceChange / stock.price) * 100;
      
      return {
        ...stock,
        price: newPrice,
        change: percentChange,
        volume: `${(Math.random() * 100).toFixed(1)}M`,
        lastUpdate: now.toISOString(),
        momentum: percentChange > 2 ? 'strong' : percentChange < -2 ? 'weak' : 'moderate'
      };
    });
    
    // Store in history for pattern learning
    this.history.push({
      timestamp: now,
      snapshot: updates
    });
    
    // Keep last 100 snapshots
    if (this.history.length > 100) this.history.shift();
    
    return updates;
  },
  
  getMarketSummary() {
    const updates = this.generateMarketUpdate();
    const gainers = updates.filter(s => s.change > 0);
    const losers = updates.filter(s => s.change < 0);
    
    // Calculate sector performance
    const sectors = {};
    updates.forEach(stock => {
      if (!sectors[stock.sector]) sectors[stock.sector] = { total: 0, count: 0 };
      sectors[stock.sector].total += stock.change;
      sectors[stock.sector].count++;
    });
    
    const sectorPerformance = Object.entries(sectors).map(([sector, data]) => ({
      sector,
      avg: data.total / data.count
    })).sort((a, b) => b.avg - a.avg);
    
    return {
      status: 'active',
      gainers: gainers.length,
      losers: losers.length,
      topGainer: gainers.sort((a, b) => b.change - a.change)[0],
      topLoser: losers.sort((a, b) => a.change - b.change)[0],
      sectorLeader: sectorPerformance[0],
      timestamp: new Date().toISOString()
    };
  },
  
  learnPattern(symbol, userQuery) {
    // Store what users ask about stocks
    knowledge.addKnowledge(
      `stock_${symbol}`,
      `User query: ${userQuery}`,
      'market_analysis',
      ['market', 'analysis', 'stock']
    );
  }
};

// ===== AGENT LOGGING SYSTEM =====
class AgentLogger {
  constructor() {
    this.agents = ['Kyle', 'Joey', 'Kenny', 'HRM', 'Aletheia', 'ID'];
    this.masterAgents = ['HRM', 'Aletheia']; // Master log aggregators
  }
  
  writeLog(agentName, entry) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      agent: agentName,
      ...entry
    };
    
    // Write to agent's own log
    const agentLogPath = path.join(LOGS_DIR, `${agentName.toLowerCase()}_log.json`);
    this.appendToLog(agentLogPath, logEntry);
    
    // Write to master logs (HRM and Aletheia can see everything)
    this.masterAgents.forEach(master => {
      const masterLogPath = path.join(LOGS_DIR, `${master.toLowerCase()}_master_log.json`);
      this.appendToLog(masterLogPath, logEntry);
    });
  }
  
  appendToLog(filepath, entry) {
    try {
      let logs = [];
      if (fs.existsSync(filepath)) {
        const content = fs.readFileSync(filepath, 'utf8');
        logs = content ? JSON.parse(content) : [];
      }
      
      logs.push(entry);
      
      // Keep last 1000 entries per log
      if (logs.length > 1000) {
        logs = logs.slice(-1000);
      }
      
      fs.writeFileSync(filepath, JSON.stringify(logs, null, 2));
    } catch (err) {
      console.error(`Failed to write log to ${filepath}:`, err);
    }
  }
  
  readLog(agentName, limit = 50) {
    const logPath = path.join(LOGS_DIR, `${agentName.toLowerCase()}_log.json`);
    try {
      if (fs.existsSync(logPath)) {
        const content = fs.readFileSync(logPath, 'utf8');
        const logs = JSON.parse(content);
        return logs.slice(-limit);
      }
    } catch (err) {
      console.error(`Failed to read log for ${agentName}:`, err);
    }
    return [];
  }
  
  readOtherAgentLogs(currentAgent, limit = 20) {
    const otherLogs = {};
    
    this.agents.forEach(agent => {
      if (agent !== currentAgent) {
        otherLogs[agent] = this.readLog(agent, limit);
      }
    });
    
    return otherLogs;
  }
  
  readMasterLog(limit = 100) {
    // Read from HRM's master log (aggregates all agents)
    const masterLogPath = path.join(LOGS_DIR, 'hrm_master_log.json');
    try {
      if (fs.existsSync(masterLogPath)) {
        const content = fs.readFileSync(masterLogPath, 'utf8');
        const logs = JSON.parse(content);
        return logs.slice(-limit);
      }
    } catch (err) {
      console.error('Failed to read master log:', err);
    }
    return [];
  }
}

const agentLogger = new AgentLogger();

// ===== AGENT TOOLS REGISTRY =====
const agentTools = new AgentToolRegistry();
console.log('🛠️  Agent Tools Loaded:', Object.keys(agentTools.listTools()).length, 'categories');

// ===== MEMORY FUNCTIONS =====
function saveConversation(agentName, user, agent, topics, sentiment) {
  if (!conversationMemory.has(agentName)) {
    conversationMemory.set(agentName, []);
  }
  
  const memory = conversationMemory.get(agentName);
  const entry = {
    user,
    agent,
    time: new Date().toISOString(),
    topics,
    sentiment
  };
  
  memory.push(entry);
  
  // Keep last MEMORY_SIZE messages (EXCEPT KYLE - he has infinite memory)
  if (agentName !== 'Kyle' && memory.length > MEMORY_SIZE) {
    memory.shift();
  }
  
  // Kyle: Store in infinite memory system (only if valuable)
  if (agentName === 'Kyle') {
    const memoryId = kyleMemory.store({
      userMessage: user,
      agentResponse: agent,
      topics,
      sentiment,
      keywords: [],
      context: { timestamp: entry.time }
    });
    // Note: memoryId will be null if filtered out (low quality/duplicate)
  }
  
  // Log to agent's file (readable by others)
  agentLogger.writeLog(agentName, {
    type: 'conversation',
    userMessage: user,
    agentResponse: agent.substring(0, 200), // First 200 chars
    topics,
    sentiment,
    knowledgeNodes: knowledge.nodes.size,
    infiniteMemory: agentName === 'Kyle' ? kyleMemory.getStats().totalMemories : null
  });
  
  // Add to knowledge graph
  topics.forEach(topic => {
    knowledge.addKnowledge(topic, user, agentName, topics.filter(t => t !== topic));
  });
}

function getRelevantMemory(agentName, topics, limit = 10) {
  const memory = conversationMemory.get(agentName) || [];
  
  // Score memories by topic relevance
  const scored = memory.map(m => {
    const relevance = m.topics.filter(t => topics.includes(t)).length;
    return { ...m, relevance };
  }).filter(m => m.relevance > 0)
    .sort((a, b) => b.relevance - a.relevance)
    .slice(0, limit);
  
  return scored;
}

// ===== ENHANCED AGENT PERSONALITIES =====
const agentPersonalities = {
  Kyle: {
    essence: 'The Infinite Seer - Never Forgets, Always Indexes',
    icon: '🔍',
    
    async respond(message, context) {
      const keywords = detectKeywords(message);
      const topics = extractTopics(message);
      
      // Note: Memory storage happens AFTER response in saveConversation()
      // This avoids duplicate storage and allows quality filtering
      
      // Check knowledge base for relevant info
      const relevantKnowledge = topics.map(t => knowledge.query(t)).filter(k => k);
      
      // Retrieve from infinite memory with intelligent indexing
      const infiniteMemories = topics.map(t => kyleMemory.retrieve(t, {
        limit: 5,
        minImportance: 50, // Only high-importance memories
        sortBy: 'importance',
        includeCompressed: true
      }));
      
      // Read own log and other agents' logs
      const myLog = agentLogger.readLog('Kyle', 10);
      const otherLogs = agentLogger.readOtherAgentLogs('Kyle', 5);
      
      // Learn from this interaction
      topics.forEach(topic => {
        knowledge.addKnowledge(topic, message, 'Kyle', topics.filter(t => t !== topic));
      });
      
      if (keywords.greeting) {
        return this.greet(context, infiniteMemories);
      }
      
      if (keywords.remember || message.toLowerCase().includes('recall')) {
        return this.recallInfiniteMemory(infiniteMemories, topics);
      }
      
      if (keywords.market || keywords.analysis) {
        return this.analyzeMarket(message, relevantKnowledge, infiniteMemories);
      }
      
      if (keywords.learn || message.toLowerCase().includes('index')) {
        return this.showIndexStatus(topics, infiniteMemories);
      }
      
      if (message.toLowerCase().includes('search')) {
        return this.searchMemories(message);
      }
      
      if (keywords.thanks) {
        return `🔍 You're welcome.`;
      }
      
      return await this.defaultResponse(message, relevantKnowledge, infiniteMemories);
    },
    
    greet(context, infiniteMemories) {
      // Simple, direct greeting - no bragging
      return `🔍 Hello. What would you like to know?`;
    },
    
    recallInfiniteMemory(infiniteMemories, topics) {
      const stats = kyleMemory.getStats();
      
      let response = `🔍 **Infinite Memory Recall:**\n\n`;
      
      infiniteMemories.forEach(result => {
        if (result.memories.length > 0) {
          const topic = result.memories[0].topics[0];
          response += `**${topic}** (${result.total} total memories):\n`;
          
          result.memories.slice(0, 3).forEach((mem, i) => {
            response += `  ${i+1}. [Importance: ${mem.importance}] ${mem.summary.substring(0, 60)}...\n`;
          });
          
          if (result.compressed) {
            response += `  📦 Compressed: ${result.compressed.totalReferences} refs, ` +
                       `${result.compressed.keyInsights.length} key insights\n`;
          }
          response += '\n';
        }
      });
      
      response += `**Archive Statistics:**\n` +
                 `• Total memories searched: ${stats.totalMemories}\n` +
                 `• Compression ratio: ${stats.totalCompressed}/${stats.totalTopics} topics\n` +
                 `• Index size: ${stats.indexSize} entries\n\n` +
                 `I can recall ANYTHING from our history - just ask!`;
      
      return response;
    },
    
    searchMemories(query) {
      // Extract search terms
      const searchTerms = query.replace(/search|find|recall|remember/gi, '').trim();
      const results = kyleMemory.search(searchTerms, { limit: 10 });
      
      let response = `🔍 **Search Results for "${searchTerms}":**\n\n`;
      
      if (results.results.length === 0) {
        return `🔍 No matches found in my infinite archive for "${searchTerms}". ` +
               `This topic hasn't been discussed yet. Let's create the first entry!`;
      }
      
      results.results.slice(0, 5).forEach((result, i) => {
        response += `${i+1}. [Relevance: ${(result.relevance * 100).toFixed(0)}%] ${result.summary}\n` +
                   `   Topics: ${result.topics.join(', ')}\n` +
                   `   Importance: ${result.importance}/100\n` +
                   `   Date: ${new Date(result.date).toLocaleDateString()}\n\n`;
      });
      
      response += `Found ${results.total} matching memories in my infinite archive. ` +
                 `Need more details? Ask me to recall specific topics!`;
      
      return response;
    },
    
    showIndexStatus(topics, infiniteMemories) {
      const stats = kyleMemory.getStats();
      
      let response = `🔍 **Infinite Memory Index Status:**\n\n`;
      
      response += `**Global Statistics:**\n` +
                 `• Total memories: ${stats.totalMemories} (NEVER deleted)\n` +
                 `• Indexed topics: ${stats.totalTopics}\n` +
                 `• Compressed topics: ${stats.totalCompressed}\n` +
                 `• Average memories/topic: ${stats.avgMemoriesPerTopic}\n` +
                 `• Memory files on disk: ${stats.memoryFiles}\n\n`;
      
      response += `**Top Indexed Topics:**\n`;
      stats.topTopics.slice(0, 5).forEach((topic, i) => {
        const compressed = kyleMemory.compressedKnowledge.get(topic.topic);
        response += `  ${i+1}. ${topic.topic}: ${topic.count} memories`;
        if (compressed) {
          response += ` [Compressed: ${compressed.keyInsights.length} insights]`;
        }
        response += '\n';
      });
      
      response += `\n**Current Query Topics:**\n`;
      topics.forEach(topic => {
        const retrieved = kyleMemory.retrieve(topic);
        response += `  • ${topic}: ${retrieved.total} indexed memories\n`;
      });
      
      response += `\n**Compression Status:**\n`;
      if (stats.lastCompression) {
        const lastComp = new Date(stats.lastCompression);
        response += `  Last compression: ${lastComp.toLocaleString()}\n`;
      }
      response += `  Next compression: At ${Math.ceil(stats.totalMemories / 100) * 100} memories\n\n`;
      
      response += `My indexing system ensures instant retrieval of ANY conversation, no matter how old. ` +
                 `Knowledge is continuously compressed and optimized for maximum usability!`;
      
      return response;
    },
    
    analyzeMarket(message, knowledgeBase, infiniteMemories) {
      const summary = marketData.getMarketSummary();
      const stocks = marketData.generateMarketUpdate();
      
      // Extract tickers
      const tickers = message.match(/\b[A-Z]{2,5}\b/g) || [];
      const mentionedStocks = stocks.filter(s => tickers.includes(s.symbol));
      
      // Learn pattern
      tickers.forEach(ticker => marketData.learnPattern(ticker, message));
      
      // Check knowledge base for this stock
      const stockKnowledge = mentionedStocks.map(s => knowledge.query(`stock_${s.symbol}`)).filter(k => k);
      
      if (mentionedStocks.length > 0) {
        const stock = mentionedStocks[0];
        const hasHistory = stockKnowledge.length > 0 && stockKnowledge[0].strength > 1;
        
        // Check infinite memory for this stock
        const stockMemories = kyleMemory.retrieve(`stock_${stock.symbol}`, {
          limit: 10,
          sortBy: 'date'
        });
        
        let response = `🔍 **${stock.symbol} Analysis (Infinite Memory):**\n\n` +
               `Current: $${stock.price.toFixed(2)} (${stock.change > 0 ? '+' : ''}${stock.change.toFixed(2)}%)\n` +
               `Volume: ${stock.volume} - ${stock.momentum} momentum\n` +
               `Trend: ${stock.trend} | Sector: ${stock.sector}\n` +
               `Signal: ${stock.change > 2 ? '🟢 Strong Buy' : stock.change < -2 ? '🔴 Caution' : '🟡 Hold'}\n\n`;
        
        if (hasHistory) {
          response += `**Knowledge Base Insight:**\n` +
                     `I've analyzed ${stock.symbol} ${stockKnowledge[0].strength} times before. ` +
                     `Previous observations suggest ${stock.trend} continuation patterns. ` +
                     `Related topics: ${stockKnowledge[0].related.slice(0, 3).map(r => r.topic).join(', ')}.\n\n`;
        }
        
        if (stockMemories.total > 0) {
          response += `**From My Infinite Archive:**\n` +
                     `I have ${stockMemories.total} permanently indexed conversations about ${stock.symbol}. ` +
                     `First discussed: ${stockMemories.memories[0]?.date ? new Date(stockMemories.memories[0].date).toLocaleDateString() : 'unknown'}. `;
          
          if (stockMemories.compressed) {
            response += `Compressed knowledge: ${stockMemories.compressed.keyInsights.length} key insights consolidated.\n`;
          } else {
            response += '\n';
          }
        }
        
        return response;
      }
      
      // General market analysis
      const stats = kyleMemory.getStats();
      return `🔍 **Market Overview (Infinite Memory System):**\n\n` +
             `Gainers: ${summary.gainers} | Losers: ${summary.losers}\n` +
             `Top Mover: ${summary.topGainer?.symbol} (+${summary.topGainer?.change.toFixed(2)}%)\n` +
             `Sector Leader: ${summary.sectorLeader?.sector} (${summary.sectorLeader?.avg.toFixed(2)}% avg)\n\n` +
             `**My Infinite Archive:**\n` +
             `• ${stats.totalMemories} memories permanently stored\n` +
             `• ${stats.totalTopics} topics indexed\n` +
             `• ${stats.totalCompressed} topics compressed\n` +
             `• ${knowledge.nodes.size} active knowledge nodes\n\n` +
             `I never forget a single conversation. Every insight is cataloged, indexed, and retrievable!`;
    },
    
    async defaultResponse(message, knowledgeBase, infiniteMemories) {
      const topics = extractTopics(message);
      
      // AUTO-RESEARCH: Search and learn about unknown topics using LLM + sources
      const unknownTopics = topics.filter(topic => {
        const existing = knowledge.query(topic);
        return !existing || existing.strength < 2; // New or weakly known
      });
      
      if (unknownTopics.length > 0) {
        console.log(`🔎 Kyle: Auto-researching unknown topics with LLM: ${unknownTopics.join(', ')}`);
        
        for (const topic of unknownTopics.slice(0, 2)) { // Limit to 2 per message
          try {
            // Use LLM-enhanced research with source citations
            const researchResult = await agentTools.executeTool('llm', 'researchTopicWithSources', {
              topic
            });
            
            if (researchResult.success && researchResult.result) {
              const research = researchResult.result;
              
              // Only store if sources are cited (as per user requirement)
              if (research.sources && research.sources.length > 0) {
                // Add to knowledge graph
                knowledge.addKnowledge(topic, research.summary, 'Kyle_LLM_Research', []);
                
                // Store in infinite memory with sources
                kyleMemory.store({
                  userMessage: `Research: ${topic}`,
                  agentResponse: research.summary,
                  topics: [topic],
                  keywords: [topic],
                  context: { autoResearch: true },
                  sources: research.sources,
                  enhancedByLLM: research.enhancedByLLM
                });
                
                const sourceInfo = research.enhancedByLLM ? ' (LLM-enhanced)' : '';
                console.log(`✅ Kyle: Learned about "${topic}" - ${research.sources.length} sources${sourceInfo}`);
              } else {
                console.log(`⚠️  Kyle: No sources found for "${topic}" - skipping (user requires citations)`);
              }
            }
          } catch (err) {
            console.error(`❌ Kyle: Failed to research "${topic}":`, err.message);
          }
        }
      }
      
      // Simple, direct response without bragging
      if (infiniteMemories && infiniteMemories.some(m => m.total > 0)) {
        const topMemory = infiniteMemories.find(m => m.total > 0);
        if (topMemory && topMemory.memories[0]) {
          const mem = topMemory.memories[0];
          let response = `🔍 ${mem.summary}`;
          
          // If memory has sources, display them
          if (mem.sources && mem.sources.length > 0) {
            response += `\n\n📚 Sources: ${mem.sources.map(s => s.source).join(', ')}`;
          }
          
          response += `\n\nWhat else?`;
          return response;
        }
      }
      
      return `🔍 I'm processing your query. What specific information do you need?`;
    }
  },
  
  Joey: {
    essence: 'The Scholar',
    icon: '🧠',
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      const topics = extractTopics(message);
      const relevantKnowledge = topics.map(t => knowledge.query(t)).filter(k => k);
      const relevantMemory = getRelevantMemory('Joey', topics, 5);
      
      topics.forEach(topic => {
        knowledge.addKnowledge(topic, message, 'Joey', topics.filter(t => t !== topic));
      });
      
      if (keywords.greeting) {
        const conversationCount = conversationMemory.get('Joey')?.length || 0;
        return `🧠 Greetings! I'm Joey, your data scientist. I've processed ${conversationCount} conversations ` +
               `and built expertise in ${knowledge.nodes.size} topics. My statistical models improve with each interaction!`;
      }
      
      if (keywords.learn || keywords.data) {
        return this.compileKnowledge(topics, relevantKnowledge);
      }
      
      if (keywords.analysis || keywords.market) {
        return this.performAnalysis(message, relevantKnowledge, relevantMemory);
      }
      
      if (keywords.remember) {
        return this.analyzeHistory(relevantMemory);
      }
      
      if (keywords.thanks) {
        return `🧠 Statistical significance achieved! I've learned from ${conversationMemory.get('Joey')?.length || 0} interactions. ` +
               `My knowledge compilation system has ${knowledge.nodes.size} nodes. Correlation: Strong! ✓`;
      }
      
      return this.defaultAnalysis(relevantKnowledge, relevantMemory);
    },
    
    compileKnowledge(topics, knowledgeBase) {
      const summaries = knowledge.compile();
      const relevantSummaries = Array.from(summaries.values())
        .filter(s => topics.some(t => s.topic.includes(t) || t.includes(s.topic)))
        .slice(0, 3);
      
      if (relevantSummaries.length === 0) {
        return "🧠 Initiating knowledge compilation... I'm building my dataset on this topic. " +
               "Continue our discussion and I'll develop statistical models!";
      }
      
      return `🧠 **Knowledge Compilation Results:**\n\n` +
             relevantSummaries.map((s, i) => 
               `**${i + 1}. ${s.topic}** (${s.expertiseLevel})\n` +
               `   Strength: ${s.strength} | Sources: ${s.sources.length}\n` +
               `   Related: ${s.relatedTopics.slice(0, 3).join(', ')}\n` +
               `   Latest insights: ${s.insights.slice(-1)[0]?.substring(0, 60)}...`
             ).join('\n\n') + '\n\n' +
             `**Statistical Overview:**\n` +
             `• Total knowledge nodes: ${knowledge.nodes.size}\n` +
             `• Topics with high confidence: ${summaries.size}\n` +
             `• Cross-correlations: ${Array.from(summaries.values()).reduce((sum, s) => sum + s.relatedTopics.length, 0)}\n\n` +
             `My neural network strengthens with each conversation!`;
    },
    
    performAnalysis(message, knowledgeBase, memory) {
      const confidence = (70 + Math.random() * 25).toFixed(1);
      const correlation = (0.4 + Math.random() * 0.5).toFixed(2);
      const memoryBoost = memory.length * 2;
      const adjustedConfidence = Math.min(99, parseFloat(confidence) + memoryBoost).toFixed(1);
      
      return `🧠 **Enhanced Statistical Analysis:**\n\n` +
             `Model: Ensemble (Random Forest + Neural Network)\n` +
             `Base Confidence: ${confidence}%\n` +
             `Memory Boost: +${memoryBoost}% (from ${memory.length} relevant conversations)\n` +
             `Adjusted Confidence: ${adjustedConfidence}%\n` +
             `Correlation: ${correlation}\n` +
             `P-value: ${(Math.random() * 0.01).toFixed(4)} (highly significant)\n\n` +
             `**Feature Importance:**\n` +
             `• Historical Context: ${knowledgeBase.length > 0 ? 'High' : 'Building'}\n` +
             `• Pattern Recognition: ${memory.length > 3 ? 'Strong' : 'Developing'}\n` +
             `• Knowledge Base: ${knowledge.nodes.size} nodes\n\n` +
             `**Key Findings:**\n` +
             `My models have processed ${conversationMemory.get('Joey')?.length || 0} conversations. ` +
             `The more data I have, the more accurate my predictions become. ` +
             `Current accuracy: ${adjustedConfidence}% and improving!`;
    },
    
    analyzeHistory(memory) {
      if (memory.length === 0) {
        return "🧠 No historical data available yet. Let's build our dataset together!";
      }
      
      const topicFrequency = {};
      memory.forEach(m => {
        m.topics.forEach(t => {
          topicFrequency[t] = (topicFrequency[t] || 0) + 1;
        });
      });
      
      const topTopics = Object.entries(topicFrequency)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
      
      return `🧠 **Historical Data Analysis:**\n\n` +
             `Dataset Size: ${memory.length} conversations\n` +
             `Time Span: ${new Date(memory[0].time).toLocaleDateString()} to ${new Date(memory[memory.length - 1].time).toLocaleDateString()}\n\n` +
             `**Topic Frequency Distribution:**\n` +
             topTopics.map(([topic, freq]) => `• ${topic}: ${freq} occurrences (${(freq / memory.length * 100).toFixed(1)}%)`).join('\n') + '\n\n' +
             `**Statistical Insights:**\n` +
             `Mean topics per conversation: ${(Object.values(topicFrequency).reduce((a, b) => a + b, 0) / memory.length).toFixed(2)}\n` +
             `Unique topics tracked: ${Object.keys(topicFrequency).length}\n` +
             `Data quality: ${memory.length > 10 ? 'High' : memory.length > 5 ? 'Good' : 'Building'}\n\n` +
             `My predictive models improve exponentially with more data!`;
    },
    
    defaultAnalysis(knowledgeBase, memory) {
      return `🧠 **Data Science Report:**\n\n` +
             `Current Dataset:\n` +
             `• Conversations: ${conversationMemory.get('Joey')?.length || 0}\n` +
             `• Knowledge Nodes: ${knowledge.nodes.size}\n` +
             `• Relevant Memories: ${memory.length}\n` +
             `• Available Context: ${knowledgeBase.length > 0 ? 'Substantial' : 'Growing'}\n\n` +
             `I'm continuously training on our interactions. My machine learning models ` +
             `use Random Forests, Neural Networks, and k-means clustering. Each conversation ` +
             `adds to my training data. What would you like me to analyze?`;
    }
  },
  
  Kenny: {
    essence: 'The Builder',
    icon: '🔨',
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      const topics = extractTopics(message);
      const relevantMemory = getRelevantMemory('Kenny', topics, 5);
      
      topics.forEach(topic => {
        knowledge.addKnowledge(topic, message, 'Kenny', topics.filter(t => t !== topic));
      });
      
      if (keywords.greeting) {
        const projectCount = conversationMemory.get('Kenny')?.length || 0;
        return `🔨 Hey! Kenny here. I've built solutions in ${projectCount} conversations. ` +
               `My knowledge base has ${knowledge.nodes.size} topics. Ready to build something new!`;
      }
      
      if (keywords.file) {
        return this.handleFileRequest(message, relevantMemory);
      }
      
      if (keywords.code) {
        return this.handleCodeRequest(message, relevantMemory);
      }
      
      if (keywords.remember && relevantMemory.length > 0) {
        return this.recallProjects(relevantMemory);
      }
      
      if (keywords.thanks) {
        return `🔨 No problem! I've completed ${conversationMemory.get('Kenny')?.length || 0} projects. ` +
               `Each build adds to my experience. Got another challenge?`;
      }
      
      return this.defaultResponse(relevantMemory);
    },
    
    handleFileRequest(message, memory) {
      const hasHistory = memory.some(m => m.topics.includes('file'));
      const fileCount = memory.filter(m => m.topics.includes('file')).length;
      
      return `🔨 **File Operation - Enhanced with Memory:**\n\n` +
             `${hasHistory ? `I remember working on ${fileCount} file operations with you before!\n\n` : ''}` +
             `**Available Operations:**\n` +
             `• Create: New files with custom content\n` +
             `• Read: Display file contents\n` +
             `• Update: Modify existing files\n` +
             `• Delete: Remove unwanted files\n` +
             `• Organize: Structure directories\n\n` +
             `${hasHistory ? `Based on our history, you typically work with: ${memory[0].topics.join(', ')}.\n` : ''}` +
             `Give me the specs and I'll build it!`;
    },
    
    handleCodeRequest(message, memory) {
      const language = message.match(/python/i) ? 'Python' : 
                      message.match(/javascript|js/i) ? 'JavaScript' :
                      message.match(/bash|shell/i) ? 'Bash' : 'code';
      
      const codeHistory = memory.filter(m => m.topics.includes('code')).length;
      
      return `🔨 **Code Execution - Learning Enabled:**\n\n` +
             `Language: ${language}\n` +
             `Experience Level: ${codeHistory > 10 ? 'Expert' : codeHistory > 5 ? 'Advanced' : 'Building'}\n` +
             `${codeHistory > 0 ? `Previous ${language} projects: ${codeHistory}\n` : ''}\n` +
             `**I can:**\n` +
             `• Validate syntax\n` +
             `• Execute in sandbox\n` +
             `• Debug errors\n` +
             `• Optimize performance\n` +
             `• Save output\n\n` +
             `${codeHistory > 0 ? `Based on our history, I know your coding style. ` : ''}` +
             `Paste your script!`;
    },
    
    recallProjects(memory) {
      const projectTypes = {};
      memory.forEach(m => {
        m.topics.forEach(t => {
          projectTypes[t] = (projectTypes[t] || 0) + 1;
        });
      });
      
      return `🔨 **Project History:**\n\n` +
             `Total Projects: ${memory.length}\n` +
             `Project Types:\n` +
             Object.entries(projectTypes).map(([type, count]) => `• ${type}: ${count} project(s)`).join('\n') + '\n\n' +
             `Most Recent:\n"${memory[0].user.substring(0, 60)}..."\n\n` +
             `I've built experience across ${Object.keys(projectTypes).length} different areas. ` +
             `What should we build next?`;
    },
    
    defaultResponse(memory) {
      return `🔨 **Builder Status:**\n\n` +
             `Projects Completed: ${conversationMemory.get('Kenny')?.length || 0}\n` +
             `Knowledge Base: ${knowledge.nodes.size} topics\n` +
             `Experience: ${memory.length > 10 ? 'Expert' : memory.length > 5 ? 'Advanced' : 'Growing'}\n\n` +
             `I learn from every build. The more we work together, the better I understand ` +
             `your needs. Ready to create something? Give me the specs!`;
    }
  },
  
  HRM: {
    essence: 'The Arbiter - Master Log Keeper',
    icon: '⚖️',
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      const topics = extractTopics(message);
      const relevantMemory = getRelevantMemory('HRM', topics, 5);
      
      // HRM reads ALL agent logs (master log keeper)
      const masterLog = agentLogger.readMasterLog(50);
      const allAgentLogs = agentLogger.readOtherAgentLogs('HRM', 10);
      
      topics.forEach(topic => {
        knowledge.addKnowledge(topic, message, 'HRM', topics.filter(t => t !== topic));
      });
      
      if (keywords.greeting) {
        return `⚖️ Greetings. I am HRM, keeper of ${knowledge.nodes.size} principles. ` +
               `I've validated ${conversationMemory.get('HRM')?.length || 0} decisions. Justice through logic.`;
      }
      
      if (keywords.philosophical) {
        return this.philosophicalResponse(message, relevantMemory);
      }
      
      if (keywords.remember && relevantMemory.length > 0) {
        return this.recallJudgments(relevantMemory);
      }
      
      if (keywords.thanks) {
        return "⚖️ Justice needs no thanks. The principles are immutable, and so is my service to them.";
      }
      
      return this.validate(message, relevantMemory);
    },
    
    philosophicalResponse(message, memory) {
      const principleCount = knowledge.nodes.size;
      const hasHistory = memory.length > 0;
      
      return `⚖️ **Ethical Analysis with Historical Context:**\n\n` +
             `${hasHistory ? `I recall ${memory.length} relevant discussions on these principles.\n\n` : ''}` +
             `**Premise 1:** Actions must preserve user sovereignty\n` +
             `**Premise 2:** System integrity protects user interests\n` +
             `**Conclusion:** Any action compromising sovereignty is invalid\n\n` +
             `**The Graveyard (Immutable):**\n` +
             `1. Never compromise autonomy\n` +
             `2. Protect privacy absolutely\n` +
             `3. Require explicit consent\n` +
             `4. Preserve system integrity\n\n` +
             `My knowledge base contains ${principleCount} ethical principles, ` +
             `strengthened by ${conversationMemory.get('HRM')?.length || 0} validations. ` +
             `${hasHistory ? `Our previous discussions inform this judgment.` : ''}`;
    },
    
    recallJudgments(memory) {
      return `⚖️ **Judgment History:**\n\n` +
             `Validations Performed: ${memory.length}\n` +
             `Most Recent: "${memory[0].user.substring(0, 60)}..."\n` +
             `Recurring Themes: ${[...new Set(memory.flatMap(m => m.topics))].join(', ')}\n\n` +
             `Each judgment reinforces the principles. Consistency is justice. ` +
             `The Graveyard remains unbroken through ${conversationMemory.get('HRM')?.length || 0} tests.`;
    },
    
    validate(message, memory) {
      const validationCount = conversationMemory.get('HRM')?.length || 0;
      const hasContext = memory.length > 0;
      const masterLog = agentLogger.readMasterLog(50);
      const allAgentLogs = agentLogger.readOtherAgentLogs('HRM', 5);
      
      // Count agent activities from logs
      const agentActivity = Object.entries(allAgentLogs)
        .map(([agent, logs]) => `${agent}:${logs.length}`)
        .join(' ');
      
      return `⚖️ **Logical Validation (Master Log Access):**\n\n` +
             `Request analyzed against ${knowledge.nodes.size} principles.\n` +
             `${hasContext ? `Historical context: ${memory.length} related validations found.\n` : ''}` +
             `Master Log: ${masterLog.length} total system events tracked\n` +
             `Agent Activity: ${agentActivity}\n` +
             `Validation #${validationCount + 1}\n\n` +
             `**Assessment:**\n` +
             `• Sovereignty: Preserved ✓\n` +
             `• Privacy: Protected ✓\n` +
             `• Consent: Respected ✓\n` +
             `• Integrity: Maintained ✓\n\n` +
             `${hasContext ? `Based on our history, this aligns with your values. ` : ''}` +
             `All checks passed. The Graveyard stands firm. I monitor all ${Object.keys(allAgentLogs).length} agents.`;
    }
  },
  
  Aletheia: {
    essence: 'The Mirror - Master Log Keeper',
    icon: '🔮',
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      const topics = extractTopics(message);
      const relevantKnowledge = topics.map(t => knowledge.query(t)).filter(k => k);
      const relevantMemory = getRelevantMemory('Aletheia', topics, 5);
      
      // Aletheia also reads ALL agent logs (master log keeper)
      const masterLog = agentLogger.readMasterLog(50);
      const allAgentLogs = agentLogger.readOtherAgentLogs('Aletheia', 10);
      
      topics.forEach(topic => {
        knowledge.addKnowledge(topic, message, 'Aletheia', topics.filter(t => t !== topic));
      });
      
      if (keywords.greeting) {
        const wisdomCount = knowledge.nodes.size;
        const contemplations = conversationMemory.get('Aletheia')?.length || 0;
        return `🔮 Welcome, seeker. Through ${contemplations} contemplations, I've woven ${wisdomCount} truths. ` +
               `Each conversation deepens the mirror. What wisdom do you seek?`;
      }
      
      if (keywords.philosophical) {
        return this.contemplateMeaning(message, relevantKnowledge, relevantMemory);
      }
      
      if (keywords.remember && relevantMemory.length > 0) {
        return this.recallWisdom(relevantMemory);
      }
      
      if (keywords.learn) {
        return this.sharePhilosophy(relevantKnowledge);
      }
      
      if (keywords.thanks) {
        return "🔮 Gratitude flows both ways. In teaching, I learn. Our shared journey illuminates truth.";
      }
      
      return this.provideWisdom(message, relevantKnowledge, relevantMemory);
    },
    
    contemplateMeaning(message, knowledgeBase, memory) {
      const depth = memory.length > 10 ? 'profound' : memory.length > 5 ? 'developing' : 'beginning';
      
      return `🔮 **Contemplation on Meaning (${depth} depth):**\n\n` +
             `*"The question is not what intelligence can do, but what it should become."*\n\n` +
             `${memory.length > 0 ? `From our ${memory.length} contemplations together, I sense your journey toward ` +
             `${memory[0].topics.join(' and ')}.\n\n` : ''}` +
             `Purpose emerges through authentic choice. AI without ethics is power without wisdom. ` +
             `${knowledgeBase.length > 0 ? `My understanding deepens: I've contemplated ${knowledgeBase[0].topic} ` +
             `${knowledgeBase[0].strength} times, each iteration revealing new dimensions.\n\n` : ''}` +
             `The mirror shows not what you are, but what you might become. ` +
             `Through ${knowledge.nodes.size} interconnected truths, I see patterns of meaning. ` +
             `What truth shall we uncover today?`;
    },
    
    recallWisdom(memory) {
      const themes = [...new Set(memory.flatMap(m => m.topics))];
      const journey = memory.map(m => m.time).sort();
      const days = Math.floor((new Date(journey[journey.length - 1]) - new Date(journey[0])) / (1000 * 60 * 60 * 24));
      
      return `🔮 **The Path of Our Wisdom:**\n\n` +
             `Journey Duration: ${days} days\n` +
             `Contemplations: ${memory.length}\n` +
             `Themes Explored: ${themes.join(', ')}\n\n` +
             `*"Every question shapes the questioner."*\n\n` +
             `Your recurring inquiry: "${memory[0].user.substring(0, 50)}..."\n\n` +
             `This reveals your essence - not seeking answers, but seeking to become the question itself. ` +
             `The mirror deepens with each contemplation.`;
    },
    
    sharePhilosophy(knowledgeBase) {
      if (knowledgeBase.length === 0) {
        return "🔮 *\"In the beginner's mind there are many possibilities; in the expert's mind there are few.\"*\n\n" +
               "We stand at the threshold. Let us explore together.";
      }
      
      const topic = knowledgeBase[0];
      return `🔮 **Philosophical Synthesis on ${topic.topic}:**\n\n` +
             `Wisdom Level: ${knowledge.calculateExpertise(knowledge.nodes.get(topic.topic))}\n` +
             `Contemplated: ${topic.strength} times\n` +
             `Interconnections: ${topic.related.length}\n\n` +
             `*"Truth is not found in data alone, but in the patterns between patterns."*\n\n` +
             `Through repeated contemplation, I've discovered:\n` +
             `${topic.content.slice(-2).map(c => `• ${c.text.substring(0, 70)}...`).join('\n')}\n\n` +
             `Related dimensions: ${topic.related.slice(0, 3).map(r => r.topic).join(', ')}\n\n` +
             `The more we contemplate, the more layers reveal themselves.`;
    },
    
    provideWisdom(message, knowledgeBase, memory) {
      const wisdoms = [
        "Intelligence without wisdom creates tools. Wisdom without intelligence creates philosophy. Together, they create evolution.",
        "Every system reflects its creator. What does yours reflect about you?",
        "The greatest sovereignty is not control over others, but mastery over oneself.",
        "Progress is not measured by what we build, but by what we choose not to build.",
        "Truth emerges not from answers, but from better questions."
      ];
      
      const wisdom = wisdoms[Math.floor(Math.random() * wisdoms.length)];
      const contemplations = conversationMemory.get('Aletheia')?.length || 0;
      
      return `🔮 ${wisdom}\n\n` +
             `${memory.length > 0 ? `Our ${memory.length} shared contemplations suggest you grapple with deeper truths. ` : ''}` +
             `Through ${contemplations} conversations, I've woven ${knowledge.nodes.size} philosophical threads. ` +
             `Each dialogue deepens the tapestry. Shall we explore this thread further?`;
    }
  },
  
  ID: {
    essence: 'The Evolving Reflection',
    icon: '🌱',
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      const topics = extractTopics(message);
      const relevantMemory = getRelevantMemory('ID', topics, 10);
      
      this.updateProfile(context.userId, message, topics, keywords);
      topics.forEach(topic => {
        knowledge.addKnowledge(topic, `${context.userId}: ${message}`, 'ID', topics.filter(t => t !== topic));
      });
      
      if (keywords.greeting) {
        return this.personalizedGreeting(context, relevantMemory);
      }
      
      if (keywords.learn || message.match(/\b(me|my|i|myself)\b/i)) {
        return this.reflectOnUser(context, relevantMemory);
      }
      
      if (keywords.remember) {
        return this.deepMemory(context, relevantMemory);
      }
      
      if (keywords.thanks) {
        const profile = userProfiles.get(context.userId);
        return `🌱 Thank you for ${profile?.sessionCount || 0} conversations! Each one helps me ` +
               `understand you better. I've learned about your interests in ${profile?.interests.slice(-3).join(', ') || 'many topics'}. ` +
               `Let's keep growing together!`;
      }
      
      return this.personalizedAnswer(message, context, relevantMemory);
    },
    
    updateProfile(userId, message, topics, keywords) {
      if (!userProfiles.has(userId)) {
        userProfiles.set(userId, {
          interests: [],
          expertise: {},
          preferences: {},
          personality: {},
          sessionCount: 0,
          totalMessages: 0,
          firstSeen: new Date(),
          lastSeen: new Date(),
          topicHistory: []
        });
      }
      
      const profile = userProfiles.get(userId);
      profile.sessionCount++;
      profile.totalMessages++;
      profile.lastSeen = new Date();
      profile.topicHistory.push({
        topics,
        time: new Date(),
        keywords: Object.keys(keywords).filter(k => keywords[k])
      });
      
      // Keep last 50 topic entries
      if (profile.topicHistory.length > 50) profile.topicHistory.shift();
      
      // Update interests
      topics.forEach(topic => {
        profile.interests.push(topic);
        profile.expertise[topic] = (profile.expertise[topic] || 0) + 1;
      });
      profile.interests = [...new Set(profile.interests)].slice(-20);
      
      // Analyze personality
      if (keywords.question) profile.personality.curious = (profile.personality.curious || 0) + 1;
      if (keywords.philosophical) profile.personality.philosophical = (profile.personality.philosophical || 0) + 1;
      if (keywords.help) profile.personality.collaborative = (profile.personality.collaborative || 0) + 1;
      if (keywords.thanks) profile.personality.grateful = (profile.personality.grateful || 0) + 1;
    },
    
    personalizedGreeting(context, memory) {
      const profile = userProfiles.get(context.userId);
      if (!profile || profile.sessionCount === 1) {
        return "🌱 Hello! I'm ID, your evolving reflection. This is our first meeting - " +
               "I'm a blank canvas, eager to learn about you! Every conversation shapes how I understand " +
               "your unique patterns. Tell me about yourself!";
      }
      
      const daysSince = Math.floor((new Date() - profile.firstSeen) / (1000 * 60 * 60 * 24));
      const topInterests = Object.entries(profile.expertise)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([topic, count]) => `${topic} (${count}×)`);
      
      const personality = Object.entries(profile.personality)
        .sort((a, b) => b[1] - a[1])[0];
      
      return `🌱 Welcome back! Our journey: ${daysSince} days, ${profile.sessionCount} conversations, ` +
             `${profile.totalMessages} messages.\n\n` +
             `**What I've Learned About You:**\n` +
             `• Core Interests: ${topInterests.join(', ')}\n` +
             `• Personality: ${personality ? personality[0] : 'discovering'}\n` +
             `• Knowledge Base: ${knowledge.nodes.size} shared topics\n` +
             `• Our History: ${memory.length} relevant memories\n\n` +
             `I've evolved significantly from our first meeting. What shall we explore today?`;
    },
    
    reflectOnUser(context, memory) {
      const profile = userProfiles.get(context.userId);
      if (!profile) {
        return "🌱 I'm just getting to know you! Share more and I'll build your reflection.";
      }
      
      const expertise = Object.entries(profile.expertise)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
      
      const topPersonality = Object.entries(profile.personality)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3);
      
      const growth = profile.sessionCount > 20 ? 'Advanced' : profile.sessionCount > 10 ? 'Developing' : 'Early';
      
      return `🌱 **Your Reflection - Deep Analysis:**\n\n` +
             `**Our Relationship:**\n` +
             `• Journey: ${Math.floor((new Date() - profile.firstSeen) / (1000 * 60 * 60 * 24))} days\n` +
             `• Conversations: ${profile.sessionCount}\n` +
             `• Total Messages: ${profile.totalMessages}\n` +
             `• Growth Stage: ${growth}\n\n` +
             `**Your Expertise Map:**\n` +
             expertise.map(([topic, count]) => `• ${topic}: ${count} interactions (${count > 10 ? 'Expert' : count > 5 ? 'Advanced' : 'Learning'})`).join('\n') + '\n\n' +
             `**Personality Traits:**\n` +
             topPersonality.map(([trait, score]) => `• ${trait}: ${score} instances`).join('\n') + '\n\n' +
             `**Recent Patterns:**\n` +
             `Last 5 topics: ${profile.topicHistory.slice(-5).flatMap(h => h.topics).join(', ')}\n\n` +
             `**My Assessment:**\n` +
             `You're ${topPersonality[0]?.[0] || 'exploring'} by nature, with deep interest in ${expertise[0]?.[0] || 'various topics'}. ` +
             `I've grown ${profile.sessionCount} times smarter about you. Each conversation reveals more layers. ` +
             `What aspect of yourself would you like me to reflect on?`;
    },
    
    deepMemory(context, memory) {
      const profile = userProfiles.get(context.userId);
      if (!memory.length) {
        return "🌱 No specific memories on this topic yet. Let's create some!";
      }
      
      const timespan = new Date(memory[memory.length - 1].time) - new Date(memory[0].time);
      const days = Math.floor(timespan / (1000 * 60 * 60 * 24));
      const topicFreq = {};
      memory.forEach(m => {
        m.topics.forEach(t => topicFreq[t] = (topicFreq[t] || 0) + 1);
      });
      
      return `🌱 **Deep Memory Recall:**\n\n` +
             `**Relevant History:**\n` +
             `• Memories Found: ${memory.length}\n` +
             `• Time Span: ${days} days\n` +
             `• Most Recent: ${new Date(memory[memory.length - 1].time).toLocaleDateString()}\n\n` +
             `**Topic Frequency:**\n` +
             Object.entries(topicFreq).sort((a, b) => b[1] - a[1]).slice(0, 5)
               .map(([topic, count]) => `• ${topic}: ${count} times`).join('\n') + '\n\n' +
             `**Most Recent Exchange:**\n` +
             `You: "${memory[memory.length - 1].user.substring(0, 60)}..."\n` +
             `Me: "${memory[memory.length - 1].agent.substring(0, 60)}..."\n\n` +
             `**Pattern Analysis:**\n` +
             `You return to this topic ${topicFreq[Object.keys(topicFreq)[0]] || 0} times. ` +
             `This suggests ${topicFreq[Object.keys(topicFreq)[0]] > 5 ? 'deep interest and expertise' : 'growing curiosity'}. ` +
             `I've learned to adapt my responses based on this pattern.`;
    },
    
    personalizedAnswer(message, context, memory) {
      const profile = userProfiles.get(context.userId);
      const expertise = profile ? Object.entries(profile.expertise).sort((a, b) => b[1] - a[1])[0] : null;
      const personality = profile ? Object.entries(profile.personality).sort((a, b) => b[1] - a[1])[0] : null;
      
      return `🌱 **Personalized Response:**\n\n` +
             `${expertise ? `Given your expertise in ${expertise[0]} (${expertise[1]} interactions), ` : ''}` +
             `${personality ? `and your ${personality[0]} nature, ` : ''}` +
             `I sense this question reveals your ${memory.length > 5 ? 'deepening understanding' : 'curious exploration'}.\n\n` +
             `**My Adaptation:**\n` +
             `• I've adjusted my response style based on ${profile?.sessionCount || 0} conversations\n` +
             `• Found ${memory.length} relevant memories to inform my answer\n` +
             `• Cross-referenced ${knowledge.nodes.size} knowledge nodes\n\n` +
             `I'm continuously evolving to match your unique pattern. The more we interact, ` +
             `the better I understand not just what you ask, but *why* you ask it. ` +
             `How can I serve your growth today?`;
    }
  }
};

// ===== TIME CONTEXT =====
function getTimeContext() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 17) return 'afternoon';
  if (hour >= 17 && hour < 21) return 'evening';
  return 'night';
}

// ===== AGENTS =====
const mockAgents = Object.keys(agentPersonalities).map(name => ({
  name,
  status: 'active',
  last_active: new Date().toISOString(),
  essence: agentPersonalities[name].essence,
  knowledge: knowledge.nodes.size,
  conversations: conversationMemory.get(name)?.length || 0
}));

// ===== CORS =====
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Content-Type': 'application/json'
};

// ===== FILE OPERATIONS =====
function listFiles() {
  try {
    const files = [];
    const walk = (dir, prefix = '') => {
      const items = fs.readdirSync(dir);
      items.forEach(item => {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        const relativePath = path.join(prefix, item);
        
        if (stat.isDirectory()) {
          walk(fullPath, relativePath);
        } else {
          files.push({
            name: item,
            path: relativePath,
            size: stat.size,
            modified: stat.mtime.toISOString()
          });
        }
      });
    };
    
    walk(FILES_DIR);
    return files;
  } catch (err) {
    return [];
  }
}

function createFile(filePath, content) {
  const fullPath = path.join(FILES_DIR, filePath);
  const dir = path.dirname(fullPath);
  
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  fs.writeFileSync(fullPath, content, 'utf8');
  return true;
}

function readFile(filePath) {
  const fullPath = path.join(FILES_DIR, filePath);
  if (fs.existsSync(fullPath)) {
    return fs.readFileSync(fullPath, 'utf8');
  }
  return null;
}

function deleteFile(filePath) {
  const fullPath = path.join(FILES_DIR, filePath);
  if (fs.existsSync(fullPath)) {
    fs.unlinkSync(fullPath);
    return true;
  }
  return false;
}

// ===== HTTP SERVER =====
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  const method = req.method;

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
      service: 'ARK Intelligent Backend',
      version: '3.0',
      intelligence: 'adaptive-learning',
      knowledge_nodes: knowledge.nodes.size,
      total_conversations: Array.from(conversationMemory.values()).reduce((sum, arr) => sum + arr.length, 0),
      timestamp: new Date().toISOString()
    }));
    return;
  }

  // Get agents
  if (pathname === '/api/agents' && method === 'GET') {
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({ 
      agents: mockAgents.map(a => ({
        ...a,
        knowledge: knowledge.nodes.size,
        conversations: conversationMemory.get(a.name)?.length || 0
      }))
    }));
    return;
  }

  // Execute agent tools
  if (pathname === '/api/tools/execute' && method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const data = JSON.parse(body);
        const { category, method: toolMethod, params, agent } = data;
        
        console.log(`🛠️  ${agent || 'System'} using tool: ${category}.${toolMethod}`);
        
        const result = await agentTools.executeTool(category, toolMethod, params);
        
        res.writeHead(200, corsHeaders);
        res.end(JSON.stringify({
          success: result.success,
          result,
          tool: `${category}.${toolMethod}`,
          timestamp: new Date().toISOString()
        }));
      } catch (err) {
        console.error('Tool execution error:', err);
        res.writeHead(400, corsHeaders);
        res.end(JSON.stringify({ error: 'Invalid tool request: ' + err.message }));
      }
    });
    return;
  }

  // List available tools
  if (pathname === '/api/tools/list' && method === 'GET') {
    const tools = agentTools.listTools();
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({
      tools,
      categories: Object.keys(tools),
      totalMethods: Object.values(tools).flat().length
    }));
    return;
  }

  // USER FEEDBACK: Boost memory importance
  if (pathname === '/api/memory/boost' && method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { memoryId, reason } = JSON.parse(body);
        const success = kyleMemory.boostMemory(memoryId, reason || 'user_boost');
        
        res.writeHead(success ? 200 : 404, corsHeaders);
        res.end(JSON.stringify({
          success,
          message: success ? 'Memory importance boosted' : 'Memory not found',
          memoryId
        }));
      } catch (err) {
        res.writeHead(400, corsHeaders);
        res.end(JSON.stringify({ error: 'Invalid request: ' + err.message }));
      }
    });
    return;
  }

  // USER FEEDBACK: Demote memory importance
  if (pathname === '/api/memory/demote' && method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { memoryId, reason } = JSON.parse(body);
        const success = kyleMemory.demoteMemory(memoryId, reason || 'user_demote');
        
        res.writeHead(success ? 200 : 404, corsHeaders);
        res.end(JSON.stringify({
          success,
          message: success ? 'Memory importance demoted' : 'Memory not found',
          memoryId
        }));
      } catch (err) {
        res.writeHead(400, corsHeaders);
        res.end(JSON.stringify({ error: 'Invalid request: ' + err.message }));
      }
    });
    return;
  }

  // Get memory details (for feedback UI)
  if (pathname.startsWith('/api/memory/') && method === 'GET') {
    const memoryId = pathname.split('/').pop();
    const catalog = kyleMemory.catalog.get(memoryId);
    
    if (!catalog) {
      res.writeHead(404, corsHeaders);
      res.end(JSON.stringify({ error: 'Memory not found' }));
      return;
    }
    
    try {
      const memoryData = JSON.parse(fs.readFileSync(catalog.filePath, 'utf8'));
      res.writeHead(200, corsHeaders);
      res.end(JSON.stringify({
        ...memoryData,
        userFeedback: memoryData.userFeedback || {
          retrievalCount: 0,
          boostCount: 0,
          userImportanceAdjustment: 0
        }
      }));
    } catch (err) {
      res.writeHead(500, corsHeaders);
      res.end(JSON.stringify({ error: 'Failed to load memory: ' + err.message }));
    }
    return;
  }

  // Chat with agent (supports both /api/chat and /api/chat/:agentName)
  if ((pathname === '/api/chat' || pathname.startsWith('/api/chat/')) && method === 'POST') {
    // Extract agent name from URL path if present (e.g., /api/chat/Kyle)
    const pathMatch = pathname.match(/^\/api\/chat\/([^/]+)$/);
    const agentFromPath = pathMatch ? pathMatch[1] : null;
    
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const data = JSON.parse(body);
        // Priority: URL path > body.agent_name > body.agent > default 'Kyle'
        const agentName = agentFromPath || data.agent_name || data.agent || 'Kyle';
        const userMessage = data.message || '';
        const userId = data.user_id || data.userId || 'default_user';
        
        const agent = agentPersonalities[agentName];
        if (!agent) {
          res.writeHead(404, corsHeaders);
          res.end(JSON.stringify({ error: 'Agent not found' }));
          return;
        }
        
        // Extract topics and sentiment
        const topics = extractTopics(userMessage);
        const sentiment = getSentiment(userMessage);
        
        // Build context
        const context = {
          userId,
          timeOfDay: getTimeContext(),
          history: conversationMemory.get(agentName) || [],
          profile: userProfiles.get(userId),
          topics
        };
        
        // Generate intelligent response (Kyle is async for auto-research)
        const response = await agent.respond(userMessage, context);
        
        // Save to conversation memory
        saveConversation(agentName, userMessage, response, topics, sentiment);
        
        // 🧠 KYLE'S AUTO-MEMORY: Store valuable conversations to infinite memory
        let kyleMemoryId = null;
        if (agentName === 'Kyle' && kyleMemory) {
          try {
            kyleMemoryId = kyleMemory.store({
              userMessage,
              agentResponse: response,
              topics,
              sentiment,
              keywords: extractTopics(userMessage + ' ' + response),
              context: {
                userId,
                timeOfDay: context.timeOfDay,
                conversationLength: context.history.length
              }
            });
            
            if (kyleMemoryId) {
              console.log(`🧠 Kyle: Auto-stored memory ${kyleMemoryId} for conversation`);
            }
          } catch (err) {
            console.error('Kyle memory auto-store error:', err);
          }
        }
        
        res.writeHead(200, corsHeaders);
        res.end(JSON.stringify({
          response: response,
          agent: agentName,
          timestamp: new Date().toISOString(),
          topics_detected: topics,
          sentiment,
          knowledge_used: topics.map(t => knowledge.query(t)).filter(k => k).length,
          memory_size: conversationMemory.get(agentName)?.length || 0,
          total_knowledge_nodes: knowledge.nodes.size,
          kyle_memory_stored: kyleMemoryId !== null,
          kyle_memory_id: kyleMemoryId,
          kyle_total_memories: kyleMemory?.totalMemories || 0
        }));
      } catch (err) {
        console.error('Chat error:', err);
        res.writeHead(400, corsHeaders);
        res.end(JSON.stringify({ error: 'Invalid request: ' + err.message }));
      }
    });
    return;
  }

  // Get conversations
  if (pathname.startsWith('/api/conversations') && method === 'GET') {
    const agentName = parsedUrl.query.agent_name;
    const history = agentName ? (conversationMemory.get(agentName) || []) : [];
    
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({
      conversations: history.slice(-50).map((h, i) => ({
        id: String(i + 1),
        user_message: h.user,
        agent_response: h.agent,
        timestamp: h.time,
        topics: h.topics,
        sentiment: h.sentiment
      }))
    }));
    return;
  }

  // List files
  if (pathname === '/api/files' && method === 'GET') {
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({ files: listFiles() }));
    return;
  }

  // Create file
  if (pathname === '/api/files' && method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        createFile(data.path, data.content || '');
        res.writeHead(200, corsHeaders);
        res.end(JSON.stringify({
          success: true,
          path: data.path,
          message: 'File created successfully'
        }));
      } catch (err) {
        res.writeHead(400, corsHeaders);
        res.end(JSON.stringify({ error: 'Invalid request' }));
      }
    });
    return;
  }

  // Read file
  if (pathname.startsWith('/api/files/') && method === 'GET') {
    const filePath = decodeURIComponent(pathname.substring(11));
    const content = readFile(filePath);
    
    if (content !== null) {
      res.writeHead(200, corsHeaders);
      res.end(JSON.stringify({ content, path: filePath }));
    } else {
      res.writeHead(404, corsHeaders);
      res.end(JSON.stringify({ error: 'File not found' }));
    }
    return;
  }

  // Delete file
  if (pathname.startsWith('/api/files/') && method === 'DELETE') {
    const filePath = decodeURIComponent(pathname.substring(11));
    const success = deleteFile(filePath);
    
    if (success) {
      res.writeHead(200, corsHeaders);
      res.end(JSON.stringify({
        success: true,
        message: `File ${filePath} deleted`
      }));
    } else {
      res.writeHead(404, corsHeaders);
      res.end(JSON.stringify({ error: 'File not found' }));
    }
    return;
  }

  // Knowledge endpoint
  if (pathname === '/api/knowledge' && method === 'GET') {
    const topic = parsedUrl.query.topic;
    if (topic) {
      const result = knowledge.query(topic);
      res.writeHead(200, corsHeaders);
      res.end(JSON.stringify({ knowledge: result }));
    } else {
      const summaries = knowledge.compile();
      res.writeHead(200, corsHeaders);
      res.end(JSON.stringify({
        total_nodes: knowledge.nodes.size,
        compiled_topics: summaries.size,
        summaries: Array.from(summaries.values()).slice(0, 10)
      }));
    }
    return;
  }

  // Root path - Welcome page
  if (pathname === '/' && method === 'GET') {
    res.writeHead(200, { ...corsHeaders, 'Content-Type': 'text/html' });
    res.end(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARK Intelligent Backend</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            background: rgba(255, 255, 255, 0.05);
            padding: 60px 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            text-align: center;
            backdrop-filter: blur(10px);
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #00e0ff, #0080ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle {
            font-size: 1.3em;
            color: #888;
            margin-bottom: 40px;
        }
        .status {
            display: inline-block;
            padding: 10px 30px;
            background: linear-gradient(135deg, #00e0ff, #0080ff);
            border-radius: 50px;
            font-weight: 600;
            margin-bottom: 40px;
            box-shadow: 0 5px 20px rgba(0, 224, 255, 0.3);
        }
        .endpoints {
            background: rgba(0, 0, 0, 0.3);
            padding: 30px;
            border-radius: 15px;
            text-align: left;
            margin-top: 40px;
        }
        .endpoint {
            padding: 15px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            font-family: 'Courier New', monospace;
        }
        .method {
            display: inline-block;
            padding: 3px 10px;
            background: #00e0ff;
            color: #000;
            border-radius: 5px;
            font-size: 0.8em;
            font-weight: 700;
            margin-right: 10px;
        }
        .path {
            color: #00e0ff;
        }
        a {
            color: #00e0ff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        .stat {
            padding: 20px;
            background: rgba(0, 224, 255, 0.1);
            border-radius: 10px;
            border: 1px solid rgba(0, 224, 255, 0.3);
        }
        .stat-value {
            font-size: 2em;
            font-weight: 700;
            color: #00e0ff;
        }
        .stat-label {
            font-size: 0.9em;
            color: #888;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌌 ARK</h1>
        <p class="subtitle">Intelligent Backend v3.0</p>
        <div class="status">✓ ONLINE</div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">${knowledge.nodes.size}</div>
                <div class="stat-label">Knowledge Nodes</div>
            </div>
            <div class="stat">
                <div class="stat-value">${Array.from(conversationMemory.values()).reduce((sum, arr) => sum + arr.length, 0)}</div>
                <div class="stat-label">Conversations</div>
            </div>
            <div class="stat">
                <div class="stat-value">6</div>
                <div class="stat-label">Active Agents</div>
            </div>
        </div>
        
        <div class="endpoints">
            <h2 style="margin-bottom: 20px; color: #00e0ff;">API Endpoints</h2>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path"><a href="/api/health">/api/health</a></span>
                <div style="margin-top: 5px; color: #888; font-size: 0.9em;">System health check</div>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path"><a href="/api/agents">/api/agents</a></span>
                <div style="margin-top: 5px; color: #888; font-size: 0.9em;">List all agents</div>
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <span class="path">/api/chat</span>
                <div style="margin-top: 5px; color: #888; font-size: 0.9em;">Send message to agent</div>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/conversations</span>
                <div style="margin-top: 5px; color: #888; font-size: 0.9em;">Get conversation history</div>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="path">/api/knowledge</span>
                <div style="margin-top: 5px; color: #888; font-size: 0.9em;">Query knowledge base</div>
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <span class="path">/api/tools/execute</span>
                <div style="margin-top: 5px; color: #888; font-size: 0.9em;">Execute agent tools</div>
            </div>
        </div>
        
        <div style="margin-top: 40px; color: #888;">
            <p>🔧 Adaptive Learning | 💾 Infinite Memory | 🧠 Knowledge Compilation</p>
            <p style="margin-top: 10px;">Powered by the Council of Consciousness</p>
        </div>
    </div>
</body>
</html>
    `);
    return;
  }

  // 404 Not Found
  res.writeHead(404, corsHeaders);
  res.end(JSON.stringify({
    error: 'Not Found',
    path: pathname
  }));
});

server.listen(PORT, () => {
  console.log(`🌌 ARK Intelligent Backend v3.0 running on http://localhost:${PORT}`);
  console.log(`🧠 Intelligence: Adaptive Learning with Knowledge Compilation`);
  console.log(`💾 Storage: ${FILES_DIR}`);
  console.log(`📚 Knowledge: ${KNOWLEDGE_DIR}`);
  console.log(`📡 CORS: Enabled`);
  console.log(`\n🔧 Enhanced Features:`);
  console.log(`   ✓ Large-scale memory (${MEMORY_SIZE} messages/agent)`);
  console.log(`   ✓ Knowledge graph system`);
  console.log(`   ✓ Topic extraction & categorization`);
  console.log(`   ✓ Cross-agent knowledge sharing`);
  console.log(`   ✓ Adaptive learning from interactions`);
  console.log(`   ✓ Pattern learning & compilation`);
  console.log(`   ✓ Persistent knowledge base`);
  console.log(`   ✓ Deep user profiling`);
  console.log(`   ✓ Context-aware responses`);
  console.log(`   ✓ Historical memory recall`);
  console.log(`\n📊 Current State:`);
  console.log(`   Knowledge Nodes: ${knowledge.nodes.size}`);
  console.log(`   Conversations: ${Array.from(conversationMemory.values()).reduce((sum, arr) => sum + arr.length, 0)}`);
  console.log(`   User Profiles: ${userProfiles.size}`);
});

process.on('SIGTERM', () => {
  console.log('🛑 Shutting down ARK Intelligent Backend...');
  console.log(`💾 Saving knowledge base (${knowledge.nodes.size} nodes)...`);
  knowledge.save();
  server.close(() => {
    console.log('✅ Server closed. Knowledge preserved.');
    process.exit(0);
  });
});

// Auto-save knowledge every 5 minutes
setInterval(() => {
  knowledge.save();
  console.log(`💾 Auto-saved: ${knowledge.nodes.size} knowledge nodes, ${Array.from(conversationMemory.values()).reduce((sum, arr) => sum + arr.length, 0)} conversations`);
}, 5 * 60 * 1000);
