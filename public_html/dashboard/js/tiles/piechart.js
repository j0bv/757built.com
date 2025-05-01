/**
 * Pie Chart Visualization
 * Using D3.js to create interactive pie charts for categorical data
 */

// Initialize pie charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const pieChartContainers = document.querySelectorAll('[id^="piechart"][id$="-visualization"]');
    pieChartContainers.forEach(container => {
        initPieChart(container.id);
    });
});

/**
 * Initialize a pie chart visualization
 * @param {string} containerId - The ID of the container element
 */
function initPieChart(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Display loading state
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
    if (!document.querySelector('style#pie-spinner')) {
        const style = document.createElement('style');
        style.id = 'pie-spinner';
        style.innerHTML = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Load sample data with delay to show loading state
    setTimeout(() => {
        const data = [
            { label: 'Category A', value: 30, color: '#FF6384' },
            { label: 'Category B', value: 25, color: '#36A2EB' },
            { label: 'Category C', value: 15, color: '#FFCE56' },
            { label: 'Category D', value: 20, color: '#4BC0C0' },
            { label: 'Category E', value: 10, color: '#9966FF' }
        ];
        
        createPieChart(container, data);
        updateTileStatus(containerId, data);
    }, 800);
    
    // Handle window resize
    window.addEventListener('resize', () => {
        // Only update if container is visible
        if (container.offsetParent !== null) {
            // Get current data from container
            const currentData = container._data;
            if (currentData) {
                createPieChart(container, currentData);
            }
        }
    });
}

/**
 * Create a responsive pie chart using D3.js
 * @param {HTMLElement} container - The container element
 * @param {Array} data - The data to visualize
 */
function createPieChart(container, data) {
    // Clear previous chart if any
    container.innerHTML = '';
    
    // Store data in container for resize events
    container._data = data;
    
    // Get container dimensions
    const containerRect = container.getBoundingClientRect();
    const width = containerRect.width;
    const height = containerRect.height;
    const radius = Math.min(width, height) / 2 * 0.8; // 80% of half the smallest dimension
    
    // Create SVG
    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .append('g')
        .attr('transform', `translate(${width / 2}, ${height / 2})`);
    
    // Create a color scale
    const color = d3.scaleOrdinal()
        .domain(data.map(d => d.label))
        .range(data.map(d => d.color || d3.schemeCategory10[0]));
    
    // Compute the position of each group on the pie
    const pie = d3.pie()
        .sort(null) // Do not sort by size
        .value(d => d.value);
    
    const dataReady = pie(data);
    
    // Inner and outer radius values to create a donut chart effect
    const innerRadius = radius * 0.5;
    const outerRadius = radius;
    
    // Build the pie chart
    const arc = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius);
    
    // For hover effect, slightly larger outer radius
    const arcHover = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius * 1.05);
    
    // Add background circle
    svg.append('circle')
        .attr('cx', 0)
        .attr('cy', 0)
        .attr('r', outerRadius)
        .attr('fill', 'rgba(0, 0, 0, 0.2)');
    
    // Add tooltip
    const tooltip = d3.select(container)
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('position', 'absolute')
        .style('visibility', 'hidden')
        .style('background-color', 'rgba(0,0,0,0.8)')
        .style('color', 'white')
        .style('padding', '8px 12px')
        .style('border-radius', '4px')
        .style('font-size', '0.8rem')
        .style('pointer-events', 'none')
        .style('z-index', '10')
        .style('text-align', 'center')
        .style('min-width', '120px');
    
    // Add the arcs
    const paths = svg.selectAll('path')
        .data(dataReady)
        .enter()
        .append('path')
        .attr('d', arc)
        .attr('fill', d => color(d.data.label))
        .attr('stroke', 'rgba(255, 255, 255, 0.5)')
        .attr('stroke-width', 1)
        .style('opacity', 0.9)
        .each(function(d) { this._current = d; }); // Store the initial angles for transitions
    
    // Add hover effects
    paths
        .on('mouseover', function(event, d) {
            // Change path
            d3.select(this)
                .transition()
                .duration(200)
                .attr('d', arcHover)
                .style('opacity', 1)
                .attr('stroke-width', 2);
            
            // Calculate percentage
            const total = d3.sum(data, item => item.value);
            const percentage = ((d.data.value / total) * 100).toFixed(1);
            
            // Show tooltip
            tooltip
                .style('visibility', 'visible')
                .html(`<strong>${d.data.label}</strong><br>
                       Value: ${d.data.value}<br>
                       <span style="font-size: 1.1em; font-weight: bold;">${percentage}%</span>`)
                .style('left', `${event.pageX - container.getBoundingClientRect().left - 60}px`)
                .style('top', `${event.pageY - container.getBoundingClientRect().top - 70}px`);
            
            // Highlight label
            svg.selectAll('.label-text')
                .filter(textData => textData.data.label === d.data.label)
                .style('font-weight', 'bold')
                .style('font-size', '10px');
        })
        .on('mousemove', function(event) {
            // Update tooltip position
            tooltip
                .style('left', `${event.pageX - container.getBoundingClientRect().left - 60}px`)
                .style('top', `${event.pageY - container.getBoundingClientRect().top - 70}px`);
        })
        .on('mouseout', function(event, d) {
            // Restore path
            d3.select(this)
                .transition()
                .duration(200)
                .attr('d', arc)
                .style('opacity', 0.9)
                .attr('stroke-width', 1);
            
            // Hide tooltip
            tooltip.style('visibility', 'hidden');
            
            // Restore label
            svg.selectAll('.label-text')
                .filter(textData => textData.data.label === d.data.label)
                .style('font-weight', 'normal')
                .style('font-size', '9px');
        });
    
    // Add text labels
    const arcLabel = d3.arc()
        .innerRadius(radius * 0.7)
        .outerRadius(radius * 0.7);
    
    // Add text labels
    const labels = svg.selectAll('.label')
        .data(dataReady)
        .enter()
        .append('text')
        .attr('class', 'label-text')
        .attr('transform', d => `translate(${arcLabel.centroid(d)})`)
        .attr('dy', '0.35em')
        .style('text-anchor', 'middle')
        .style('font-size', '9px')
        .style('fill', 'white')
        .text(d => {
            const total = d3.sum(data, item => item.value);
            const percentage = ((d.data.value / total) * 100).toFixed(0);
            return percentage >= 5 ? `${percentage}%` : '';
        });
    
    // Add a center text with the total
    const total = d3.sum(data, d => d.value);
    
    svg.append('text')
        .attr('class', 'center-text')
        .attr('text-anchor', 'middle')
        .attr('dy', '-0.2em')
        .style('font-size', '1rem')
        .style('fill', 'white')
        .style('font-weight', 'bold')
        .text(total);
    
    svg.append('text')
        .attr('class', 'center-text-label')
        .attr('text-anchor', 'middle')
        .attr('dy', '1em')
        .style('font-size', '0.8rem')
        .style('fill', 'rgba(255, 255, 255, 0.7)')
        .text('Total');
    
    // Add chart title
    svg.append('text')
        .attr('class', 'chart-title')
        .attr('x', 0)
        .attr('y', -height / 2 + 20)
        .attr('text-anchor', 'middle')
        .attr('fill', 'white')
        .attr('font-size', '1rem')
        .attr('font-weight', 'bold')
        .text('Category Distribution');
    
    // Add a legend
    const legendRectSize = 12;
    const legendSpacing = 4;
    const legendHeight = legendRectSize + legendSpacing;
    
    // Calculate the starting position for the legend
    // Position it at the bottom of the chart with some padding
    const legendStartY = height / 2 - (data.length * legendHeight) - 20;
    
    const legend = svg.selectAll('.legend')
        .data(dataReady)
        .enter()
        .append('g')
        .attr('class', 'legend')
        .attr('transform', (d, i) => `translate(-${width / 4}, ${legendStartY + i * 20})`);
    
    // Add colored squares to the legend
    legend.append('rect')
        .attr('width', legendRectSize)
        .attr('height', legendRectSize)
        .style('fill', d => color(d.data.label))
        .style('stroke', 'white');
    
    // Add legend text
    legend.append('text')
        .attr('x', legendRectSize + legendSpacing)
        .attr('y', legendRectSize - legendSpacing)
        .style('font-size', '0.7rem')
        .style('fill', 'rgba(255, 255, 255, 0.9)')
        .text(d => d.data.label);
    
    // Add initial animation
    paths.each(function(d) {
        d.endAngle = d.startAngle;
    })
    .transition()
    .duration(750)
    .attrTween('d', function(d) {
        const interpolate = d3.interpolate(
            { startAngle: d.startAngle, endAngle: d.startAngle },
            { startAngle: d.startAngle, endAngle: d.endAngle }
        );
        return t => arc(interpolate(t));
    });
    
    // Make labels invisible initially and then fade them in
    labels.style('opacity', 0)
        .transition()
        .delay(750)
        .duration(500)
        .style('opacity', 1);
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
        const total = d3.sum(data, d => d.value);
        statusText.textContent = `${data.length} categories, total: ${total}`;
    }
}

/**
 * Update pie chart with new data
 * @param {string} containerId - The container ID
 * @param {Array} data - New data array
 */
function updatePieChart(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    createPieChart(container, data);
    updateTileStatus(containerId, data);
}

// Make update function available globally
window.updatePieChart = updatePieChart; 