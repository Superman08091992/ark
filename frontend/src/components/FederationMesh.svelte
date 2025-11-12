<script>
  import { onMount, onDestroy } from 'svelte';
  
  // Federation mesh data
  let peers = [];
  let syncTraffic = [];
  let networkHealth = 100;
  let totalPeers = 0;
  let activeSyncs = 0;
  let dataIntegrity = 100;
  
  // Trust tier colors
  const tierColors = {
    'core': '#00ff88',
    'trusted': '#00e0ff',
    'verified': '#ffce47',
    'unverified': '#ff4444'
  };
  
  // WebSocket connection
  let ws = null;
  let updateInterval = null;
  
  onMount(() => {
    // Initialize with mock data
    initializeMockData();
    
    // Set up WebSocket for real-time updates
    connectWebSocket();
    
    // Periodic updates
    updateInterval = setInterval(updateMetrics, 2000);
  });
  
  onDestroy(() => {
    if (ws) ws.close();
    if (updateInterval) clearInterval(updateInterval);
  });
  
  function connectWebSocket() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/federation`;
      
      ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleFederationUpdate(data);
      };
      
      ws.onerror = () => {
        console.error('Federation WebSocket error');
      };
    } catch (error) {
      console.error('Failed to connect federation WebSocket:', error);
    }
  }
  
  function handleFederationUpdate(data) {
    if (data.type === 'peer_update') {
      peers = data.peers;
      totalPeers = peers.length;
    } else if (data.type === 'sync_event') {
      syncTraffic = [...syncTraffic, data.event].slice(-50); // Keep last 50 events
      activeSyncs = syncTraffic.filter(e => e.status === 'active').length;
    } else if (data.type === 'health_update') {
      networkHealth = data.health;
      dataIntegrity = data.integrity;
    }
  }
  
  function initializeMockData() {
    peers = [
      { id: 'peer-1', name: 'ARK-Node-Alpha', trustTier: 'core', status: 'active', latency: 12, dataShared: 1247 },
      { id: 'peer-2', name: 'ARK-Node-Beta', trustTier: 'trusted', status: 'active', latency: 45, dataShared: 892 },
      { id: 'peer-3', name: 'ARK-Node-Gamma', trustTier: 'trusted', status: 'syncing', latency: 78, dataShared: 534 },
      { id: 'peer-4', name: 'ARK-Node-Delta', trustTier: 'verified', status: 'active', latency: 23, dataShared: 445 },
      { id: 'peer-5', name: 'ARK-Node-Epsilon', trustTier: 'verified', status: 'idle', latency: 156, dataShared: 198 },
    ];
    
    totalPeers = peers.length;
    
    syncTraffic = [
      { timestamp: Date.now() - 5000, peer: 'ARK-Node-Beta', action: 'memory_sync', status: 'complete', bytes: 1024 },
      { timestamp: Date.now() - 3000, peer: 'ARK-Node-Gamma', action: 'reflection_sync', status: 'active', bytes: 2048 },
      { timestamp: Date.now() - 1000, peer: 'ARK-Node-Alpha', action: 'identity_sync', status: 'complete', bytes: 512 },
    ];
    
    activeSyncs = syncTraffic.filter(e => e.status === 'active').length;
    networkHealth = 94;
    dataIntegrity = 99.7;
  }
  
  function updateMetrics() {
    // Simulate real-time metric changes
    networkHealth = Math.max(85, Math.min(100, networkHealth + (Math.random() - 0.5) * 3));
    dataIntegrity = Math.max(95, Math.min(100, dataIntegrity + (Math.random() - 0.5) * 0.5));
    
    // Simulate random sync events
    if (Math.random() < 0.3) {
      const randomPeer = peers[Math.floor(Math.random() * peers.length)];
      const actions = ['memory_sync', 'reflection_sync', 'identity_sync', 'knowledge_sync'];
      const newEvent = {
        timestamp: Date.now(),
        peer: randomPeer.name,
        action: actions[Math.floor(Math.random() * actions.length)],
        status: Math.random() < 0.7 ? 'complete' : 'active',
        bytes: Math.floor(Math.random() * 3000) + 500
      };
      syncTraffic = [...syncTraffic, newEvent].slice(-50);
      activeSyncs = syncTraffic.filter(e => e.status === 'active').length;
    }
    
    // Update peer latencies
    peers = peers.map(peer => ({
      ...peer,
      latency: Math.max(10, peer.latency + (Math.random() - 0.5) * 20)
    }));
  }
  
  function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  }
  
  function formatTimestamp(timestamp) {
    const now = Date.now();
    const diff = Math.floor((now - timestamp) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  }
</script>

<div class="federation-mesh">
  <div class="mesh-header">
    <h2 class="mesh-title">
      <span class="title-icon">🌐</span>
      Federation Mesh
    </h2>
    <div class="mesh-stats">
      <div class="stat-badge">
        <span class="stat-label">Network Health</span>
        <span class="stat-value" class:healthy={networkHealth > 90} class:warning={networkHealth <= 90 && networkHealth > 75}>
          {networkHealth.toFixed(1)}%
        </span>
      </div>
      <div class="stat-badge">
        <span class="stat-label">Data Integrity</span>
        <span class="stat-value" class:healthy={dataIntegrity > 99}>
          {dataIntegrity.toFixed(2)}%
        </span>
      </div>
      <div class="stat-badge">
        <span class="stat-label">Active Peers</span>
        <span class="stat-value">{totalPeers}</span>
      </div>
      <div class="stat-badge">
        <span class="stat-label">Active Syncs</span>
        <span class="stat-value">{activeSyncs}</span>
      </div>
    </div>
  </div>
  
  <div class="mesh-content">
    <!-- Peer Topology Visualization -->
    <div class="topology-panel">
      <h3 class="panel-title">Peer Topology</h3>
      <div class="topology-graph">
        <div class="central-node">
          <div class="node-core">ARK Core</div>
        </div>
        {#each peers as peer, i}
          <div 
            class="peer-node" 
            style="--angle: {(360 / peers.length) * i}deg; --tier-color: {tierColors[peer.trustTier]}"
            class:active={peer.status === 'active'}
            class:syncing={peer.status === 'syncing'}
          >
            <div class="node-content">
              <div class="node-name">{peer.name}</div>
              <div class="node-tier">{peer.trustTier}</div>
              <div class="node-latency">{Math.floor(peer.latency)}ms</div>
            </div>
            <div class="connection-line"></div>
          </div>
        {/each}
      </div>
    </div>
    
    <!-- Peer Details Table -->
    <div class="peers-panel">
      <h3 class="panel-title">Connected Peers</h3>
      <div class="peers-table">
        <table>
          <thead>
            <tr>
              <th>Peer</th>
              <th>Trust Tier</th>
              <th>Status</th>
              <th>Latency</th>
              <th>Data Shared</th>
            </tr>
          </thead>
          <tbody>
            {#each peers as peer}
              <tr>
                <td>
                  <div class="peer-name">
                    <span class="peer-dot" style="background: {tierColors[peer.trustTier]}"></span>
                    {peer.name}
                  </div>
                </td>
                <td>
                  <span class="tier-badge" style="color: {tierColors[peer.trustTier]}">
                    {peer.trustTier}
                  </span>
                </td>
                <td>
                  <span class="status-badge" class:active={peer.status === 'active'}>
                    {peer.status}
                  </span>
                </td>
                <td>{Math.floor(peer.latency)}ms</td>
                <td>{formatBytes(peer.dataShared * 1024)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- Sync Traffic Feed -->
    <div class="traffic-panel">
      <h3 class="panel-title">Sync Traffic (Live)</h3>
      <div class="traffic-feed">
        {#each syncTraffic.slice().reverse() as event}
          <div class="traffic-event" class:active={event.status === 'active'}>
            <span class="event-time">{formatTimestamp(event.timestamp)}</span>
            <span class="event-peer">{event.peer}</span>
            <span class="event-action">{event.action.replace('_', ' ')}</span>
            <span class="event-status" class:complete={event.status === 'complete'}>
              {event.status}
            </span>
            <span class="event-bytes">{formatBytes(event.bytes)}</span>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  .federation-mesh {
    padding: 2rem;
    height: 100%;
    overflow-y: auto;
    background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
  }
  
  .mesh-header {
    margin-bottom: 2rem;
  }
  
  .mesh-title {
    font-size: 2rem;
    color: #00e0ff;
    margin: 0 0 1.5rem 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .title-icon {
    font-size: 2.5rem;
    animation: rotate 20s linear infinite;
  }
  
  @keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .mesh-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  .stat-badge {
    background: rgba(0, 224, 255, 0.1);
    border: 1px solid rgba(0, 224, 255, 0.3);
    border-radius: 12px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .stat-label {
    font-size: 0.85rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .stat-value {
    font-size: 1.75rem;
    font-weight: bold;
    color: #00e0ff;
  }
  
  .stat-value.healthy {
    color: #00ff88;
  }
  
  .stat-value.warning {
    color: #ffce47;
  }
  
  .mesh-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto;
    gap: 1.5rem;
  }
  
  .topology-panel {
    grid-column: 1 / -1;
    background: rgba(26, 26, 46, 0.5);
    border: 1px solid rgba(0, 224, 255, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
  }
  
  .panel-title {
    font-size: 1.25rem;
    color: #ffce47;
    margin: 0 0 1.5rem 0;
    text-transform: uppercase;
    letter-spacing: 2px;
  }
  
  .topology-graph {
    position: relative;
    height: 500px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .central-node {
    position: absolute;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: radial-gradient(circle, #00e0ff 0%, #0066ff 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 40px rgba(0, 224, 255, 0.6);
    z-index: 10;
  }
  
  .node-core {
    font-weight: bold;
    font-size: 1.1rem;
    color: #fff;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
  }
  
  .peer-node {
    position: absolute;
    width: 140px;
    height: 100px;
    transform: rotate(var(--angle)) translateY(-200px) rotate(calc(-1 * var(--angle)));
    transition: all 0.3s ease;
  }
  
  .peer-node.active {
    animation: pulse-node 2s infinite;
  }
  
  .peer-node.syncing .node-content {
    border-color: var(--tier-color);
    box-shadow: 0 0 20px var(--tier-color);
    animation: sync-flash 1s infinite;
  }
  
  @keyframes pulse-node {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
  
  @keyframes sync-flash {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  
  .node-content {
    background: rgba(26, 26, 46, 0.9);
    border: 2px solid var(--tier-color);
    border-radius: 12px;
    padding: 0.75rem;
    text-align: center;
    backdrop-filter: blur(10px);
  }
  
  .node-name {
    font-size: 0.85rem;
    font-weight: bold;
    color: #fff;
    margin-bottom: 0.25rem;
  }
  
  .node-tier {
    font-size: 0.7rem;
    color: var(--tier-color);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.25rem;
  }
  
  .node-latency {
    font-size: 0.7rem;
    color: #888;
  }
  
  .connection-line {
    position: absolute;
    width: 2px;
    height: 200px;
    background: linear-gradient(to bottom, var(--tier-color), transparent);
    top: 50%;
    left: 50%;
    transform: translateX(-50%) translateY(-100%);
    opacity: 0.3;
  }
  
  .peers-panel {
    background: rgba(26, 26, 46, 0.5);
    border: 1px solid rgba(0, 224, 255, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
  }
  
  .peers-table {
    overflow-x: auto;
  }
  
  .peers-table table {
    width: 100%;
    border-collapse: collapse;
  }
  
  .peers-table th {
    text-align: left;
    padding: 0.75rem;
    color: #00e0ff;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 1px solid rgba(0, 224, 255, 0.3);
  }
  
  .peers-table td {
    padding: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
  
  .peers-table tr:hover {
    background: rgba(0, 224, 255, 0.05);
  }
  
  .peer-name {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .peer-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    box-shadow: 0 0 10px currentColor;
  }
  
  .tier-badge {
    font-weight: bold;
    text-transform: uppercase;
    font-size: 0.8rem;
  }
  
  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    background: rgba(136, 136, 136, 0.2);
    color: #888;
    font-size: 0.75rem;
    text-transform: uppercase;
  }
  
  .status-badge.active {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }
  
  .traffic-panel {
    background: rgba(26, 26, 46, 0.5);
    border: 1px solid rgba(0, 224, 255, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
  }
  
  .traffic-feed {
    max-height: 400px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .traffic-event {
    display: grid;
    grid-template-columns: auto 1fr auto auto auto;
    gap: 1rem;
    padding: 0.75rem;
    background: rgba(0, 224, 255, 0.05);
    border-left: 3px solid rgba(0, 224, 255, 0.3);
    border-radius: 8px;
    font-size: 0.85rem;
    transition: all 0.3s ease;
  }
  
  .traffic-event.active {
    background: rgba(255, 206, 71, 0.1);
    border-left-color: #ffce47;
    animation: pulse-traffic 1.5s infinite;
  }
  
  @keyframes pulse-traffic {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
  
  .event-time {
    color: #888;
    font-size: 0.75rem;
  }
  
  .event-peer {
    color: #00e0ff;
    font-weight: 500;
  }
  
  .event-action {
    color: #ffce47;
    text-transform: capitalize;
  }
  
  .event-status {
    color: #888;
    font-size: 0.75rem;
    text-transform: uppercase;
  }
  
  .event-status.complete {
    color: #00ff88;
  }
  
  .event-bytes {
    color: #888;
    font-size: 0.75rem;
    font-family: 'Courier New', monospace;
  }
  
  /* Scrollbar styling */
  .traffic-feed::-webkit-scrollbar,
  .federation-mesh::-webkit-scrollbar {
    width: 8px;
  }
  
  .traffic-feed::-webkit-scrollbar-track,
  .federation-mesh::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
  }
  
  .traffic-feed::-webkit-scrollbar-thumb,
  .federation-mesh::-webkit-scrollbar-thumb {
    background: rgba(0, 224, 255, 0.3);
    border-radius: 4px;
  }
  
  .traffic-feed::-webkit-scrollbar-thumb:hover,
  .federation-mesh::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 224, 255, 0.5);
  }
  
  /* Responsive */
  @media (max-width: 1024px) {
    .mesh-content {
      grid-template-columns: 1fr;
    }
    
    .topology-graph {
      height: 400px;
    }
    
    .peer-node {
      transform: rotate(var(--angle)) translateY(-150px) rotate(calc(-1 * var(--angle)));
    }
    
    .connection-line {
      height: 150px;
    }
  }
</style>
