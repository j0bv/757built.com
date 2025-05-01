/**
 * Data Visualizer Module for Document Viewer
 * Handles various D3.js visualizations for data files
 */
(function() {
    // Main visualization class
    class DataVisualizer {
        constructor(containerId) {
            this.container = document.getElementById(containerId);
            if (!this.container) {
                console.error('Visualization container not found:', containerId);
                return;
            }
            
            this.currentData = null;
            this.currentConfig = null;
            this.tooltip = null;
            
            // Initialize tooltip
            this.createTooltip();
        }
        
        /**
         * Create tooltip element
         */
        createTooltip() {
            this.tooltip = d3.select("body").append("div")
                .attr("class", "vis-tooltip")
                .style("opacity", 0)
                .style("position", "absolute")
                .style("background-color", "rgba(0, 0, 0, 0.8)")
                .style("color", "white")
                .style("padding", "8px")
                .style("border-radius", "4px")
                .style("pointer-events", "none")
                .style("font-size", "12px")
                .style("z-index", 1000);
        }
        
        /**
         * Load data from file
         * @param {string} filePath - Path to the data file
         * @param {string} fileType - Type of file (csv, json, tsv)
         * @returns {Promise} - Promise resolving to the loaded data
         */
        async loadData(filePath, fileType) {
            try {
                let data;
                switch(fileType.toLowerCase()) {
                    case 'csv':
                        data = await d3.csv(filePath);
                        break;
                    case 'json':
                        data = await d3.json(filePath);
                        break;
                    case 'tsv':
                        data = await d3.tsv(filePath);
                        break;
                    default:
                        throw new Error(`Unsupported file type: ${fileType}`);
                }
                
                this.currentData = data;
                return data;
            } catch (error) {
                console.error('Error loading data:', error);
                throw error;
            }
        }
        
        /**
         * Create visualization based on type and configuration
         * @param {string} visType - Type of visualization to create
         * @param {object} config - Configuration for the visualization
         */
        createVisualization(visType, config) {
            if (!this.currentData) {
                console.error('No data loaded');
                return;
            }
            
            this.currentConfig = config;
            
            // Clear container
            this.container.innerHTML = '';
            
            // Create visualization based on type
            switch(visType.toLowerCase()) {
                case 'bar':
                case 'barchart':
                    this.createBarChart(this.currentData, config);
                    break;
                case 'line':
                case 'linechart':
                    this.createLineChart(this.currentData, config);
                    break;
                case 'pie':
                case 'piechart':
                    this.createPieChart(this.currentData, config);
                    break;
                case 'scatter':
                case 'scatterplot':
                    this.createScatterPlot(this.currentData, config);
                    break;
                case 'map':
                case 'worldmap':
                    this.createWorldMap(this.currentData, config);
                    break;
                case 'network':
                case 'forcedirected':
                    this.createForceDirectedGraph(this.currentData, config);
                    break;
                case 'treemap':
                    this.createTreemap(this.currentData, config);
                    break;
                default:
                    console.error(`Unsupported visualization type: ${visType}`);
            }
        }
        
        /**
         * Create a bar chart visualization
         * @param {array} data - Data array for the visualization
         * @param {object} config - Chart configuration options
         */
        createBarChart(data, config) {
            const { 
                width = 800, 
                height = 400, 
                margin = { top: 30, right: 30, bottom: 70, left: 60 },
                xField = 'x',
                yField = 'y',
                color = '#4285F4',
                title = 'Bar Chart',
                xLabel = '',
                yLabel = '',
                sortBy = null
            } = config;
            
            // Format data if necessary
            let formattedData = data;
            if (data[0] && (typeof data[0][xField] !== 'undefined' && typeof data[0][yField] !== 'undefined')) {
                // Data is already in the right format
            } else {
                // If the data is in a different format, transform it
                formattedData = Object.entries(data).map(([key, value]) => ({
                    [xField]: key, 
                    [yField]: +value
                }));
            }
            
            // Sort data if requested
            if (sortBy === 'asc') {
                formattedData.sort((a, b) => a[yField] - b[yField]);
            } else if (sortBy === 'desc') {
                formattedData.sort((a, b) => b[yField] - a[yField]);
            }
            
            // Create SVG
            const svg = d3.select(this.container)
                .append("svg")
                .attr("width", width)
                .attr("height", height)
                .attr("class", "bar-chart");
            
            // Add title
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", margin.top / 2)
                .attr("text-anchor", "middle")
                .attr("class", "chart-title")
                .text(title);
            
            // Create chart group
            const chart = svg.append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);
            
            // Set up scales
            const x = d3.scaleBand()
                .domain(formattedData.map(d => d[xField]))
                .range([0, width - margin.left - margin.right])
                .padding(0.2);
            
            const y = d3.scaleLinear()
                .domain([0, d3.max(formattedData, d => +d[yField])])
                .nice()
                .range([height - margin.top - margin.bottom, 0]);
            
            // Add axes
            chart.append("g")
                .attr("transform", `translate(0,${height - margin.top - margin.bottom})`)
                .attr("class", "x-axis")
                .call(d3.axisBottom(x))
                .selectAll("text")
                .attr("transform", "translate(-10,0)rotate(-45)")
                .style("text-anchor", "end");
            
            chart.append("g")
                .attr("class", "y-axis")
                .call(d3.axisLeft(y));
            
            // Add axis labels
            if (xLabel) {
                svg.append("text")
                    .attr("x", width / 2)
                    .attr("y", height - 5)
                    .attr("text-anchor", "middle")
                    .attr("class", "axis-label")
                    .text(xLabel);
            }
            
            if (yLabel) {
                svg.append("text")
                    .attr("transform", "rotate(-90)")
                    .attr("x", -(height / 2))
                    .attr("y", 15)
                    .attr("text-anchor", "middle")
                    .attr("class", "axis-label")
                    .text(yLabel);
            }
            
            // Add bars
            chart.selectAll(".bar")
                .data(formattedData)
                .join("rect")
                .attr("class", "bar")
                .attr("x", d => x(d[xField]))
                .attr("y", d => y(+d[yField]))
                .attr("width", x.bandwidth())
                .attr("height", d => height - margin.top - margin.bottom - y(+d[yField]))
                .attr("fill", color)
                .on("mouseover", (event, d) => {
                    d3.select(event.currentTarget).attr("fill", d3.color(color).darker(0.5));
                    
                    this.tooltip.transition()
                        .duration(200)
                        .style("opacity", 0.9);
                    this.tooltip.html(`<strong>${d[xField]}:</strong> ${d[yField]}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", (event) => {
                    d3.select(event.currentTarget).attr("fill", color);
                    this.tooltip.transition()
                        .duration(500)
                        .style("opacity", 0);
                });
            
            // Add animation
            chart.selectAll(".bar")
                .attr("y", height - margin.top - margin.bottom)
                .attr("height", 0)
                .transition()
                .duration(800)
                .attr("y", d => y(+d[yField]))
                .attr("height", d => height - margin.top - margin.bottom - y(+d[yField]));
        }
        
        /**
         * Create a line chart visualization
         * @param {array} data - Data array for the visualization
         * @param {object} config - Chart configuration options
         */
        createLineChart(data, config) {
            const { 
                width = 800, 
                height = 400, 
                margin = { top: 30, right: 50, bottom: 50, left: 60 },
                xField = 'x',
                yField = 'y',
                color = '#4285F4',
                title = 'Line Chart',
                xLabel = '',
                yLabel = '',
                curve = 'curveLinear'
            } = config;
            
            // Process data if needed
            let formattedData = data;
            
            // Create SVG
            const svg = d3.select(this.container)
                .append("svg")
                .attr("width", width)
                .attr("height", height)
                .attr("class", "line-chart");
            
            // Add title
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", margin.top / 2)
                .attr("text-anchor", "middle")
                .attr("class", "chart-title")
                .text(title);
            
            // Create chart group
            const chart = svg.append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);
            
            // Set up scales
            const x = d3.scalePoint()
                .domain(formattedData.map(d => d[xField]))
                .range([0, width - margin.left - margin.right]);
            
            const y = d3.scaleLinear()
                .domain([0, d3.max(formattedData, d => +d[yField])])
                .nice()
                .range([height - margin.top - margin.bottom, 0]);
            
            // Add axes
            chart.append("g")
                .attr("transform", `translate(0,${height - margin.top - margin.bottom})`)
                .attr("class", "x-axis")
                .call(d3.axisBottom(x))
                .selectAll("text")
                .style("text-anchor", "end")
                .attr("dx", "-.8em")
                .attr("dy", ".15em")
                .attr("transform", "rotate(-45)");
            
            chart.append("g")
                .attr("class", "y-axis")
                .call(d3.axisLeft(y));
            
            // Add axis labels
            if (xLabel) {
                svg.append("text")
                    .attr("x", width / 2)
                    .attr("y", height - 5)
                    .attr("text-anchor", "middle")
                    .attr("class", "axis-label")
                    .text(xLabel);
            }
            
            if (yLabel) {
                svg.append("text")
                    .attr("transform", "rotate(-90)")
                    .attr("x", -(height / 2))
                    .attr("y", 15)
                    .attr("text-anchor", "middle")
                    .attr("class", "axis-label")
                    .text(yLabel);
            }
            
            // Create line generator
            const line = d3.line()
                .x(d => x(d[xField]))
                .y(d => y(+d[yField]))
                .curve(d3[curve]);
            
            // Add the line path
            const path = chart.append("path")
                .datum(formattedData)
                .attr("fill", "none")
                .attr("stroke", color)
                .attr("stroke-width", 2)
                .attr("class", "line")
                .attr("d", line);
            
            // Animate the line
            const pathLength = path.node().getTotalLength();
            path.attr("stroke-dasharray", pathLength + " " + pathLength)
                .attr("stroke-dashoffset", pathLength)
                .transition()
                .duration(2000)
                .attr("stroke-dashoffset", 0);
            
            // Add data points
            chart.selectAll(".data-point")
                .data(formattedData)
                .join("circle")
                .attr("class", "data-point")
                .attr("cx", d => x(d[xField]))
                .attr("cy", d => y(+d[yField]))
                .attr("r", 5)
                .attr("fill", color)
                .style("opacity", 0)
                .transition()
                .delay((d, i) => i * 100)
                .duration(500)
                .style("opacity", 1);
            
            // Add interactivity
            chart.selectAll(".data-point")
                .on("mouseover", (event, d) => {
                    d3.select(event.currentTarget)
                        .attr("r", 8)
                        .attr("fill", d3.color(color).darker(0.5));
                    
                    this.tooltip.transition()
                        .duration(200)
                        .style("opacity", 0.9);
                    this.tooltip.html(`<strong>${d[xField]}:</strong> ${d[yField]}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", (event) => {
                    d3.select(event.currentTarget)
                        .attr("r", 5)
                        .attr("fill", color);
                    
                    this.tooltip.transition()
                        .duration(500)
                        .style("opacity", 0);
                });
        }
        
        // Additional visualization methods would be implemented here
        // createPieChart, createScatterPlot, createWorldMap, createForceDirectedGraph, etc.
    }
    
    // Expose the visualizer to the global scope
    window.DataVisualizer = DataVisualizer;
})(); 