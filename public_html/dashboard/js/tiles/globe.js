/**
 * Globe Visualization
 * Using D3.js geo projections to create an interactive 3D globe
 */

// Initialize globe visualizations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const globeContainers = document.querySelectorAll('#globe-visualization, #full-globe-view');
    globeContainers.forEach(container => {
        initGlobe(container.id);
    });
});

/**
 * Initialize a globe visualization
 * @param {string} containerId - The ID of the container element
 */
function initGlobe(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Create initial loading state
    container.innerHTML = `
        <div class="globe-loading">
            <div class="spinner"></div>
            <div>Loading globe data...</div>
        </div>
    `;
    
    // Style loading indicator
    const loading = container.querySelector('.globe-loading');
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
    
    // Add spinner animation if not already added
    if (!document.querySelector('style#globe-spinner')) {
        const style = document.createElement('style');
        style.id = 'globe-spinner';
        style.innerHTML = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Load data
    Promise.all([
        d3.json('https://unpkg.com/world-atlas@2.0.2/countries-110m.json'),
        loadPointData(containerId)
    ]).then(([worldData, pointData]) => {
        createGlobe(container, worldData, pointData);
        updateTileStatus(containerId, pointData);
    }).catch(error => {
        console.error('Error loading globe data:', error);
        showErrorMessage(containerId, 'Failed to load globe data');
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        // Only update if container is visible
        if (container.offsetParent !== null) {
            // Get current data from container
            const worldData = container._worldData;
            const pointData = container._pointData;
            if (worldData && pointData) {
                createGlobe(container, worldData, pointData);
            }
        }
    });
}

/**
 * Load point data for the globe
 * @param {string} containerId - The ID of the container element
 * @returns {Promise} - Promise resolving to the point data
 */
function loadPointData(containerId) {
    // For demonstration, generate sample point data
    return new Promise((resolve) => {
        // Sample points data - format: [longitude, latitude, value, name]
        const points = [
            [-73.9857, 40.7484, 100, 'New York'],
            [-0.1278, 51.5074, 85, 'London'],
            [2.3522, 48.8566, 80, 'Paris'],
            [139.6917, 35.6895, 95, 'Tokyo'],
            [116.4074, 39.9042, 90, 'Beijing'],
            [77.2090, 28.6139, 70, 'New Delhi'],
            [-118.2437, 34.0522, 75, 'Los Angeles'],
            [-43.1729, -22.9068, 65, 'Rio de Janeiro'],
            [28.9784, 41.0082, 60, 'Istanbul'],
            [151.2093, -33.8688, 55, 'Sydney'],
            [31.2357, 30.0444, 50, 'Cairo'],
            [18.4241, -33.9249, 45, 'Cape Town'],
            [37.6173, 55.7558, 70, 'Moscow'],
            [121.4737, 31.2304, 85, 'Shanghai'],
            [103.8198, 1.3521, 75, 'Singapore'],
            [-99.1332, 19.4326, 65, 'Mexico City'],
            [-70.6693, -33.4489, 50, 'Santiago'],
            [101.6869, 3.1390, 60, 'Kuala Lumpur'],
            [13.4050, 52.5200, 70, 'Berlin'],
            [-58.3816, -34.6037, 55, 'Buenos Aires']
        ];
        
        // Simulate network delay
        setTimeout(() => {
            resolve(points);
        }, 800);
    });
}

/**
 * Create globe visualization
 * @param {HTMLElement} container - The container element
 * @param {Object} worldData - GeoJSON world data
 * @param {Array} pointData - Array of point data [lon, lat, value, name]
 */
function createGlobe(container, worldData, pointData) {
    // Clear container
    container.innerHTML = '';
    
    // Store data in container for resize events
    container._worldData = worldData;
    container._pointData = pointData;
    
    // Set dimensions
    const width = container.clientWidth;
    const height = container.clientHeight;
    const sensitivity = 75;
    
    // Create SVG element
    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Create a group for the globe
    const globeGroup = svg.append('g')
        .attr('class', 'globe')
        .attr('transform', `translate(${width/2}, ${height/2})`);
    
    // Create tooltip
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
    
    // Initial projection scale based on container size
    const scale = Math.min(width, height) / 2.5;
    
    // Create a projection
    const projection = d3.geoOrthographic()
        .scale(scale)
        .translate([0, 0])
        .clipAngle(90);
    
    // Create a path generator
    const path = d3.geoPath()
        .projection(projection);
    
    // Extract features from GeoJSON
    const countries = topojson.feature(worldData, worldData.objects.countries).features;
    
    // Create a transparent sphere for oceans
    globeGroup.append('path')
        .datum({type: 'Sphere'})
        .attr('class', 'ocean')
        .attr('d', path)
        .style('fill', '#3498db')
        .style('opacity', 0.6)
        .style('stroke', 'none');
    
    // Draw countries
    globeGroup.selectAll('.country')
        .data(countries)
        .enter()
        .append('path')
        .attr('class', 'country')
        .attr('d', path)
        .style('fill', '#2c3e50')
        .style('stroke', '#ecf0f1')
        .style('stroke-width', 0.3)
        .style('vector-effect', 'non-scaling-stroke')
        .on('mouseover', function(event, d) {
            d3.select(this)
                .style('fill', '#34495e')
                .style('stroke', '#fff')
                .style('stroke-width', 0.5);
        })
        .on('mouseout', function() {
            d3.select(this)
                .style('fill', '#2c3e50')
                .style('stroke', '#ecf0f1')
                .style('stroke-width', 0.3);
        });
    
    // Add graticule
    const graticule = d3.geoGraticule()
        .step([10, 10]);
    
    globeGroup.append('path')
        .datum(graticule)
        .attr('class', 'graticule')
        .attr('d', path)
        .style('fill', 'none')
        .style('stroke', '#ecf0f1')
        .style('stroke-width', 0.2)
        .style('stroke-opacity', 0.3)
        .style('vector-effect', 'non-scaling-stroke');
    
    // Add points
    const points = globeGroup.selectAll('.point')
        .data(pointData)
        .enter()
        .append('g')
        .attr('class', 'point')
        .attr('transform', d => {
            const coords = projection([d[0], d[1]]);
            return coords ? `translate(${coords})` : null;
        });
    
    // Only show points on visible side of the globe
    points.filter(d => {
        const coords = projection([d[0], d[1]]);
        return coords !== null;
    });
    
    // Size scale for points
    const sizeScale = d3.scaleLinear()
        .domain(d3.extent(pointData, d => d[2]))
        .range([3, 10]);
    
    // Color scale for points
    const colorScale = d3.scaleLinear()
        .domain(d3.extent(pointData, d => d[2]))
        .range(['#f1c40f', '#e74c3c']);
    
    // Add point markers
    points.append('circle')
        .attr('r', d => sizeScale(d[2]))
        .style('fill', d => colorScale(d[2]))
        .style('stroke', '#fff')
        .style('stroke-width', 0.5)
        .style('cursor', 'pointer')
        .style('opacity', 0.8)
        .on('mouseover', function(event, d) {
            // Highlight point
            d3.select(this)
                .style('opacity', 1)
                .attr('r', d => sizeScale(d[2]) * 1.5);
            
            // Show tooltip
            tooltip.transition()
                .duration(200)
                .style('opacity', 0.9);
            
            tooltip.html(`
                <strong>${d[3]}</strong><br>
                Value: ${d[2]}<br>
                Lat: ${d[1].toFixed(2)}, Lon: ${d[0].toFixed(2)}
            `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function(event, d) {
            // Reset point
            d3.select(this)
                .style('opacity', 0.8)
                .attr('r', d => sizeScale(d[2]));
            
            // Hide tooltip
            tooltip.transition()
                .duration(500)
                .style('opacity', 0);
        });
    
    // Add point pulses for animation
    points.append('circle')
        .attr('r', d => sizeScale(d[2]))
        .style('fill', d => colorScale(d[2]))
        .style('stroke', 'none')
        .style('opacity', 0.5)
        .call(pulse);
    
    // Add pulse animation
    function pulse(selection) {
        selection.transition()
            .duration(2000)
            .attr('r', d => sizeScale(d[2]) * 2)
            .style('opacity', 0)
            .on('end', function() {
                d3.select(this)
                    .attr('r', d => sizeScale(d[2]))
                    .style('opacity', 0.5)
                    .call(pulse);
            });
    }
    
    // Rotation state
    let rotate = [0, 0, 0];
    let lastTime = d3.now();
    
    // Auto-rotation
    const autoRotationSpeed = 0.5; // degrees per second
    
    function autoRotate() {
        const currentTime = d3.now();
        const elapsed = currentTime - lastTime;
        lastTime = currentTime;
        
        // Update rotation
        rotate[0] += autoRotationSpeed * elapsed / 1000;
        
        // Apply rotation
        projection.rotate(rotate);
        
        // Update paths
        globeGroup.selectAll('path')
            .attr('d', path);
        
        // Update points
        globeGroup.selectAll('.point')
            .attr('transform', d => {
                const coords = projection([d[0], d[1]]);
                return coords ? `translate(${coords})` : null;
            })
            .style('display', d => {
                const coords = projection([d[0], d[1]]);
                return coords ? null : 'none';
            });
    }
    
    // Create rotation controls
    const dragBehavior = d3.drag()
        .on('start', function() {
            // Stop auto-rotation when user interacts
            if (container._rotationTimer) {
                container._rotationTimer.stop();
                container._rotationTimer = null;
            }
        })
        .on('drag', function(event) {
            // Update rotation based on mouse movement
            const rotate0 = projection.rotate();
            const k = sensitivity / projection.scale();
            projection.rotate([
                rotate0[0] + event.dx * k,
                rotate0[1] - event.dy * k
            ]);
            
            // Update rotate state
            rotate = projection.rotate();
            
            // Update paths
            globeGroup.selectAll('path')
                .attr('d', path);
            
            // Update points
            globeGroup.selectAll('.point')
                .attr('transform', d => {
                    const coords = projection([d[0], d[1]]);
                    return coords ? `translate(${coords})` : null;
                })
                .style('display', d => {
                    const coords = projection([d[0], d[1]]);
                    return coords ? null : 'none';
                });
        })
        .on('end', function() {
            // Restart auto-rotation when interaction ends
            container._rotationTimer = d3.timer(autoRotate);
        });
    
    // Apply drag behavior to the globe
    svg.call(dragBehavior);
    
    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([scale * 0.7, scale * 3])
        .on('zoom', function(event) {
            // Update projection scale
            projection.scale(event.transform.k);
            
            // Update paths
            globeGroup.selectAll('path')
                .attr('d', path);
            
            // Update points
            globeGroup.selectAll('.point')
                .attr('transform', d => {
                    const coords = projection([d[0], d[1]]);
                    return coords ? `translate(${coords})` : null;
                })
                .style('display', d => {
                    const coords = projection([d[0], d[1]]);
                    return coords ? null : 'none';
                });
            
            // Update point sizes
            globeGroup.selectAll('.point circle')
                .attr('r', d => sizeScale(d[2]) * (scale / event.transform.k) * 0.5);
        });
    
    // Apply zoom behavior to the SVG
    svg.call(zoom);
    
    // Start auto-rotation
    container._rotationTimer = d3.timer(autoRotate);
    
    // Add legend
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(20, ${height - 140})`);
    
    // Legend background
    legend.append('rect')
        .attr('width', 120)
        .attr('height', 120)
        .attr('rx', 5)
        .attr('ry', 5)
        .style('fill', 'rgba(0, 0, 0, 0.6)');
    
    // Legend title
    legend.append('text')
        .attr('x', 10)
        .attr('y', 20)
        .style('fill', '#fff')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .text('Data Points');
    
    // Legend scale
    const valueExtent = d3.extent(pointData, d => d[2]);
    const legendScale = d3.scaleLinear()
        .domain(valueExtent)
        .range([80, 20]);
    
    // Add circles to legend
    const legendItems = [valueExtent[0], (valueExtent[0] + valueExtent[1]) / 2, valueExtent[1]];
    
    legend.selectAll('.legend-item')
        .data(legendItems)
        .enter()
        .append('g')
        .attr('class', 'legend-item')
        .attr('transform', d => `translate(20, ${legendScale(d)})`);
    
    legend.selectAll('.legend-item')
        .append('circle')
        .attr('r', d => sizeScale(d))
        .style('fill', d => colorScale(d))
        .style('stroke', '#fff')
        .style('stroke-width', 0.5);
    
    legend.selectAll('.legend-item')
        .append('text')
        .attr('x', 15)
        .attr('y', 4)
        .style('fill', '#fff')
        .style('font-size', '10px')
        .text(d => d);
    
    // Legend instructions
    legend.append('text')
        .attr('x', 10)
        .attr('y', 100)
        .style('fill', '#fff')
        .style('font-size', '10px')
        .text('Drag to rotate');
    
    legend.append('text')
        .attr('x', 10)
        .attr('y', 115)
        .style('fill', '#fff')
        .style('font-size', '10px')
        .text('Scroll to zoom');
}

/**
 * Update tile status with data information
 * @param {string} containerId - The ID of the container element
 * @param {Array} pointData - Array of point data
 */
function updateTileStatus(containerId, pointData) {
    // Find the parent tile
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const tile = container.closest('.tile');
    if (!tile) return;
    
    // Update status text
    const statusText = tile.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = `Displaying ${pointData.length} nodes`;
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
 * Add a temporary point to the globe
 * @param {string} containerId - The ID of the container element
 * @param {Array} point - Point data [lon, lat, value, name]
 */
function addPointToGlobe(containerId, point) {
    const container = document.getElementById(containerId);
    if (!container || !container._pointData) return;
    
    // Add point to the dataset
    container._pointData.push(point);
    
    // Redraw the globe
    createGlobe(container, container._worldData, container._pointData);
    updateTileStatus(containerId, container._pointData);
}

// Make function available globally
window.addPointToGlobe = addPointToGlobe; 