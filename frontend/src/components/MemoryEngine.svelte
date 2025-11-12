<script>
  import { onMount, onDestroy } from 'svelte';
  
  // Memory engine data
  let memoryStats = {
    ingestion_rate: 0,
    consolidation_rate: 0,
    dedup_rate: 0,
    quarantine_count: 0,
    trust_distribution: { core: 0, sandbox: 0, external: 0 },
    confidence_deltas: [],
    logs: []
  };
  
  // WebSocket connection
  let ws = null;
  let updateInterval = null;
  let connected = false;
  
  // Chart data
  let consolidationData = [];
  let trustPieData = [];
  
  onMount(() => {
    // Initialize with mock data
    initializeMockData();
    
    // Set up WebSocket for real-time updates
    connectWebSocket();
    
    // Periodic updates (if WebSocket not available)
    updateInterval = setInterval(updateMetrics, 2000);
  });
  
  onDestroy(() => {
    if (ws) ws.close();
    if (updateInterval) clearInterval(updateInterval);
  });
  
  function connectWebSocket() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/memory`;
      
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        connected = true;
        console.log('Memory WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleMemoryUpdate(data);
        } catch (e) {
          console.error('Invalid memory data', e);
        }
      };
      
      ws.onclose = () => {
        connected = false;
        console.log('Memory socket closed');
      };
      
      ws.onerror = () => {
        connected = false;
        console.error('Memory WebSocket error');
      };
    } catch (error) {
      console.error('Failed to connect memory WebSocket:', error);
    }
  }
  
  function handleMemoryUpdate(data) {
    memoryStats = {
      ...memoryStats,
      ...data
    };
    updateChartData();
  }
  
  function initializeMockData() {
    memoryStats = {
      ingestion_rate: 8,
      consolidation_rate: 7,
      dedup_rate: 92.5,
      quarantine_count: 1,
      trust_distribution: { core: 10, sandbox: 3, external: 1 },
      confidence_deltas: generateMockDeltas(50),
      logs: [
        { timestamp: new Date(Date.now() - 120000).toISOString(), message: 'Consolidated 5 new traces' },
        { timestamp: new Date(Date.now() - 60000).toISOString(), message: 'Deduplicated 2 redundant items' },
        { timestamp: new Date().toISOString(), message: 'Memory sync complete' }
      ]
    };
    updateChartData();
  }
  
  function generateMockDeltas(count) {
    return Array.from({ length: count }, () => (Math.random() - 0.5) * 0.2);
  }
  
  function updateMetrics() {
    // Simulate real-time metric changes (if no WebSocket)
    if (!connected) {
      memoryStats = {
        ...memoryStats,
        ingestion_rate: Math.max(0, memoryStats.ingestion_rate + (Math.random() - 0.5) * 2),
        consolidation_rate: Math.max(0, memoryStats.consolidation_rate + (Math.random() - 0.5) * 1.5),
        dedup_rate: Math.max(85, Math.min(99, memoryStats.dedup_rate + (Math.random() - 0.5) * 0.5)),
        quarantine_count: Math.max(0, memoryStats.quarantine_count + (Math.random() < 0.1 ? 1 : 0))
      };
      
      // Add new confidence delta
      if (Math.random() < 0.3) {
        const newDelta = (Math.random() - 0.5) * 0.3;
        memoryStats.confidence_deltas = [...memoryStats.confidence_deltas, newDelta].slice(-50);
      }
      
      // Add new log entry occasionally
      if (Math.random() < 0.2) {
        const messages = [
          'Consolidated memory batch',
          'Deduplicated redundant traces',
          'Quarantined suspicious entry',
          'Updated confidence scores',
          'Cross-referenced with peer data'
        ];
        const newLog = {
          timestamp: new Date().toISOString(),
          message: messages[Math.floor(Math.random() * messages.length)]
        };
        memoryStats.logs = [...memoryStats.logs, newLog].slice(-20);
      }
      
      updateChartData();
    }
  }
  
  function updateChartData() {
    consolidationData = [
      { name: 'Ingestion', value: memoryStats.ingestion_rate },
      { name: 'Consolidation', value: memoryStats.consolidation_rate }
    ];
    
    trustPieData = [
      { name: 'Core', value: memoryStats.trust_distribution.core, color: '#00e0ff' },
      { name: 'Sandbox', value: memoryStats.trust_distribution.sandbox, color: '#facc15' },
      { name: 'External', value: memoryStats.trust_distribution.external, color: '#ef4444' }
    ];
  }
  
  function formatTimestamp(isoString) {
    const date = new Date(isoString);
    const now = Date.now();
    const diff = Math.floor((now - date.getTime()) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return date.toLocaleTimeString();
  }
  
  function getDeltaColor(delta) {
    return delta >= 0 ? '#22c55e' : '#ef4444';
  }
  
  function getDeltaOpacity(delta) {
    return Math.min(Math.abs(delta) * 5, 1);
  }
</script>

<div class="memory-engine">
  <div class="engine-header">
    <h2 class="engine-title">
      <span class="title-icon">🧠</span>
      Memory Engine
    </h2>
    <div class="connection-badge" class:connected={connected}>
      <span class="status-dot"></span>
      {connected ? 'Live' : 'Simulated'}
    </div>
  </div>
  
  <div class="engine-grid">
    <!-- Consolidation Graph -->
    <div class="card consolidation-card">
      <h3 class="card-title">Memory Consolidation Rate</h3>
      <div class="chart-container">
        <div class="bar-chart">
          {#each consolidationData as item}
            <div class="bar-group">
              <div class="bar-label">{item.name}</div>
              <div class="bar-wrapper">
                <div 
                  class="bar" 
                  style="height: {item.value * 10}px; width: 60px;"
                  class:ingestion={item.name === 'Ingestion'}
                  class:consolidation={item.name === 'Consolidation'}
                >
                  <span class="bar-value">{item.value.toFixed(1)}/s</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
      <div class="chart-subtitle">
        Ingestion: New memories | Consolidation: Processed & stored
      </div>
    </div>
    
    <!-- Deduplication Gauge -->
    <div class="card dedup-card">
      <h3 class="card-title">Deduplication Efficiency</h3>
      <div class="gauge-container">
        <svg class="gauge-svg" viewBox="0 0 200 200">
          <circle
            class="gauge-bg"
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            stroke-width="20"
          />
          <circle
            class="gauge-fill"
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="#00e0ff"
            stroke-width="20"
            stroke-dasharray="{(memoryStats.dedup_rate / 100) * 502.65} 502.65"
            stroke-linecap="round"
            transform="rotate(-90 100 100)"
          />
          <text
            class="gauge-text"
            x="100"
            y="100"
            text-anchor="middle"
            dominant-baseline="middle"
          >
            {memoryStats.dedup_rate.toFixed(1)}%
          </text>
        </svg>
      </div>
      <div class="gauge-subtitle">
        Unique memory retention
      </div>
    </div>
    
    <!-- Trust Tier Distribution -->
    <div class="card trust-card">
      <h3 class="card-title">Trust Tier Distribution</h3>
      <div class="pie-container">
        <svg class="pie-svg" viewBox="0 0 200 200">
          {#each trustPieData as segment, i}
            {@const total = trustPieData.reduce((sum, s) => sum + s.value, 0)}
            {@const percentage = total > 0 ? (segment.value / total) * 100 : 0}
            {@const startAngle = trustPieData.slice(0, i).reduce((sum, s) => sum + (s.value / total) * 360, 0)}
            {@const endAngle = startAngle + (percentage / 100) * 360}
            {@const largeArc = percentage > 50 ? 1 : 0}
            {@const startX = 100 + 70 * Math.cos((startAngle - 90) * Math.PI / 180)}
            {@const startY = 100 + 70 * Math.sin((startAngle - 90) * Math.PI / 180)}
            {@const endX = 100 + 70 * Math.cos((endAngle - 90) * Math.PI / 180)}
            {@const endY = 100 + 70 * Math.sin((endAngle - 90) * Math.PI / 180)}
            
            <path
              d="M 100 100 L {startX} {startY} A 70 70 0 {largeArc} 1 {endX} {endY} Z"
              fill={segment.color}
              opacity="0.8"
            />
          {/each}
          <circle cx="100" cy="100" r="40" fill="#0a0a0f" />
        </svg>
      </div>
      <div class="pie-legend">
        {#each trustPieData as segment}
          <div class="legend-item">
            <span class="legend-dot" style="background: {segment.color}"></span>
            <span class="legend-label">{segment.name}: {segment.value}</span>
          </div>
        {/each}
      </div>
    </div>
    
    <!-- Confidence Delta Heatmap -->
    <div class="card delta-card">
      <h3 class="card-title">Confidence Deltas (Last 50 Reflections)</h3>
      <div class="delta-heatmap">
        {#each memoryStats.confidence_deltas as delta, i}
          <div 
            class="delta-bar"
            style="background-color: {getDeltaColor(delta)}; opacity: {getDeltaOpacity(delta)};"
            title="Delta: {delta.toFixed(3)}"
          ></div>
        {/each}
      </div>
      <div class="delta-legend">
        <div class="legend-item">
          <span class="legend-square" style="background: #22c55e"></span>
          <span>Confidence Growth</span>
        </div>
        <div class="legend-item">
          <span class="legend-square" style="background: #ef4444"></span>
          <span>Confidence Loss</span>
        </div>
      </div>
    </div>
    
    <!-- Quarantine Panel -->
    <div class="card quarantine-card">
      <h3 class="card-title">Quarantine Zone</h3>
      <div class="quarantine-content">
        <div class="quarantine-count" class:warning={memoryStats.quarantine_count > 0}>
          {memoryStats.quarantine_count}
        </div>
        <div class="quarantine-label">
          {memoryStats.quarantine_count === 1 ? 'Trace' : 'Traces'} Isolated
        </div>
        {#if memoryStats.quarantine_count > 0}
          <div class="quarantine-alert">
            <span class="alert-icon">⚠️</span>
            Suspicious entries detected
          </div>
        {:else}
          <div class="quarantine-safe">
            <span class="safe-icon">✅</span>
            All clear
          </div>
        {/if}
      </div>
    </div>
    
    <!-- Recent Memory Events -->
    <div class="card logs-card">
      <h3 class="card-title">Recent Memory Events</h3>
      <div class="logs-container">
        {#each memoryStats.logs.slice().reverse().slice(0, 10) as log}
          <div class="log-entry">
            <span class="log-icon">🧩</span>
            <span class="log-time">{formatTimestamp(log.timestamp)}</span>
            <span class="log-message">{log.message}</span>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  .memory-engine {
    padding: 2rem;
    height: 100%;
    overflow-y: auto;
    background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
  }
  
  .engine-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .engine-title {
    font-size: 2rem;
    color: #00e0ff;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .title-icon {
    font-size: 2.5rem;
    animation: pulse-icon 3s infinite;
  }
  
  @keyframes pulse-icon {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.1); opacity: 0.8; }
  }
  
  .connection-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    font-size: 0.85rem;
    color: #888;
  }
  
  .connection-badge.connected {
    border-color: #00ff88;
    color: #00ff88;
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #888;
    animation: pulse-dot 2s infinite;
  }
  
  .connection-badge.connected .status-dot {
    background: #00ff88;
  }
  
  @keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  
  .engine-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  
  .card {
    background: rgba(26, 26, 46, 0.5);
    border: 1px solid rgba(0, 224, 255, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    transition: all 0.3s ease;
  }
  
  .card:hover {
    border-color: #00e0ff;
    box-shadow: 0 0 20px rgba(0, 224, 255, 0.2);
  }
  
  .card-title {
    font-size: 1.1rem;
    color: #ffce47;
    margin: 0 0 1.5rem 0;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  /* Consolidation Card */
  .consolidation-card {
    grid-column: span 2;
  }
  
  .chart-container {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    min-height: 200px;
    margin-bottom: 1rem;
  }
  
  .bar-chart {
    display: flex;
    gap: 3rem;
    align-items: flex-end;
  }
  
  .bar-group {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }
  
  .bar-wrapper {
    display: flex;
    align-items: flex-end;
    height: 150px;
  }
  
  .bar {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 0.5rem;
    border-radius: 8px 8px 0 0;
    transition: all 0.5s ease;
    position: relative;
  }
  
  .bar.ingestion {
    background: linear-gradient(to top, #00e0ff, #0088ff);
  }
  
  .bar.consolidation {
    background: linear-gradient(to top, #ffce47, #ff8800);
  }
  
  .bar-value {
    color: #fff;
    font-weight: bold;
    font-size: 0.9rem;
  }
  
  .bar-label {
    color: #00e0ff;
    font-size: 0.9rem;
    font-weight: 500;
  }
  
  .chart-subtitle {
    text-align: center;
    color: #888;
    font-size: 0.85rem;
  }
  
  /* Deduplication Gauge */
  .gauge-container {
    display: flex;
    justify-content: center;
    margin-bottom: 1rem;
  }
  
  .gauge-svg {
    width: 200px;
    height: 200px;
  }
  
  .gauge-fill {
    transition: stroke-dasharray 0.5s ease;
  }
  
  .gauge-text {
    fill: #00e0ff;
    font-size: 32px;
    font-weight: bold;
  }
  
  .gauge-subtitle {
    text-align: center;
    color: #888;
    font-size: 0.85rem;
  }
  
  /* Trust Tier Pie Chart */
  .pie-container {
    display: flex;
    justify-content: center;
    margin-bottom: 1rem;
  }
  
  .pie-svg {
    width: 200px;
    height: 200px;
  }
  
  .pie-legend {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    color: #ccc;
  }
  
  .legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
  
  .legend-square {
    width: 16px;
    height: 16px;
    border-radius: 4px;
  }
  
  .legend-label {
    flex: 1;
  }
  
  /* Confidence Delta Heatmap */
  .delta-card {
    grid-column: span 2;
  }
  
  .delta-heatmap {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 1rem;
  }
  
  .delta-bar {
    width: 12px;
    height: 40px;
    border-radius: 4px;
    transition: all 0.3s ease;
  }
  
  .delta-bar:hover {
    transform: scaleY(1.2);
    cursor: pointer;
  }
  
  .delta-legend {
    display: flex;
    gap: 2rem;
    justify-content: center;
    font-size: 0.85rem;
    color: #ccc;
  }
  
  /* Quarantine Panel */
  .quarantine-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  
  .quarantine-count {
    font-size: 3rem;
    font-weight: bold;
    color: #00ff88;
  }
  
  .quarantine-count.warning {
    color: #ffce47;
    animation: pulse-warning 2s infinite;
  }
  
  @keyframes pulse-warning {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }
  
  .quarantine-label {
    color: #888;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .quarantine-alert,
  .quarantine-safe {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 12px;
    font-size: 0.85rem;
  }
  
  .quarantine-alert {
    background: rgba(255, 206, 71, 0.1);
    border: 1px solid rgba(255, 206, 71, 0.3);
    color: #ffce47;
  }
  
  .quarantine-safe {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
  }
  
  .alert-icon,
  .safe-icon {
    font-size: 1.2rem;
  }
  
  /* Logs Panel */
  .logs-card {
    grid-column: span 3;
  }
  
  .logs-container {
    max-height: 300px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .log-entry {
    display: grid;
    grid-template-columns: auto auto 1fr;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(0, 224, 255, 0.05);
    border-left: 3px solid rgba(0, 224, 255, 0.3);
    border-radius: 8px;
    font-size: 0.85rem;
    transition: all 0.3s ease;
  }
  
  .log-entry:hover {
    background: rgba(0, 224, 255, 0.1);
    border-left-color: #00e0ff;
  }
  
  .log-icon {
    font-size: 1.1rem;
  }
  
  .log-time {
    color: #888;
    font-size: 0.8rem;
    white-space: nowrap;
  }
  
  .log-message {
    color: #ccc;
  }
  
  /* Scrollbar styling */
  .logs-container::-webkit-scrollbar,
  .memory-engine::-webkit-scrollbar {
    width: 8px;
  }
  
  .logs-container::-webkit-scrollbar-track,
  .memory-engine::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
  }
  
  .logs-container::-webkit-scrollbar-thumb,
  .memory-engine::-webkit-scrollbar-thumb {
    background: rgba(0, 224, 255, 0.3);
    border-radius: 4px;
  }
  
  .logs-container::-webkit-scrollbar-thumb:hover,
  .memory-engine::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 224, 255, 0.5);
  }
  
  /* Responsive */
  @media (max-width: 1024px) {
    .engine-grid {
      grid-template-columns: 1fr;
    }
    
    .consolidation-card,
    .delta-card,
    .logs-card {
      grid-column: span 1;
    }
  }
  
  @media (max-width: 640px) {
    .memory-engine {
      padding: 1rem;
    }
    
    .engine-title {
      font-size: 1.5rem;
    }
    
    .bar-chart {
      gap: 1.5rem;
    }
  }
</style>
