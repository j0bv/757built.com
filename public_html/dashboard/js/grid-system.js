/**
 * Grid System for Dashboard Layout
 * Provides advanced grid functionality, inspired by terminal_dashboard.css
 */

class GridSystem {
    constructor(gridContainer) {
        this.container = typeof gridContainer === 'string' 
            ? document.querySelector(gridContainer) 
            : gridContainer;
        
        this.tiles = [];
        this.gridMatrix = [];
        this.gridSize = { rows: 12, cols: 12 }; // Default 12x12 grid
        this.gapSize = 8; // Gap between tiles in pixels
        
        // Initialize grid
        this.initGrid();
        
        // Track moving state
        this.currentMovingTile = null;
        this.moveStartPosition = { x: 0, y: 0 };
        this.originalTilePosition = { x: 0, y: 0, row: 0, col: 0 };

        // Setup resize observer to handle container resizing
        this.resizeObserver = new ResizeObserver(() => this.recalculateGrid());
        this.resizeObserver.observe(this.container);
    }

    /**
     * Initialize the grid system
     */
    initGrid() {
        if (!this.container) return;
        
        // Make sure container has position relative
        if (getComputedStyle(this.container).position === 'static') {
            this.container.style.position = 'relative';
        }
        
        // Add grid class to container
        this.container.classList.add('dashboard-grid-system');
        
        // Initialize grid matrix
        this.resetGridMatrix();
        
        // Get all existing tiles
        const existingTiles = this.container.querySelectorAll('.tile');
        existingTiles.forEach(tile => this.registerTile(tile));
        
        // Add event handlers
        this.setupEventHandlers();
    }

    /**
     * Reset grid occupancy matrix
     */
    resetGridMatrix() {
        this.gridMatrix = Array(this.gridSize.rows).fill().map(() => 
            Array(this.gridSize.cols).fill(false));
    }

    /**
     * Register a tile with the grid system
     * @param {HTMLElement} tileElement - The tile to register
     */
    registerTile(tileElement) {
        if (!tileElement) return;
        
        // Default size (4x3) and position if not set
        if (!tileElement.hasAttribute('data-grid-position')) {
            const nextPosition = this.findNextAvailablePosition(4, 3);
            tileElement.setAttribute('data-grid-position', 
                `${nextPosition.row},${nextPosition.col},${nextPosition.row+3},${nextPosition.col+4}`);
        }
        
        // Parse grid position
        const position = this.parseGridPosition(tileElement);
        
        // Update tile style
        this.updateTilePosition(tileElement, position);
        
        // Mark grid as occupied
        this.markGridOccupied(position);
        
        // Initialize dragging
        this.initTileDrag(tileElement);
        
        // Initialize resizing
        this.initTileResize(tileElement);
        
        // Add to tiles array
        this.tiles.push({
            element: tileElement,
            position: position
        });
    }

    /**
     * Parse grid position from tile data attribute
     * @param {HTMLElement} tileElement - The tile element
     * @returns {Object} Position object
     */
    parseGridPosition(tileElement) {
        const posAttr = tileElement.getAttribute('data-grid-position');
        if (!posAttr) return null;
        
        const [startRow, startCol, endRow, endCol] = posAttr.split(',').map(Number);
        
        return {
            startRow: startRow || 0,
            startCol: startCol || 0,
            endRow: endRow || (startRow + 2),
            endCol: endCol || (startCol + 2)
        };
    }

    /**
     * Update tile's visual position based on grid position
     * @param {HTMLElement} tileElement - The tile element
     * @param {Object} position - Position object
     */
    updateTilePosition(tileElement, position) {
        if (!tileElement || !position) return;
        
        // Calculate cell size
        const cellWidth = this.container.clientWidth / this.gridSize.cols;
        const cellHeight = this.container.clientHeight / this.gridSize.rows;
        
        // Calculate position
        const left = position.startCol * cellWidth;
        const top = position.startRow * cellHeight;
        const width = (position.endCol - position.startCol) * cellWidth - this.gapSize;
        const height = (position.endRow - position.startRow) * cellHeight - this.gapSize;
        
        // Update tile position and size
        tileElement.style.position = 'absolute';
        tileElement.style.left = `${left}px`;
        tileElement.style.top = `${top}px`;
        tileElement.style.width = `${width}px`;
        tileElement.style.height = `${height}px`;
        
        // Store the current position in a data attribute
        tileElement.setAttribute('data-grid-position', 
            `${position.startRow},${position.startCol},${position.endRow},${position.endCol}`);
    }

    /**
     * Mark grid cells as occupied
     * @param {Object} position - Position object
     */
    markGridOccupied(position) {
        if (!position) return;
        
        for (let row = position.startRow; row < position.endRow; row++) {
            for (let col = position.startCol; col < position.endCol; col++) {
                if (row < this.gridSize.rows && col < this.gridSize.cols) {
                    this.gridMatrix[row][col] = true;
                }
            }
        }
    }

    /**
     * Mark grid cells as unoccupied
     * @param {Object} position - Position object
     */
    markGridUnoccupied(position) {
        if (!position) return;
        
        for (let row = position.startRow; row < position.endRow; row++) {
            for (let col = position.startCol; col < position.endCol; col++) {
                if (row < this.gridSize.rows && col < this.gridSize.cols) {
                    this.gridMatrix[row][col] = false;
                }
            }
        }
    }

    /**
     * Find next available position for a tile of given size
     * @param {number} widthCells - Width in cells
     * @param {number} heightCells - Height in cells
     * @returns {Object} Position object
     */
    findNextAvailablePosition(widthCells, heightCells) {
        for (let row = 0; row <= this.gridSize.rows - heightCells; row++) {
            for (let col = 0; col <= this.gridSize.cols - widthCells; col++) {
                // Check if this position is available
                let isAvailable = true;
                
                for (let r = row; r < row + heightCells; r++) {
                    for (let c = col; c < col + widthCells; c++) {
                        if (this.gridMatrix[r][c]) {
                            isAvailable = false;
                            break;
                        }
                    }
                    if (!isAvailable) break;
                }
                
                if (isAvailable) {
                    return {
                        row: row,
                        col: col
                    };
                }
            }
        }
        
        // If no space found, return the top position
        return { row: 0, col: 0 };
    }

    /**
     * Initialize dragging for a tile
     * @param {HTMLElement} tileElement - The tile element
     */
    initTileDrag(tileElement) {
        const header = tileElement.querySelector('.tile-header');
        if (!header) return;
        
        header.addEventListener('mousedown', (e) => {
            // Ignore if clicking on a control button
            if (e.target.closest('.tile-control')) return;
            
            // Start dragging
            this.currentMovingTile = tileElement;
            this.moveStartPosition = { x: e.clientX, y: e.clientY };
            this.originalTilePosition = { ...this.parseGridPosition(tileElement) };
            
            // Add dragging class
            tileElement.classList.add('dragging');
            
            // Mark position as unoccupied temporarily
            this.markGridUnoccupied(this.originalTilePosition);
            
            // Prevent text selection
            e.preventDefault();
        });
    }

    /**
     * Handle mouse move for dragging
     * @param {MouseEvent} e - Mouse event
     */
    handleMouseMove(e) {
        if (!this.currentMovingTile) return;
        
        // Calculate movement
        const dx = e.clientX - this.moveStartPosition.x;
        const dy = e.clientY - this.moveStartPosition.y;
        
        // Convert to grid cells
        const cellWidth = this.container.clientWidth / this.gridSize.cols;
        const cellHeight = this.container.clientHeight / this.gridSize.rows;
        
        const colMove = Math.round(dx / cellWidth);
        const rowMove = Math.round(dy / cellHeight);
        
        // New position
        const newPosition = {
            startRow: this.originalTilePosition.startRow + rowMove,
            startCol: this.originalTilePosition.startCol + colMove,
            endRow: this.originalTilePosition.endRow + rowMove,
            endCol: this.originalTilePosition.endCol + colMove
        };
        
        // Validate position
        this.validatePosition(newPosition);
        
        // Check if position is valid
        if (this.isPositionAvailable(newPosition)) {
            this.updateTilePosition(this.currentMovingTile, newPosition);
        }
    }

    /**
     * Handle mouse up for dragging
     */
    handleMouseUp() {
        if (!this.currentMovingTile) return;
        
        // Get current position
        const position = this.parseGridPosition(this.currentMovingTile);
        
        // Mark as occupied
        this.markGridOccupied(position);
        
        // Update tiles array
        const tileIndex = this.tiles.findIndex(t => t.element === this.currentMovingTile);
        if (tileIndex >= 0) {
            this.tiles[tileIndex].position = position;
        }
        
        // Remove dragging class
        this.currentMovingTile.classList.remove('dragging');
        
        // Reset
        this.currentMovingTile = null;
    }

    /**
     * Initialize resizing for a tile
     * @param {HTMLElement} tileElement - The tile element
     */
    initTileResize(tileElement) {
        const resizeHandle = tileElement.querySelector('.resize-handle');
        if (!resizeHandle) return;
        
        let isResizing = false;
        let startX, startY, startWidth, startHeight;
        let startPosition;
        
        resizeHandle.addEventListener('mousedown', (e) => {
            // Start resizing
            isResizing = true;
            tileElement.classList.add('resizing');
            
            // Record starting position
            startX = e.clientX;
            startY = e.clientY;
            startWidth = tileElement.offsetWidth;
            startHeight = tileElement.offsetHeight;
            startPosition = this.parseGridPosition(tileElement);
            
            // Mark position as unoccupied temporarily (except the starting cell)
            this.markGridUnoccupied(startPosition);
            this.gridMatrix[startPosition.startRow][startPosition.startCol] = true;
            
            // Prevent default
            e.preventDefault();
            e.stopPropagation();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            // Calculate new size
            const dw = e.clientX - startX;
            const dh = e.clientY - startY;
            
            // Convert to grid cells
            const cellWidth = this.container.clientWidth / this.gridSize.cols;
            const cellHeight = this.container.clientHeight / this.gridSize.rows;
            
            const colChange = Math.max(0, Math.round(dw / cellWidth));
            const rowChange = Math.max(0, Math.round(dh / cellHeight));
            
            // New position
            const newPosition = {
                startRow: startPosition.startRow,
                startCol: startPosition.startCol,
                endRow: Math.min(this.gridSize.rows, startPosition.startRow + (startPosition.endRow - startPosition.startRow) + rowChange),
                endCol: Math.min(this.gridSize.cols, startPosition.startCol + (startPosition.endCol - startPosition.startCol) + colChange)
            };
            
            // Ensure minimum size
            if (newPosition.endCol - newPosition.startCol < 2) {
                newPosition.endCol = newPosition.startCol + 2;
            }
            if (newPosition.endRow - newPosition.startRow < 2) {
                newPosition.endRow = newPosition.startRow + 2;
            }
            
            // Check if position is valid
            if (this.isPositionAvailableForResize(newPosition, startPosition)) {
                this.updateTilePosition(tileElement, newPosition);
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (!isResizing) return;
            
            isResizing = false;
            tileElement.classList.remove('resizing');
            
            // Get current position
            const position = this.parseGridPosition(tileElement);
            
            // Mark as occupied
            this.markGridOccupied(position);
            
            // Update tiles array
            const tileIndex = this.tiles.findIndex(t => t.element === tileElement);
            if (tileIndex >= 0) {
                this.tiles[tileIndex].position = position;
            }
            
            // Trigger resize event for visualizations
            window.dispatchEvent(new Event('resize'));
        });
    }

    /**
     * Set up global event handlers
     */
    setupEventHandlers() {
        // Mouse move handler for dragging
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        
        // Mouse up handler for dragging
        document.addEventListener('mouseup', () => this.handleMouseUp());
        
        // Handle adding new tiles
        document.addEventListener('dashboard:addTile', (e) => {
            if (e.detail && e.detail.tileElement) {
                this.registerTile(e.detail.tileElement);
            }
        });
        
        // Handle removing tiles
        document.addEventListener('dashboard:removeTile', (e) => {
            if (e.detail && e.detail.tileId) {
                this.removeTile(e.detail.tileId);
            }
        });
    }

    /**
     * Remove a tile from the grid
     * @param {string} tileId - Tile ID to remove
     */
    removeTile(tileId) {
        const tileIndex = this.tiles.findIndex(t => t.element.getAttribute('data-tile-id') === tileId);
        
        if (tileIndex >= 0) {
            // Mark grid as available
            this.markGridUnoccupied(this.tiles[tileIndex].position);
            
            // Remove from array
            this.tiles.splice(tileIndex, 1);
        }
    }

    /**
     * Validate position to ensure it's within grid boundaries
     * @param {Object} position - Position object to validate
     */
    validatePosition(position) {
        // Ensure it doesn't go outside the grid
        if (position.startRow < 0) {
            const shift = -position.startRow;
            position.startRow += shift;
            position.endRow += shift;
        }
        
        if (position.startCol < 0) {
            const shift = -position.startCol;
            position.startCol += shift;
            position.endCol += shift;
        }
        
        if (position.endRow > this.gridSize.rows) {
            const shift = position.endRow - this.gridSize.rows;
            position.startRow -= shift;
            position.endRow -= shift;
            
            // Readjust if still out of bounds
            if (position.startRow < 0) {
                position.startRow = 0;
                position.endRow = Math.min(position.endRow - position.startRow, this.gridSize.rows);
            }
        }
        
        if (position.endCol > this.gridSize.cols) {
            const shift = position.endCol - this.gridSize.cols;
            position.startCol -= shift;
            position.endCol -= shift;
            
            // Readjust if still out of bounds
            if (position.startCol < 0) {
                position.startCol = 0;
                position.endCol = Math.min(position.endCol - position.startCol, this.gridSize.cols);
            }
        }
    }

    /**
     * Check if a position is available (not occupied)
     * @param {Object} position - Position to check
     * @returns {boolean} True if available
     */
    isPositionAvailable(position) {
        // Check bounds
        if (position.startRow < 0 || position.startCol < 0 || 
            position.endRow > this.gridSize.rows || position.endCol > this.gridSize.cols) {
            return false;
        }
        
        // Check for occupation
        for (let row = position.startRow; row < position.endRow; row++) {
            for (let col = position.startCol; col < position.endCol; col++) {
                if (this.gridMatrix[row][col]) {
                    return false;
                }
            }
        }
        
        return true;
    }

    /**
     * Check if a position is available for resize (accounting for original position)
     * @param {Object} position - New position
     * @param {Object} original - Original position
     * @returns {boolean} True if available
     */
    isPositionAvailableForResize(position, original) {
        // Check bounds
        if (position.startRow < 0 || position.startCol < 0 || 
            position.endRow > this.gridSize.rows || position.endCol > this.gridSize.cols) {
            return false;
        }
        
        // Check only new cells
        for (let row = original.startRow; row < position.endRow; row++) {
            for (let col = original.startCol; col < position.endCol; col++) {
                // Skip cells in the original position
                if (row >= original.startRow && row < original.endRow && 
                    col >= original.startCol && col < original.endCol) {
                    continue;
                }
                
                // Check if new cell is occupied
                if (row < this.gridSize.rows && col < this.gridSize.cols && this.gridMatrix[row][col]) {
                    return false;
                }
            }
        }
        
        return true;
    }

    /**
     * Recalculate grid when container resizes
     */
    recalculateGrid() {
        // Update all tile positions
        this.tiles.forEach(tile => {
            this.updateTilePosition(tile.element, tile.position);
        });
    }

    /**
     * Add a new tile to the grid
     * @param {HTMLElement} tileElement - Tile element to add
     */
    addTile(tileElement) {
        this.registerTile(tileElement);
    }
}

// Export grid system
window.GridSystem = GridSystem;

// Initialize grid on load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize main grid
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (dashboardGrid) {
        window.dashboardGridSystem = new GridSystem(dashboardGrid);
    }
}); 