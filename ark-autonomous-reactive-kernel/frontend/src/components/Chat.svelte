<script>
  import { onMount, createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  export let agent;
  
  let messages = [];
  let inputMessage = '';
  let isTyping = false;
  let messagesContainer;
  
  // Agent color mapping
  const agentColors = {
    'Kyle': '#00e0ff',
    'Joey': '#8a2be2', 
    'Kenny': '#ff6b35',
    'HRM': '#ffd700',
    'Aletheia': '#9370db',
    'ID': '#20b2aa'
  };
  
  onMount(() => {
    loadConversationHistory();
  });
  
  async function loadConversationHistory() {
    try {
      const response = await fetch(`/api/conversations?agent_name=${agent.name}&limit=20`);
      if (response.ok) {
        const data = await response.json();
        messages = data.conversations.reverse().map(conv => ([
          {
            type: 'user',
            content: conv.user_message,
            timestamp: new Date(conv.timestamp)
          },
          {
            type: 'agent',
            content: conv.agent_response,
            timestamp: new Date(conv.timestamp)
          }
        ])).flat();
        scrollToBottom();
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  }
  
  async function sendMessage() {
    if (!inputMessage.trim()) return;
    
    const userMessage = {
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };
    
    messages = [...messages, userMessage];
    const messageToSend = inputMessage.trim();
    inputMessage = '';
    isTyping = true;
    
    scrollToBottom();
    
    try {
      const response = await fetch(`/api/chat/${agent.name}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: messageToSend
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status}`);
      }
      
      const data = await response.json();
      
      const agentMessage = {
        type: 'agent',
        content: data.response || 'I apologize, but I encountered an issue processing your message.',
        timestamp: new Date(),
        tools_used: data.tools_used || [],
        files_created: data.files_created || []
      };
      
      messages = [...messages, agentMessage];
      scrollToBottom();
      
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        type: 'agent',
        content: `I apologize, but I'm having trouble connecting right now. Error: ${error.message}`,
        timestamp: new Date(),
        isError: true
      };
      messages = [...messages, errorMessage];
    } finally {
      isTyping = false;
      scrollToBottom();
    }
  }
  
  function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }
  
  function scrollToBottom() {
    setTimeout(() => {
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }, 100);
  }
  
  function formatTimestamp(timestamp) {
    return timestamp.toLocaleTimeString();
  }
  
  function goBack() {
    dispatch('back');
  }
</script>

<div class="chat-interface" style="--agent-color: {agentColors[agent.name] || '#00e0ff'}">
  <!-- Chat Header -->
  <header class="chat-header">
    <button class="back-button" on:click={goBack}>
      ← Back to Council
    </button>
    
    <div class="agent-info">
      <div class="agent-avatar">
        {#if agent.name === 'Kyle'}🔍
        {:else if agent.name === 'Joey'}🧠
        {:else if agent.name === 'Kenny'}🔨
        {:else if agent.name === 'HRM'}⚖️
        {:else if agent.name === 'Aletheia'}🔮
        {:else if agent.name === 'ID'}🌱
        {:else}🤖{/if}
      </div>
      <div class="agent-details">
        <h2 class="agent-name">{agent.name}</h2>
        <p class="agent-essence">{agent.essence}</p>
      </div>
    </div>
    
    <div class="agent-status">
      <span class="status-indicator"></span>
      {agent.status}
    </div>
  </header>
  
  <!-- Messages Container -->
  <div class="messages-container" bind:this={messagesContainer}>
    <div class="messages-list">
      {#if messages.length === 0}
        <div class="welcome-message">
          <div class="welcome-avatar">
            {#if agent.name === 'Kyle'}🔍
            {:else if agent.name === 'Joey'}🧠
            {:else if agent.name === 'Kenny'}🔨
            {:else if agent.name === 'HRM'}⚖️
            {:else if agent.name === 'Aletheia'}🔮
            {:else if agent.name === 'ID'}🌱
            {:else}🤖{/if}
          </div>
          <p>
            Greetings. I am <strong>{agent.name}</strong>, {agent.essence.toLowerCase()}. 
            How may I assist you in your journey toward deeper understanding?
          </p>
        </div>
      {/if}
      
      {#each messages as message, index}
        <div class="message" class:user-message={message.type === 'user'} class:agent-message={message.type === 'agent'}>
          <div class="message-content">
            {#if message.type === 'user'}
              <div class="user-avatar">👤</div>
            {:else}
              <div class="agent-message-avatar">
                {#if agent.name === 'Kyle'}🔍
                {:else if agent.name === 'Joey'}🧠
                {:else if agent.name === 'Kenny'}🔨
                {:else if agent.name === 'HRM'}⚖️
                {:else if agent.name === 'Aletheia'}🔮
                {:else if agent.name === 'ID'}🌱
                {:else}🤖{/if}
              </div>
            {/if}
            
            <div class="message-bubble" class:error-message={message.isError}>
              <div class="message-text">
                {@html message.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/`(.*?)`/g, '<code>$1</code>')}
              </div>
              
              {#if message.tools_used && message.tools_used.length > 0}
                <div class="tools-used">
                  <span class="tools-label">🛠️ Tools:</span>
                  {#each message.tools_used as tool}
                    <span class="tool-tag">{tool}</span>
                  {/each}
                </div>
              {/if}
              
              {#if message.files_created && message.files_created.length > 0}
                <div class="files-created">
                  <span class="files-label">📁 Files:</span>
                  {#each message.files_created as file}
                    <span class="file-tag">{file}</span>
                  {/each}
                </div>
              {/if}
              
              <div class="message-timestamp">
                {formatTimestamp(message.timestamp)}
              </div>
            </div>
          </div>
        </div>
      {/each}
      
      {#if isTyping}
        <div class="message agent-message typing-message">
          <div class="message-content">
            <div class="agent-message-avatar">
              {#if agent.name === 'Kyle'}🔍
              {:else if agent.name === 'Joey'}🧠
              {:else if agent.name === 'Kenny'}🔨
              {:else if agent.name === 'HRM'}⚖️
              {:else if agent.name === 'Aletheia'}🔮
              {:else if agent.name === 'ID'}🌱
              {:else}🤖{/if}
            </div>
            <div class="message-bubble">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
  
  <!-- Input Area -->
  <div class="input-area">
    <div class="input-container">
      <textarea
        bind:value={inputMessage}
        on:keydown={handleKeyPress}
        placeholder="Share your thoughts with {agent.name}..."
        rows="3"
        disabled={isTyping}
      ></textarea>
      <button 
        class="send-button" 
        on:click={sendMessage}
        disabled={!inputMessage.trim() || isTyping}
      >
        {#if isTyping}
          <div class="sending-spinner"></div>
        {:else}
          Send
        {/if}
      </button>
    </div>
  </div>
</div>

<style>
  .chat-interface {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 60px);
    background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
  }
  
  .chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    background: rgba(26, 26, 46, 0.8);
    border-bottom: 2px solid var(--agent-color);
    backdrop-filter: blur(10px);
  }
  
  .back-button {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: #fff;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .back-button:hover {
    border-color: var(--agent-color);
    background: rgba(255, 255, 255, 0.1);
  }
  
  .agent-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .agent-avatar {
    font-size: 2rem;
    filter: drop-shadow(0 0 10px var(--agent-color));
  }
  
  .agent-name {
    margin: 0;
    color: var(--agent-color);
    font-size: 1.2rem;
    text-shadow: 0 0 10px var(--agent-color);
  }
  
  .agent-essence {
    margin: 0;
    color: #ffce47;
    font-size: 0.9rem;
    font-style: italic;
  }
  
  .agent-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    color: #ccc;
  }
  
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--agent-color);
    animation: pulse 2s infinite;
  }
  
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .messages-list {
    max-width: 800px;
    margin: 0 auto;
  }
  
  .welcome-message {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 2rem;
    background: rgba(26, 26, 46, 0.5);
    border-radius: 15px;
    border: 2px solid var(--agent-color);
    margin-bottom: 2rem;
  }
  
  .welcome-avatar {
    font-size: 2rem;
    filter: drop-shadow(0 0 10px var(--agent-color));
  }
  
  .message {
    margin-bottom: 1rem;
  }
  
  .message-content {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .user-message .message-content {
    flex-direction: row-reverse;
  }
  
  .user-avatar, .agent-message-avatar {
    font-size: 1.5rem;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  .user-avatar {
    background: linear-gradient(45deg, #00e0ff, #ffce47);
  }
  
  .agent-message-avatar {
    background: rgba(26, 26, 46, 0.8);
    border: 2px solid var(--agent-color);
    filter: drop-shadow(0 0 5px var(--agent-color));
  }
  
  .message-bubble {
    max-width: 70%;
    padding: 1rem;
    border-radius: 15px;
    position: relative;
  }
  
  .user-message .message-bubble {
    background: linear-gradient(45deg, #00e0ff, #ffce47);
    color: #0a0a0f;
    margin-left: auto;
  }
  
  .agent-message .message-bubble {
    background: rgba(26, 26, 46, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #fff;
  }
  
  .error-message {
    background: rgba(255, 68, 68, 0.2) !important;
    border-color: #ff4444 !important;
  }
  
  .message-text {
    line-height: 1.5;
    margin-bottom: 0.5rem;
  }
  
  .message-text :global(strong) {
    color: var(--agent-color);
  }
  
  .message-text :global(code) {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.9em;
  }
  
  .tools-used, .files-created {
    margin-top: 0.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    align-items: center;
  }
  
  .tools-label, .files-label {
    font-size: 0.8rem;
    color: #888;
  }
  
  .tool-tag, .file-tag {
    background: rgba(255, 255, 255, 0.1);
    color: var(--agent-color);
    padding: 0.2rem 0.5rem;
    border-radius: 8px;
    font-size: 0.8rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .message-timestamp {
    font-size: 0.7rem;
    color: #888;
    margin-top: 0.5rem;
    text-align: right;
  }
  
  .user-message .message-timestamp {
    text-align: left;
  }
  
  .typing-message .message-bubble {
    background: rgba(26, 26, 46, 0.6);
  }
  
  .typing-indicator {
    display: flex;
    gap: 0.3rem;
    align-items: center;
    padding: 0.5rem 0;
  }
  
  .typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--agent-color);
    animation: typing 1.4s infinite ease-in-out;
  }
  
  .typing-indicator span:nth-child(1) {
    animation-delay: -0.32s;
  }
  
  .typing-indicator span:nth-child(2) {
    animation-delay: -0.16s;
  }
  
  @keyframes typing {
    0%, 80%, 100% {
      transform: scale(0.8);
      opacity: 0.5;
    }
    40% {
      transform: scale(1);
      opacity: 1;
    }
  }
  
  .input-area {
    padding: 1rem 2rem 2rem;
    background: rgba(26, 26, 46, 0.8);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .input-container {
    max-width: 800px;
    margin: 0 auto;
    display: flex;
    gap: 1rem;
    align-items: flex-end;
  }
  
  .input-container textarea {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    padding: 1rem;
    color: #fff;
    font-family: inherit;
    font-size: 1rem;
    resize: none;
    transition: border-color 0.3s ease;
  }
  
  .input-container textarea:focus {
    outline: none;
    border-color: var(--agent-color);
    box-shadow: 0 0 10px rgba(0, 224, 255, 0.3);
  }
  
  .input-container textarea::placeholder {
    color: #888;
  }
  
  .send-button {
    background: linear-gradient(45deg, var(--agent-color), #ffce47);
    border: none;
    color: #0a0a0f;
    padding: 1rem 1.5rem;
    border-radius: 15px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 80px;
  }
  
  .send-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  }
  
  .send-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .sending-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(10, 10, 15, 0.3);
    border-top: 2px solid #0a0a0f;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
  
  /* Responsive design */
  @media (max-width: 768px) {
    .chat-header {
      padding: 1rem;
      flex-direction: column;
      gap: 1rem;
    }
    
    .input-area {
      padding: 1rem;
    }
    
    .input-container {
      flex-direction: column;
      align-items: stretch;
    }
    
    .message-bubble {
      max-width: 90%;
    }
  }
</style>