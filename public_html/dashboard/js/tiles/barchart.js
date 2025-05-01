/**
 * Bar Chart Visualization
 * Using D3.js to create interactive bar charts for data visualization
 */

// Initialize bar charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const barChartContainers = document.querySelectorAll('#barchart-visualization');
    barChartContainers.forEach(container => {
        initBarChart(container.id);
    });
});

/**
 * Initialize a bar chart visualization
 * @param {string} containerId - The ID of the container element
 */
function initBarChart(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Create initial loading state
    container.innerHTML = `
        <div class="chart-loading">
            <div class="spinner"></div>
            <div>Loading chart data...</div>
        </div>
    `;
    
    // Style loading indicator
    const loading = container.querySelector('.chart-loading');
    loading.style.display = 'flex';
    loading.style.flexDirection = 'column';
    loading.style.alignItems = 'center';
    loading.style.justifyContent = 'center';
    loading.style.height = '100%';
    loading.style.color = '#95a5a6';
    loading.style.fontSize = '14px';
    
    const spinner = container.querySelector('.spinner');
    spinner.style.border = '4px solid rgba(0, 0, 0, 0.1)';
    spinner.style.borderTop = '4px solid #3498db';
    spinner.style.borderRadius = '50%';
    spinner.style.width = '40px';
    spinner.style.height = '40px';
    spinner.style.animation = 'spin 1s linear infinite';
    spinner.style.marginBottom = '10px';
    
    // Add spinner animation
    const style = document.createElement('style');
    style.innerHTML = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    // Load data with a slight delay to show loading animation
    setTimeout(() => {
        loadChartData(containerId)
            .then(data => {
                createBarChart(container, data);
                updateTileStatus(containerId, data);
            })
            .catch(error => {
                console.error('Error loading chart data:', error);
                showErrorMessage(containerId, 'Failed to load chart data');
            });
    }, 800);
    
    // Handle window resize
    window.addEventListener('resize', () => {
        // Only update if container is visible
        if (container.offsetParent !== null) {
            // Get current data from container
            const currentData = container._data;
            if (currentData) {
                createBarChart(container, currentData);
            }
        }
    });
}

/**
 * Load chart data
 * @param {string} containerId - The ID of the container element
 * @returns {Promise} - Promise resolving to the chart data
 */
function loadChartData(containerId) {
    // For demonstration, generate sample data
    return new Promise((resolve) => {
        // Sample data
        const data = [
            { category: 'Category A', value: 420 },
            { category: 'Category B', value: 310 },
            { category: 'Category C', value: 580 },
            { category: 'Category D', value: 290 },
            { category: 'Category E', value: 490 },
            { category: 'Category F', value: 350 },
            { category: 'Category G', value: 220 }
        ];
        
        // Simulate network delay
        setTimeout(() => {
            resolve(data);
        }, 500);
    });
}

/**
 * Create bar chart visualization
 * @param {HTMLElement} container - The container element
 * @param {Array} data - Chart data array
 */
function createBarChart(container, data) {
    // Clear container
    container.innerHTML = '';
    
    // Store data in container for resize events
    container._data = data;
    
    // Calculate chart dimensions
    const margin = { top: 40, right: 30, bottom: 90, left: 60 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = container.clientHeight - margin.top - margin.bottom;
    
    // Create SVG element
    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Create scales
    const x = d3.scaleBand()
        .range([0, width])
        .domain(data.map(d => d.category))
        .padding(0.3);
    
    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value) * 1.1]) // Add 10% padding at top
        .range([height, 0]);
    
    // Add X axis
    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll('text')
        .attr('transform', 'translate(-10,0)rotate(-45)')
        .style('text-anchor', 'end')
        .style('font-size', '12px');
    
    // Add Y axis
    svg.append('g')
        .call(d3.axisLeft(y))
        .selectAll('text')
        .style('font-size', '12px');
    
    // Add Y axis label
    svg.append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', -margin.left + 15)
        .attr('x', -(height / 2))
        .attr('text-anchor', 'middle')
        .style('font-size', '14px')
        .text('Value');
    
    // Add chart title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', -margin.top / 2)
        .attr('text-anchor', 'middle')
        .style('font-size', '16px')
        .style('font-weight', 'bold')
        .text('Data Distribution by Category');
    
    // Create color scale
    const colorScale = d3.scaleOrdinal()
        .domain(data.map(d => d.category))
        .range(['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e']);
    
    // Add tooltip
    const tooltip = d3.select(container)
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background-color', 'rgba(0, 0, 0, 0.8)')
        .style('color', 'white')
        .style('border-radius', '4px')
        .style('padding', '8px')
        .style('font-size', '12px')
        .style('pointer-events', 'none')
        .style('z-index', 100);
    
    // Add bars
    svg.selectAll('rect')
        .data(data)
        .enter()
        .append('rect')
        .attr('x', d => x(d.category))
        .attr('y', height) // Start at bottom for animation
        .attr('width', x.bandwidth())
        .attr('height', 0) // Start with height 0 for animation
        .attr('fill', d => colorScale(d.category))
        .attr('rx', 3) // Rounded corners
        .attr('ry', 3)
        // Add interaction
        .on('mouseover', function(event, d) {
            // Highlight bar
            d3.select(this)
                .attr('opacity', 0.8)
                .attr('stroke', '#333')
                .attr('stroke-width', 2);
            
            // Show tooltip
            tooltip.transition()
                .duration(200)
                .style('opacity', 0.9);
            
            tooltip.html(`
                <strong>${d.category}</strong><br>
                Value: ${d.value}
            `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
            
            // Show value label
            svg.append('text')
                .attr('class', 'value-label')
                .attr('x', x(d.category) + x.bandwidth() / 2)
                .attr('y', y(d.value) - 5)
                .attr('text-anchor', 'middle')
                .text(d.value)
                .style('font-size', '12px')
                .style('font-weight', 'bold');
        })
        .on('mouseout', function() {
            // Remove highlight
            d3.select(this)
                .attr('opacity', 1)
                .attr('stroke', 'none')
                .attr('stroke-width', 0);
            
            // Hide tooltip
            tooltip.transition()
                .duration(500)
                .style('opacity', 0);
            
            // Remove value label
            svg.selectAll('.value-label').remove();
        })
        // Animate bars
        .transition()
        .duration(800)
        .delay((d, i) => i * 100)
        .attr('y', d => y(d.value))
        .attr('height', d => height - y(d.value));
    
    // Add grid lines
    svg.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(y)
            .tickSize(-width)
            .tickFormat('')
        )
        .style('stroke-dasharray', '3,3')
        .style('stroke-opacity', 0.2)
        .selectAll('line')
        .style('stroke', '#999');
    
    // Add data value labels
    svg.selectAll('.value-text')
        .data(data)
        .enter()
        .append('text')
        .attr('class', 'value-text')
        .attr('x', d => x(d.category) + x.bandwidth() / 2)
        .attr('y', d => y(d.value) - 5)
        .attr('opacity', 0) // Start invisible for animation
        .attr('text-anchor', 'middle')
        .style('font-size', '11px')
        .text(d => d.value)
        // Animate labels
        .transition()
        .duration(800)
        .delay((d, i) => 800 + i * 100)
        .attr('opacity', 1);
    
    // Add a legend
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${width - 150}, ${height + 40})`);
    
    legend.selectAll('rect')
        .data(data.slice(0, 5)) // Show only first 5 for space
        .enter()
        .append('rect')
        .attr('x', 0)
        .attr('y', (d, i) => i * 20)
        .attr('width', 10)
        .attr('height', 10)
        .attr('fill', d => colorScale(d.category));
    
    legend.selectAll('text')
        .data(data.slice(0, 5)) // Show only first 5 for space
        .enter()
        .append('text')
        .attr('x', 15)
        .attr('y', (d, i) => i * 20 + 8)
        .style('font-size', '10px')
        .text(d => d.category);
}

/**
 * Update tile status with data information
 * @param {string} containerId - The ID of the container element
 * @param {Array} data - The chart data
 */
function updateTileStatus(containerId, data) {
    // Find the parent tile
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const tile = container.closest('.tile');
    if (!tile) return;
    
    // Update status text
    const statusText = tile.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = `${data.length} categories`;
    }
}

/**
 * Show error message in the container
 * @param {string} containerId - The ID of the container element
 * @param {string} message - The error message
 */
function showErrorMessage(containerId, message) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    // Add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #e74c3c; margin-bottom: 1rem;"></i>
        <p style="text-align: center;">${message}</p>
    `;
    
    // Style error message
    errorDiv.style.display = 'flex';
    errorDiv.style.flexDirection = 'column';
    errorDiv.style.alignItems = 'center';
    errorDiv.style.justifyContent = 'center';
    errorDiv.style.height = '100%';
    errorDiv.style.color = '#e74c3c';
    errorDiv.style.padding = '20px';
    
    container.appendChild(errorDiv);
    
    // Update status if in a tile
    const tile = container.closest('.tile');
    if (tile) {
        const statusText = tile.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = 'Error loading data';
        }
    }
}

/**
 * External function to update chart with new data
 * @param {string} containerId - The ID of the container element
 * @param {Array} data - New chart data
 */
function updateBarChart(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    createBarChart(container, data);
    updateTileStatus(containerId, data);
}

// Make update function available globally
window.updateBarChart = updateBarChart; 