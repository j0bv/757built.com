/**
 * Terminal Component for Dashboard
 * Provides an interactive command line interface for data interaction
 * Inspired by terminal.class.js reference
 */

class DashboardTerminal {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        // Default options
        this.options = {
            prompt: '> ',
            greeting: 'Dashboard Terminal v1.0.0\nType "help" for available commands.',
            maxHistory: 100,
            theme: 'default',
            ...options
        };
        
        // Terminal state
        this.history = [];
        this.historyIndex = -1;
        this.commandBuffer = '';
        this.cursorPosition = 0;
        
        // Available commands
        this.commands = {
            help: this.showHelp.bind(this),
            clear: this.clear.bind(this),
            echo: this.echo.bind(this),
            history: this.showHistory.bind(this),
            data: this.queryData.bind(this),
            filter: this.filterData.bind(this),
            theme: this.changeTheme.bind(this),
            graph: this.graphCommand.bind(this)
        };
        
        // Initialize the terminal
        this.initTerminal();
    }
    
    /**
     * Initialize the terminal interface
     */
    initTerminal() {
        // Create terminal elements
        this.container.innerHTML = `
            <div class="terminal-output"></div>
            <div class="terminal-input-line">
                <span class="terminal-prompt">${this.options.prompt}</span>
                <span class="terminal-input" contenteditable="true" spellcheck="false"></span>
                <span class="terminal-cursor"></span>
            </div>
        `;
        
        // Get elements
        this.outputElement = this.container.querySelector('.terminal-output');
        this.inputElement = this.container.querySelector('.terminal-input');
        this.cursorElement = this.container.querySelector('.terminal-cursor');
        this.promptElement = this.container.querySelector('.terminal-prompt');
        
        // Set initial theme
        this.applyTheme(this.options.theme);
        
        // Print greeting
        this.print(this.options.greeting);
        
        // Add event listeners
        this.inputElement.addEventListener('keydown', this.handleKeyDown.bind(this));
        this.inputElement.addEventListener('input', this.handleInput.bind(this));
        this.inputElement.addEventListener('click', this.updateCursorPosition.bind(this));
        this.inputElement.addEventListener('focus', () => {
            this.cursorElement.classList.add('active');
        });
        this.inputElement.addEventListener('blur', () => {
            this.cursorElement.classList.remove('active');
        });
        
        // Auto focus if container is clicked
        this.container.addEventListener('click', (e) => {
            if (e.target === this.container || e.target === this.outputElement) {
                this.inputElement.focus();
            }
        });
        
        // Focus input
        this.inputElement.focus();
        
        // Start cursor blink
        this.startCursorBlink();
    }
    
    /**
     * Create blinking cursor effect
     */
    startCursorBlink() {
        this.cursorElement.classList.add('blink');
    }
    
    /**
     * Update cursor position based on input selection
     */
    updateCursorPosition() {
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            if (range.startContainer === this.inputElement.firstChild || 
                range.startContainer === this.inputElement) {
                this.cursorPosition = range.startOffset;
                this.updateCursorVisualPosition();
            }
        }
    }
    
    /**
     * Update the visual position of the cursor
     */
    updateCursorVisualPosition() {
        // Get the computed style of the input
        const inputStyle = window.getComputedStyle(this.inputElement);
        const fontSize = parseFloat(inputStyle.fontSize);
        
        // Calculate position
        const text = this.inputElement.textContent.substring(0, this.cursorPosition);
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        context.font = `${fontSize}px ${inputStyle.fontFamily}`;
        const textWidth = context.measureText(text).width;
        
        // Set cursor position
        this.cursorElement.style.left = `${this.promptElement.offsetWidth + textWidth}px`;
    }
    
    /**
     * Handle keydown events
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeyDown(e) {
        switch(e.key) {
            case 'Enter':
                e.preventDefault();
                this.execute();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.navigateHistory(-1);
                break;
                
            case 'ArrowDown':
                e.preventDefault();
                this.navigateHistory(1);
                break;
                
            case 'ArrowLeft':
                if (this.cursorPosition > 0) {
                    this.cursorPosition--;
                    this.updateCursorVisualPosition();
                }
                break;
                
            case 'ArrowRight':
                if (this.cursorPosition < this.inputElement.textContent.length) {
                    this.cursorPosition++;
                    this.updateCursorVisualPosition();
                }
                break;
                
            case 'Home':
                e.preventDefault();
                this.cursorPosition = 0;
                this.updateCursorVisualPosition();
                break;
                
            case 'End':
                e.preventDefault();
                this.cursorPosition = this.inputElement.textContent.length;
                this.updateCursorVisualPosition();
                break;
                
            case 'Tab':
                e.preventDefault();
                this.autoComplete();
                break;
                
            case 'c':
                if (e.ctrlKey) {
                    e.preventDefault();
                    this.clear();
                    this.resetInput();
                }
                break;
                
            case 'l':
                if (e.ctrlKey) {
                    e.preventDefault();
                    this.clear();
                }
                break;
        }
    }
    
    /**
     * Handle input events
     */
    handleInput() {
        this.commandBuffer = this.inputElement.textContent;
        this.cursorPosition = this.getCaretPosition();
        this.updateCursorVisualPosition();
    }
    
    /**
     * Get the current caret position in the input element
     * @returns {number} Caret position
     */
    getCaretPosition() {
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            if (range.commonAncestorContainer.parentNode === this.inputElement ||
                range.commonAncestorContainer === this.inputElement) {
                return range.startOffset;
            }
        }
        return this.inputElement.textContent.length;
    }
    
    /**
     * Navigate command history
     * @param {number} direction - Direction to navigate (1 = down, -1 = up)
     */
    navigateHistory(direction) {
        if (this.history.length === 0) return;
        
        // Save current command if we're at the initial state
        if (this.historyIndex === -1 && this.commandBuffer) {
            this.savedCommand = this.commandBuffer;
        }
        
        // Calculate new index
        this.historyIndex += direction;
        
        // Bounds checking
        if (this.historyIndex >= this.history.length) {
            this.historyIndex = this.history.length;
            this.inputElement.textContent = this.savedCommand || '';
        } else if (this.historyIndex < 0) {
            this.historyIndex = -1;
            this.inputElement.textContent = this.savedCommand || '';
        } else {
            this.inputElement.textContent = this.history[this.historyIndex];
        }
        
        // Update command buffer and cursor
        this.commandBuffer = this.inputElement.textContent;
        this.cursorPosition = this.inputElement.textContent.length;
        this.updateCursorVisualPosition();
    }
    
    /**
     * Execute the current command
     */
    execute() {
        const command = this.commandBuffer.trim();
        
        // Print command to output
        this.print(`${this.options.prompt}${command}`, 'input');
        
        // Add to history if not empty
        if (command) {
            this.addToHistory(command);
        }
        
        // Process command
        if (command) {
            this.processCommand(command);
        }
        
        // Reset input
        this.resetInput();
    }
    
    /**
     * Reset the input field
     */
    resetInput() {
        this.inputElement.textContent = '';
        this.commandBuffer = '';
        this.cursorPosition = 0;
        this.historyIndex = -1;
        this.updateCursorVisualPosition();
    }
    
    /**
     * Add a command to history
     * @param {string} command - Command to add
     */
    addToHistory(command) {
        // Don't add duplicates consecutively
        if (this.history.length > 0 && this.history[0] === command) {
            return;
        }
        
        // Add to beginning
        this.history.unshift(command);
        
        // Trim history to max size
        if (this.history.length > this.options.maxHistory) {
            this.history.pop();
        }
    }
    
    /**
     * Process and execute a command
     * @param {string} commandLine - Command string to process
     */
    processCommand(commandLine) {
        // Parse command and arguments
        const parts = commandLine.split(' ');
        const command = parts[0].toLowerCase();
        const args = parts.slice(1);
        
        // Execute command if it exists
        if (command in this.commands) {
            try {
                this.commands[command](args);
            } catch (error) {
                this.print(`Error executing command: ${error.message}`, 'error');
            }
        } else {
            this.print(`Command not found: ${command}. Type "help" for available commands.`, 'error');
        }
    }
    
    /**
     * Print text to the terminal
     * @param {string} text - Text to print
     * @param {string} type - Type of output (default, input, error, success)
     */
    print(text, type = 'default') {
        const lines = text.split('\n');
        
        lines.forEach(line => {
            const element = document.createElement('div');
            element.className = `terminal-line terminal-${type}`;
            element.textContent = line;
            this.outputElement.appendChild(element);
        });
        
        // Scroll to bottom
        this.container.scrollTop = this.container.scrollHeight;
    }
    
    /**
     * Clear the terminal output
     */
    clear() {
        this.outputElement.innerHTML = '';
        return '';
    }
    
    /**
     * Auto-complete command
     */
    autoComplete() {
        const input = this.commandBuffer.trim();
        
        // Find commands that start with the input
        const matches = Object.keys(this.commands).filter(cmd => 
            cmd.startsWith(input) && cmd !== input
        );
        
        if (matches.length === 1) {
            // Single match - complete the command
            this.inputElement.textContent = matches[0];
            this.commandBuffer = matches[0];
            this.cursorPosition = matches[0].length;
            this.updateCursorVisualPosition();
        } else if (matches.length > 1) {
            // Multiple matches - show options
            this.print(`\nMatching commands: ${matches.join(', ')}`, 'info');
            this.print(`${this.options.prompt}${input}`, 'input');
        }
    }
    
    /**
     * Apply terminal theme
     * @param {string} theme - Theme name
     */
    applyTheme(theme) {
        // Remove previous theme
        this.container.classList.remove('terminal-theme-default', 'terminal-theme-dark', 'terminal-theme-light', 'terminal-theme-green', 'terminal-theme-retro');
        
        // Add new theme
        this.container.classList.add(`terminal-theme-${theme}`);
        
        // Update current theme
        this.options.theme = theme;
    }
    
    /**
     * Command: help - Show available commands
     */
    showHelp() {
        const helpText = `
Available commands:
  help                     Show this help text
  clear                    Clear the terminal
  echo [text]              Display text
  history                  Show command history
  data [source] [query]    Query data from a source
  filter [criteria]        Filter current data view
  theme [name]             Change terminal theme (dark, light, green, retro)
  graph [type] [options]   Create a visualization

Keyboard shortcuts:
  Up/Down Arrow            Navigate command history
  Tab                      Auto-complete command
  Ctrl+C                   Clear line
  Ctrl+L                   Clear terminal
`;
        this.print(helpText);
        return '';
    }
    
    /**
     * Command: echo - Echo text
     * @param {Array} args - Command arguments
     */
    echo(args) {
        const text = args.join(' ');
        if (text) {
            this.print(text);
        }
        return text;
    }
    
    /**
     * Command: history - Show command history
     */
    showHistory() {
        if (this.history.length === 0) {
            this.print('Command history is empty');
        } else {
            const historyList = this.history.map((cmd, i) => `${this.history.length - i}: ${cmd}`).join('\n');
            this.print(historyList);
        }
        return '';
    }
    
    /**
     * Command: theme - Change terminal theme
     * @param {Array} args - Command arguments
     */
    changeTheme(args) {
        const theme = args[0] || 'default';
        const validThemes = ['default', 'dark', 'light', 'green', 'retro'];
        
        if (validThemes.includes(theme)) {
            this.applyTheme(theme);
            this.print(`Theme changed to ${theme}`, 'success');
        } else {
            this.print(`Invalid theme: ${theme}. Available themes: ${validThemes.join(', ')}`, 'error');
        }
        return '';
    }
    
    /**
     * Command: data - Query data from a source
     * @param {Array} args - Command arguments
     */
    queryData(args) {
        if (args.length === 0) {
            this.print(`
Available data sources:
  entities     - Knowledge graph entities
  connections  - Network connections 
  metrics      - System metrics
  geo          - Geographic data
  time         - Time series data
            `, 'info');
            return '';
        }
        
        const source = args[0];
        const query = args.slice(1).join(' ');
        
        // Simulate data query
        setTimeout(() => {
            switch (source) {
                case 'entities':
                    this.print(`Querying entities${query ? ` with filter: ${query}` : ''}...`, 'info');
                    this.print(`Found 423 entities${query ? ' matching criteria' : ''}.`, 'success');
                    this.simulateDataTable();
                    break;
                    
                case 'connections':
                    this.print(`Querying connections${query ? ` with filter: ${query}` : ''}...`, 'info');
                    this.print(`Found 618 connections${query ? ' matching criteria' : ''}.`, 'success');
                    this.simulateDataTable();
                    break;
                    
                case 'metrics':
                    this.print(`Querying metrics${query ? ` with filter: ${query}` : ''}...`, 'info');
                    this.print('System metrics data:', 'success');
                    this.print(`
CPU Usage: 24.5%
Memory: 6.2GB / 16GB
Disk I/O: 12.3MB/s read, 5.6MB/s write
Network: 8.4Mbps down, 2.1Mbps up
Active Sessions: 15
                    `, 'data');
                    break;
                
                case 'geo':
                    this.print(`Querying geographic data${query ? ` with filter: ${query}` : ''}...`, 'info');
                    this.print(`Found 157 geographic entities${query ? ' matching criteria' : ''}.`, 'success');
                    this.simulateDataTable();
                    break;
                    
                case 'time':
                    this.print(`Querying time series data${query ? ` with filter: ${query}` : ''}...`, 'info');
                    this.print(`Found 30 time points${query ? ' matching criteria' : ''}.`, 'success');
                    this.simulateDataTable();
                    break;
                    
                default:
                    this.print(`Unknown data source: ${source}. Type "data" to see available sources.`, 'error');
            }
        }, 500);
        
        return '';
    }
    
    /**
     * Command: filter - Filter current data view
     * @param {Array} args - Command arguments
     */
    filterData(args) {
        if (args.length === 0) {
            this.print('Usage: filter [criteria]', 'info');
            this.print('Example: filter type=organization AND country=USA', 'info');
            return '';
        }
        
        const criteria = args.join(' ');
        this.print(`Applying filter: ${criteria}`, 'info');
        
        // Simulate filter operation
        setTimeout(() => {
            this.print('Filter applied. Showing 42 results:', 'success');
            this.simulateDataTable(5);
        }, 300);
        
        return '';
    }
    
    /**
     * Command: graph - Create a visualization
     * @param {Array} args - Command arguments
     */
    graphCommand(args) {
        if (args.length === 0) {
            this.print(`
Available graph types:
  bar       - Bar chart
  line      - Line chart
  pie       - Pie chart
  network   - Network graph
  globe     - 3D globe
  map       - 2D map
  
Usage: graph [type] [options]
Example: graph pie data=entities group=category
            `, 'info');
            return '';
        }
        
        const type = args[0];
        const options = args.slice(1);
        
        this.print(`Creating ${type} chart...`, 'info');
        
        // Dispatch event to create visualization
        const event = new CustomEvent('terminal:createGraph', {
            detail: {
                type: type,
                options: options
            }
        });
        document.dispatchEvent(event);
        
        setTimeout(() => {
            this.print(`${type} chart created successfully.`, 'success');
        }, 500);
        
        return '';
    }
    
    /**
     * Helper: Simulate a data table
     * @param {number} rows - Number of rows to show
     */
    simulateDataTable(rows = 5) {
        // Display simulated data table
        const tableHeaders = ['ID', 'Name', 'Type', 'Date Created', 'Status'];
        const tableRows = [
            ['E-1024', 'Acme Corporation', 'Organization', '2022-03-15', 'Active'],
            ['E-1025', 'John Smith', 'Person', '2022-03-16', 'Active'],
            ['E-1026', 'Building A', 'Location', '2022-03-17', 'Active'],
            ['E-1027', 'Project Alpha', 'Project', '2022-03-18', 'In Progress'],
            ['E-1028', 'Device XYZ', 'Device', '2022-03-19', 'Offline']
        ].slice(0, rows);
        
        // Create header
        let tableOutput = '\n';
        tableHeaders.forEach(header => {
            tableOutput += header.padEnd(20);
        });
        tableOutput += '\n';
        
        // Add separator
        tableOutput += '-'.repeat(tableHeaders.length * 20) + '\n';
        
        // Add rows
        tableRows.forEach(row => {
            row.forEach(cell => {
                tableOutput += cell.toString().padEnd(20);
            });
            tableOutput += '\n';
        });
        
        this.print(tableOutput, 'data');
    }
}

/**
 * Initialize terminal when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize any terminal container in the dashboard
    const terminals = document.querySelectorAll('.terminal-container');
    terminals.forEach(container => {
        if (container.id) {
            window[`terminal_${container.id}`] = new DashboardTerminal(container.id);
        }
    });
});

/**
 * Initialize a terminal in a specific container
 * @param {string} containerId - Container ID
 * @param {Object} options - Terminal options
 */
function initTerminal(containerId, options = {}) {
    // Check if terminal already exists
    if (window[`terminal_${containerId}`]) {
        return window[`terminal_${containerId}`];
    }
    
    // Create new terminal
    const terminal = new DashboardTerminal(containerId, options);
    window[`terminal_${containerId}`] = terminal;
    return terminal;
}

// Make initTerminal available globally
window.initTerminal = initTerminal; 