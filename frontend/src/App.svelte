<script>
  import { onMount } from 'svelte';
  import Council from './components/Council.svelte';
  import Chat from './components/Chat.svelte';
  import FileManager from './components/FileManager.svelte';
  import StatusBar from './components/StatusBar.svelte';
  
  let currentView = 'council';
  let selectedAgent = null;
  let systemStatus = 'awakening';
  
  // API base URL
  const API_BASE = '/api';
  
  // WebSocket connection
  let ws = null;
  let connectionStatus = 'disconnected';
  
  onMount(() => {
    // Initialize WebSocket connection
    connectWebSocket();
    
    // Check system health
    checkSystemHealth();
  });
  
  function connectWebSocket() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        connectionStatus = 'connected';
        console.log('🌌 A.R.K. WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('📡 A.R.K. message received:', data);
        // Handle real-time updates from agents
      };
      
      ws.onclose = () => {
        connectionStatus = 'disconnected';
        console.log('📡 A.R.K. WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('📡 A.R.K. WebSocket error:', error);
        connectionStatus = 'error';
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      connectionStatus = 'error';
    }
  }
  
  async function checkSystemHealth() {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (response.ok) {
        const health = await response.json();
        systemStatus = health.status;
      } else {
        systemStatus = 'error';
      }
    } catch (error) {
      console.error('Health check failed:', error);
      systemStatus = 'error';
    }
  }
  
  function handleViewChange(view) {
    currentView = view;
    selectedAgent = null;
  }
  
  function handleAgentSelect(agent) {
    selectedAgent = agent;
    currentView = 'chat';
  }
  
  function handleBackToCouncil() {
    currentView = 'council';
    selectedAgent = null;
  }
</script>

<main class="ark-interface">
  <!-- Navigation Header -->
  <header class="ark-header">
    <div class="ark-brand">
      <h1 class="ark-title">A.R.K.</h1>
      <span class="ark-subtitle">Autonomous Reactive Kernel</span>
    </div>
    
    <nav class="ark-nav">
      <button 
        class="nav-btn" 
        class:active={currentView === 'council'}
        on:click={() => handleViewChange('council')}
      >
        🌌 Council
      </button>
      <button 
        class="nav-btn" 
        class:active={currentView === 'files'}
        on:click={() => handleViewChange('files')}
      >
        📂 Files
      </button>
    </nav>
    
    <div class="connection-status" class:connected={connectionStatus === 'connected'}>
      <span class="status-dot"></span>
      {connectionStatus === 'connected' ? 'Online' : 'Offline'}
    </div>
  </header>
  
  <!-- Main Content Area -->
  <div class="ark-content">
    {#if currentView === 'council'}
      <Council on:selectAgent={e => handleAgentSelect(e.detail)} />
    {:else if currentView === 'chat' && selectedAgent}
      <Chat 
        agent={selectedAgent} 
        on:back={handleBackToCouncil}
      />
    {:else if currentView === 'files'}
      <FileManager />
    {/if}
  </div>
  
  <!-- Status Bar -->
  <StatusBar {systemStatus} {connectionStatus} />
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: #0a0a0f;
    color: #ffffff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    overflow-x: hidden;
  }
  
  .ark-interface {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
  }
  
  .ark-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    background: rgba(26, 26, 46, 0.8);
    border-bottom: 2px solid #00e0ff;
    backdrop-filter: blur(10px);
  }
  
  .ark-brand {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .ark-title {
    font-size: 2rem;
    font-weight: bold;
    color: #00e0ff;
    text-shadow: 0 0 20px rgba(0, 224, 255, 0.5);
    margin: 0;
  }
  
  .ark-subtitle {
    color: #ffce47;
    font-size: 0.9rem;
    opacity: 0.8;
  }
  
  .ark-nav {
    display: flex;
    gap: 1rem;
  }
  
  .nav-btn {
    background: transparent;
    border: 1px solid rgba(0, 224, 255, 0.3);
    color: #ffffff;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 0.9rem;
  }
  
  .nav-btn:hover {
    border-color: #00e0ff;
    background: rgba(0, 224, 255, 0.1);
    transform: translateY(-1px);
  }
  
  .nav-btn.active {
    background: linear-gradient(45deg, #00e0ff, #ffce47);
    color: #0a0a0f;
    font-weight: bold;
    border-color: transparent;
  }
  
  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    color: #888;
  }
  
  .connection-status.connected {
    color: #00ff88;
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ff4444;
    animation: pulse 2s infinite;
  }
  
  .connection-status.connected .status-dot {
    background: #00ff88;
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
  
  .ark-content {
    flex: 1;
    overflow: hidden;
  }
  
  /* Responsive design */
  @media (max-width: 768px) {
    .ark-header {
      flex-direction: column;
      gap: 1rem;
      padding: 1rem;
    }
    
    .ark-brand {
      flex-direction: column;
      gap: 0.5rem;
      text-align: center;
    }
    
    .ark-title {
      font-size: 1.5rem;
    }
  }
</style>