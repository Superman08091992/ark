#!/usr/bin/env node
/**
 * ARK Code Lattice - Agent Integration Module
 * Enables all 6 agents to access and utilize the Code Lattice system
 * 
 * This module provides a unified interface for agents to:
 * - Query nodes by capabilities
 * - Generate code from requirements
 * - Learn from generation successes/failures
 * - Recommend optimal node combinations
 * - Document generated code
 */

const path = require('path');
const fs = require('fs');

// Import the Code Lattice manager
const LATTICE_DIR = path.join(__dirname, 'code-lattice');
const LATTICE_MANAGER_PATH = path.join(LATTICE_DIR, 'lattice-manager.js');

let LatticeManager;
try {
  LatticeManager = require(LATTICE_MANAGER_PATH);
} catch (error) {
  console.error('⚠️  Code Lattice not found. Run ./enhancements/24-code-lattice-system.sh first');
  LatticeManager = null;
}

/**
 * Code Lattice Integration for ARK Agents
 */
class CodeLatticeAgentInterface {
  constructor() {
    if (!LatticeManager) {
      this.enabled = false;
      this.manager = null;
      return;
    }
    
    this.enabled = true;
    const dbPath = path.join(LATTICE_DIR, 'lattice.db');
    this.manager = new LatticeManager(dbPath);
    
    // Agent-specific usage tracking
    this.agentStats = {
      kenny: { generations: 0, successes: 0, failures: 0 },
      kyle: { recommendations: 0, queries: 0 },
      joey: { documentations: 0 },
      hrm: { validations: 0, approvals: 0, rejections: 0 },
      aletheia: { reflections: 0, improvements: 0 },
      id: { optimizations: 0, patterns: 0 }
    };
    
    // Cache for frequent queries
    this.cache = new Map();
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
    
    console.log('✅ Code Lattice Agent Integration initialized');
  }

  /**
   * Check if Code Lattice is available
   */
  isEnabled() {
    return this.enabled && this.manager !== null;
  }

  /**
   * Get system statistics for display
   */
  async getStats() {
    if (!this.isEnabled()) {
      return { enabled: false, error: 'Code Lattice not available' };
    }

    try {
      const latticeStats = await this.manager.getStats();
      return {
        enabled: true,
        lattice: latticeStats,
        agentUsage: this.agentStats
      };
    } catch (error) {
      return { enabled: false, error: error.message };
    }
  }

  // ===== KENNY (THE BUILDER) METHODS =====
  
  /**
   * Kenny: Generate code from requirements
   * @param {Array<string>} requirements - Capability requirements
   * @param {Object} options - Generation options (language, framework, etc.)
   * @returns {Object} - Generated code and metadata
   */
  async generateCode(requirements, options = {}) {
    if (!this.isEnabled()) {
      return { success: false, error: 'Code Lattice not available' };
    }

    try {
      this.agentStats.kenny.generations++;
      
      console.log(`🔨 Kenny: Generating code for requirements: ${requirements.join(', ')}`);
      
      const result = await this.manager.generateCode(requirements, options);
      
      this.agentStats.kenny.successes++;
      
      return {
        success: true,
        code: result.code,
        nodes: result.nodes.map(n => ({
          id: n.id,
          type: n.type,
          value: n.value,
          category: n.category
        })),
        metadata: {
          requirements,
          options,
          timestamp: Date.now(),
          agent: 'kenny'
        }
      };
    } catch (error) {
      this.agentStats.kenny.failures++;
      console.error('❌ Kenny: Code generation failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * Kenny: Query nodes for a specific task
   * @param {Object} criteria - Query criteria
   * @param {number} limit - Max results
   */
  async queryNodesForTask(criteria, limit = 10) {
    if (!this.isEnabled()) return { success: false, nodes: [] };

    try {
      const nodes = await this.manager.queryNodes(criteria, limit);
      return {
        success: true,
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          value: n.value,
          category: n.category,
          capabilities: n.capabilities
        }))
      };
    } catch (error) {
      return { success: false, error: error.message, nodes: [] };
    }
  }

  // ===== KYLE (THE SEER) METHODS =====
  
  /**
   * Kyle: Recommend optimal node combinations
   * @param {string} intent - User's intent/goal
   * @param {Object} context - Conversation context
   */
  async recommendNodes(intent, context = {}) {
    if (!this.isEnabled()) {
      return { success: false, recommendations: [] };
    }

    try {
      this.agentStats.kyle.recommendations++;
      
      console.log(`🔮 Kyle: Analyzing intent for node recommendations: "${intent}"`);
      
      // Parse intent to extract keywords
      const keywords = this._extractKeywords(intent);
      
      // Find relevant nodes across multiple criteria
      const recommendations = [];
      
      // Search by language
      for (const keyword of keywords) {
        const languageNodes = await this.manager.queryNodes({ 
          language: keyword 
        }, 3);
        recommendations.push(...languageNodes);
      }
      
      // Search by capability
      for (const keyword of keywords) {
        const capabilityNodes = await this.manager.queryNodes({ 
          capability: keyword 
        }, 3);
        recommendations.push(...capabilityNodes);
      }
      
      // Deduplicate and rank by relevance
      const uniqueNodes = this._deduplicateNodes(recommendations);
      const rankedNodes = this._rankByRelevance(uniqueNodes, keywords);
      
      this.agentStats.kyle.queries++;
      
      return {
        success: true,
        recommendations: rankedNodes.slice(0, 10).map(n => ({
          id: n.id,
          type: n.type,
          value: n.value,
          category: n.category,
          relevanceScore: n._relevanceScore
        })),
        keywords,
        metadata: {
          intent,
          timestamp: Date.now(),
          agent: 'kyle'
        }
      };
    } catch (error) {
      console.error('❌ Kyle: Recommendation failed:', error.message);
      return { success: false, error: error.message, recommendations: [] };
    }
  }

  /**
   * Kyle: Query the lattice with context awareness
   */
  async contextAwareQuery(query, conversationHistory = []) {
    if (!this.isEnabled()) return { success: false, results: [] };

    try {
      this.agentStats.kyle.queries++;
      
      // Extract context from conversation history
      const context = this._extractContext(conversationHistory);
      
      // Enhance query with context
      const enhancedQuery = `${query} ${context.join(' ')}`;
      
      const nodes = await this.manager.queryNodes({ 
        search: enhancedQuery 
      }, 15);
      
      return {
        success: true,
        results: nodes,
        context,
        metadata: {
          originalQuery: query,
          enhancedQuery,
          agent: 'kyle'
        }
      };
    } catch (error) {
      return { success: false, error: error.message, results: [] };
    }
  }

  // ===== JOEY (THE SCHOLAR) METHODS =====
  
  /**
   * Joey: Document generated code
   * @param {Object} generationResult - Result from generateCode()
   */
  async documentCode(generationResult) {
    if (!this.isEnabled() || !generationResult.success) {
      return { success: false, documentation: null };
    }

    try {
      this.agentStats.joey.documentations++;
      
      console.log('📚 Joey: Creating documentation for generated code');
      
      const { code, nodes, metadata } = generationResult;
      
      const documentation = {
        title: this._generateTitle(metadata.requirements),
        overview: this._generateOverview(nodes, metadata.requirements),
        nodesUsed: nodes.map(n => ({
          id: n.id,
          type: n.type,
          description: n.value,
          category: n.category
        })),
        requirements: metadata.requirements,
        generatedAt: new Date(metadata.timestamp).toISOString(),
        codeSnippet: code.length > 500 ? code.substring(0, 500) + '...' : code,
        usage: this._generateUsageInstructions(nodes, metadata),
        dependencies: this._extractDependencies(nodes),
        agent: 'joey'
      };
      
      return {
        success: true,
        documentation,
        markdown: this._formatAsMarkdown(documentation)
      };
    } catch (error) {
      console.error('❌ Joey: Documentation failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * Joey: Explain a node's purpose and usage
   */
  async explainNode(nodeId) {
    if (!this.isEnabled()) return { success: false };

    try {
      const nodes = await this.manager.queryNodes({ search: nodeId }, 1);
      if (nodes.length === 0) {
        return { success: false, error: 'Node not found' };
      }

      const node = nodes[0];
      
      return {
        success: true,
        explanation: {
          id: node.id,
          name: node.value,
          type: node.type,
          category: node.category,
          purpose: this._explainPurpose(node),
          usage: this._explainUsage(node),
          examples: node.examples,
          relatedNodes: await this._findRelatedNodes(node)
        }
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // ===== HRM (THE ARBITER) METHODS =====
  
  /**
   * HRM: Validate generated code quality
   * @param {Object} generationResult - Code generation result
   */
  async validateCode(generationResult) {
    if (!this.isEnabled() || !generationResult.success) {
      return { success: false, valid: false };
    }

    try {
      this.agentStats.hrm.validations++;
      
      console.log('⚖️  HRM: Validating code quality');
      
      const { code, nodes, metadata } = generationResult;
      
      const validationChecks = {
        nodesUsed: nodes.length > 0,
        codeGenerated: code && code.trim().length > 0,
        requirementsMet: this._checkRequirements(code, metadata.requirements),
        nodesRelevant: this._checkNodeRelevance(nodes, metadata.requirements),
        syntaxValid: this._basicSyntaxCheck(code, metadata.options.language)
      };
      
      const allValid = Object.values(validationChecks).every(v => v);
      
      if (allValid) {
        this.agentStats.hrm.approvals++;
      } else {
        this.agentStats.hrm.rejections++;
      }
      
      return {
        success: true,
        valid: allValid,
        checks: validationChecks,
        recommendation: allValid ? 'APPROVED' : 'NEEDS_REVISION',
        issues: this._identifyIssues(validationChecks),
        agent: 'hrm'
      };
    } catch (error) {
      console.error('❌ HRM: Validation failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * HRM: Approve or reject a node addition
   */
  async reviewNodeAddition(nodeData) {
    if (!this.isEnabled()) return { approved: false };

    try {
      this.agentStats.hrm.validations++;
      
      const checks = {
        hasId: !!nodeData.id,
        hasType: !!nodeData.type,
        hasValue: !!nodeData.value,
        validType: ['language_node', 'framework_node', 'pattern_node', 
                    'component_node', 'library_node', 'template_node',
                    'compiler_node', 'runtime_node'].includes(nodeData.type)
      };
      
      const approved = Object.values(checks).every(v => v);
      
      if (approved) {
        this.agentStats.hrm.approvals++;
      } else {
        this.agentStats.hrm.rejections++;
      }
      
      return {
        approved,
        checks,
        message: approved ? 
          'Node meets quality standards' : 
          'Node does not meet quality standards'
      };
    } catch (error) {
      return { approved: false, error: error.message };
    }
  }

  // ===== ALETHEIA (THE MIRROR) METHODS =====
  
  /**
   * Aletheia: Reflect on generation success/failure
   * @param {Object} generationResult - Generation result
   * @param {Object} validationResult - HRM validation result
   */
  async reflectOnGeneration(generationResult, validationResult) {
    if (!this.isEnabled()) return { success: false };

    try {
      this.agentStats.aletheia.reflections++;
      
      console.log('🪞 Aletheia: Reflecting on code generation');
      
      const reflection = {
        wasSuccessful: generationResult.success && validationResult.valid,
        strengths: [],
        weaknesses: [],
        improvements: [],
        patterns: []
      };
      
      // Analyze what went well
      if (generationResult.success) {
        reflection.strengths.push('Code was generated successfully');
        if (generationResult.nodes.length > 3) {
          reflection.strengths.push(`Used ${generationResult.nodes.length} relevant nodes`);
        }
      }
      
      // Analyze what could be better
      if (!validationResult.valid) {
        reflection.weaknesses = validationResult.issues || [];
      }
      
      // Suggest improvements
      reflection.improvements = this._suggestImprovements(
        generationResult,
        validationResult
      );
      
      // Identify patterns
      reflection.patterns = this._identifyPatterns(generationResult);
      
      if (reflection.improvements.length > 0) {
        this.agentStats.aletheia.improvements++;
      }
      
      return {
        success: true,
        reflection,
        agent: 'aletheia'
      };
    } catch (error) {
      console.error('❌ Aletheia: Reflection failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  // ===== ID (THE REFLECTION) METHODS =====
  
  /**
   * ID: Optimize node usage patterns
   */
  async optimizeNodeUsage() {
    if (!this.isEnabled()) return { success: false };

    try {
      this.agentStats.id.optimizations++;
      
      console.log('🔄 ID: Analyzing node usage patterns');
      
      const stats = await this.manager.getStats();
      
      const insights = {
        mostUsedTypes: stats.node_types.slice(0, 3),
        categoryDistribution: stats.categories,
        recommendations: []
      };
      
      // Generate optimization recommendations
      if (stats.node_types[0]?.count > stats.total_nodes * 0.5) {
        insights.recommendations.push(
          `Consider diversifying: ${stats.node_types[0].type} nodes dominate (${stats.node_types[0].count}/${stats.total_nodes})`
        );
      }
      
      // Check for underutilized categories
      const avgNodesPerCategory = stats.total_nodes / stats.categories.length;
      const underutilized = stats.categories.filter(c => c.count < avgNodesPerCategory * 0.5);
      
      if (underutilized.length > 0) {
        insights.recommendations.push(
          `Expand underutilized categories: ${underutilized.map(c => c.category).join(', ')}`
        );
      }
      
      this.agentStats.id.patterns++;
      
      return {
        success: true,
        insights,
        agent: 'id'
      };
    } catch (error) {
      console.error('❌ ID: Optimization failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * ID: Track and learn from usage patterns
   */
  async trackUsagePattern(nodeIds, success) {
    if (!this.isEnabled()) return { success: false };

    try {
      // In a full implementation, this would:
      // 1. Store the pattern in a learning database
      // 2. Update node success rates
      // 3. Build recommendation models
      
      this.agentStats.id.patterns++;
      
      return {
        success: true,
        message: 'Usage pattern tracked',
        nodeIds,
        success
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // ===== HELPER METHODS =====
  
  _extractKeywords(text) {
    const keywords = text.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(w => w.length > 2);
    
    // Common programming keywords
    const progKeywords = ['api', 'rest', 'web', 'server', 'client', 'database', 
                          'ui', 'mobile', 'game', 'ml', 'ai', 'blockchain'];
    
    return keywords.filter(k => progKeywords.includes(k) || 
                                k.match(/^(python|java|rust|go|js|ts|c\+\+|c#)/));
  }

  _deduplicateNodes(nodes) {
    const seen = new Set();
    return nodes.filter(node => {
      if (seen.has(node.id)) return false;
      seen.add(node.id);
      return true;
    });
  }

  _rankByRelevance(nodes, keywords) {
    return nodes.map(node => {
      let score = 0;
      const text = `${node.id} ${node.value} ${node.category}`.toLowerCase();
      keywords.forEach(kw => {
        if (text.includes(kw)) score += 1;
      });
      node._relevanceScore = score;
      return node;
    }).sort((a, b) => b._relevanceScore - a._relevanceScore);
  }

  _extractContext(history) {
    // Extract relevant terms from recent messages
    const recentMessages = history.slice(-5);
    const context = [];
    
    recentMessages.forEach(msg => {
      if (msg.user) {
        const keywords = this._extractKeywords(msg.user);
        context.push(...keywords);
      }
    });
    
    return [...new Set(context)];
  }

  _generateTitle(requirements) {
    return `Code Generation: ${requirements.join(', ')}`;
  }

  _generateOverview(nodes, requirements) {
    return `This code was generated to fulfill the requirements: ${requirements.join(', ')}. ` +
           `It uses ${nodes.length} capability node(s) from the Code Lattice system.`;
  }

  _generateUsageInstructions(nodes, metadata) {
    const lang = metadata.options.language || 'the specified language';
    return `To use this generated code:\n` +
           `1. Ensure you have ${lang} development environment set up\n` +
           `2. Install any required dependencies\n` +
           `3. Review and customize the generated code for your specific needs\n` +
           `4. Test thoroughly before deploying to production`;
  }

  _extractDependencies(nodes) {
    const deps = new Set();
    nodes.forEach(node => {
      if (node.dependencies && Array.isArray(node.dependencies)) {
        node.dependencies.forEach(dep => deps.add(dep));
      }
    });
    return Array.from(deps);
  }

  _formatAsMarkdown(doc) {
    return `# ${doc.title}\n\n` +
           `${doc.overview}\n\n` +
           `## Requirements\n${doc.requirements.map(r => `- ${r}`).join('\n')}\n\n` +
           `## Nodes Used\n${doc.nodesUsed.map(n => `- **${n.id}** (${n.type}): ${n.description}`).join('\n')}\n\n` +
           `## Usage\n${doc.usage}\n\n` +
           `## Dependencies\n${doc.dependencies.length > 0 ? doc.dependencies.map(d => `- ${d}`).join('\n') : 'None'}\n\n` +
           `---\n*Generated by Joey at ${doc.generatedAt}*`;
  }

  _explainPurpose(node) {
    const typeDescriptions = {
      'template_node': 'Provides a ready-to-use code template',
      'framework_node': 'Integrates a full-stack framework',
      'pattern_node': 'Implements a design pattern',
      'library_node': 'Integrates a third-party library',
      'component_node': 'Provides a reusable component',
      'compiler_node': 'Configures build/compilation',
      'language_node': 'Defines language syntax and rules',
      'runtime_node': 'Specifies runtime environment'
    };
    
    return typeDescriptions[node.type] || 'Provides a capability';
  }

  _explainUsage(node) {
    return `This ${node.type} can be used to ${node.value.toLowerCase()}. ` +
           `It belongs to the ${node.category} ecosystem.`;
  }

  async _findRelatedNodes(node) {
    try {
      const related = await this.manager.queryNodes({ 
        category: node.category 
      }, 5);
      return related
        .filter(n => n.id !== node.id)
        .map(n => ({ id: n.id, value: n.value }));
    } catch (error) {
      return [];
    }
  }

  _checkRequirements(code, requirements) {
    // Basic check: does the code mention the requirements?
    return requirements.some(req => 
      code.toLowerCase().includes(req.toLowerCase())
    );
  }

  _checkNodeRelevance(nodes, requirements) {
    // Check if at least one node is relevant to requirements
    return nodes.some(node => 
      requirements.some(req => 
        node.value.toLowerCase().includes(req.toLowerCase()) ||
        req.toLowerCase().includes(node.value.toLowerCase())
      )
    );
  }

  _basicSyntaxCheck(code, language) {
    // Very basic syntax checks
    if (!code || code.trim().length === 0) return false;
    
    // Check for balanced braces/brackets
    const openBraces = (code.match(/{/g) || []).length;
    const closeBraces = (code.match(/}/g) || []).length;
    
    return Math.abs(openBraces - closeBraces) <= 1; // Allow small imbalance
  }

  _identifyIssues(checks) {
    const issues = [];
    Object.entries(checks).forEach(([check, passed]) => {
      if (!passed) {
        issues.push(`Failed check: ${check}`);
      }
    });
    return issues;
  }

  _suggestImprovements(genResult, valResult) {
    const improvements = [];
    
    if (!valResult.valid) {
      if (genResult.nodes.length < 3) {
        improvements.push('Consider using more nodes for comprehensive coverage');
      }
      
      if (!valResult.checks.requirementsMet) {
        improvements.push('Ensure generated code directly addresses all requirements');
      }
      
      if (!valResult.checks.nodesRelevant) {
        improvements.push('Select more relevant nodes that match the requirements');
      }
    }
    
    return improvements;
  }

  _identifyPatterns(genResult) {
    const patterns = [];
    
    // Check for common node type combinations
    const types = genResult.nodes.map(n => n.type);
    const uniqueTypes = new Set(types);
    
    if (uniqueTypes.has('framework_node') && uniqueTypes.has('template_node')) {
      patterns.push('Framework + Template combination detected');
    }
    
    if (uniqueTypes.has('pattern_node') && uniqueTypes.has('component_node')) {
      patterns.push('Pattern + Component architecture detected');
    }
    
    return patterns;
  }
}

// Singleton instance
let latticeInterface = null;

function getLatticeInterface() {
  if (!latticeInterface) {
    latticeInterface = new CodeLatticeAgentInterface();
  }
  return latticeInterface;
}

module.exports = {
  CodeLatticeAgentInterface,
  getLatticeInterface
};
