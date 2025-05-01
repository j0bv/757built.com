/**
 * Network Graph Visualization
 * Using D3.js force-directed graph to visualize knowledge graph
 */

// Initialize all network graph visualizations when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize any network graphs found on the page
    const networkContainers = document.querySelectorAll('#network-visualization, #full-network-view');
    networkContainers.forEach(container => {
        initNetworkGraph(container.id);
    });
});

/**
 * Initialize a network graph visualization
 * @param {string} containerId - The ID of the container element
 */
function initNetworkGraph(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Set dimensions based on container
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Create SVG element
    const svg = d3.select(`#${containerId}`)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .append('g');
    
    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 8])
        .on('zoom', (event) => {
            svg.attr('transform', event.transform);
        });
    
    d3.select(`#${containerId} svg`).call(zoom);
    
    // Create tooltip
    const tooltip = d3.select(`#${containerId}`)
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
    
    // Load data and create visualization
    loadNetworkData(containerId)
        .then(data => {
            createNetworkGraph(svg, data, tooltip, width, height);
            updateTileStatus(containerId, data);
        })
        .catch(error => {
            console.error('Error loading network data:', error);
            showErrorMessage(containerId, 'Failed to load network data');
        });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        // Only update if container is visible
        if (container.offsetParent !== null) {
            updateNetworkGraph(containerId);
        }
    });
}

/**
 * Load network graph data
 * @param {string} containerId - The ID of the container element
 * @returns {Promise} - Promise resolving to the network data
 */
function loadNetworkData(containerId) {
    // For now, generate sample data based on the schema.py
    // In a real implementation, this would fetch data from an API
    
    return new Promise((resolve) => {
        // Sample node types from schema.py
        const nodeTypes = [
            'RESEARCH_PAPER', 'PATENT', 'PROJECT', 'BUILDING', 
            'DATASET', 'PERSON', 'FUNDING', 'DOCUMENT', 
            'LOCALITY', 'REGION'
        ];
        
        // Sample edge types from schema.py
        const edgeTypes = [
            'DERIVES_FROM', 'IMPLEMENTS', 'INFLUENCED', 'SUPERSEDES',
            'AUTHORED_BY', 'FUNDED_BY', 'LOCATED_IN', 'SERVES_REGION',
            'WORKED_WITH', 'CITED_BY', 'CONTRACTED_BY', 'MERGED_WITH', 
            'ACQUIRED', 'PARTNERED_WITH', 'INVESTED_IN', 'SUPPLIES_TO', 
            'PROVIDES_SERVICE_TO', 'HOSTS_AT', 'LOCATED_NEAR', 'ORIGINATED_FROM'
        ];
        
        // Generate nodes
        const nodes = [];
        let nodeId = 0;
        
        // Create nodes for each type
        nodeTypes.forEach(type => {
            // Create different number of nodes for each type
            const count = Math.floor(Math.random() * 15) + 5;
            
            for (let i = 0; i < count; i++) {
                nodes.push({
                    id: `node${nodeId++}`,
                    name: `${type.charAt(0)}${type.substring(1).toLowerCase()} ${i + 1}`,
                    type: type,
                    value: Math.random() * 10 + 1, // For node size
                    group: nodeTypes.indexOf(type) // For color grouping
                });
            }
        });
        
        // Generate links between nodes
        const links = [];
        const nodeCount = nodes.length;
        const linkCount = Math.min(nodeCount * 2, 200); // Limit total links
        
        for (let i = 0; i < linkCount; i++) {
            const source = Math.floor(Math.random() * nodeCount);
            let target = Math.floor(Math.random() * nodeCount);
            
            // Avoid self-links
            while (target === source) {
                target = Math.floor(Math.random() * nodeCount);
            }
            
            // Assign random edge type
            const edgeType = edgeTypes[Math.floor(Math.random() * edgeTypes.length)];
            
            links.push({
                source: nodes[source].id,
                target: nodes[target].id,
                type: edgeType,
                value: Math.random() * 2 + 1 // For line thickness
            });
        }
        
        // Return the network data
        setTimeout(() => {
            resolve({ nodes, links });
        }, 500); // Simulate network delay
    });
}

/**
 * Create network graph visualization
 * @param {d3.Selection} svg - The SVG element
 * @param {Object} data - Network data with nodes and links
 * @param {d3.Selection} tooltip - The tooltip element
 * @param {number} width - The width of the container
 * @param {number} height - The height of the container
 */
function createNetworkGraph(svg, data, tooltip, width, height) {
    // Create a color scale for node types
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10);
    
    // Create a force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => d.value * 2 + 10));
    
    // Create links
    const link = svg.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(data.links)
        .enter()
        .append('line')
        .attr('stroke-width', d => d.value)
        .attr('stroke', '#666')
        .attr('stroke-opacity', 0.6);
    
    // Create nodes
    const node = svg.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(data.nodes)
        .enter()
        .append('circle')
        .attr('r', d => d.value + 5)
        .attr('fill', d => colorScale(d.group))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add node labels
    const labels = svg.append('g')
        .attr('class', 'labels')
        .selectAll('text')
        .data(data.nodes)
        .enter()
        .append('text')
        .text(d => d.name)
        .attr('font-size', 10)
        .attr('dx', 12)
        .attr('dy', 4)
        .style('fill', '#fff')
        .style('pointer-events', 'none')
        .style('opacity', 0.7);
    
    // Node tooltip
    node.on('mouseover', function(event, d) {
            d3.select(this)
                .attr('stroke', '#ff0')
                .attr('stroke-width', 2);
            
            tooltip.transition()
                .duration(200)
                .style('opacity', 0.9);
            
            tooltip.html(`
                <strong>${d.name}</strong><br>
                Type: ${d.type}<br>
                Value: ${d.value.toFixed(1)}
            `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this)
                .attr('stroke', '#fff')
                .attr('stroke-width', 1.5);
            
            tooltip.transition()
                .duration(500)
                .style('opacity', 0);
        });
    
    // Link tooltip
    link.on('mouseover', function(event, d) {
            d3.select(this)
                .attr('stroke', '#ff0')
                .attr('stroke-width', d.value + 1);
            
            tooltip.transition()
                .duration(200)
                .style('opacity', 0.9);
            
            tooltip.html(`
                <strong>Relation: ${d.type}</strong><br>
                From: ${d.source.name}<br>
                To: ${d.target.name}
            `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .attr('stroke', '#666')
                .attr('stroke-width', d.value);
            
            tooltip.transition()
                .duration(500)
                .style('opacity', 0);
        });
    
    // Add legend
    const legendData = [...new Set(data.nodes.map(d => d.type))];
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${width - 150}, 20)`);
    
    legend.selectAll('rect')
        .data(legendData)
        .enter()
        .append('rect')
        .attr('x', 0)
        .attr('y', (d, i) => i * 20)
        .attr('width', 10)
        .attr('height', 10)
        .attr('fill', (d, i) => colorScale(i));
    
    legend.selectAll('text')
        .data(legendData)
        .enter()
        .append('text')
        .attr('x', 15)
        .attr('y', (d, i) => i * 20 + 9)
        .text(d => d.charAt(0) + d.substring(1).toLowerCase())
        .style('font-size', '10px')
        .style('fill', '#fff');
    
    // Update positions on simulation tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        labels
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    // Store simulation for later updates
    const container = document.getElementById(svg.node().parentNode.parentNode.id);
    container._simulation = simulation;
}

/**
 * Update network graph on resize
 * @param {string} containerId - The ID of the container element
 */
function updateNetworkGraph(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const svg = d3.select(`#${containerId} svg`);
    if (svg.empty()) return;
    
    // Update dimensions
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    
    // Update force center if simulation exists
    if (container._simulation) {
        container._simulation
            .force('center', d3.forceCenter(width / 2, height / 2))
            .alpha(0.3)
            .restart();
    }
}

/**
 * Update tile status with data information
 * @param {string} containerId - The ID of the container element
 * @param {Object} data - The network data
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
        statusText.textContent = `Showing ${data.links.length} connections`;
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
        <i class="fas fa-exclamation-triangle"></i>
        <p>${message}</p>
    `;
    
    // Style error message
    errorDiv.style.display = 'flex';
    errorDiv.style.flexDirection = 'column';
    errorDiv.style.alignItems = 'center';
    errorDiv.style.justifyContent = 'center';
    errorDiv.style.height = '100%';
    errorDiv.style.color = '#e74c3c';
    errorDiv.style.gap = '10px';
    errorDiv.style.textAlign = 'center';
    
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