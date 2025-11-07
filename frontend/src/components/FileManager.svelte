<script>
  import { onMount } from 'svelte';
  
  let files = [];
  let loading = true;
  let error = null;
  let selectedFile = null;
  let fileContent = '';
  let showCreateModal = false;
  let newFileName = '';
  let newFileContent = '';
  let searchQuery = '';
  let sortBy = 'modified'; // 'name', 'size', 'modified'
  let sortOrder = 'desc'; // 'asc', 'desc'
  
  // File type icons
  const fileIcons = {
    'json': '📄',
    'csv': '📊',
    'txt': '📝',
    'md': '📋',
    'py': '🐍',
    'js': '⚡',
    'html': '🌐',
    'css': '🎨',
    'pdf': '📕',
    'log': '📜'
  };
  
  onMount(() => {
    loadFiles();
  });
  
  async function loadFiles() {
    try {
      loading = true;
      const response = await fetch('/api/files');
      
      if (!response.ok) {
        throw new Error(`Failed to load files: ${response.status}`);
      }
      
      const data = await response.json();
      files = data.files || [];
      error = null;
    } catch (err) {
      error = err.message;
      console.error('Failed to load files:', err);
    } finally {
      loading = false;
    }
  }
  
  async function loadFileContent(filePath) {
    try {
      const response = await fetch(`/api/files/${encodeURIComponent(filePath)}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load file: ${response.status}`);
      }
      
      const data = await response.json();
      fileContent = data.content || '';
      selectedFile = filePath;
    } catch (err) {
      error = `Failed to load file content: ${err.message}`;
      console.error('Failed to load file content:', err);
    }
  }
  
  async function saveFile(filePath, content) {
    try {
      const response = await fetch('/api/files', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          path: filePath,
          content: content
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to save file: ${response.status}`);
      }
      
      await loadFiles();
      return true;
    } catch (err) {
      error = `Failed to save file: ${err.message}`;
      console.error('Failed to save file:', err);
      return false;
    }
  }
  
  async function deleteFile(filePath) {
    if (!confirm(`Are you sure you want to delete "${filePath}"?`)) {
      return;
    }
    
    try {
      const response = await fetch(`/api/files/${encodeURIComponent(filePath)}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete file: ${response.status}`);
      }
      
      if (selectedFile === filePath) {
        selectedFile = null;
        fileContent = '';
      }
      
      await loadFiles();
    } catch (err) {
      error = `Failed to delete file: ${err.message}`;
      console.error('Failed to delete file:', err);
    }
  }
  
  async function createNewFile() {
    if (!newFileName.trim()) {
      alert('Please enter a filename');
      return;
    }
    
    const success = await saveFile(newFileName.trim(), newFileContent);
    if (success) {
      showCreateModal = false;
      newFileName = '';
      newFileContent = '';
    }
  }
  
  async function saveCurrentFile() {
    if (!selectedFile) return;
    
    const success = await saveFile(selectedFile, fileContent);
    if (success) {
      alert('File saved successfully!');
    }
  }
  
  function getFileIcon(filename) {
    const extension = filename.split('.').pop()?.toLowerCase();
    return fileIcons[extension] || '📄';
  }
  
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
  
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
  }
  
  // Computed filtered and sorted files
  $: filteredAndSortedFiles = files
    .filter(file => 
      file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      file.path.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'size':
          aValue = a.size;
          bValue = b.size;
          break;
        case 'modified':
          aValue = new Date(a.modified);
          bValue = new Date(b.modified);
          break;
        default:
          return 0;
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  
  function toggleSort(field) {
    if (sortBy === field) {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = field;
      sortOrder = 'desc';
    }
  }
</script>

<div class="file-manager">
  <!-- File Manager Header -->
  <header class="fm-header">
    <div class="header-title">
      <h2>📂 A.R.K. File System</h2>
      <p>Manage files created by the Council of Consciousness</p>
    </div>
    
    <div class="header-actions">
      <button class="create-btn" on:click={() => showCreateModal = true}>
        ➕ Create File
      </button>
      <button class="refresh-btn" on:click={loadFiles} disabled={loading}>
        🔄 Refresh
      </button>
    </div>
  </header>
  
  <div class="fm-content">
    <!-- File List Panel -->
    <div class="file-list-panel">
      <div class="file-controls">
        <input
          type="text"
          placeholder="Search files..."
          bind:value={searchQuery}
          class="search-input"
        />
        
        <div class="sort-controls">
          <button 
            class="sort-btn" 
            class:active={sortBy === 'name'}
            on:click={() => toggleSort('name')}
          >
            Name {sortBy === 'name' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
          </button>
          <button 
            class="sort-btn"
            class:active={sortBy === 'size'} 
            on:click={() => toggleSort('size')}
          >
            Size {sortBy === 'size' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
          </button>
          <button 
            class="sort-btn"
            class:active={sortBy === 'modified'}
            on:click={() => toggleSort('modified')}
          >
            Modified {sortBy === 'modified' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
          </button>
        </div>
      </div>
      
      {#if loading}
        <div class="loading-state">
          <div class="loading-spinner"></div>
          <p>Loading files...</p>
        </div>
      {:else if error}
        <div class="error-state">
          <p>❌ {error}</p>
          <button class="retry-btn" on:click={loadFiles}>Retry</button>
        </div>
      {:else if filteredAndSortedFiles.length === 0}
        <div class="empty-state">
          <p>📂 No files found</p>
          {#if searchQuery}
            <button class="clear-search-btn" on:click={() => searchQuery = ''}>
              Clear search
            </button>
          {:else}
            <p>Files created by agents will appear here</p>
          {/if}
        </div>
      {:else}
        <div class="files-list">
          {#each filteredAndSortedFiles as file}
            <div 
              class="file-item"
              class:selected={selectedFile === file.path}
              on:click={() => loadFileContent(file.path)}
              role="button"
              tabindex="0"
            >
              <div class="file-icon">
                {getFileIcon(file.name)}
              </div>
              
              <div class="file-info">
                <div class="file-name" title={file.path}>
                  {file.name}
                </div>
                <div class="file-meta">
                  {formatFileSize(file.size)} • {formatDate(file.modified)}
                </div>
              </div>
              
              <button 
                class="delete-btn"
                on:click|stopPropagation={() => deleteFile(file.path)}
                title="Delete file"
              >
                🗑️
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    
    <!-- File Content Panel -->
    <div class="file-content-panel">
      {#if selectedFile}
        <div class="content-header">
          <h3>📄 {selectedFile}</h3>
          <button class="save-btn" on:click={saveCurrentFile}>
            💾 Save
          </button>
        </div>
        
        <div class="content-editor">
          <textarea
            bind:value={fileContent}
            placeholder="File content will appear here..."
            class="content-textarea"
          ></textarea>
        </div>
      {:else}
        <div class="no-file-selected">
          <div class="selection-prompt">
            <h3>📋 Select a file to view its content</h3>
            <p>Click on any file from the list to view and edit its contents.</p>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Create File Modal -->
{#if showCreateModal}
  <div class="modal-overlay" on:click={() => showCreateModal = false}>
    <div class="modal-content" on:click|stopPropagation>
      <div class="modal-header">
        <h3>📝 Create New File</h3>
        <button class="close-btn" on:click={() => showCreateModal = false}>
          ✖️
        </button>
      </div>
      
      <div class="modal-body">
        <div class="form-group">
          <label for="filename">Filename:</label>
          <input
            type="text"
            id="filename"
            bind:value={newFileName}
            placeholder="e.g., my_document.txt"
            class="filename-input"
          />
        </div>
        
        <div class="form-group">
          <label for="content">Content:</label>
          <textarea
            id="content"
            bind:value={newFileContent}
            placeholder="Enter file content here..."
            class="content-input"
            rows="10"
          ></textarea>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="cancel-btn" on:click={() => showCreateModal = false}>
          Cancel
        </button>
        <button class="create-file-btn" on:click={createNewFile}>
          Create File
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .file-manager {
    height: calc(100vh - 60px);
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
  }
  
  .fm-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 2rem;
    background: rgba(26, 26, 46, 0.8);
    border-bottom: 2px solid #00e0ff;
    backdrop-filter: blur(10px);
  }
  
  .header-title h2 {
    margin: 0;
    color: #00e0ff;
    font-size: 1.5rem;
  }
  
  .header-title p {
    margin: 0.3rem 0 0 0;
    color: #ccc;
    font-size: 0.9rem;
  }
  
  .header-actions {
    display: flex;
    gap: 1rem;
  }
  
  .create-btn, .refresh-btn {
    background: linear-gradient(45deg, #00e0ff, #ffce47);
    border: none;
    color: #0a0a0f;
    padding: 0.7rem 1.2rem;
    border-radius: 20px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .create-btn:hover, .refresh-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  }
  
  .refresh-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
  
  .fm-content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  
  .file-list-panel {
    width: 350px;
    background: rgba(26, 26, 46, 0.6);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
  }
  
  .file-controls {
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .search-input {
    width: 100%;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 20px;
    padding: 0.7rem 1rem;
    color: #fff;
    font-size: 0.9rem;
    margin-bottom: 1rem;
  }
  
  .search-input:focus {
    outline: none;
    border-color: #00e0ff;
    box-shadow: 0 0 10px rgba(0, 224, 255, 0.3);
  }
  
  .search-input::placeholder {
    color: #888;
  }
  
  .sort-controls {
    display: flex;
    gap: 0.5rem;
  }
  
  .sort-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #ccc;
    padding: 0.4rem 0.8rem;
    border-radius: 15px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .sort-btn:hover {
    border-color: #00e0ff;
    color: #00e0ff;
  }
  
  .sort-btn.active {
    background: rgba(0, 224, 255, 0.2);
    border-color: #00e0ff;
    color: #00e0ff;
  }
  
  .loading-state, .error-state, .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 2rem;
  }
  
  .loading-spinner {
    width: 30px;
    height: 30px;
    border: 3px solid rgba(0, 224, 255, 0.3);
    border-top: 3px solid #00e0ff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  .retry-btn, .clear-search-btn {
    background: transparent;
    border: 1px solid #00e0ff;
    color: #00e0ff;
    padding: 0.5rem 1rem;
    border-radius: 15px;
    cursor: pointer;
  }
  
  .files-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
  }
  
  .file-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-bottom: 0.5rem;
  }
  
  .file-item:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .file-item.selected {
    background: rgba(0, 224, 255, 0.2);
    border: 1px solid #00e0ff;
  }
  
  .file-icon {
    font-size: 1.2rem;
    width: 24px;
    text-align: center;
  }
  
  .file-info {
    flex: 1;
    min-width: 0;
  }
  
  .file-name {
    font-size: 0.9rem;
    font-weight: 500;
    color: #fff;
    truncate: ellipsis;
    overflow: hidden;
    white-space: nowrap;
  }
  
  .file-meta {
    font-size: 0.75rem;
    color: #888;
    margin-top: 0.2rem;
  }
  
  .delete-btn {
    background: transparent;
    border: none;
    color: #ff6b6b;
    cursor: pointer;
    padding: 0.2rem;
    border-radius: 5px;
    opacity: 0;
    transition: all 0.3s ease;
  }
  
  .file-item:hover .delete-btn {
    opacity: 1;
  }
  
  .delete-btn:hover {
    background: rgba(255, 107, 107, 0.2);
  }
  
  .file-content-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: rgba(10, 10, 15, 0.8);
  }
  
  .content-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .content-header h3 {
    margin: 0;
    color: #00e0ff;
    font-size: 1.1rem;
  }
  
  .save-btn {
    background: linear-gradient(45deg, #00e0ff, #ffce47);
    border: none;
    color: #0a0a0f;
    padding: 0.5rem 1rem;
    border-radius: 15px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .save-btn:hover {
    transform: translateY(-1px);
  }
  
  .content-editor {
    flex: 1;
    padding: 1rem 1.5rem;
  }
  
  .content-textarea {
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 1rem;
    color: #fff;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    resize: none;
  }
  
  .content-textarea:focus {
    outline: none;
    border-color: #00e0ff;
    box-shadow: 0 0 10px rgba(0, 224, 255, 0.3);
  }
  
  .no-file-selected {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .selection-prompt {
    text-align: center;
    color: #888;
  }
  
  .selection-prompt h3 {
    color: #ccc;
    margin-bottom: 0.5rem;
  }
  
  /* Modal Styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .modal-content {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 2px solid #00e0ff;
    border-radius: 15px;
    width: 90%;
    max-width: 500px;
    max-height: 80vh;
    overflow: hidden;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .modal-header h3 {
    margin: 0;
    color: #00e0ff;
  }
  
  .close-btn {
    background: transparent;
    border: none;
    color: #ff6b6b;
    cursor: pointer;
    font-size: 1rem;
  }
  
  .modal-body {
    padding: 1.5rem;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-group label {
    display: block;
    color: #ccc;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }
  
  .filename-input, .content-input {
    width: 100%;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 0.7rem;
    color: #fff;
    font-size: 0.9rem;
  }
  
  .filename-input:focus, .content-input:focus {
    outline: none;
    border-color: #00e0ff;
    box-shadow: 0 0 5px rgba(0, 224, 255, 0.3);
  }
  
  .content-input {
    font-family: 'Courier New', monospace;
    resize: vertical;
  }
  
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    padding: 1rem 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .cancel-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: #ccc;
    padding: 0.7rem 1.2rem;
    border-radius: 15px;
    cursor: pointer;
  }
  
  .create-file-btn {
    background: linear-gradient(45deg, #00e0ff, #ffce47);
    border: none;
    color: #0a0a0f;
    padding: 0.7rem 1.2rem;
    border-radius: 15px;
    font-weight: bold;
    cursor: pointer;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Responsive design */
  @media (max-width: 768px) {
    .fm-content {
      flex-direction: column;
    }
    
    .file-list-panel {
      width: 100%;
      height: 40%;
    }
    
    .file-content-panel {
      height: 60%;
    }
  }
</style>