// State for pagination and filtering
const state = {
  currentPage: 1,
  limit: 50,
  totalPages: 1,
  status: '',
  bot: '',
  sortBy: 'submitted_at',
  sortOrder: 'desc'
};

// DOM elements
const elements = {
  statusFilter: document.getElementById('statusFilter'),
  botFilter: document.getElementById('botFilter'),
  sortBy: document.getElementById('sortBy'),
  sortOrder: document.getElementById('sortOrder'),
  refreshButton: document.getElementById('refreshButton'),
  prevPage: document.getElementById('prevPage'),
  nextPage: document.getElementById('nextPage'),
  pageInfo: document.getElementById('pageInfo'),
  tableBody: document.getElementById('linksTableBody'),
  totalCount: document.getElementById('total-count').querySelector('.count'),
  completedCount: document.getElementById('completed-count').querySelector('.count'),
  pendingCount: document.getElementById('pending-count').querySelector('.count'),
  failedCount: document.getElementById('failed-count').querySelector('.count'),
  processingCount: document.getElementById('processing-count').querySelector('.count')
};

// Format date strings for display
function formatDate(dateString) {
  if (!dateString) return 'N/A';
  
  const date = new Date(dateString);
  const now = new Date();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  
  // Format time
  const time = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
  
  // Check if date is today
  if (date.toDateString() === now.toDateString()) {
    return `${time} • Today`;
  }
  
  // Check if date is yesterday
  if (date.toDateString() === yesterday.toDateString()) {
    return `${time} • Yesterday`;
  }
  
  // For dates within the current year, don't show year
  if (date.getFullYear() === now.getFullYear()) {
    return `${time} • ${date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })}`;
  }
  
  // For older dates, include the year
  return `${time} • ${date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })}`;
}

// Format URL for display (truncate if too long)
function formatUrl(url) {
  if (!url) return '';
  if (url.length <= 50) return url;
  return url.substring(0, 47) + '...';
}

// Get bot display name
function getBotDisplayName(botCode) {
  const names = {
    'sun-shield': 'Helia Sun Shield',
    'growth-ray': 'Helia Growth Ray',
    'sunbeam': 'Helia Sunbeam',
    'inner-dawn': 'Helia Inner Dawn'
  };
  return names[botCode] || botCode;
}

// Get status class for styling
function getStatusClass(status) {
  return `status-${status}`;
}

// Fetch data from API based on current filters and pagination
async function fetchData() {
  // Show loading state
  elements.tableBody.innerHTML = `
    <tr class="loading-row">
      <td colspan="6">Loading data...</td>
    </tr>
  `;
  
  try {
    const offset = (state.currentPage - 1) * state.limit;
    const queryParams = new URLSearchParams({
      status: state.status,
      bot: state.bot,
      sort_by: state.sortBy,
      sort_order: state.sortOrder,
      limit: state.limit,
      offset: offset
    });
    
    // Remove empty params
    for (const [key, value] of [...queryParams.entries()]) {
      if (!value) queryParams.delete(key);
    }
    
    const response = await fetch(`/api/stats/data?${queryParams}`);
    if (!response.ok) throw new Error('Failed to fetch data');
    
    const data = await response.json();
    updateTable(data.links);
    updateSummary(data.summary);
    updatePagination(data.total);
  } catch (error) {
    elements.tableBody.innerHTML = `
      <tr class="error-row">
        <td colspan="6">Error loading data: ${error.message}</td>
      </tr>
    `;
  }
}

// Update the table with link data
function updateTable(links) {
  if (!links || links.length === 0) {
    elements.tableBody.innerHTML = `
      <tr>
        <td colspan="6">No records found</td>
      </tr>
    `;
    return;
  }
  
  elements.tableBody.innerHTML = links.map(link => `
    <tr>
      <td>${formatDate(link.submitted_at)}</td>
      <td title="${link.link}">${formatUrl(link.link)}</td>
      <td>${link.type}</td>
      <td>${getBotDisplayName(link.bot)}</td>
      <td class="${getStatusClass(link.status)}">${link.status}</td>
      <td class="error-message" title="${link.error_message || ''}">${link.error_message || ''}</td>
    </tr>
  `).join('');
}

// Update summary cards with counts
function updateSummary(summary) {
  elements.totalCount.textContent = Object.values(summary).reduce((a, b) => a + b, 0) || 0;
  elements.completedCount.textContent = summary.completed || 0;
  elements.pendingCount.textContent = summary.pending || 0;
  elements.failedCount.textContent = summary.failed || 0;
  elements.processingCount.textContent = summary.processing || 0;
}

// Update pagination controls
function updatePagination(total) {
  state.totalPages = Math.ceil(total / state.limit);
  elements.pageInfo.textContent = `Page ${state.currentPage} of ${state.totalPages}`;
  elements.prevPage.disabled = state.currentPage <= 1;
  elements.nextPage.disabled = state.currentPage >= state.totalPages;
}

// Event handlers
elements.statusFilter.addEventListener('change', e => {
  state.status = e.target.value;
  state.currentPage = 1;
  fetchData();
});

elements.botFilter.addEventListener('change', e => {
  state.bot = e.target.value;
  state.currentPage = 1;
  fetchData();
});

elements.sortBy.addEventListener('change', e => {
  state.sortBy = e.target.value;
  fetchData();
});

elements.sortOrder.addEventListener('change', e => {
  state.sortOrder = e.target.value;
  fetchData();
});

elements.refreshButton.addEventListener('click', () => {
  fetchData();
});

elements.prevPage.addEventListener('click', () => {
  if (state.currentPage > 1) {
    state.currentPage--;
    fetchData();
  }
});

elements.nextPage.addEventListener('click', () => {
  if (state.currentPage < state.totalPages) {
    state.currentPage++;
    fetchData();
  }
});

// Auto-refresh every 30 seconds
let refreshInterval = setInterval(fetchData, 30000);

// Clear interval when page is hidden
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    clearInterval(refreshInterval);
  } else {
    refreshInterval = setInterval(fetchData, 30000);
  }
});

// Initial data load
document.addEventListener('DOMContentLoaded', () => {
  fetchData();
});