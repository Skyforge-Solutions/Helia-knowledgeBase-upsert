// Pinecone Admin Interface Logic

// DOM Elements
const elements = {
  indexInfo: document.getElementById('index-info'),
  namespacesList: document.getElementById('namespaces-list'),
  namespaceDetailsContainer: document.getElementById('namespace-details-container'),
  selectedNamespaceName: document.getElementById('selected-namespace-name'),
  backButton: document.getElementById('back-button'),
  clearNamespaceBtn: document.getElementById('clear-namespace-btn'),
  namespaceSamples: document.getElementById('namespace-samples'),
  confirmationModal: document.getElementById('confirmation-modal'),
  modalTitle: document.getElementById('modal-title'),
  modalMessage: document.getElementById('modal-message'),
  modalCancel: document.getElementById('modal-cancel'),
  modalConfirm: document.getElementById('modal-confirm'),
  // Search form elements
  searchForm: document.getElementById('search-form'),
  searchButton: document.getElementById('search-button'),
  searchButtonText: document.querySelector('#search-button .btn-text'),
  searchButtonLoading: document.querySelector('#search-button .btn-loading'),
  searchNamespaceSelect: document.getElementById('search-namespace'),
  searchQuery: document.getElementById('search-query'),
  searchLimit: document.getElementById('search-limit'),
  searchResults: document.getElementById('search-results')
};

// State
const state = {
  selectedNamespace: null,
  stats: null,
  isLoading: {
    indexInfo: false,
    namespaces: false,
    samples: false,
    search: false,
    clearOperation: false
  }
};

// Set loading state for different UI components
function setLoading(component, isLoading) {
  state.isLoading[component] = isLoading;
  
  if (component === 'search') {
    elements.searchButton.disabled = isLoading;
    elements.searchButtonText.style.display = isLoading ? 'none' : 'inline-block';
    elements.searchButtonLoading.style.display = isLoading ? 'inline-block' : 'none';
  } else if (component === 'clearOperation') {
    elements.clearNamespaceBtn.disabled = isLoading;
    elements.clearNamespaceBtn.textContent = isLoading ? 'Clearing...' : 'Clear Namespace Data';
  }
}

// Show error message
function showError(container, message) {
  container.innerHTML = `
    <div class="message error">
      <strong>Error:</strong> ${message}
    </div>
  `;
}

// Show success message
function showSuccess(container, message) {
  container.innerHTML = `
    <div class="message success">
      ${message}
    </div>
  `;
}

// Show no data message
function showNoData(container, message = "No data available") {
  container.innerHTML = `<div class="no-data">${message}</div>`;
}

// Show loading indicator
function showLoading(container, message = "Loading...") {
  container.innerHTML = `
    <div class="loading-container">
      <div class="loading-spinner"></div>
      <div>${message}</div>
    </div>
  `;
}

// Fetch index stats
async function fetchPineconeStats() {
  setLoading('indexInfo', true);
  setLoading('namespaces', true);
  
  try {
    const response = await fetch('/pinecone-admin/api/stats');
    if (!response.ok) throw new Error('Failed to fetch Pinecone stats');
    
    const data = await response.json();
    state.stats = data;
    renderIndexInfo(data);
    renderNamespaces(data);
    populateSearchNamespaces(data.namespaces);
  } catch (error) {
    console.error('Error fetching Pinecone stats:', error);
    showError(elements.indexInfo, error.message);
    showError(elements.namespacesList, error.message);
  } finally {
    setLoading('indexInfo', false);
    setLoading('namespaces', false);
  }
}

// Populate the search namespace dropdown
function populateSearchNamespaces(namespaces) {
  // Clear existing options except the first one
  while (elements.searchNamespaceSelect.options.length > 1) {
    elements.searchNamespaceSelect.remove(1);
  }

  // Add options for each namespace
  Object.entries(namespaces).forEach(([namespace, info]) => {
    const displayName = info.display_name || namespace;
    const option = document.createElement('option');
    option.value = namespace;
    option.textContent = displayName;
    elements.searchNamespaceSelect.appendChild(option);
  });
}

// Search vectors in a namespace
async function searchNamespace(namespace, query, limit) {
  setLoading('search', true);
  showLoading(elements.searchResults, "Searching...");
  
  try {
    const response = await fetch(`/pinecone-admin/api/namespace/${namespace}/search?query=${encodeURIComponent(query)}&top_k=${limit}`);
    if (!response.ok) throw new Error('Search failed');
    
    const data = await response.json();
    renderSearchResults(data);
  } catch (error) {
    console.error('Error searching:', error);
    showError(elements.searchResults, error.message);
  } finally {
    setLoading('search', false);
  }
}

// Render search results
function renderSearchResults(data) {
  if (!data.results || data.results.length === 0) {
    showNoData(elements.searchResults, "No results found");
    return;
  }

  // Create the search results header with query and stats
  let resultsHtml = `
    <div class="search-query">
      <strong>Query:</strong> ${data.query}
    </div>
    <div class="search-stats">
      <span class="search-stats-label">Found ${data.results.length} results in "${data.display_name}" namespace</span>
    </div>
  `;

  // Create result items
  const resultItems = data.results.map((result, index) => {
    // Get text content or excerpt
    const text = result.text || '(No text available)';
    const textExcerpt = text.length > 300 ? 
      text.substring(0, 300) + '...' : 
      text;

    return `
      <div class="sample-item">
        <div class="sample-header">
          <div class="sample-id">ID: ${result.id}</div>
          <div class="sample-score">Score: ${result.score.toFixed(4)}</div>
        </div>
        <div class="sample-text">${textExcerpt}</div>
      </div>
    `;
  }).join('');

  elements.searchResults.innerHTML = resultsHtml + resultItems;
}

// Render index information
function renderIndexInfo(data) {
  elements.indexInfo.innerHTML = `
    <div class="info-item">
      <div class="info-label">Index Name</div>
      <div class="info-value">${data.index_name}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Total Vectors</div>
      <div class="info-value">${data.total_vectors.toLocaleString()}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Dimension</div>
      <div class="info-value">${data.dimension}</div>
    </div>
    <div class="info-item">
      <div class="info-label">Namespaces</div>
      <div class="info-value">${Object.keys(data.namespaces).length}</div>
    </div>
  `;
}

// Render namespaces list
function renderNamespaces(data) {
  if (Object.keys(data.namespaces).length === 0) {
    showNoData(elements.namespacesList, "No namespaces found");
    return;
  }

  elements.namespacesList.innerHTML = Object.entries(data.namespaces)
    .map(([namespace, info]) => {
      const displayName = info.display_name || namespace;
      return `
        <div class="namespace-item" data-namespace="${namespace}">
          <div class="namespace-header">
            <h3>${displayName}</h3>
            <div class="vector-count">${info.vector_count.toLocaleString()} vectors</div>
          </div>
          <button class="view-btn" data-namespace="${namespace}" data-name="${displayName}">View Details</button>
        </div>
      `;
    })
    .join('');

  // Add event listeners to view buttons
  document.querySelectorAll('.view-btn').forEach(button => {
    button.addEventListener('click', (e) => {
      const namespace = e.target.dataset.namespace;
      const displayName = e.target.dataset.name;
      showNamespaceDetails(namespace, displayName);
    });
  });
}

// Show namespace details
async function showNamespaceDetails(namespace, displayName) {
  state.selectedNamespace = namespace;
  elements.selectedNamespaceName.textContent = displayName;
  elements.namespacesList.parentElement.style.display = 'none';
  elements.namespaceDetailsContainer.style.display = 'block';
  
  // Fetch and show sample vectors
  fetchNamespaceSamples(namespace);
}

// Fetch sample vectors from namespace
async function fetchNamespaceSamples(namespace) {
  setLoading('samples', true);
  showLoading(elements.namespaceSamples, "Loading samples...");
  
  try {
    const response = await fetch(`/pinecone-admin/api/namespace/${namespace}/sample`);
    if (!response.ok) throw new Error('Failed to fetch samples');
    
    const data = await response.json();
    renderSamples(data.samples);
  } catch (error) {
    console.error('Error fetching samples:', error);
    showError(elements.namespaceSamples, error.message);
  } finally {
    setLoading('samples', false);
  }
}

// Render sample vectors
function renderSamples(samples) {
  if (!samples || samples.length === 0) {
    showNoData(elements.namespaceSamples, "No samples available");
    return;
  }

  const sampleItems = samples.map(sample => {
    // Prepare metadata display (not showing vector values as they're too large)
    const metadata = sample.metadata || {};
    const metadataHtml = Object.entries(metadata)
      .filter(([key]) => key !== 'text' && !key.includes('vector'))
      .map(([key, value]) => `
        <div class="metadata-item">
          <span class="metadata-key">${key}:</span>
          <span class="metadata-value">${typeof value === 'object' ? JSON.stringify(value) : value}</span>
        </div>
      `)
      .join('');

    // Get text content or excerpt
    const text = metadata.text || '(No text available)';
    const textExcerpt = text.length > 300 ? 
      text.substring(0, 300) + '...' : 
      text;

    return `
      <div class="sample-item">
        <div class="sample-header">
          <div class="sample-id">ID: ${sample.id}</div>
          <div class="sample-score">Score: ${sample.score.toFixed(4)}</div>
        </div>
        <div class="sample-text">${textExcerpt}</div>
        <div class="sample-metadata">
          <div class="metadata-header">Metadata</div>
          ${metadataHtml || '<div class="no-data">No additional metadata</div>'}
        </div>
      </div>
    `;
  }).join('');

  elements.namespaceSamples.innerHTML = sampleItems;
}

// Clear namespace data (but preserve the namespace itself)
async function clearNamespace() {
  // Close the modal
  hideModal();
  
  if (!state.selectedNamespace) return;
  
  // Show loading state
  setLoading('clearOperation', true);
  
  try {
    const response = await fetch(`/pinecone-admin/api/namespace/${state.selectedNamespace}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) throw new Error('Failed to clear namespace');
    
    // Show success message
    showSuccess(elements.namespaceSamples, `
      Namespace data cleared successfully.
      <a href="/pinecone-admin">Refresh</a> to see updated stats.
    `);
    
    // Re-fetch samples (should be empty now)
    setTimeout(() => {
      fetchNamespaceSamples(state.selectedNamespace);
    }, 2000);
    
  } catch (error) {
    console.error('Error clearing namespace:', error);
    showError(elements.namespaceSamples, error.message);
  } finally {
    setLoading('clearOperation', false);
  }
}

// Show confirmation modal
function showConfirmationModal(title, message, onConfirm) {
  elements.modalTitle.textContent = title;
  elements.modalMessage.textContent = message;
  elements.confirmationModal.style.display = 'flex';
  
  // Set up confirm action
  elements.modalConfirm.onclick = onConfirm;
}

// Hide confirmation modal
function hideModal() {
  elements.confirmationModal.style.display = 'none';
}

// Event Listeners
elements.backButton.addEventListener('click', () => {
  elements.namespaceDetailsContainer.style.display = 'none';
  elements.namespacesList.parentElement.style.display = 'block';
  state.selectedNamespace = null;
});

elements.clearNamespaceBtn.addEventListener('click', () => {
  showConfirmationModal(
    'Clear Namespace Data',
    `Are you sure you want to delete all vectors in the "${state.selectedNamespace}" namespace? This action cannot be undone.`,
    clearNamespace
  );
});

elements.modalCancel.addEventListener('click', hideModal);

// Search form submission
elements.searchForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const namespace = elements.searchNamespaceSelect.value;
  const query = elements.searchQuery.value.trim();
  const limit = elements.searchLimit.value;
  
  if (!namespace) {
    alert('Please select a namespace');
    return;
  }
  
  if (!query) {
    alert('Please enter a search query');
    return;
  }
  
  searchNamespace(namespace, query, limit);
});

// Close modal when clicking outside
window.addEventListener('click', (e) => {
  if (e.target === elements.confirmationModal) {
    hideModal();
  }
});

// Initial data fetch on page load
document.addEventListener('DOMContentLoaded', () => {
  fetchPineconeStats();
});