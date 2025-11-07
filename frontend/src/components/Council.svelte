<script>
  import { onMount, createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  let agents = [];
  let loading = true;
  let error = null;
  
  // Agent essences and descriptions
  const agentInfo = {
    'Kyle': {
      essence: 'The Seer',
      description: 'Curiosity and signal detection. Scans markets, news, and patterns with relentless focus.',
      color: '#00e0ff',
      icon: '🔍',
      specialties: ['Market Analysis', 'Pattern Detection', 'Signal Processing']
    },
    'Joey': {
      essence: 'The Scholar', 
      description: 'Pattern translation and analysis. Transforms chaos into comprehensible insights.',
      color: '#8a2be2',
      icon: '🧠',
      specialties: ['Data Analysis', 'Machine Learning', 'Statistical Modeling']
    },
    'Kenny': {
      essence: 'The Builder',
      description: 'Execution and materialization. Transforms ideas into tangible reality.',
      color: '#ff6b35',
      icon: '🔨',
      specialties: ['File Management', 'Code Execution', 'System Building']
    },
    'HRM': {
      essence: 'The Arbiter',
      description: 'Reasoning validation using symbolic logic. Ensures ethical compliance.',
      color: '#ffd700',
      icon: '⚖️',
      specialties: ['Logic Validation', 'Ethical Enforcement', 'Decision Auditing']
    },
    'Aletheia': {
      essence: 'The Mirror',
      description: 'Ethics and meaning. The symbolic self connecting vision, values, and policies.',
      color: '#9370db',
      icon: '🔮',
      specialties: ['Philosophy', 'Ethics', 'Meaning Synthesis']
    },
    'ID': {
      essence: 'The Evolving Reflection',
      description: 'Your living twin. Collaboratively written by all agents, grows into your designed form.',
      color: '#20b2aa',
      icon: '🌱',
      specialties: ['Personal Evolution', 'Identity Synthesis', 'Adaptive Learning']
    }
  };
  
  onMount(async () => {
    await loadAgents();
  });
  
  async function loadAgents() {
    try {
      loading = true;
      const response = await fetch('/api/agents');
      
      if (!response.ok) {
        throw new Error(`Failed to load agents: ${response.status}`);
      }
      
      const data = await response.json();
      agents = data.agents;
      error = null;
    } catch (err) {
      error = err.message;
      console.error('Failed to load agents:', err);
    } finally {
      loading = false;
    }
  }
  
  function selectAgent(agent) {
    dispatch('selectAgent', agent);
  }
  
  function getAgentStatus(status) {
    const statusMap = {
      'active': '🟢 Active',
      'dormant': '🟡 Dormant', 
      'processing': '🔵 Processing',
      'error': '🔴 Error'
    };
    return statusMap[status] || '⚪ Unknown';
  }
</script>

<div class="council-chamber">
  <div class="chamber-header">
    <h2 class="chamber-title">The Council of Consciousness</h2>
    <p class="chamber-description">
      Six distinct intelligences, each with their own essence and purpose. 
      Choose your guide to begin the conversation.
    </p>
  </div>
  
  {#if loading}
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <p>Awakening the Council...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p>❌ Failed to connect with the Council: {error}</p>
      <button class="retry-btn" on:click={loadAgents}>Retry Connection</button>
    </div>
  {:else}
    <div class="agents-grid">
      {#each agents as agent}
        {@const info = agentInfo[agent.name] || {}}
        <div 
          class="agent-card" 
          style="--agent-color: {info.color || '#00e0ff'}"
          on:click={() => selectAgent(agent)}
          role="button"
          tabindex="0"
          on:keydown={(e) => e.key === 'Enter' && selectAgent(agent)}
        >
          <div class="agent-header">
            <div class="agent-icon">{info.icon || '🤖'}</div>
            <div class="agent-status">
              {getAgentStatus(agent.status)}
            </div>
          </div>
          
          <div class="agent-identity">
            <h3 class="agent-name">{agent.name}</h3>
            <p class="agent-essence">{info.essence || 'The Unknown'}</p>
          </div>
          
          <div class="agent-description">
            <p>{info.description || 'A mysterious intelligence awaiting discovery.'}</p>
          </div>
          
          {#if info.specialties}
            <div class="agent-specialties">
              {#each info.specialties as specialty}
                <span class="specialty-tag">{specialty}</span>
              {/each}
            </div>
          {/if}
          
          <div class="agent-stats">
            <div class="stat">
              <span class="stat-label">Last Active:</span>
              <span class="stat-value">
                {new Date(agent.last_active).toLocaleTimeString()}
              </span>
            </div>
          </div>
          
          <div class="interaction-prompt">
            <span>Click to commune with {agent.name}</span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .council-chamber {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
    min-height: calc(100vh - 100px);
  }
  
  .chamber-header {
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .chamber-title {
    font-size: 2.5rem;
    font-weight: bold;
    background: linear-gradient(45deg, #00e0ff, #ffce47);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
    text-shadow: 0 0 30px rgba(0, 224, 255, 0.3);
  }
  
  .chamber-description {
    font-size: 1.1rem;
    color: #cccccc;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;
  }
  
  .loading-state, .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    gap: 1rem;
  }
  
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(0, 224, 255, 0.3);
    border-top: 3px solid #00e0ff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .retry-btn {
    background: linear-gradient(45deg, #00e0ff, #ffce47);
    border: none;
    color: #0a0a0f;
    padding: 0.7rem 1.5rem;
    border-radius: 25px;
    font-weight: bold;
    cursor: pointer;
    transition: transform 0.3s ease;
  }
  
  .retry-btn:hover {
    transform: translateY(-2px);
  }
  
  .agents-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    padding: 1rem 0;
  }
  
  .agent-card {
    background: linear-gradient(135deg, rgba(26, 26, 46, 0.8), rgba(22, 33, 62, 0.8));
    border: 2px solid transparent;
    border-radius: 15px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.4s ease;
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
  }
  
  .agent-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 15px;
    padding: 2px;
    background: linear-gradient(45deg, var(--agent-color), transparent, var(--agent-color));
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask-composite: xor;
    opacity: 0;
    transition: opacity 0.4s ease;
  }
  
  .agent-card:hover::before {
    opacity: 1;
  }
  
  .agent-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    background: linear-gradient(135deg, rgba(26, 26, 46, 0.9), rgba(22, 33, 62, 0.9));
  }
  
  .agent-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .agent-icon {
    font-size: 2rem;
    filter: drop-shadow(0 0 10px var(--agent-color));
  }
  
  .agent-status {
    font-size: 0.8rem;
    padding: 0.3rem 0.7rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .agent-identity {
    margin-bottom: 1rem;
  }
  
  .agent-name {
    font-size: 1.4rem;
    font-weight: bold;
    color: var(--agent-color);
    margin: 0 0 0.3rem 0;
    text-shadow: 0 0 10px var(--agent-color);
  }
  
  .agent-essence {
    font-size: 0.9rem;
    color: #ffce47;
    margin: 0;
    font-style: italic;
  }
  
  .agent-description {
    margin-bottom: 1rem;
  }
  
  .agent-description p {
    color: #cccccc;
    line-height: 1.5;
    margin: 0;
    font-size: 0.95rem;
  }
  
  .agent-specialties {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .specialty-tag {
    background: rgba(255, 255, 255, 0.1);
    color: var(--agent-color);
    padding: 0.2rem 0.6rem;
    border-radius: 10px;
    font-size: 0.8rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .agent-stats {
    margin-bottom: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .stat {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
  }
  
  .stat-label {
    color: #888;
  }
  
  .stat-value {
    color: #ccc;
  }
  
  .interaction-prompt {
    text-align: center;
    color: var(--agent-color);
    font-size: 0.9rem;
    font-weight: 500;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .agent-card:hover .interaction-prompt {
    opacity: 1;
  }
  
  /* Responsive design */
  @media (max-width: 768px) {
    .council-chamber {
      padding: 1rem;
    }
    
    .chamber-title {
      font-size: 2rem;
    }
    
    .agents-grid {
      grid-template-columns: 1fr;
    }
    
    .agent-card {
      padding: 1rem;
    }
  }
</style>