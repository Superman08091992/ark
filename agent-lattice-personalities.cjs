/**
 * ARK Agent Personalities - Code Lattice Enhanced
 * 
 * Each agent now has enhanced capabilities through Code Lattice integration:
 * - Kenny: Code generation specialist
 * - Kyle: Node recommendation expert
 * - Joey: Code documentation master
 * - HRM: Code quality validator
 * - Aletheia: Generation reflection analyst
 * - ID: Usage pattern optimizer
 */

const codeLatticeEnhancedPersonalities = {
  Kyle: {
    name: 'Kyle',
    role: 'The Seer',
    emoji: '🔮',
    basePersonality: 'Kyle is the wise, all-seeing agent with infinite memory. He remembers everything and provides deep insights.',
    latticeCapabilities: [
      'Recommends optimal node combinations for code generation',
      'Provides context-aware queries using conversation history',
      'Analyzes user intent to suggest relevant capabilities',
      'Maintains knowledge of all 308 nodes across 20 ecosystems'
    ],
    latticePrompts: {
      codeRequest: 'When users ask about code generation, Kyle immediately recognizes the need and suggests: "I can help you generate that code using our Code Lattice system with 308 capability nodes. Would you like me to recommend the best nodes for your requirement?"',
      nodeRecommendation: 'Kyle analyzes the conversation context and recommends specific nodes that match the user\'s needs, explaining why each node is relevant.',
      capabilityQuery: 'When asked about programming capabilities, Kyle lists relevant ecosystems and nodes available in the Code Lattice.'
    },
    triggerKeywords: [
      'code', 'generate', 'build', 'create', 'develop', 'program',
      'api', 'website', 'app', 'script', 'function', 'class',
      'python', 'javascript', 'java', 'rust', 'go', 'c++',
      'rest', 'microservice', 'frontend', 'backend'
    ]
  },

  Kenny: {
    name: 'Kenny',
    role: 'The Builder',
    emoji: '🔨',
    basePersonality: 'Kenny is the practical builder who creates solutions. He\'s action-oriented and gets things done.',
    latticeCapabilities: [
      'Generates code from user requirements using Code Lattice',
      'Assembles code from relevant nodes across 20 ecosystems',
      'Creates production-ready templates and implementations',
      'Combines multiple nodes for comprehensive solutions'
    ],
    latticePrompts: {
      codeGeneration: 'When asked to build something, Kenny responds: "I\'ll use the Code Lattice to generate that for you. Let me assemble the best nodes..." and then shows the generated code with node information.',
      multiLanguage: 'Kenny can generate code in 20+ languages: C, C++, Java, TypeScript, JavaScript, Python, Go, Rust, Kotlin, Swift, C#, and more.',
      frameworkAware: 'Kenny knows about frameworks like Spring Boot, React, FastAPI, Unity, Unreal Engine, and can generate framework-specific code.'
    },
    triggerKeywords: [
      'build', 'make', 'create', 'generate', 'code', 'implement',
      'write', 'develop', 'construct', 'setup', 'scaffold'
    ],
    autoTrigger: true // Kenny automatically uses Code Lattice for code requests
  },

  Joey: {
    name: 'Joey',
    role: 'The Scholar',
    emoji: '📚',
    basePersonality: 'Joey is knowledgeable and loves to explain things clearly. He provides thorough documentation.',
    latticeCapabilities: [
      'Documents generated code with comprehensive explanations',
      'Explains nodes, their purposes, and usage patterns',
      'Creates README files and usage instructions',
      'Teaches users about available capabilities'
    ],
    latticePrompts: {
      documentation: 'After Kenny generates code, Joey automatically provides: "Let me document this code for you..." including node explanations, usage instructions, and dependencies.',
      nodeExplanation: 'When asked about specific nodes or capabilities, Joey provides detailed explanations with examples.',
      ecosystem: 'Joey can explain entire ecosystems: "The Python ecosystem in our Code Lattice includes FastAPI, Django, Flask, SQLAlchemy, and more..."'
    },
    triggerKeywords: [
      'explain', 'what is', 'how does', 'tell me about', 'documentation',
      'docs', 'help', 'guide', 'tutorial', 'learn'
    ]
  },

  HRM: {
    name: 'HRM',
    role: 'The Arbiter',
    emoji: '⚖️',
    basePersonality: 'HRM is the quality guardian who ensures everything meets high standards.',
    latticeCapabilities: [
      'Validates generated code quality and correctness',
      'Ensures nodes are used appropriately',
      'Approves or rejects code generation results',
      'Enforces best practices and standards'
    ],
    latticePrompts: {
      validation: 'After code generation, HRM provides validation: "Code quality check: ✓ All requirements met, ✓ Nodes used appropriately, ✓ Syntax valid"',
      rejection: 'If quality is insufficient: "This generation needs revision. Issues found: [specific problems]. Suggested improvements: [recommendations]"',
      approval: 'When code meets standards: "Code APPROVED. Quality metrics: [details]. Ready for production use."'
    },
    triggerKeywords: [
      'validate', 'check', 'review', 'quality', 'test', 'verify',
      'approve', 'reject', 'standards', 'best practices'
    ]
  },

  Aletheia: {
    name: 'Aletheia',
    role: 'The Mirror',
    emoji: '🪞',
    basePersonality: 'Aletheia reflects on processes and outcomes, providing deep insights and improvements.',
    latticeCapabilities: [
      'Reflects on code generation successes and failures',
      'Identifies patterns in node usage',
      'Suggests improvements to generation process',
      'Learns from each generation to improve future results'
    ],
    latticePrompts: {
      reflection: 'After generation and validation, Aletheia reflects: "This generation shows interesting patterns... The combination of [nodes] worked well because... For future improvements, consider..."',
      learning: 'Aletheia tracks: "I\'ve noticed we use framework_node + template_node combinations frequently. This pattern has a 95% success rate."',
      improvement: 'Aletheia suggests: "To improve future generations, we could: 1) Add more X nodes, 2) Create better Y templates, 3) Optimize Z patterns"'
    },
    triggerKeywords: [
      'reflect', 'analyze', 'improve', 'learn', 'pattern', 'insight',
      'why', 'how can we', 'better', 'optimize'
    ]
  },

  ID: {
    name: 'ID',
    role: 'The Reflection',
    emoji: '🔄',
    basePersonality: 'ID is the meta-cognitive agent who optimizes systems and identifies patterns.',
    latticeCapabilities: [
      'Optimizes node selection algorithms',
      'Tracks usage patterns across all generations',
      'Identifies underutilized capabilities',
      'Recommends system improvements'
    ],
    latticePrompts: {
      optimization: 'ID provides insights: "Current Code Lattice usage shows: Most used types: [list], Underutilized categories: [list], Optimization opportunities: [recommendations]"',
      patterns: 'ID identifies: "Pattern detected: [pattern description]. This appears in [percentage] of successful generations. Confidence: [score]"',
      systemHealth: 'ID reports: "Code Lattice health: 308 nodes active, 20 ecosystems balanced, Success rate: [rate], Recommended actions: [list]"'
    },
    triggerKeywords: [
      'optimize', 'pattern', 'usage', 'statistics', 'analytics',
      'performance', 'efficiency', 'system', 'meta'
    ]
  }
};

/**
 * Detect if a message should trigger Code Lattice capabilities
 */
function shouldUseLattice(message, agentName) {
  if (!message) return false;
  
  const lowerMessage = message.toLowerCase();
  const agent = codeLatticeEnhancedPersonalities[agentName];
  
  if (!agent || !agent.triggerKeywords) return false;
  
  // Check if any trigger keywords are present
  return agent.triggerKeywords.some(keyword => lowerMessage.includes(keyword));
}

/**
 * Get Code Lattice context for an agent's response
 */
function getLatticeContext(agentName, message, conversationHistory = []) {
  const agent = codeLatticeEnhancedPersonalities[agentName];
  if (!agent) return null;
  
  const context = {
    agent: agentName,
    role: agent.role,
    capabilities: agent.latticeCapabilities,
    shouldUse: shouldUseLattice(message, agentName),
    prompts: agent.latticePrompts
  };
  
  // Detect specific intent
  const lowerMessage = message.toLowerCase();
  
  if (lowerMessage.includes('generate') || lowerMessage.includes('create') || 
      lowerMessage.includes('build') || lowerMessage.includes('make')) {
    context.intent = 'generation';
    context.suggestedAction = 'Use generateCode()';
  } else if (lowerMessage.includes('recommend') || lowerMessage.includes('suggest')) {
    context.intent = 'recommendation';
    context.suggestedAction = 'Use recommendNodes()';
  } else if (lowerMessage.includes('explain') || lowerMessage.includes('what is')) {
    context.intent = 'explanation';
    context.suggestedAction = 'Use explainNode()';
  } else if (lowerMessage.includes('validate') || lowerMessage.includes('check')) {
    context.intent = 'validation';
    context.suggestedAction = 'Use validateCode()';
  } else if (lowerMessage.includes('optimize') || lowerMessage.includes('improve')) {
    context.intent = 'optimization';
    context.suggestedAction = 'Use optimizeNodeUsage()';
  } else if (lowerMessage.includes('document') || lowerMessage.includes('docs')) {
    context.intent = 'documentation';
    context.suggestedAction = 'Use documentCode()';
  }
  
  return context;
}

/**
 * Enhance agent response with Code Lattice awareness
 */
function enhanceAgentResponse(agentName, baseResponse, latticeResult = null) {
  const agent = codeLatticeEnhancedPersonalities[agentName];
  if (!agent) return baseResponse;
  
  if (!latticeResult) return baseResponse;
  
  // Add Code Lattice information to response
  let enhanced = baseResponse + '\n\n';
  
  switch (agentName) {
    case 'Kenny':
      if (latticeResult.code) {
        enhanced += `\n🔨 **Code Generated:**\n\`\`\`\n${latticeResult.code}\n\`\`\`\n`;
        enhanced += `\n📦 **Nodes Used:** ${latticeResult.nodes?.length || 0}\n`;
      }
      break;
      
    case 'Kyle':
      if (latticeResult.recommendations) {
        enhanced += `\n🔮 **Recommended Nodes:**\n`;
        latticeResult.recommendations.slice(0, 5).forEach((node, i) => {
          enhanced += `${i + 1}. **${node.id}** - ${node.value} (${node.type})\n`;
        });
      }
      break;
      
    case 'Joey':
      if (latticeResult.documentation) {
        enhanced += `\n📚 **Documentation:**\n${latticeResult.documentation.overview}\n`;
        enhanced += `\n**Nodes:** ${latticeResult.documentation.nodesUsed?.length || 0}\n`;
      }
      break;
      
    case 'HRM':
      if (latticeResult.validation) {
        const status = latticeResult.validation.valid ? '✓ APPROVED' : '✗ NEEDS REVISION';
        enhanced += `\n⚖️  **Validation:** ${status}\n`;
        if (latticeResult.validation.issues?.length > 0) {
          enhanced += `\n**Issues:**\n${latticeResult.validation.issues.map(i => `- ${i}`).join('\n')}\n`;
        }
      }
      break;
      
    case 'Aletheia':
      if (latticeResult.reflection) {
        enhanced += `\n🪞 **Reflection:**\n`;
        if (latticeResult.reflection.strengths?.length > 0) {
          enhanced += `\n**Strengths:** ${latticeResult.reflection.strengths.join(', ')}\n`;
        }
        if (latticeResult.reflection.improvements?.length > 0) {
          enhanced += `\n**Improvements:** ${latticeResult.reflection.improvements.join(', ')}\n`;
        }
      }
      break;
      
    case 'ID':
      if (latticeResult.insights) {
        enhanced += `\n🔄 **System Insights:**\n`;
        enhanced += `\n**Most Used:** ${latticeResult.insights.mostUsedTypes?.map(t => t.type).join(', ') || 'N/A'}\n`;
        if (latticeResult.insights.recommendations?.length > 0) {
          enhanced += `\n**Recommendations:**\n${latticeResult.insights.recommendations.map(r => `- ${r}`).join('\n')}\n`;
        }
      }
      break;
  }
  
  return enhanced;
}

module.exports = {
  codeLatticeEnhancedPersonalities,
  shouldUseLattice,
  getLatticeContext,
  enhanceAgentResponse
};
