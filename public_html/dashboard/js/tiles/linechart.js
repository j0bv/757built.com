/**
 * Line Chart Visualization
 * Using D3.js to create interactive line charts for time series and trend data
 */

// Initialize line charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const lineChartContainers = document.querySelectorAll('[id^="linechart"][id$="-visualization"]');
    lineChartContainers.forEach(container => {
        initLineChart(container.id);
    });
});

/**
 * Initialize a line chart visualization
 * @param {string} containerId - The ID of the container element
 */
function initLineChart(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Sample data for the line chart
    const data = generateSampleTimeSeriesData();
    
    // Create line chart
    createLineChart(container, data);
}

/**
 * Create a responsive line chart using D3.js
 * @param {HTMLElement} container - The container element
 * @param {Array} data - The data to visualize
 */
function createLineChart(container, data) {
    // Clear previous chart if any
    container.innerHTML = '';
    
    // Get container dimensions
    const containerRect = container.getBoundingClientRect();
    const width = containerRect.width;
    const height = containerRect.height;
    
    // Set margins
    const margin = {top: 30, right: 50, bottom: 40, left: 60};
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // Create SVG
    const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);
    
    // Create scales
    const xScale = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value) * 1.1]) // Add 10% padding to top
        .range([innerHeight, 0]);
    
    // Create line generator
    const line = d3.line()
        .x(d => xScale(d.date))
        .y(d => yScale(d.value))
        .curve(d3.curveMonotoneX); // Smoother curve
    
    // Create area generator for the gradient fill below the line
    const area = d3.area()
        .x(d => xScale(d.date))
        .y0(innerHeight)
        .y1(d => yScale(d.value))
        .curve(d3.curveMonotoneX);
    
    // Create gradient
    const gradient = svg.append('defs')
        .append('linearGradient')
        .attr('id', `line-gradient-${container.id}`)
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', 0)
        .attr('y1', yScale(0))
        .attr('x2', 0)
        .attr('y2', yScale(d3.max(data, d => d.value)));
    
    gradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', 'rgba(53, 162, 235, 0.05)');
    
    gradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', 'rgba(53, 162, 235, 0.3)');
    
    // Add the area
    svg.append('path')
        .datum(data)
        .attr('class', 'area')
        .attr('d', area)
        .attr('fill', `url(#line-gradient-${container.id})`)
        .attr('opacity', 0.8);
    
    // Add the line
    svg.append('path')
        .datum(data)
        .attr('class', 'line')
        .attr('d', line)
        .attr('fill', 'none')
        .attr('stroke', '#36a2eb')
        .attr('stroke-width', 2)
        .attr('stroke-linejoin', 'round');
    
    // Add X axis
    const xAxis = svg.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(xScale)
            .tickFormat(d3.timeFormat('%b %d'))
            .ticks(Math.min(data.length, 7)));
    
    // Add Y axis
    const yAxis = svg.append('g')
        .attr('class', 'y-axis')
        .call(d3.axisLeft(yScale)
            .tickFormat(d => `${d.toFixed(0)}`)
            .ticks(5));
    
    // Style axes
    svg.selectAll('.domain')
        .attr('stroke', 'rgba(255, 255, 255, 0.2)');
    
    svg.selectAll('.tick line')
        .attr('stroke', 'rgba(255, 255, 255, 0.2)');
    
    svg.selectAll('.tick text')
        .attr('fill', 'rgba(255, 255, 255, 0.7)')
        .attr('font-size', '0.7rem');
    
    // Add axis labels
    svg.append('text')
        .attr('class', 'x-axis-label')
        .attr('x', innerWidth / 2)
        .attr('y', innerHeight + margin.bottom - 5)
        .attr('text-anchor', 'middle')
        .attr('fill', 'rgba(255, 255, 255, 0.7)')
        .attr('font-size', '0.8rem')
        .text('Time');
    
    svg.append('text')
        .attr('class', 'y-axis-label')
        .attr('transform', 'rotate(-90)')
        .attr('x', -innerHeight / 2)
        .attr('y', -margin.left + 15)
        .attr('text-anchor', 'middle')
        .attr('fill', 'rgba(255, 255, 255, 0.7)')
        .attr('font-size', '0.8rem')
        .text('Value');
    
    // Add grid lines
    svg.selectAll('grid-line')
        .data(yScale.ticks(5))
        .enter()
        .append('line')
        .attr('class', 'grid-line')
        .attr('x1', 0)
        .attr('x2', innerWidth)
        .attr('y1', d => yScale(d))
        .attr('y2', d => yScale(d))
        .attr('stroke', 'rgba(255, 255, 255, 0.1)')
        .attr('stroke-dasharray', '3,3');
    
    // Add data points
    const dataPoints = svg.selectAll('.data-point')
        .data(data)
        .enter()
        .append('circle')
        .attr('class', 'data-point')
        .attr('cx', d => xScale(d.date))
        .attr('cy', d => yScale(d.value))
        .attr('r', 3) // Small radius by default
        .attr('fill', '#36a2eb')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1)
        .attr('opacity', 0.7);
    
    // Add tooltip
    const tooltip = d3.select(container)
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('position', 'absolute')
        .style('visibility', 'hidden')
        .style('background-color', 'rgba(0,0,0,0.8)')
        .style('color', 'white')
        .style('padding', '5px 10px')
        .style('border-radius', '4px')
        .style('font-size', '0.8rem')
        .style('pointer-events', 'none')
        .style('z-index', '10')
        .style('width', 'auto');
    
    // Add hover effects
    dataPoints
        .on('mouseover', function(event, d) {
            // Highlight point
            d3.select(this)
                .attr('r', 6)
                .attr('opacity', 1)
                .attr('stroke-width', 2);
            
            // Show tooltip
            tooltip
                .style('visibility', 'visible')
                .html(`<strong>Date:</strong> ${d.date.toLocaleDateString()}<br/>
                       <strong>Value:</strong> ${d.value.toFixed(2)}<br/>
                       <strong>Change:</strong> <span style="color:${d.change >= 0 ? '#4CAF50' : '#F44336'}">${d.change >= 0 ? '+' : ''}${d.change.toFixed(2)}%</span>`)
                .style('left', `${event.pageX - container.getBoundingClientRect().left + 10}px`)
                .style('top', `${event.pageY - container.getBoundingClientRect().top - 28}px`);
            
            // Add vertical guide line
            svg.append('line')
                .attr('class', 'guide-line')
                .attr('x1', xScale(d.date))
                .attr('x2', xScale(d.date))
                .attr('y1', yScale(d.value))
                .attr('y2', innerHeight)
                .attr('stroke', 'rgba(255, 255, 255, 0.5)')
                .attr('stroke-dasharray', '3,3');
        })
        .on('mousemove', function(event, d) {
            // Update tooltip position
            tooltip
                .style('left', `${event.pageX - container.getBoundingClientRect().left + 10}px`)
                .style('top', `${event.pageY - container.getBoundingClientRect().top - 28}px`);
        })
        .on('mouseout', function() {
            // Restore point style
            d3.select(this)
                .attr('r', 3)
                .attr('opacity', 0.7)
                .attr('stroke-width', 1);
            
            // Hide tooltip
            tooltip.style('visibility', 'hidden');
            
            // Remove guide line
            svg.selectAll('.guide-line').remove();
        });
    
    // Add chart title
    svg.append('text')
        .attr('class', 'chart-title')
        .attr('x', innerWidth / 2)
        .attr('y', -margin.top / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', 'white')
        .attr('font-size', '1rem')
        .attr('font-weight', 'bold')
        .text('Time Series Trend');
    
    // Add zoom capability
    const zoom = d3.zoom()
        .scaleExtent([1, 10])
        .extent([[0, 0], [innerWidth, innerHeight]])
        .on('zoom', function(event) {
            // Update the scales based on zoom
            const newXScale = event.transform.rescaleX(xScale);
            const newYScale = event.transform.rescaleY(yScale);
            
            // Update axes
            xAxis.call(d3.axisBottom(newXScale).tickFormat(d3.timeFormat('%b %d')));
            yAxis.call(d3.axisLeft(newYScale).tickFormat(d => `${d.toFixed(0)}`));
            
            // Update line
            svg.select('.line')
                .attr('d', d3.line()
                    .x(d => newXScale(d.date))
                    .y(d => newYScale(d.value))
                    .curve(d3.curveMonotoneX));
            
            // Update area
            svg.select('.area')
                .attr('d', d3.area()
                    .x(d => newXScale(d.date))
                    .y0(innerHeight)
                    .y1(d => newYScale(d.value))
                    .curve(d3.curveMonotoneX));
            
            // Update data points
            svg.selectAll('.data-point')
                .attr('cx', d => newXScale(d.date))
                .attr('cy', d => newYScale(d.value));
            
            // Update grid lines
            svg.selectAll('.grid-line')
                .data(newYScale.ticks(5))
                .attr('y1', d => newYScale(d))
                .attr('y2', d => newYScale(d));
        });
    
    // Apply zoom to SVG
    svg.call(zoom);
    
    // Add zoom instructions
    svg.append('text')
        .attr('class', 'zoom-instructions')
        .attr('x', innerWidth - 5)
        .attr('y', innerHeight - 5)
        .attr('text-anchor', 'end')
        .attr('fill', 'rgba(255, 255, 255, 0.5)')
        .attr('font-size', '0.7rem')
        .text('Scroll to zoom, drag to pan');
}

/**
 * Generate sample time series data
 * @returns {Array} Array of data points
 */
function generateSampleTimeSeriesData() {
    const data = [];
    const today = new Date();
    let previousValue = Math.random() * 300 + 200;
    
    for (let i = 30; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        
        // Add some random change to previous value
        const change = (Math.random() - 0.5) * 20;
        const percentChange = (change / previousValue) * 100;
        
        const value = previousValue + change;
        previousValue = value;
        
        data.push({
            date: date,
            value: value,
            change: percentChange
        });
    }
    
    return data;
}

/**
 * Update line chart with new data
 * @param {string} containerId - The container ID
 * @param {Array} data - New data array
 */
function updateLineChart(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // If no data provided, generate sample data
    const chartData = data || generateSampleTimeSeriesData();
    
    // Create/update chart
    createLineChart(container, chartData);
} 