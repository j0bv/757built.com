/**
 * 757Built Dashboard
 * Main JavaScript file for dashboard functionality
 */

// Initialize dashboard when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

/**
 * Initialize the dashboard
 */
function initDashboard() {
    // Initialize components
    initTabSystem();
    initDropdownMenu();
    initTiles();
    initModals();
    initThemeSystem();
    
    // Set up global keyboard shortcuts
    initKeyboardShortcuts();
    
    // Update status items
    updateStatusBar();
    
    // Initialize event handlers
    setupEventHandlers();
}

/**
 * Initialize tab system
 */
function initTabSystem() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const newTabBtn = document.querySelector('.new-tab');
    
    // Tab click handler
    tabs.forEach(tab => {
        // Tab click
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                }
            });
        });
        
        // Close tab button
        const closeBtn = tab.querySelector('.close-tab');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // Don't close if it's the last tab
                if (tabs.length <= 1) return;
                
                const tabId = tab.getAttribute('data-tab');
                const tabContent = document.getElementById(tabId);
                
                // If closing active tab, activate another tab
                if (tab.classList.contains('active')) {
                    const nextTab = tab.nextElementSibling || tab.previousElementSibling;
                    if (nextTab && nextTab.classList.contains('tab')) {
                        nextTab.click();
                    }
                }
                
                // Remove tab and content
                tab.remove();
                if (tabContent) tabContent.remove();
            });
        }
    });
    
    // New tab button
    if (newTabBtn) {
        newTabBtn.addEventListener('click', () => {
            createNewTab();
        });
    }
}

/**
 * Create a new dashboard tab
 */
function createNewTab() {
    // Create unique ID for the new tab
    const tabId = `dashboard-${Date.now()}`;
    
    // Create tab element
    const tabsContainer = document.querySelector('.tabs');
    const newTab = document.createElement('div');
    newTab.className = 'tab';
    newTab.setAttribute('data-tab', tabId);
    newTab.innerHTML = `
        <i class="fas fa-th-large"></i>
        <span>New Dashboard</span>
        <button class="close-tab"><i class="fas fa-times"></i></button>
    `;
    
    // Insert before the new tab button
    const newTabBtn = document.querySelector('.new-tab');
    tabsContainer.insertBefore(newTab, newTabBtn);
    
    // Create tab content
    const tabContentsContainer = document.querySelector('.dashboard-content');
    const newTabContent = document.createElement('div');
    newTabContent.className = 'tab-content';
    newTabContent.id = tabId;
    newTabContent.innerHTML = `
        <div class="dashboard-grid"></div>
    `;
    tabContentsContainer.appendChild(newTabContent);
    
    // Initialize grid system for new tab
    const grid = newTabContent.querySelector('.dashboard-grid');
    new GridSystem(grid);
    
    // Setup event handlers
    const closeBtn = newTab.querySelector('.close-tab');
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        newTab.remove();
        newTabContent.remove();
        
        // Activate another tab
        document.querySelector('.tab').click();
    });
    
    // Click handler to activate the tab
    newTab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        newTab.classList.add('active');
        
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        newTabContent.classList.add('active');
    });
    
    // Activate the new tab
    newTab.click();
    
    // Show toast
    showToast('Created new dashboard tab');
}

/**
 * Initialize dropdown menu system
 */
function initDropdownMenu() {
    // Menu action handlers
    const menuActions = document.querySelectorAll('[data-action]');
    
    menuActions.forEach(action => {
        action.addEventListener('click', (e) => {
            e.preventDefault();
            const actionType = action.getAttribute('data-action');
            
            // Handle different actions
            switch(actionType) {
                case 'tile-marketplace':
                    toggleModal('tile-marketplace-modal', true);
                    break;
                case 'toggle-theme':
                    toggleDarkMode();
                    break;
                case 'fullscreen':
                    toggleFullscreen();
                    break;
                case 'show-grid':
                    toggleGridLines();
                    break;
                case 'new-dashboard':
                    createNewTab();
                    break;
                case 'add-globe':
                case 'add-map':
                case 'add-network':
                case 'add-barchart':
                case 'add-linechart':
                case 'add-piechart':
                case 'add-timeline':
                case 'add-terminal':
                case 'add-table':
                    addTileFromMenu(actionType.replace('add-', ''));
                    break;
                case 'open-documents':
                    openDocumentsTab();
                    break;
                default:
                    // Handle other actions or display message
                    console.log(`Action: ${actionType}`);
            }
        });
    });
    
    // Theme selection
    const themeOptions = document.querySelectorAll('[data-theme]');
    themeOptions.forEach(option => {
        option.addEventListener('click', (e) => {
            e.preventDefault();
            const theme = option.getAttribute('data-theme');
            setTheme(theme);
        });
    });
}

/**
 * Toggle grid lines for the dashboard
 */
function toggleGridLines() {
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (dashboardGrid) {
        dashboardGrid.classList.toggle('show-grid');
        
        const isShowing = dashboardGrid.classList.contains('show-grid');
        showToast(`Grid lines ${isShowing ? 'shown' : 'hidden'}`);
    }
}

/**
 * Initialize tile system
 */
function initTiles() {
    const tiles = document.querySelectorAll('.tile');
    
    tiles.forEach(tile => {
        // Tile controls
        initTileControls(tile);
    });
    
    // Tile marketplace handlers
    initTileMarketplace();
}

/**
 * Initialize tile controls (close, maximize, settings)
 */
function initTileControls(tile) {
    const controls = tile.querySelectorAll('.tile-control');
    
    controls.forEach(control => {
        control.addEventListener('click', () => {
            const action = control.getAttribute('data-action');
            const tileId = tile.getAttribute('data-tile-id');
            
            switch(action) {
                case 'close':
                    // Add animation class
                    tile.classList.add('removing');
                    
                    // Wait for animation to complete
                    setTimeout(() => {
                        // Dispatch event to the grid system
                        document.dispatchEvent(new CustomEvent('dashboard:removeTile', {
                            detail: { tileId: tileId }
                        }));
                        
                        // Remove the tile
                        tile.remove();
                    }, 300);
                    break;
                case 'maximize':
                    toggleTileMaximize(tile);
                    break;
                case 'settings':
                    showTileSettings(tileId);
                    break;
            }
        });
    });
    
    // Footer action buttons
    const actions = tile.querySelectorAll('.tile-action');
    actions.forEach(action => {
        action.addEventListener('click', () => {
            const actionType = action.getAttribute('data-action');
            
            switch(actionType) {
                case 'refresh':
                    refreshTile(tile);
                    break;
                case 'export':
                    exportTileData(tile);
                    break;
                case 'clear':
                    clearTile(tile);
                    break;
                case 'copy':
                    copyTileContent(tile);
                    break;
            }
        });
    });
}

/**
 * Toggle tile maximize state
 */
function toggleTileMaximize(tile) {
    tile.classList.toggle('maximized');
    
    const icon = tile.querySelector('[data-action="maximize"] i');
    if (icon) {
        if (tile.classList.contains('maximized')) {
            icon.classList.remove('fa-expand');
            icon.classList.add('fa-compress');
            
            // Store original position
            tile.setAttribute('data-original-position', tile.getAttribute('data-grid-position'));
            
            // Move the tile to a temporary full-screen overlay
            document.body.classList.add('has-maximized-tile');
            tile.style.position = 'fixed';
            tile.style.top = '50px';
            tile.style.left = '0';
            tile.style.width = '100%';
            tile.style.height = 'calc(100vh - 100px)';
            tile.style.zIndex = '1000';
        } else {
            icon.classList.remove('fa-compress');
            icon.classList.add('fa-expand');
            
            // Restore original position
            const originalPosition = tile.getAttribute('data-original-position');
            if (originalPosition) {
                // Restore grid position
                tile.setAttribute('data-grid-position', originalPosition);
                
                // Let the grid system handle positioning
                if (window.dashboardGridSystem) {
                    const position = window.dashboardGridSystem.parseGridPosition(tile);
                    window.dashboardGridSystem.updateTilePosition(tile, position);
                } else {
                    // Remove inline styles
                    tile.style.position = '';
                    tile.style.top = '';
                    tile.style.left = '';
                    tile.style.width = '';
                    tile.style.height = '';
                    tile.style.zIndex = '';
                }
            }
            
            document.body.classList.remove('has-maximized-tile');
        }
    }
    
    // Trigger resize event for visualizations
    window.dispatchEvent(new Event('resize'));
}

/**
 * Refresh tile content
 */
function refreshTile(tile) {
    const tileId = tile.getAttribute('data-tile-id');
    const content = tile.querySelector('.tile-content');
    
    // Add loading indicator
    content.classList.add('loading');
    
    // Get tile type
    const tileType = tile.getAttribute('data-tile-type') || tileId.replace(/[0-9]+$/, '');
    
    // Simulate refresh - would be replaced with actual data fetching
    setTimeout(() => {
        content.classList.remove('loading');
        
        // Update tile status
        const statusText = tile.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
        }
        
        // Trigger visualization update
        updateVisualization(tile, tileType);
    }, 800);
}

/**
 * Update the visualization in a tile
 */
function updateVisualization(tile, tileType) {
    const vizContainer = tile.querySelector('.visualization-container');
    if (!vizContainer) return;
    
    const vizId = vizContainer.id;
    
    // Update based on tile type
    switch(tileType) {
        case 'barchart':
            if (window.updateBarChart) {
                window.updateBarChart(vizId, generateRandomBarChartData());
            }
            break;
        case 'linechart':
            if (window.updateLineChart) {
                window.updateLineChart(vizId);
            }
            break;
        case 'piechart':
            if (window.updatePieChart) {
                window.updatePieChart(vizId, generateRandomPieChartData());
            }
            break;
        case 'globe':
            if (window.updateGlobe) {
                window.updateGlobe(vizId);
            }
            break;
        case 'network':
            if (window.updateNetwork) {
                window.updateNetwork(vizId);
            }
            break;
        case 'terminal':
            // For terminals, just print a message
            const terminalId = vizId.replace('-visualization', '');
            const terminal = window[`terminal_${terminalId}`];
            if (terminal) {
                terminal.print('Terminal refreshed', 'info');
            }
            break;
    }
}

/**
 * Generate random data for bar charts
 */
function generateRandomBarChartData() {
    const categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E'];
    return categories.map(category => ({
        category: category,
        value: Math.floor(Math.random() * 500) + 100
    }));
}

/**
 * Generate random data for pie charts
 */
function generateRandomPieChartData() {
    const categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E'];
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
    
    return categories.map((category, i) => ({
        label: category,
        value: Math.floor(Math.random() * 50) + 10,
        color: colors[i]
    }));
}

/**
 * Clear tile content (mainly for terminal)
 */
function clearTile(tile) {
    const tileId = tile.getAttribute('data-tile-id');
    const tileType = tile.getAttribute('data-tile-type') || tileId.replace(/[0-9]+$/, '');
    
    if (tileType === 'terminal') {
        const terminal = window[`terminal_${tileId}`];
        if (terminal) {
            terminal.clear();
        }
    }
}

/**
 * Copy tile content to clipboard
 */
function copyTileContent(tile) {
    const tileId = tile.getAttribute('data-tile-id');
    const tileType = tile.getAttribute('data-tile-type') || tileId.replace(/[0-9]+$/, '');
    
    if (tileType === 'terminal') {
        const terminal = window[`terminal_${tileId}`];
        if (terminal && terminal.outputElement) {
            const text = terminal.outputElement.innerText;
            navigator.clipboard.writeText(text)
                .then(() => showToast('Terminal content copied to clipboard'))
                .catch(err => console.error('Could not copy text: ', err));
        }
    } else {
        // For other tiles, attempt to get SVG or canvas content
        const vizContainer = tile.querySelector('.visualization-container');
        if (vizContainer) {
            const svg = vizContainer.querySelector('svg');
            if (svg) {
                const svgData = new XMLSerializer().serializeToString(svg);
                navigator.clipboard.writeText(svgData)
                    .then(() => showToast('Visualization SVG copied to clipboard'))
                    .catch(err => console.error('Could not copy SVG: ', err));
            } else {
                showToast('No content available to copy');
            }
        }
    }
}

/**
 * Export tile data
 */
function exportTileData(tile) {
    const tileId = tile.getAttribute('data-tile-id');
    const title = tile.querySelector('.tile-title span').textContent;
    
    // For demonstration, simulate export of SVG/PNG
    const vizContainer = tile.querySelector('.visualization-container');
    if (vizContainer) {
        const svg = vizContainer.querySelector('svg');
        if (svg) {
            // In a real app, this would create a download
            showToast(`Exporting ${title} as SVG/PNG...`);
            
            // Simulate processing time
            setTimeout(() => {
                showToast(`${title} exported successfully!`);
            }, 1000);
        } else {
            showToast('No visualization to export');
        }
    }
}

/**
 * Show tile settings modal
 */
function showTileSettings(tileId) {
    // In a real app, this would open a settings modal
    // For demonstration, just show a toast
    showToast(`Settings for tile ${tileId}`);
}

/**
 * Initialize tile marketplace system
 */
function initTileMarketplace() {
    const addButtons = document.querySelectorAll('.add-tile-btn');
    const categoryButtons = document.querySelectorAll('.category-btn');
    const graphSearch = document.getElementById('graph-search');
    
    // Add tile buttons
    addButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tileType = button.closest('.tile-card').getAttribute('data-tile-type');
            addTileFromLibrary(tileType);
            toggleModal('tile-marketplace-modal', false);
        });
    });
    
    // Category filter buttons
    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active category
            categoryButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            const category = button.getAttribute('data-category');
            filterMarketplaceTiles(category);
        });
    });
    
    // Graph search functionality
    if (graphSearch) {
        graphSearch.addEventListener('input', (e) => {
            const searchText = e.target.value.toLowerCase();
            filterGraphLibrary(searchText);
        });
    }
    
    // Create graph button
    const createGraphBtn = document.querySelector('.create-graph-btn');
    if (createGraphBtn) {
        createGraphBtn.addEventListener('click', () => {
            // In a real app, this would create a new visualization
            // based on selected options
            
            // For demonstration, create a random chart
            const types = ['barchart', 'linechart', 'piechart', 'network', 'globe'];
            const randomType = types[Math.floor(Math.random() * types.length)];
            
            addTileFromLibrary(randomType);
            toggleModal('tile-marketplace-modal', false);
        });
    }
}

/**
 * Filter Graph Library items based on search text using fuzzy matching
 */
function filterGraphLibrary(searchText) {
    const tileCards = document.querySelectorAll('.tile-card');
    const searchLower = searchText.toLowerCase();

    if (!searchLower) {
        tileCards.forEach(card => card.style.display = '');
        return;
    }

    const results = [];
    tileCards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const description = card.querySelector('p').textContent.toLowerCase();
        const fullText = `${title} ${description}`;
        const score = calculateFuzzyScore(fullText, searchLower);

        if (score > 0) {
            results.push({ card, score });
        }
    });

    // Sort results by score (descending)
    results.sort((a, b) => b.score - a.score);

    // Show/hide cards based on results
    tileCards.forEach(card => card.style.display = 'none');
    results.forEach(result => result.card.style.display = '');
}

/**
 * Calculate a simple fuzzy match score.
 * Higher score means better match.
 * @param {string} text - The text to search within
 * @param {string} pattern - The search pattern
 * @returns {number} - The match score
 */
function calculateFuzzyScore(text, pattern) {
    let score = 0;
    let patternIndex = 0;
    let textIndex = 0;
    let consecutiveMatches = 0;

    // Score for starting match
    if (text.startsWith(pattern)) {
        score += 100; // High score for exact start match
    }

    while (textIndex < text.length && patternIndex < pattern.length) {
        if (text[textIndex] === pattern[patternIndex]) {
            score += 10; // Base score for match
            score += consecutiveMatches * 5; // Bonus for consecutive matches
            patternIndex++;
            consecutiveMatches++;
        } else {
            score -= 1; // Penalty for skipping text character
            consecutiveMatches = 0;
        }
        textIndex++;
    }

    // Bonus if pattern is fully matched
    if (patternIndex === pattern.length) {
        score += 50;
    }
    
    // Penalty if pattern not fully matched
    else {
        score -= (pattern.length - patternIndex) * 10;
    }
    
    // Higher score for shorter text (more relevant match)
    score -= text.length * 0.1;

    return Math.max(0, score); // Ensure score is not negative
}

/**
 * Filter marketplace tiles by category
 */
function filterMarketplaceTiles(category) {
    const tiles = document.querySelectorAll('.tile-card');
    
    tiles.forEach(tile => {
        const tileType = tile.getAttribute('data-tile-type');
        
        if (category === 'all') {
            tile.style.display = '';
        } else {
            // Match category to tile type
            let showTile = false;
            
            switch(category) {
                case 'maps':
                    showTile = ['globe', 'map', 'heatmap'].includes(tileType);
                    break;
                case 'charts':
                    showTile = ['barchart', 'linechart', 'piechart', 'timeline'].includes(tileType);
                    break;
                case 'tables':
                    showTile = ['datatable'].includes(tileType);
                    break;
                case 'tools':
                    showTile = ['terminal'].includes(tileType);
                    break;
            }
            
            tile.style.display = showTile ? '' : 'none';
        }
    });
}

/**
 * Add a new tile from the menu
 */
function addTileFromMenu(tileType) {
    addTileToGrid(tileType);
    showToast(`Added new ${tileType} tile`);
}

/**
 * Add a new tile from the library
 */
function addTileFromLibrary(tileType) {
    addTileToGrid(tileType);
    showToast(`Added new ${tileType} tile from library`);
}

/**
 * Add a new tile to the grid
 */
function addTileToGrid(tileType) {
    // Find active dashboard grid
    const activeContent = document.querySelector('.tab-content.active');
    if (!activeContent) return;
    
    const grid = activeContent.querySelector('.dashboard-grid');
    if (!grid) return;
    
    // Generate tile ID
    const tileId = `${tileType}${Date.now()}`;
    
    // Get tile icon and title
    let icon = 'fas fa-chart-bar';
    let title = 'New Visualization';
    
    switch(tileType) {
        case 'globe':
            icon = 'fas fa-globe';
            title = 'Global Distribution';
            break;
        case 'network':
            icon = 'fas fa-project-diagram';
            title = 'Network Graph';
            break;
        case 'map':
            icon = 'fas fa-map';
            title = '2D Map';
            break;
        case 'barchart':
            icon = 'fas fa-chart-bar';
            title = 'Bar Chart';
            break;
        case 'linechart':
            icon = 'fas fa-chart-line';
            title = 'Line Chart';
            break;
        case 'piechart':
            icon = 'fas fa-chart-pie';
            title = 'Pie Chart';
            break;
        case 'timeline':
            icon = 'fas fa-stream';
            title = 'Timeline';
            break;
        case 'terminal':
            icon = 'fas fa-terminal';
            title = 'Command Terminal';
            break;
        case 'datatable':
            icon = 'fas fa-table';
            title = 'Data Table';
            break;
        case 'heatmap':
            icon = 'fas fa-fire';
            title = 'Heat Map';
            break;
    }
    
    // Create tile HTML
    const tileElement = document.createElement('div');
    tileElement.className = 'tile adding';
    tileElement.setAttribute('data-tile-id', tileId);
    tileElement.setAttribute('data-tile-type', tileType);
    tileElement.innerHTML = `
        <div class="tile-header">
            <div class="tile-title">
                <i class="${icon}"></i>
                <span>${title}</span>
            </div>
            <div class="tile-controls">
                <button class="tile-control" data-action="maximize"><i class="fas fa-expand"></i></button>
                <button class="tile-control" data-action="settings"><i class="fas fa-cog"></i></button>
                <button class="tile-control" data-action="close"><i class="fas fa-times"></i></button>
            </div>
        </div>
        <div class="tile-content">
            <div class="${tileType === 'terminal' ? 'terminal-container' : 'visualization-container'}" id="${tileId}${tileType === 'terminal' ? '' : '-visualization'}"></div>
        </div>
        <div class="tile-footer">
            <div class="tile-status">
                <span class="status-text">Loading...</span>
            </div>
            <div class="tile-actions">
                <button class="tile-action" data-action="refresh"><i class="fas fa-sync-alt"></i></button>
                <button class="tile-action" data-action="export"><i class="fas fa-download"></i></button>
            </div>
        </div>
        <div class="resize-handle"></div>
    `;
    
    // Add to grid
    grid.appendChild(tileElement);
    
    // Initialize tile controls
    initTileControls(tileElement);
    
    // Notify grid system about the new tile
    document.dispatchEvent(new CustomEvent('dashboard:addTile', {
        detail: { tileElement: tileElement }
    }));
    
    // Initialize visualization
    initializeTileContent(tileElement, tileType);
    
    // Remove animation class after animation completes
    setTimeout(() => {
        tileElement.classList.remove('adding');
    }, 300);
}

/**
 * Initialize content in a newly created tile
 */
function initializeTileContent(tileElement, tileType) {
    const tileId = tileElement.getAttribute('data-tile-id');
    
    // Different initialization based on tile type
    switch(tileType) {
        case 'barchart':
            // In a real implementation, this would fetch data and initialize
            if (window.updateBarChart) {
                setTimeout(() => {
                    window.updateBarChart(`${tileId}-visualization`, generateRandomBarChartData());
                    updateTileStatus(tileElement, '5 categories');
                }, 500);
            }
            break;
            
        case 'linechart':
            if (window.updateLineChart) {
                setTimeout(() => {
                    window.updateLineChart(`${tileId}-visualization`);
                    updateTileStatus(tileElement, '30 data points');
                }, 500);
            }
            break;
            
        case 'piechart':
            if (window.updatePieChart) {
                setTimeout(() => {
                    window.updatePieChart(`${tileId}-visualization`, generateRandomPieChartData());
                    updateTileStatus(tileElement, '5 categories');
                }, 500);
            }
            break;
            
        case 'terminal':
            setTimeout(() => {
                window.initTerminal(tileId);
                updateTileStatus(tileElement, 'Ready');
            }, 300);
            break;
            
        default:
            // For unimplemented visualizations
            const container = tileElement.querySelector('.visualization-container');
            if (container) {
                container.innerHTML = `
                    <div style="height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-muted);">
                        <i class="${getIconForTileType(tileType)}" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                        <div>${title} Visualization</div>
                        <div style="font-size: 0.9rem; margin-top: 0.5rem;">Implementation pending</div>
                    </div>
                `;
                updateTileStatus(tileElement, 'Placeholder');
            }
    }
}

/**
 * Get icon class for a tile type
 */
function getIconForTileType(tileType) {
    switch(tileType) {
        case 'globe': return 'fas fa-globe';
        case 'network': return 'fas fa-project-diagram';
        case 'map': return 'fas fa-map';
        case 'barchart': return 'fas fa-chart-bar';
        case 'linechart': return 'fas fa-chart-line';
        case 'piechart': return 'fas fa-chart-pie';
        case 'timeline': return 'fas fa-stream';
        case 'terminal': return 'fas fa-terminal';
        case 'datatable': return 'fas fa-table';
        case 'heatmap': return 'fas fa-fire';
        default: return 'fas fa-chart-line';
    }
}

/**
 * Update the status text of a tile
 */
function updateTileStatus(tileElement, statusText) {
    const status = tileElement.querySelector('.status-text');
    if (status) {
        status.textContent = statusText;
    }
}

/**
 * Show a toast notification
 */
function showToast(message) {
    // Remove existing toast
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `
        <i class="fas fa-info-circle"></i>
        <span>${message}</span>
    `;
    
    // Style the toast
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = 'rgba(52, 152, 219, 0.9)';
    toast.style.color = 'white';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '4px';
    toast.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
    toast.style.zIndex = '1000';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.gap = '10px';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    
    // Add to DOM
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        
        // Remove from DOM after animation
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

/**
 * Initialize modal functionality
 */
function initModals() {
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(modal => {
        // Close button
        const closeBtn = modal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                toggleModal(modal.id, false);
            });
        }
        
        // Cancel button
        const cancelBtn = modal.querySelector('.cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                toggleModal(modal.id, false);
            });
        }
        
        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                toggleModal(modal.id, false);
            }
        });
    });
}

/**
 * Toggle modal visibility
 */
function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    if (show) {
        modal.classList.add('active');
    } else {
        modal.classList.remove('active');
    }
}

/**
 * Initialize theme system
 */
function initThemeSystem() {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('dashboardTheme') || 'default';
    setTheme(savedTheme);
    
    // Initialize theme toggle
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleDarkMode);
    }
}

/**
 * Set theme for dashboard
 */
function setTheme(theme) {
    // Remove existing theme classes
    document.body.classList.remove('terminal-theme', 'hologram-theme', 'dark-theme', 'light-theme');
    
    // Add new theme class
    if (theme !== 'default') {
        document.body.classList.add(`${theme}-theme`);
    }
    
    // Save preference
    localStorage.setItem('dashboardTheme', theme);
    
    // Update theme indicator
    const themeIndicator = document.querySelector('.theme-indicator');
    if (themeIndicator) {
        const icon = themeIndicator.querySelector('i');
        const text = themeIndicator.querySelector('span') || themeIndicator;
        
        switch(theme) {
            case 'terminal':
                icon.className = 'fas fa-terminal';
                text.textContent = 'Terminal';
                break;
            case 'hologram':
                icon.className = 'fas fa-atom';
                text.textContent = 'Hologram';
                break;
            case 'dark':
                icon.className = 'fas fa-moon';
                text.textContent = 'Dark';
                break;
            case 'light':
                icon.className = 'fas fa-sun';
                text.textContent = 'Light';
                break;
            default:
                icon.className = 'fas fa-palette';
                text.textContent = 'Default';
        }
    }
}

/**
 * Toggle dark/light mode
 */
function toggleDarkMode() {
    const isDark = document.body.classList.contains('dark-theme');
    setTheme(isDark ? 'light' : 'dark');
}

/**
 * Initialize keyboard shortcuts
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Check if we should ignore this (input fields, etc.)
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || 
            e.target.isContentEditable) {
            return;
        }
        
        // Check for modifier keys
        const hasCtrl = e.ctrlKey || e.metaKey; // metaKey for Mac
        
        // Handle shortcuts
        if (hasCtrl) {
            switch(e.key.toLowerCase()) {
                case 'n': // Ctrl+N: New Dashboard
                    e.preventDefault();
                    createNewTab();
                    break;
                case 'o': // Ctrl+O: Open Dashboard
                    e.preventDefault();
                    document.querySelector('[data-action="open-dashboard"]')?.click();
                    break;
                case 's': // Ctrl+S: Save Dashboard
                    e.preventDefault();
                    document.querySelector('[data-action="save-dashboard"]')?.click();
                    break;
                case 'c': // Ctrl+C: Copy Tile
                    if (!e.shiftKey && !window.getSelection().toString()) {
                        e.preventDefault();
                        document.querySelector('[data-action="copy-tile"]')?.click();
                    }
                    break;
                case 'v': // Ctrl+V: Paste Tile
                    e.preventDefault();
                    document.querySelector('[data-action="paste-tile"]')?.click();
                    break;
                case 'z': // Ctrl+Z: Undo
                    e.preventDefault();
                    document.querySelector('[data-action="undo"]')?.click();
                    break;
                case 'y': // Ctrl+Y: Redo
                    e.preventDefault();
                    document.querySelector('[data-action="redo"]')?.click();
                    break;
                case '0': // Ctrl+0: Reset Zoom
                    e.preventDefault();
                    document.querySelector('[data-action="reset-zoom"]')?.click();
                    break;
                case '=': // Ctrl++: Zoom In
                case '+':
                    e.preventDefault();
                    document.querySelector('[data-action="zoom-in"]')?.click();
                    break;
                case '-': // Ctrl+-: Zoom Out
                    e.preventDefault();
                    document.querySelector('[data-action="zoom-out"]')?.click();
                    break;
            }
        } else if (e.key === 'F11') { // F11: Fullscreen
            e.preventDefault();
            toggleFullscreen();
        } else if (e.key === 'Delete') { // Delete: Delete selected tile
            e.preventDefault();
            document.querySelector('[data-action="delete-tile"]')?.click();
        }
    });
}

/**
 * Setup global event handlers
 */
function setupEventHandlers() {
    // Listen for terminal graph creation
    document.addEventListener('terminal:createGraph', (e) => {
        if (e.detail) {
            addTileFromLibrary(e.detail.type);
        }
    });
    
    // Listen for window resize
    window.addEventListener('resize', () => {
        // Update any dynamic elements that need resize handling
        // This is in addition to the grid system's own resize handling
    });
}

/**
 * Toggle fullscreen mode
 */
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error(`Error attempting to enable fullscreen: ${err.message}`);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

/**
 * Update status bar information
 */
function updateStatusBar() {
    const lastUpdated = document.getElementById('last-updated');
    if (lastUpdated) {
        const now = new Date();
        lastUpdated.textContent = now.toLocaleString();
    }
} 