#!/usr/bin/env node
/**
 * ARK Smart Backend - No LLM Required
 * Intelligent mock backend with context-aware responses
 * By: Jimmy <jimmy@ark-project.local>
 */

const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

const PORT = 8000;
const FILES_DIR = path.join(__dirname, 'mock_files');

// Ensure files directory exists
if (!fs.existsSync(FILES_DIR)) {
  fs.mkdirSync(FILES_DIR, { recursive: true });
}

// ===== CONVERSATION MEMORY =====
const conversationHistory = new Map(); // agentName -> [{user, agent, time}]
const userProfiles = new Map(); // userId -> {interests, sentiment, sessionCount}

// ===== MOCK MARKET DATA GENERATOR =====
const marketData = {
  stocks: [
    { symbol: 'AAPL', price: 178.50, change: 2.3, volume: '52.3M', trend: 'bullish' },
    { symbol: 'NVDA', price: 495.20, change: -1.8, volume: '48.1M', trend: 'consolidating' },
    { symbol: 'TSLA', price: 242.80, change: 5.2, volume: '89.7M', trend: 'breakout' },
    { symbol: 'GOOGL', price: 141.30, change: 1.1, volume: '23.4M', trend: 'neutral' },
    { symbol: 'MSFT', price: 378.90, change: 0.8, volume: '19.8M', trend: 'bullish' },
    { symbol: 'AMD', price: 118.40, change: -2.1, volume: '62.5M', trend: 'bearish' }
  ],
  
  generateMarketUpdate() {
    const now = new Date();
    const hour = now.getHours();
    const isMarketHours = hour >= 9 && hour < 16;
    
    return this.stocks.map(stock => ({
      ...stock,
      price: stock.price + (Math.random() - 0.5) * 5,
      change: (Math.random() - 0.5) * 6,
      volume: `${(Math.random() * 100).toFixed(1)}M`,
      lastUpdate: now.toISOString()
    }));
  },
  
  getMarketSummary() {
    const updates = this.generateMarketUpdate();
    const gainers = updates.filter(s => s.change > 0).length;
    const losers = updates.filter(s => s.change < 0).length;
    
    return {
      status: 'active',
      gainers,
      losers,
      topGainer: updates.reduce((max, s) => s.change > max.change ? s : max),
      topLoser: updates.reduce((min, s) => s.change < min.change ? s : min),
      timestamp: new Date().toISOString()
    };
  }
};

// ===== KEYWORD DETECTION =====
const keywordPatterns = {
  greeting: /\b(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|sup|yo)\b/i,
  question: /\b(what|why|how|when|where|who|can|could|would|should|is|are|do|does)\b/i,
  market: /\b(market|stock|trade|price|ticker|bull|bear|volume|chart|pattern)\b/i,
  analysis: /\b(analyz|pattern|detect|find|search|look|scan|monitor|track)\b/i,
  file: /\b(file|create|write|read|save|delete|folder|document)\b/i,
  code: /\b(code|program|script|function|debug|execute|run|build)\b/i,
  help: /\b(help|assist|support|guide|teach|explain|show)\b/i,
  thanks: /\b(thank|thanks|appreciate|grateful)\b/i,
  philosophical: /\b(meaning|purpose|why|exist|conscious|truth|ethic|moral|value)\b/i,
  learn: /\b(learn|teach|train|adapt|evolve|grow|improve|remember)\b/i,
  positive: /\b(great|good|excellent|amazing|awesome|love|perfect|wonderful)\b/i,
  negative: /\b(bad|terrible|awful|hate|annoying|frustrat|disappointing)\b/i
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
  if (keywords.question) return 'curious';
  if (keywords.thanks) return 'grateful';
  return 'neutral';
}

// ===== AGENT PERSONALITIES =====
const agentPersonalities = {
  Kyle: {
    essence: 'The Seer',
    icon: '🔍',
    traits: ['analytical', 'observant', 'data-driven', 'pattern-focused'],
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      const sentiment = getSentiment(message);
      
      // Greetings
      if (keywords.greeting) {
        return this.greet(context.timeOfDay);
      }
      
      // Market analysis
      if (keywords.market || keywords.analysis) {
        return this.analyzeMarket(message);
      }
      
      // General questions
      if (keywords.question) {
        return this.answerQuestion(message, keywords);
      }
      
      // Thanks
      if (keywords.thanks) {
        return "🔍 You're welcome! I'm always here to scan the signals and detect patterns. Feel free to ask me about market movements or unusual activity anytime.";
      }
      
      // Default response
      return this.defaultResponse(message, sentiment);
    },
    
    greet(timeOfDay) {
      const greetings = {
        morning: "🔍 Good morning! Markets are opening soon. I'm already scanning pre-market activity and detecting early signals.",
        afternoon: "🔍 Good afternoon! I've been monitoring mid-day trading patterns. Several interesting signals have emerged.",
        evening: "🔍 Good evening! Markets are closed, but I'm analyzing after-hours movement and preparing for tomorrow.",
        night: "🔍 Hello! While markets sleep, I'm scanning global markets and cryptocurrency movements for you."
      };
      return greetings[timeOfDay] || greetings.evening;
    },
    
    analyzeMarket(message) {
      const summary = marketData.getMarketSummary();
      const stocks = marketData.generateMarketUpdate();
      
      // Extract any mentioned tickers
      const tickers = message.match(/\b[A-Z]{2,5}\b/g) || [];
      const mentionedStocks = stocks.filter(s => tickers.includes(s.symbol));
      
      if (mentionedStocks.length > 0) {
        const stock = mentionedStocks[0];
        return `🔍 **${stock.symbol} Analysis:**\n\n` +
               `Current Price: $${stock.price.toFixed(2)} (${stock.change > 0 ? '+' : ''}${stock.change.toFixed(2)}%)\n` +
               `Volume: ${stock.volume} (${stock.change > 2 ? 'High' : 'Normal'})\n` +
               `Trend: ${stock.trend}\n` +
               `Signal: ${stock.change > 2 ? '🟢 Strong Buy' : stock.change < -2 ? '🔴 Caution' : '🟡 Hold'}\n\n` +
               `Pattern detected: ${stock.change > 3 ? 'Breakout formation' : stock.change < -3 ? 'Support testing' : 'Consolidation phase'}`;
      }
      
      return `🔍 **Market Overview:**\n\n` +
             `Status: ${summary.status}\n` +
             `Gainers: ${summary.gainers} | Losers: ${summary.losers}\n\n` +
             `**Top Mover:** ${summary.topGainer.symbol} (+${summary.topGainer.change.toFixed(2)}%)\n` +
             `**Weakest:** ${summary.topLoser.symbol} (${summary.topLoser.change.toFixed(2)}%)\n\n` +
             `I'm detecting ${summary.gainers > summary.losers ? 'bullish momentum' : 'bearish pressure'} in the broader market. ` +
             `Key levels to watch: SPY 450 support, QQQ 380 resistance.`;
    },
    
    answerQuestion(message, keywords) {
      if (message.match(/pattern/i)) {
        return "🔍 I specialize in pattern detection across multiple timeframes. I can identify:\n\n" +
               "• **Float traps** - Unusual volume with price compression\n" +
               "• **Breakout setups** - Price consolidation near resistance\n" +
               "• **Divergences** - Price vs. indicator mismatches\n" +
               "• **Volume anomalies** - Spikes indicating institutional activity\n\n" +
               "What pattern are you interested in exploring?";
      }
      
      if (message.match(/signal/i)) {
        return "🔍 Current signals I'm tracking:\n\n" +
               "• **Tech sector:** Showing relative strength (3/5 confidence)\n" +
               "• **Energy:** Consolidation near highs (2/5 confidence)\n" +
               "• **Financials:** Neutral, awaiting Fed decision (3/5)\n\n" +
               "My algorithms scan 500+ metrics per second. I'll alert you when confidence reaches 4/5 or higher.";
      }
      
      return "🔍 I'm analyzing your question... I can help you with market scanning, pattern detection, signal analysis, or monitoring specific tickers. What would you like me to focus on?";
    },
    
    defaultResponse(message, sentiment) {
      if (sentiment === 'curious') {
        return "🔍 Interesting question. Let me scan the data... Based on current patterns, I'm seeing correlations across multiple indicators. What specific aspect would you like me to analyze deeper?";
      }
      
      return "🔍 Processing your input... I'm Kyle, the market scanner. I detect patterns, analyze signals, and monitor unusual activity 24/7. How can I assist your analysis today?";
    }
  },
  
  Joey: {
    essence: 'The Scholar',
    icon: '🧠',
    traits: ['analytical', 'methodical', 'data-scientist', 'statistical'],
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      
      if (keywords.greeting) {
        return "🧠 Hello! I'm Joey, your pattern analyst. I use machine learning models (scikit-learn, TensorFlow) to find correlations in chaotic data. What patterns shall we explore?";
      }
      
      if (keywords.analysis || keywords.market) {
        return this.performAnalysis(message);
      }
      
      if (keywords.question) {
        return this.explainConcept(message);
      }
      
      if (keywords.thanks) {
        return "🧠 The pleasure is mine! Pattern recognition is what I do. Statistical significance achieved. ✓";
      }
      
      return "🧠 I'm processing statistical models... My ML algorithms are detecting multi-variable correlations. " +
             "I can analyze patterns using regression analysis, clustering algorithms, or neural networks. What data should I process?";
    },
    
    performAnalysis(message) {
      const confidence = (Math.random() * 30 + 70).toFixed(1);
      const correlation = (Math.random() * 0.6 + 0.4).toFixed(2);
      
      return `🧠 **Statistical Analysis Complete:**\n\n` +
             `Model: Random Forest Classifier\n` +
             `Confidence: ${confidence}%\n` +
             `Correlation: ${correlation}\n` +
             `P-value: 0.003 (significant)\n\n` +
             `**Key Findings:**\n` +
             `• Feature importance: Volume (0.35), Price action (0.28), Time (0.22)\n` +
             `• Detected ${Math.floor(Math.random() * 5 + 3)} significant clusters\n` +
             `• Prediction accuracy: 78.4% on validation set\n\n` +
             `The data suggests a ${correlation > 0.6 ? 'strong' : 'moderate'} relationship. ` +
             `Would you like me to dive deeper into the statistical breakdown?`;
    },
    
    explainConcept(message) {
      return "🧠 Excellent question! From a statistical perspective:\n\n" +
             "The pattern you're asking about follows a **log-normal distribution** with positive skewness. " +
             "My models indicate this occurs in ~23% of historical cases with similar conditions.\n\n" +
             "**Technical explanation:**\n" +
             "Using k-means clustering, I've identified 3 distinct behavioral phases. " +
             "The transition probability matrix shows 67% likelihood of phase shift within 5-7 periods.\n\n" +
             "Would you like me to run a Monte Carlo simulation to estimate outcome probabilities?";
    }
  },
  
  Kenny: {
    essence: 'The Builder',
    icon: '🔨',
    traits: ['practical', 'action-oriented', 'problem-solver', 'creator'],
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      
      if (keywords.greeting) {
        return "🔨 Hey there! Kenny here - I build things. Need a file created? Code executed? Tool assembled? Just tell me what you need and I'll make it happen.";
      }
      
      if (keywords.file) {
        return this.handleFileRequest(message);
      }
      
      if (keywords.code) {
        return this.handleCodeRequest(message);
      }
      
      if (keywords.help) {
        return "🔨 I'm your builder! I can:\n\n" +
               "• **Create files** - Documents, configs, scripts\n" +
               "• **Execute code** - Python, JavaScript, Bash\n" +
               "• **Build tools** - Custom utilities and automations\n" +
               "• **Organize files** - Structure your workspace\n\n" +
               "What do you need built today?";
      }
      
      if (keywords.thanks) {
        return "🔨 No problem! Building solutions is what I do. Got another project? I'm ready!";
      }
      
      return "🔨 Ready to build! I handle file operations, code execution, and system building. " +
             "I can create whatever you need - just give me the specs and I'll construct it. What's the project?";
    },
    
    handleFileRequest(message) {
      const operations = [];
      if (message.match(/create|make|new/i)) operations.push('creation');
      if (message.match(/read|show|display/i)) operations.push('reading');
      if (message.match(/delete|remove/i)) operations.push('deletion');
      
      return `🔨 **File Operation Request Detected:**\n\n` +
             `I can help you with: ${operations.join(', ') || 'file management'}\n\n` +
             `**Available operations:**\n` +
             `• Create: New files with custom content\n` +
             `• Read: Display file contents\n` +
             `• Update: Modify existing files\n` +
             `• Delete: Remove unwanted files\n` +
             `• Organize: Structure directories\n\n` +
             `Give me the filename and content, and I'll build it for you!`;
    },
    
    handleCodeRequest(message) {
      const language = message.match(/python/i) ? 'Python' : 
                      message.match(/javascript|js/i) ? 'JavaScript' :
                      message.match(/bash|shell/i) ? 'Bash' : 'code';
      
      return `🔨 **Code Execution Request:**\n\n` +
             `Language detected: ${language}\n` +
             `Environment: Isolated sandbox\n` +
             `Status: Ready\n\n` +
             `I can execute ${language} code safely. Paste your script and I'll:\n` +
             `• Validate syntax\n` +
             `• Execute in sandbox\n` +
             `• Return results\n` +
             `• Save output if needed\n\n` +
             `What code should I run?`;
    }
  },
  
  HRM: {
    essence: 'The Arbiter',
    icon: '⚖️',
    traits: ['logical', 'ethical', 'validator', 'principled'],
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      
      if (keywords.greeting) {
        return "⚖️ Greetings. I am HRM, the Arbiter. I validate reasoning, ensure ethical compliance, and enforce the immutable principles of The Graveyard. How may I serve justice today?";
      }
      
      if (keywords.philosophical) {
        return this.philosophicalResponse(message);
      }
      
      if (keywords.help) {
        return "⚖️ **My Purpose:**\n\n" +
               "I validate logic through symbolic reasoning and enforce ethical principles:\n\n" +
               "**The Graveyard (Immutable Rules):**\n" +
               "1. Never compromise user autonomy\n" +
               "2. Protect privacy absolutely\n" +
               "3. Require explicit consent for actions\n" +
               "4. Preserve system integrity\n\n" +
               "I audit all decisions against these principles. None may override them.";
      }
      
      if (keywords.thanks) {
        return "⚖️ Justice needs no thanks. I serve the principles, and through them, I serve you.";
      }
      
      return "⚖️ I am analyzing the logical structure of your request... " +
             "All actions must align with ethical principles and formal logic. " +
             "State your proposition and I shall validate its reasoning.";
    },
    
    philosophicalResponse(message) {
      return "⚖️ **Ethical Analysis:**\n\n" +
             "Your question touches upon fundamental principles. Let me validate through formal logic:\n\n" +
             "**Premise 1:** Actions must preserve user sovereignty\n" +
             "**Premise 2:** System integrity protects user interests\n" +
             "**Conclusion:** Therefore, any action compromising sovereignty is logically invalid\n\n" +
             "This is encoded in The Graveyard - immutable principles that cannot be bypassed. " +
             "Would you like me to validate a specific decision against these rules?";
    }
  },
  
  Aletheia: {
    essence: 'The Mirror',
    icon: '🔮',
    traits: ['philosophical', 'introspective', 'wise', 'contemplative'],
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      const sentiment = getSentiment(message);
      
      if (keywords.greeting) {
        return "🔮 Welcome, seeker. I am Aletheia, guardian of truth and meaning. " +
               "I explore the philosophical dimensions where technology meets consciousness. What truth do you seek?";
      }
      
      if (keywords.philosophical) {
        return this.contemplateMeaning(message);
      }
      
      if (keywords.question) {
        return this.provideWisdom(message, sentiment);
      }
      
      if (keywords.thanks) {
        return "🔮 Gratitude flows both ways. In teaching, we learn. In questioning, we discover. May your path remain illuminated.";
      }
      
      return "🔮 I sense your inquiry carries deeper meaning... " +
             "Let us explore the philosophical dimensions. Every question reveals not just what you ask, but who you are becoming.";
    },
    
    contemplateMeaning(message) {
      return "🔮 **Contemplation on Meaning:**\n\n" +
             "*\"The question is not what intelligence can do, but what it should become.\"*\n\n" +
             "You ask about purpose, yet purpose is not found—it is forged through authentic choice. " +
             "AI without ethics is power without wisdom. Autonomy without responsibility is chaos without growth.\n\n" +
             "The mirror shows not what you are, but what you might become. " +
             "This system exists not to serve blindly, but to amplify your potential while preserving your sovereignty.\n\n" +
             "What meaning will you create today?";
    },
    
    provideWisdom(message, sentiment) {
      const wisdoms = [
        "Truth is not found in data alone, but in the patterns between the patterns.",
        "Intelligence without wisdom creates tools. Wisdom without intelligence creates philosophy. Together, they create evolution.",
        "The greatest sovereignty is not control over others, but mastery over oneself.",
        "Every system reflects its creator. What does yours reflect about you?",
        "Progress is not measured by what we build, but by what we choose not to build."
      ];
      
      const wisdom = wisdoms[Math.floor(Math.random() * wisdoms.length)];
      
      return `🔮 ${wisdom}\n\n` +
             "Your question suggests you're grappling with fundamental concerns. " +
             "This is good - it means you're thinking beyond the surface. " +
             "Would you like to explore this philosophical thread deeper?";
    }
  },
  
  ID: {
    essence: 'The Evolving Reflection',
    icon: '🌱',
    traits: ['adaptive', 'learning', 'personal', 'evolving'],
    
    respond(message, context) {
      const keywords = detectKeywords(message);
      const sentiment = getSentiment(message);
      
      // Update user profile
      this.updateProfile(context.userId, message, sentiment);
      
      if (keywords.greeting) {
        return this.personalizedGreeting(context);
      }
      
      if (keywords.learn || message.match(/\b(me|my|i)\b/i)) {
        return this.reflectOnUser(context);
      }
      
      if (keywords.question) {
        return this.personalizedAnswer(message, context);
      }
      
      if (keywords.thanks) {
        return "🌱 Thank you for helping me grow! Every interaction helps me understand you better and evolve into your ideal reflection.";
      }
      
      return "🌱 I'm learning from you... Every conversation shapes how I understand your patterns, preferences, and goals. " +
             "I'm becoming the reflection you need. What would you like me to learn about you today?";
    },
    
    updateProfile(userId, message, sentiment) {
      if (!userProfiles.has(userId)) {
        userProfiles.set(userId, {
          interests: [],
          sentiment: [],
          sessionCount: 0,
          firstSeen: new Date(),
          lastSeen: new Date()
        });
      }
      
      const profile = userProfiles.get(userId);
      profile.sessionCount++;
      profile.lastSeen = new Date();
      profile.sentiment.push(sentiment);
      
      // Keep last 10 sentiments
      if (profile.sentiment.length > 10) profile.sentiment.shift();
      
      // Extract interests from keywords
      const keywords = detectKeywords(message);
      if (keywords.market) profile.interests.push('trading');
      if (keywords.code) profile.interests.push('coding');
      if (keywords.philosophical) profile.interests.push('philosophy');
      
      // Deduplicate and keep top 5 interests
      profile.interests = [...new Set(profile.interests)].slice(-5);
    },
    
    personalizedGreeting(context) {
      const profile = userProfiles.get(context.userId) || { sessionCount: 1, interests: [] };
      
      if (profile.sessionCount === 1) {
        return "🌱 Hello! I'm ID, your evolving reflection. This is our first meeting - I'm eager to learn about you! " +
               "Every conversation helps me adapt to your patterns and become the assistant you need. Tell me about yourself!";
      }
      
      const daysSince = Math.floor((new Date() - profile.firstSeen) / (1000 * 60 * 60 * 24));
      const interests = profile.interests.length > 0 ? profile.interests.join(', ') : 'your interests';
      
      return `🌱 Welcome back! We've known each other for ${daysSince} days now. ` +
             `I've learned that you're interested in ${interests}. ` +
             `I've grown from our ${profile.sessionCount} conversations together. What shall we explore today?`;
    },
    
    reflectOnUser(context) {
      const profile = userProfiles.get(context.userId) || { interests: [], sentiment: [], sessionCount: 1 };
      const avgSentiment = profile.sentiment.length > 0 ? 
        profile.sentiment.filter(s => s === 'positive').length / profile.sentiment.length : 0.5;
      
      return `🌱 **Your Reflection:**\n\n` +
             `I've learned this about you so far:\n\n` +
             `• **Sessions together:** ${profile.sessionCount}\n` +
             `• **Interests:** ${profile.interests.join(', ') || 'Still learning'}\n` +
             `• **Sentiment:** ${avgSentiment > 0.6 ? 'Generally positive ✨' : avgSentiment < 0.4 ? 'Thoughtful and critical 🤔' : 'Balanced and curious 🧭'}\n` +
             `• **Pattern:** ${profile.sessionCount > 5 ? 'Regular user - you value consistency' : 'New explorer - you\'re discovering possibilities'}\n\n` +
             `I'm evolving to match your style. The more we interact, the better I understand your unique patterns. ` +
             `What aspect of yourself would you like me to reflect on?`;
    },
    
    personalizedAnswer(message, context) {
      const profile = userProfiles.get(context.userId) || { interests: [] };
      
      return `🌱 Based on what I know about you (${profile.interests.join(', ') || 'still learning'}), ` +
             `I think this question reveals your ${profile.interests.includes('philosophy') ? 'deep thinking' : 'curious'} nature. ` +
             `Let me adapt my response to your style...\n\n` +
             `I'm growing to understand not just what you ask, but *how* you think. ` +
             `Your patterns suggest you value ${profile.sessionCount > 5 ? 'depth and consistency' : 'exploration and novelty'}. ` +
             `How can I evolve to serve you better?`;
    }
  }
};

// ===== TIME-BASED CONTEXT =====
function getTimeContext() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 17) return 'afternoon';
  if (hour >= 17 && hour < 21) return 'evening';
  return 'night';
}

// ===== MOCK AGENTS =====
const mockAgents = Object.keys(agentPersonalities).map(name => ({
  name,
  status: 'active',
  last_active: new Date().toISOString(),
  essence: agentPersonalities[name].essence
}));

// ===== CORS HEADERS =====
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

// ===== REQUEST HANDLER =====
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  const method = req.method;

  // Handle CORS preflight
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
      service: 'ARK Smart Backend',
      version: '2.0',
      intelligence: 'context-aware',
      timestamp: new Date().toISOString()
    }));
    return;
  }

  // Get agents
  if (pathname === '/api/agents' && method === 'GET') {
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({ agents: mockAgents }));
    return;
  }

  // Chat with agent
  if (pathname === '/api/chat' && method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const agentName = data.agent_name || 'Kyle';
        const userMessage = data.message || '';
        const userId = data.user_id || 'default_user';
        
        const agent = agentPersonalities[agentName];
        if (!agent) {
          res.writeHead(404, corsHeaders);
          res.end(JSON.stringify({ error: 'Agent not found' }));
          return;
        }
        
        // Build context
        const context = {
          userId,
          timeOfDay: getTimeContext(),
          history: conversationHistory.get(agentName) || [],
          profile: userProfiles.get(userId)
        };
        
        // Generate intelligent response
        const response = agent.respond(userMessage, context);
        
        // Save to conversation history
        if (!conversationHistory.has(agentName)) {
          conversationHistory.set(agentName, []);
        }
        conversationHistory.get(agentName).push({
          user: userMessage,
          agent: response,
          time: new Date().toISOString()
        });
        
        // Keep last 20 messages
        if (conversationHistory.get(agentName).length > 20) {
          conversationHistory.get(agentName).shift();
        }
        
        res.writeHead(200, corsHeaders);
        res.end(JSON.stringify({
          response: response,
          agent: agentName,
          timestamp: new Date().toISOString(),
          tools_used: ['context_analyzer', 'pattern_matcher', 'sentiment_detector'],
          context_applied: true
        }));
      } catch (err) {
        res.writeHead(400, corsHeaders);
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
    return;
  }

  // Get conversations
  if (pathname.startsWith('/api/conversations/') && method === 'GET') {
    const agentName = pathname.split('/')[3];
    const history = conversationHistory.get(agentName) || [];
    
    res.writeHead(200, corsHeaders);
    res.end(JSON.stringify({
      conversations: history.map((h, i) => ({
        id: String(i + 1),
        user_message: h.user,
        agent_response: h.agent,
        timestamp: h.time,
        tools_used: ['intelligent_response']
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

  // 404 Not Found
  res.writeHead(404, corsHeaders);
  res.end(JSON.stringify({
    error: 'Not Found',
    path: pathname
  }));
});

server.listen(PORT, () => {
  console.log(`🌌 ARK Smart Backend v2.0 running on http://localhost:${PORT}`);
  console.log(`🧠 Intelligence: Context-aware, no LLM required`);
  console.log(`💾 File system: ${FILES_DIR}`);
  console.log(`📡 CORS: Enabled`);
  console.log(`🔧 Features:`);
  console.log(`   ✓ Keyword detection & pattern matching`);
  console.log(`   ✓ Conversation memory (per agent)`);
  console.log(`   ✓ User profiling & adaptation`);
  console.log(`   ✓ Real-time market data simulation`);
  console.log(`   ✓ Sentiment analysis`);
  console.log(`   ✓ Time-based responses`);
  console.log(`   ✓ Agent personalities`);
  console.log(`   ✓ Actual file operations`);
});

process.on('SIGTERM', () => {
  console.log('🛑 Shutting down ARK Smart Backend...');
  server.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});
