<script>
  export let systemStatus = 'awakening';
  export let connectionStatus = 'disconnected';
  
  // Status descriptions
  const statusDescriptions = {
    'awakening': 'System is initializing...',
    'awakened': 'All systems operational',
    'processing': 'Agents are processing tasks',
    'error': 'System error detected',
    'maintenance': 'System maintenance in progress'
  };
  
  // Get current time
  let currentTime = new Date().toLocaleTimeString();
  
  // Update time every second
  setInterval(() => {
    currentTime = new Date().toLocaleTimeString();
  }, 1000);
  
  function getStatusColor(status) {
    switch (status) {
      case 'awakened': return '#00ff88';
      case 'processing': return '#ffce47';
      case 'awakening': return '#00e0ff';
      case 'error': return '#ff4444';
      case 'maintenance': return '#ff8800';
      default: return '#888888';
    }
  }
  
  function getConnectionColor(status) {
    switch (status) {
      case 'connected': return '#00ff88';
      case 'connecting': return '#ffce47';
      case 'disconnected': return '#ff4444';
      case 'error': return '#ff4444';
      default: return '#888888';
    }
  }
</script>

<footer class="status-bar">
  <!-- System Status -->
  <div class="status-section">
    <div class="status-item">
      <span 
        class="status-dot" 
        style="background-color: {getStatusColor(systemStatus)}"
      ></span>
      <span class="status-text">
        {statusDescriptions[systemStatus] || 'Unknown status'}
      </span>
    </div>
  </div>
  
  <!-- Connection Status -->
  <div class="status-section">
    <div class="status-item">
      <span 
        class="status-dot" 
        style="background-color: {getConnectionColor(connectionStatus)}"
      ></span>
      <span class="status-text">
        {connectionStatus === 'connected' ? 'Real-time connection active' : 
         connectionStatus === 'connecting' ? 'Establishing connection...' :
         connectionStatus === 'error' ? 'Connection error' :
         'Offline mode'}
      </span>
    </div>
  </div>
  
  <!-- System Info -->
  <div class="status-section">
    <div class="status-item">
      <span class="info-text">A.R.K. v1.0</span>
    </div>
    <div class="status-item">
      <span class="info-text">{currentTime}</span>
    </div>
  </div>
  
  <!-- Agent Activity Indicator -->
  <div class="status-section">
    <div class="status-item">
      <div class="activity-indicator">
        <div class="pulse-dot"></div>
        <span class="activity-text">Council Active</span>
      </div>
    </div>
  </div>
</footer>

<style>
  .status-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 2rem;
    background: rgba(26, 26, 46, 0.9);
    border-top: 1px solid rgba(0, 224, 255, 0.3);
    font-size: 0.8rem;
    color: #ccc;
    backdrop-filter: blur(10px);
    min-height: 40px;
  }
  
  .status-section {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .status-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }
  
  .status-text {
    color: #ccc;
    font-size: 0.85rem;
  }
  
  .info-text {
    color: #888;
    font-size: 0.8rem;
  }
  
  .activity-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .pulse-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #00e0ff;
    animation: pulse 1.5s infinite;
  }
  
  .activity-text {
    color: #00e0ff;
    font-size: 0.8rem;
    font-weight: 500;
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.6;
      transform: scale(0.8);
    }
  }
  
  /* Responsive design */
  @media (max-width: 768px) {
    .status-bar {
      padding: 0.5rem 1rem;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    
    .status-section {
      gap: 0.5rem;
    }
    
    .status-text, .info-text, .activity-text {
      font-size: 0.75rem;
    }
  }
  
  @media (max-width: 480px) {
    .status-bar {
      justify-content: center;
    }
    
    .status-section:nth-child(3) {
      display: none; /* Hide system info on very small screens */
    }
  }
</style>