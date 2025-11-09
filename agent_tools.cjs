/**
 * ARK Agent Tools - Extended Capabilities
 * Agents can send emails, make calls, browse web, and more
 */

let nodemailer;
try {
  nodemailer = require('nodemailer');
} catch (e) {
  console.log('⚠️  nodemailer not installed - email features disabled');
}
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);
const { getLatticeInterface } = require('./code-lattice-agent-integration.cjs');

// ===== EMAIL CAPABILITIES =====
class EmailTool {
  constructor() {
    // Configure email transporter (use environment variables in production)
    if (nodemailer) {
      this.transporter = nodemailer.createTransport({
        host: process.env.SMTP_HOST || 'smtp.gmail.com',
        port: process.env.SMTP_PORT || 587,
        secure: false,
        auth: {
          user: process.env.EMAIL_USER || 'ark-system@example.com',
          pass: process.env.EMAIL_PASS || 'your-password'
        }
      });
    } else {
      this.transporter = null;
    }
  }

  async sendEmail({ to, subject, body, from = 'ARK System <ark@example.com>' }) {
    if (!this.transporter) {
      return {
        success: false,
        error: 'Email not configured - set SMTP_HOST, EMAIL_USER, EMAIL_PASS environment variables'
      };
    }
    
    try {
      const info = await this.transporter.sendMail({
        from,
        to,
        subject,
        text: body,
        html: `<div style="font-family: Arial, sans-serif;">${body.replace(/\n/g, '<br>')}</div>`
      });

      return {
        success: true,
        messageId: info.messageId,
        response: info.response
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async readEmails({ folder = 'INBOX', limit = 10 }) {
    // Placeholder for IMAP email reading
    return {
      success: false,
      message: 'Email reading requires IMAP configuration'
    };
  }
}

// ===== PHONE/SMS CAPABILITIES =====
class PhoneTool {
  constructor() {
    // Twilio or similar service configuration
    this.accountSid = process.env.TWILIO_ACCOUNT_SID;
    this.authToken = process.env.TWILIO_AUTH_TOKEN;
    this.fromNumber = process.env.TWILIO_PHONE_NUMBER;
  }

  async makeCall({ to, message }) {
    // Text-to-speech call using Twilio
    return {
      success: false,
      message: 'Phone calls require Twilio API configuration',
      placeholder: {
        to,
        message,
        twimlUrl: 'https://your-server.com/twiml-response'
      }
    };
  }

  async sendSMS({ to, message }) {
    // Send SMS via Twilio
    return {
      success: false,
      message: 'SMS requires Twilio API configuration',
      placeholder: {
        to,
        body: message
      }
    };
  }
}

// ===== WEB BROWSING CAPABILITIES =====
class WebBrowserTool {
  async fetchURL(url) {
    return new Promise((resolve, reject) => {
      const protocol = url.startsWith('https') ? https : http;
      
      protocol.get(url, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          resolve({
            success: true,
            statusCode: res.statusCode,
            headers: res.headers,
            body: data,
            length: data.length
          });
        });
      }).on('error', (err) => {
        resolve({
          success: false,
          error: err.message
        });
      });
    });
  }

  async searchWeb(query) {
    // DuckDuckGo instant answers (no API key needed)
    const url = `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json`;
    const result = await this.fetchURL(url);
    
    if (result.success) {
      try {
        const data = JSON.parse(result.body);
        return {
          success: true,
          query,
          abstract: data.Abstract,
          abstractSource: data.AbstractSource,
          abstractURL: data.AbstractURL,
          relatedTopics: data.RelatedTopics?.slice(0, 5) || []
        };
      } catch (err) {
        return { success: false, error: 'Failed to parse search results' };
      }
    }
    
    return result;
  }

  async extractWebContent(url) {
    const result = await this.fetchURL(url);
    
    if (result.success) {
      // Simple HTML content extraction
      let text = result.body
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      
      return {
        success: true,
        url,
        content: text.substring(0, 5000), // First 5000 chars
        fullLength: text.length
      };
    }
    
    return result;
  }
}

// ===== FILE SYSTEM OPERATIONS =====
class FileSystemTool {
  constructor(baseDir = '/home/user/webapp/agent_workspace') {
    this.baseDir = baseDir;
    if (!fs.existsSync(baseDir)) {
      fs.mkdirSync(baseDir, { recursive: true });
    }
  }

  validatePath(requestedPath) {
    const resolved = path.resolve(this.baseDir, requestedPath);
    if (!resolved.startsWith(this.baseDir)) {
      throw new Error('Path traversal detected');
    }
    return resolved;
  }

  async writeFile(params) {
    const { filePath, content } = params;
    try {
      const fullPath = this.validatePath(filePath);
      const dir = path.dirname(fullPath);
      
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      fs.writeFileSync(fullPath, content, 'utf8');
      
      return {
        success: true,
        path: fullPath,
        size: Buffer.byteLength(content, 'utf8')
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async readFile(params) {
    const { filePath } = params;
    try {
      const fullPath = this.validatePath(filePath);
      const content = fs.readFileSync(fullPath, 'utf8');
      
      return {
        success: true,
        path: fullPath,
        content,
        size: content.length
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async listFiles(params = {}) {
    const { dirPath = '.' } = params;
    try {
      const fullPath = this.validatePath(dirPath);
      const files = fs.readdirSync(fullPath);
      
      const fileDetails = files.map(file => {
        const filePath = path.join(fullPath, file);
        const stats = fs.statSync(filePath);
        
        return {
          name: file,
          size: stats.size,
          isDirectory: stats.isDirectory(),
          modified: stats.mtime
        };
      });
      
      return {
        success: true,
        path: fullPath,
        files: fileDetails
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async deleteFile(params) {
    const { filePath } = params;
    try {
      const fullPath = this.validatePath(filePath);
      fs.unlinkSync(fullPath);
      
      return {
        success: true,
        path: fullPath,
        message: 'File deleted'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// ===== CODE EXECUTION =====
class CodeExecutionTool {
  async executeJavaScript(code, timeout = 5000) {
    try {
      // Sandbox the code execution
      const vm = require('vm');
      const sandbox = {
        console: {
          log: (...args) => args.join(' ')
        },
        Math, Date, JSON, Array, Object, String, Number
      };
      
      const script = new vm.Script(code);
      const context = vm.createContext(sandbox);
      
      const result = script.runInContext(context, { timeout });
      
      return {
        success: true,
        result,
        output: sandbox.console.log.toString()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async executePython(code) {
    try {
      // Write code to temp file and execute
      const tempFile = `/tmp/ark_python_${Date.now()}.py`;
      fs.writeFileSync(tempFile, code);
      
      const { stdout, stderr } = await execAsync(`python3 ${tempFile}`, { timeout: 10000 });
      
      fs.unlinkSync(tempFile);
      
      return {
        success: true,
        stdout,
        stderr
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async executeShell(command) {
    try {
      const { stdout, stderr } = await execAsync(command, { 
        timeout: 10000,
        cwd: '/home/user/webapp'
      });
      
      return {
        success: true,
        stdout,
        stderr
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// ===== DATA ANALYSIS =====
class DataAnalysisTool {
  analyzeNumbers(numbers) {
    if (!Array.isArray(numbers) || numbers.length === 0) {
      return { success: false, error: 'Invalid input' };
    }

    const sorted = [...numbers].sort((a, b) => a - b);
    const sum = numbers.reduce((a, b) => a + b, 0);
    const mean = sum / numbers.length;
    const median = sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : sorted[Math.floor(sorted.length / 2)];
    
    const variance = numbers.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / numbers.length;
    const stdDev = Math.sqrt(variance);

    return {
      success: true,
      count: numbers.length,
      sum,
      mean,
      median,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      range: sorted[sorted.length - 1] - sorted[0],
      variance,
      standardDeviation: stdDev
    };
  }

  parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    const data = lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim());
      const row = {};
      headers.forEach((header, index) => {
        row[header] = values[index];
      });
      return row;
    });

    return {
      success: true,
      headers,
      rowCount: data.length,
      data
    };
  }
}

// ===== IMAGE GENERATION =====
class ImageTool {
  async generatePlaceholder(text, width = 400, height = 300) {
    // SVG placeholder generation
    const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#4A90E2"/>
  <text x="50%" y="50%" font-family="Arial" font-size="24" fill="white" 
        text-anchor="middle" dominant-baseline="middle">${text}</text>
</svg>`;

    return {
      success: true,
      format: 'svg',
      content: svg,
      width,
      height
    };
  }

  async generateQRCode(data) {
    // Simple QR code API call
    const url = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(data)}`;
    
    return {
      success: true,
      url,
      data,
      message: 'QR code URL generated'
    };
  }
}

// ===== CALENDAR/SCHEDULING =====
class CalendarTool {
  async createEvent({ title, startTime, endTime, description }) {
    // iCalendar format generation
    const ics = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ARK System//EN
BEGIN:VEVENT
UID:${Date.now()}@ark-system
DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').split('.')[0]}Z
DTSTART:${new Date(startTime).toISOString().replace(/[-:]/g, '').split('.')[0]}Z
DTEND:${new Date(endTime).toISOString().replace(/[-:]/g, '').split('.')[0]}Z
SUMMARY:${title}
DESCRIPTION:${description}
END:VEVENT
END:VCALENDAR`;

    return {
      success: true,
      ics,
      title,
      message: 'Calendar event created'
    };
  }

  getCurrentTime() {
    const now = new Date();
    return {
      success: true,
      timestamp: now.toISOString(),
      unix: now.getTime(),
      formatted: now.toLocaleString(),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
  }
}

// ===== LLM INTEGRATION (Ollama) =====
class LLMTool {
  constructor() {
    this.ollamaHost = process.env.OLLAMA_HOST || 'http://localhost:11434';
    this.defaultModel = process.env.OLLAMA_MODEL || 'llama2';
  }

  /**
   * Query Ollama LLM for information
   * @param {string} prompt - The prompt to send to the LLM
   * @param {string} model - Model to use (default: llama2)
   * @param {number} timeout - Request timeout in milliseconds
   * @returns {Object} LLM response with text and metadata
   */
  async queryOllama({ prompt, model = null, timeout = 30000 }) {
    const selectedModel = model || this.defaultModel;
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(`${this.ollamaHost}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel,
          prompt,
          stream: false
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        return {
          success: false,
          error: `Ollama API error: ${response.status} ${response.statusText}`
        };
      }
      
      const data = await response.json();
      
      return {
        success: true,
        response: data.response,
        model: selectedModel,
        context: data.context,
        created_at: data.created_at,
        done: data.done
      };
    } catch (error) {
      if (error.name === 'AbortError') {
        return {
          success: false,
          error: 'Request timeout - LLM took too long to respond'
        };
      }
      
      return {
        success: false,
        error: `Failed to query Ollama: ${error.message}`,
        hint: 'Is Ollama running? Start with: ollama serve'
      };
    }
  }

  /**
   * Research a topic with LLM enhancement and source citations
   * Combines web search for sources + LLM for enhanced understanding
   * @param {string} topic - Topic to research
   * @param {Object} webTool - WebBrowserTool instance for searching
   * @returns {Object} Research results with summary and sources
   */
  async researchTopicWithSources({ topic, webTool }) {
    if (!webTool) {
      return {
        success: false,
        error: 'WebBrowserTool instance required for source research'
      };
    }
    
    try {
      // Step 1: Get web sources
      console.log(`🔍 LLM: Researching "${topic}" - fetching sources...`);
      const webResults = await webTool.searchWeb(topic);
      
      if (!webResults.success) {
        return {
          success: false,
          error: 'Failed to fetch web sources',
          details: webResults.error
        };
      }
      
      // Step 2: Extract source information
      const sources = [];
      if (webResults.abstract && webResults.abstractSource) {
        sources.push({
          content: webResults.abstract,
          source: webResults.abstractSource,
          url: webResults.abstractURL || 'N/A',
          type: 'primary'
        });
      }
      
      // Add related topics as additional sources
      if (webResults.relatedTopics && webResults.relatedTopics.length > 0) {
        webResults.relatedTopics.slice(0, 3).forEach((topic, idx) => {
          if (topic.Text) {
            sources.push({
              content: topic.Text,
              source: topic.FirstURL ? new URL(topic.FirstURL).hostname : 'DuckDuckGo',
              url: topic.FirstURL || 'N/A',
              type: 'related'
            });
          }
        });
      }
      
      // If no sources found, return error
      if (sources.length === 0) {
        return {
          success: false,
          error: 'No sources found for topic',
          topic,
          webResults
        };
      }
      
      // Step 3: Enhance with LLM analysis
      console.log(`🧠 LLM: Analyzing "${topic}" with ${sources.length} sources...`);
      
      const sourceContext = sources.map((s, i) => 
        `[Source ${i + 1}: ${s.source}]\n${s.content}`
      ).join('\n\n');
      
      const prompt = `You are a research analyst. Summarize the following information about "${topic}" in a clear, concise way. Extract key facts, definitions, and concepts. Be factual and precise.

Sources:
${sourceContext}

Provide a structured summary with:
1. Definition/Overview (1-2 sentences)
2. Key Facts (3-5 bullet points)
3. Important Concepts (if applicable)

Keep it concise and knowledge-dense. Focus on learnable information.`;

      const llmResult = await this.queryOllama({ 
        prompt, 
        timeout: 45000 // 45s for research queries
      });
      
      if (!llmResult.success) {
        // Fallback: Return web sources without LLM enhancement
        console.log(`⚠️  LLM: Failed to enhance, using raw sources`);
        return {
          success: true,
          topic,
          summary: sources[0].content, // Use primary source as summary
          enhancedByLLM: false,
          sources: sources.map(s => ({
            source: s.source,
            url: s.url,
            excerpt: s.content.substring(0, 200) + '...'
          })),
          timestamp: new Date().toISOString()
        };
      }
      
      // Step 4: Return enhanced research with sources
      console.log(`✅ LLM: Research complete for "${topic}" (${sources.length} sources cited)`);
      
      return {
        success: true,
        topic,
        summary: llmResult.response,
        enhancedByLLM: true,
        model: llmResult.model,
        sources: sources.map(s => ({
          source: s.source,
          url: s.url,
          excerpt: s.content.substring(0, 200) + '...',
          type: s.type
        })),
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      return {
        success: false,
        error: `Research failed: ${error.message}`,
        topic
      };
    }
  }

  /**
   * Extract structured knowledge from text using LLM
   * @param {string} text - Text to analyze
   * @returns {Object} Extracted facts, definitions, formulas
   */
  async extractKnowledge({ text }) {
    const prompt = `Extract all learnable information from this text. Focus on:
- Definitions (what things ARE)
- Facts (objective statements)
- Formulas or equations
- Causal relationships (X causes Y)
- Principles or laws

Text:
${text}

Return in this format:
DEFINITIONS:
- [item]

FACTS:
- [item]

FORMULAS:
- [item]

RELATIONSHIPS:
- [item]

If a category has nothing, skip it.`;

    const result = await this.queryOllama({ prompt, timeout: 30000 });
    
    if (!result.success) {
      return result;
    }
    
    return {
      success: true,
      extractedKnowledge: result.response,
      originalText: text.substring(0, 200) + '...'
    };
  }
}

// ===== TOOL REGISTRY =====
class AgentToolRegistry {
  constructor() {
    this.email = new EmailTool();
    this.phone = new PhoneTool();
    this.web = new WebBrowserTool();
    this.filesystem = new FileSystemTool();
    this.code = new CodeExecutionTool();
    this.data = new DataAnalysisTool();
    this.image = new ImageTool();
    this.calendar = new CalendarTool();
    this.llm = new LLMTool();
    this.lattice = getLatticeInterface(); // Code Lattice integration
  }

  async executeTool(category, method, params) {
    try {
      if (!this[category]) {
        return { success: false, error: `Unknown tool category: ${category}` };
      }

      if (typeof this[category][method] !== 'function') {
        return { success: false, error: `Unknown method: ${method} in ${category}` };
      }

      // Special handling for LLM research - inject web tool
      if (category === 'llm' && method === 'researchTopicWithSources') {
        params.webTool = this.web;
      }

      // Call method with proper params (spread if object, direct if primitive)
      let result;
      if (params && typeof params === 'object' && !Array.isArray(params)) {
        result = await this[category][method](params);
      } else {
        result = await this[category][method](params);
      }
      
      return result;
    } catch (error) {
      return {
        success: false,
        error: error.message,
        stack: error.stack
      };
    }
  }

  listTools() {
    return {
      email: ['sendEmail', 'readEmails'],
      phone: ['makeCall', 'sendSMS'],
      web: ['fetchURL', 'searchWeb', 'extractWebContent'],
      filesystem: ['writeFile', 'readFile', 'listFiles', 'deleteFile'],
      code: ['executeJavaScript', 'executePython', 'executeShell'],
      data: ['analyzeNumbers', 'parseCSV'],
      image: ['generatePlaceholder', 'generateQRCode'],
      calendar: ['createEvent', 'getCurrentTime'],
      llm: ['queryOllama', 'researchTopicWithSources', 'extractKnowledge'],
      lattice: ['getStats', 'generateCode', 'queryNodesForTask', 'recommendNodes', 
                'contextAwareQuery', 'documentCode', 'explainNode', 'validateCode', 
                'reviewNodeAddition', 'reflectOnGeneration', 'optimizeNodeUsage', 
                'trackUsagePattern']
    };
  }
}

module.exports = {
  AgentToolRegistry,
  EmailTool,
  PhoneTool,
  WebBrowserTool,
  FileSystemTool,
  CodeExecutionTool,
  DataAnalysisTool,
  ImageTool,
  CalendarTool,
  LLMTool
};
