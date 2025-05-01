/**
 * Document Viewer Component
 * Handles document rendering, navigation, and analysis
 */
(function() {
    // Document viewer class
    class DocumentViewer {
        constructor() {
            // DOM elements
            this.container = document.getElementById('document-view-content');
            this.tabsContainer = document.getElementById('document-tabs');
            this.explorerContainer = document.getElementById('document-explorer');
            this.outlineContainer = document.getElementById('document-outline');
            
            // State management
            this.openDocuments = new Map(); // Map of open documents
            this.activeDocument = null; // Currently active document
            this.documentCache = new Map(); // Cache for document content
            
            // Initialize libraries
            this.initPdfjs();
            this.initMarkdownRenderer();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Configure syntax highlighting
            hljs.configure({
                languages: ['javascript', 'html', 'css', 'python', 'java', 'json', 'xml', 'markdown']
            });
        }
        
        /**
         * Initialize PDF.js library
         */
        initPdfjs() {
            // Set PDF.js worker path
            if (window.pdfjsLib) {
                window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
            }
        }
        
        /**
         * Initialize Markdown renderer
         */
        initMarkdownRenderer() {
            this.markdownRenderer = window.markdownit({
                html: true,
                linkify: true,
                typographer: true,
                highlight: function(str, lang) {
                    if (lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(str, { language: lang }).value;
                        } catch (__) {}
                    }
                    return ''; // Use external default escaping
                }
            });
        }
        
        /**
         * Setup event listeners
         */
        setupEventListeners() {
            // Document tabs click event
            if (this.tabsContainer) {
                this.tabsContainer.addEventListener('click', (e) => {
                    const tab = e.target.closest('.document-tab');
                    if (tab) {
                        const docId = tab.dataset.docId;
                        if (e.target.closest('.close-doc-tab')) {
                            this.closeDocument(docId);
                        } else {
                            this.activateDocument(docId);
                        }
                    }
                });
            }
            
            // Document actions
            document.querySelectorAll('.document-action').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = btn.getAttribute('title')?.toLowerCase() || '';
                    if (this.activeDocument) {
                        switch (action) {
                            case 'print':
                                this.printDocument(this.activeDocument);
                                break;
                            case 'download':
                                this.downloadDocument(this.activeDocument);
                                break;
                            case 'search':
                                this.toggleDocumentSearch();
                                break;
                            case 'visualize':
                                this.visualizeDocument(this.activeDocument);
                                break;
                            case 'compare':
                                this.showCompareModal();
                                break;
                            case 'share':
                                this.shareDocument(this.activeDocument);
                                break;
                            default:
                                console.log('Action not implemented:', action);
                        }
                    } else {
                        alert('Please open a document first.');
                    }
                });
            });
            
            // Explorer actions
            document.querySelectorAll('.document-sidebar .document-action').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = btn.getAttribute('title')?.toLowerCase() || '';
                    switch (action) {
                        case 'new file':
                            this.showNewFileModal();
                            break;
                        case 'upload file':
                            this.showUploadFileModal();
                            break;
                        case 'new folder':
                            this.showNewFolderModal();
                            break;
                        case 'refresh':
                            if (window.documentExplorer) {
                                window.documentExplorer.init();
                            }
                            break;
                        default:
                            console.log('Explorer action not implemented:', action);
                    }
                });
            });
            
            // Outline navigation
            if (this.outlineContainer) {
                this.outlineContainer.addEventListener('click', (e) => {
                    const outlineItem = e.target.closest('.outline-item');
                    if (outlineItem) {
                        const targetId = outlineItem.dataset.target;
                        this.scrollToElement(targetId);
                    }
                });
            }
            
            // Document tab in main tabs bar
            document.querySelector('.tab[data-tab="document-view"]')?.addEventListener('click', () => {
                // Ensure document explorer is initialized when tab is clicked
                if (window.documentExplorer) {
                    window.documentExplorer.init();
                }
            });
            
            // Main menu "Documents" dropdown
            document.querySelector('a[data-action="open-documents"]')?.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Find the document tab and activate it
                const documentTab = document.querySelector('.tab[data-tab="document-view"]');
                if (documentTab) {
                    // Remove active class from all tabs
                    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                    documentTab.classList.add('active');
                    
                    // Hide all tab content
                    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                    
                    // Show document view content
                    document.getElementById('document-view')?.classList.add('active');
                    
                    // Ensure document explorer is initialized
                    if (window.documentExplorer) {
                        window.documentExplorer.init();
                    }
                }
            });
        }
        
        /**
         * Initialize events when document is ready
         */
        initEvents() {
            // Attach all event listeners
            this.setupEventListeners();
            
            // Add method stubs for actions that aren't fully implemented
            this.downloadDocument = function(doc) {
                console.log('Downloading document:', doc.title);
                alert('Download started for: ' + doc.title);
                
                // Create a temporary link for download
                const a = document.createElement('a');
                const blob = new Blob([doc.content], {type: 'text/plain'});
                a.href = URL.createObjectURL(blob);
                a.download = doc.title;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            };
            
            this.toggleDocumentSearch = function() {
                console.log('Toggle search');
                alert('Search functionality coming soon!');
            };
            
            this.showCompareModal = function() {
                console.log('Show compare modal');
                alert('Document comparison coming soon!');
            };
            
            this.shareDocument = function(doc) {
                console.log('Share document:', doc.title);
                alert('Share link generated for: ' + doc.title);
            };
            
            this.showNewFileModal = function() {
                console.log('Show new file modal');
                alert('New file creation coming soon!');
            };
            
            this.showUploadFileModal = function() {
                console.log('Show upload file modal');
                alert('File upload coming soon!');
            };
            
            this.showNewFolderModal = function() {
                console.log('Show new folder modal');
                alert('New folder creation coming soon!');
            };
        }
        
        /**
         * Open a document
         * @param {string} docId - Document ID or path
         * @param {string} docType - Document type (pdf, markdown, code, etc.)
         * @param {string} docTitle - Document title
         * @param {string} docContent - Document content or URL
         */
        openDocument(docId, docType, docTitle, docContent) {
            // Check if document is already open
            if (this.openDocuments.has(docId)) {
                this.activateDocument(docId);
                return;
            }
            
            // Create document object
            const document = {
                id: docId,
                type: docType,
                title: docTitle,
                content: docContent
            };
            
            // Add to open documents
            this.openDocuments.set(docId, document);
            
            // Create tab
            this.createDocumentTab(document);
            
            // Set as active
            this.activateDocument(docId);
        }
        
        /**
         * Create a document tab
         * @param {object} document - Document object
         */
        createDocumentTab(document) {
            if (!this.tabsContainer) return;
            
            const tab = document.createElement('div');
            tab.className = 'document-tab';
            tab.dataset.docId = document.id;
            
            // Set icon based on document type
            let icon = 'fa-file-alt';
            switch (document.type) {
                case 'pdf':
                    icon = 'fa-file-pdf';
                    break;
                case 'markdown':
                    icon = 'fa-file-markdown';
                    break;
                case 'code':
                    icon = 'fa-file-code';
                    break;
                case 'image':
                    icon = 'fa-file-image';
                    break;
                case 'csv':
                case 'excel':
                    icon = 'fa-file-csv';
                    break;
                case 'json':
                    icon = 'fa-file-code';
                    break;
            }
            
            tab.innerHTML = `
                <i class="fas ${icon}"></i>
                <span class="tab-title">${document.title}</span>
                <button class="close-doc-tab"><i class="fas fa-times"></i></button>
            `;
            
            this.tabsContainer.appendChild(tab);
        }
        
        /**
         * Activate a document
         * @param {string} docId - Document ID
         */
        activateDocument(docId) {
            // Check if document exists
            if (!this.openDocuments.has(docId)) return;
            
            // Set active document
            this.activeDocument = this.openDocuments.get(docId);
            
            // Update tabs
            if (this.tabsContainer) {
                this.tabsContainer.querySelectorAll('.document-tab').forEach(tab => {
                    tab.classList.remove('active');
                    if (tab.dataset.docId === docId) {
                        tab.classList.add('active');
                    }
                });
            }
            
            // Render document
            this.renderDocument(this.activeDocument);
            
            // Generate document outline
            this.generateOutline(this.activeDocument);
        }
        
        /**
         * Close a document
         * @param {string} docId - Document ID
         */
        closeDocument(docId) {
            // Check if document exists
            if (!this.openDocuments.has(docId)) return;
            
            // Remove from open documents
            this.openDocuments.delete(docId);
            
            // Remove tab
            if (this.tabsContainer) {
                const tab = this.tabsContainer.querySelector(`.document-tab[data-doc-id="${docId}"]`);
                if (tab) tab.remove();
            }
            
            // If active document was closed, activate another one
            if (this.activeDocument && this.activeDocument.id === docId) {
                if (this.openDocuments.size > 0) {
                    const nextDocId = Array.from(this.openDocuments.keys())[0];
                    this.activateDocument(nextDocId);
                } else {
                    this.activeDocument = null;
                    this.showEmptyState();
                }
            }
        }
        
        /**
         * Show empty state when no documents are open
         */
        showEmptyState() {
            if (this.container) {
                this.container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-file-alt fa-3x"></i>
                        <p>Select a document to view</p>
                    </div>
                `;
            }
            
            // Clear outline
            if (this.outlineContainer) {
                this.outlineContainer.innerHTML = '';
            }
        }
        
        /**
         * Render document based on type
         * @param {object} document - Document object
         */
        renderDocument(document) {
            if (!this.container) return;
            
            // Clear container
            this.container.innerHTML = '';
            
            // Render based on document type
            switch (document.type) {
                case 'pdf':
                    this.renderPdfDocument(document);
                    break;
                case 'markdown':
                    this.renderMarkdownDocument(document);
                    break;
                case 'code':
                    this.renderCodeDocument(document);
                    break;
                case 'image':
                    this.renderImageDocument(document);
                    break;
                case 'csv':
                    this.renderCsvDocument(document);
                    break;
                case 'json':
                    this.renderJsonDocument(document);
                    break;
                default:
                    this.renderTextDocument(document);
            }
        }
        
        /**
         * Render PDF document
         * @param {object} document - Document object
         */
        renderPdfDocument(document) {
            // Create PDF viewer container
            const viewerContainer = document.createElement('div');
            viewerContainer.id = 'pdf-viewer';
            viewerContainer.className = 'pdf-viewer';
            this.container.appendChild(viewerContainer);
            
            // Use PDF.js to render PDF
            if (window.pdfjsLib) {
                const loadingTask = pdfjsLib.getDocument(document.content);
                loadingTask.promise.then(pdf => {
                    // PDF loaded successfully
                    console.log('PDF loaded');
                    
                    // Get first page
                    pdf.getPage(1).then(page => {
                        const scale = 1.5;
                        const viewport = page.getViewport({ scale });
                        
                        // Prepare canvas
                        const canvas = document.createElement('canvas');
                        const context = canvas.getContext('2d');
                        canvas.height = viewport.height;
                        canvas.width = viewport.width;
                        
                        viewerContainer.appendChild(canvas);
                        
                        // Render PDF page
                        const renderContext = {
                            canvasContext: context,
                            viewport: viewport
                        };
                        
                        page.render(renderContext);
                    });
                }, error => {
                    console.error('Error loading PDF:', error);
                    this.container.innerHTML = `<div class="error-message">Error loading PDF: ${error.message}</div>`;
                });
            } else {
                this.container.innerHTML = `
                    <div class="error-message">
                        <p>PDF.js library not loaded. Cannot display PDF document.</p>
                    </div>
                `;
            }
        }
        
        /**
         * Render Markdown document
         * @param {object} document - Document object
         */
        renderMarkdownDocument(document) {
            // Create markdown container
            const markdownContainer = document.createElement('div');
            markdownContainer.className = 'markdown-content';
            
            // Render markdown
            if (this.markdownRenderer) {
                // Convert markdown to HTML
                const htmlContent = this.markdownRenderer.render(document.content);
                markdownContainer.innerHTML = htmlContent;
                
                // Apply syntax highlighting to code blocks
                markdownContainer.querySelectorAll('pre code').forEach(block => {
                    hljs.highlightElement(block);
                });
            } else {
                markdownContainer.innerHTML = `<pre>${document.content}</pre>`;
            }
            
            this.container.appendChild(markdownContainer);
        }
        
        /**
         * Render code document with syntax highlighting
         * @param {object} document - Document object
         */
        renderCodeDocument(document) {
            // Get language from file extension
            const fileExtension = document.title.split('.').pop().toLowerCase();
            let language = 'plaintext';
            
            // Map common extensions to languages
            const extensionMap = {
                'js': 'javascript',
                'html': 'html',
                'css': 'css',
                'py': 'python',
                'java': 'java',
                'json': 'json',
                'xml': 'xml',
                'md': 'markdown'
            };
            
            if (extensionMap[fileExtension]) {
                language = extensionMap[fileExtension];
            }
            
            // Create code editor container
            const codeContainer = document.createElement('div');
            codeContainer.className = 'code-viewer';
            
            if (window.CodeMirror) {
                // Use CodeMirror for better editing experience
                const editor = CodeMirror(codeContainer, {
                    value: document.content,
                    mode: language,
                    theme: 'default',
                    lineNumbers: true,
                    readOnly: true
                });
            } else {
                // Fallback to highlight.js
                const pre = document.createElement('pre');
                const code = document.createElement('code');
                code.className = `language-${language}`;
                code.textContent = document.content;
                pre.appendChild(code);
                codeContainer.appendChild(pre);
                
                hljs.highlightElement(code);
            }
            
            this.container.appendChild(codeContainer);
        }
        
        /**
         * Render image document
         * @param {object} document - Document object
         */
        renderImageDocument(document) {
            const imageContainer = document.createElement('div');
            imageContainer.className = 'image-viewer';
            
            const img = document.createElement('img');
            img.src = document.content;
            img.alt = document.title;
            
            imageContainer.appendChild(img);
            this.container.appendChild(imageContainer);
            
            // Initialize viewer.js for image zoom and pan
            if (window.Viewer) {
                new Viewer(img, {
                    inline: true,
                    navbar: false,
                    toolbar: {
                        zoomIn: true,
                        zoomOut: true,
                        oneToOne: true,
                        reset: true,
                        rotateLeft: true,
                        rotateRight: true
                    }
                });
            }
        }
        
        /**
         * Render CSV document as a table
         * @param {object} document - Document object
         */
        renderCsvDocument(document) {
            const tableContainer = document.createElement('div');
            tableContainer.className = 'table-viewer';
            
            // Parse CSV data
            let rows = [];
            if (typeof document.content === 'string') {
                rows = d3.csvParse(document.content);
            } else if (Array.isArray(document.content)) {
                rows = document.content;
            }
            
            if (rows.length > 0) {
                // Get column headers
                const columns = Object.keys(rows[0]);
                
                // Create table
                const table = document.createElement('table');
                table.className = 'data-table';
                
                // Create table header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                columns.forEach(column => {
                    const th = document.createElement('th');
                    th.textContent = column;
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Create table body
                const tbody = document.createElement('tbody');
                rows.forEach(row => {
                    const tr = document.createElement('tr');
                    columns.forEach(column => {
                        const td = document.createElement('td');
                        td.textContent = row[column];
                        tr.appendChild(td);
                    });
                    tbody.appendChild(tr);
                });
                table.appendChild(tbody);
                
                tableContainer.appendChild(table);
            } else {
                tableContainer.innerHTML = '<p>No data available</p>';
            }
            
            this.container.appendChild(tableContainer);
        }
        
        /**
         * Render JSON document with syntax highlighting and collapsible sections
         * @param {object} document - Document object
         */
        renderJsonDocument(document) {
            const jsonContainer = document.createElement('div');
            jsonContainer.className = 'json-viewer';
            
            // Parse JSON data if it's a string
            let jsonData = document.content;
            if (typeof document.content === 'string') {
                try {
                    jsonData = JSON.parse(document.content);
                } catch (e) {
                    jsonContainer.innerHTML = `<div class="error-message">Invalid JSON: ${e.message}</div>`;
                    this.container.appendChild(jsonContainer);
                    return;
                }
            }
            
            // Format JSON with indentation
            const formattedJson = JSON.stringify(jsonData, null, 2);
            
            // Create pre and code elements
            const pre = document.createElement('pre');
            const code = document.createElement('code');
            code.className = 'language-json';
            code.textContent = formattedJson;
            pre.appendChild(code);
            
            jsonContainer.appendChild(pre);
            this.container.appendChild(jsonContainer);
            
            // Apply syntax highlighting
            hljs.highlightElement(code);
        }
        
        /**
         * Render plain text document
         * @param {object} document - Document object
         */
        renderTextDocument(document) {
            const textContainer = document.createElement('div');
            textContainer.className = 'text-viewer';
            
            const pre = document.createElement('pre');
            pre.textContent = document.content;
            
            textContainer.appendChild(pre);
            this.container.appendChild(textContainer);
        }
        
        /**
         * Generate document outline from headings
         * @param {object} document - Document object
         */
        generateOutline(document) {
            if (!this.outlineContainer) return;
            
            // Clear outline container
            this.outlineContainer.innerHTML = '<h3>Document Outline</h3>';
            
            if (document.type === 'markdown') {
                // Create outline from markdown headings
                const headings = this.container.querySelectorAll('h1, h2, h3, h4, h5, h6');
                if (headings.length > 0) {
                    const outlineList = document.createElement('ul');
                    outlineList.className = 'outline-list';
                    
                    headings.forEach((heading, index) => {
                        // Add ID to heading if not exists
                        if (!heading.id) {
                            heading.id = `heading-${index}`;
                        }
                        
                        // Create outline item
                        const item = document.createElement('li');
                        item.className = `outline-item level-${heading.tagName.toLowerCase()}`;
                        item.dataset.target = heading.id;
                        item.innerHTML = heading.textContent;
                        
                        outlineList.appendChild(item);
                    });
                    
                    this.outlineContainer.appendChild(outlineList);
                } else {
                    this.outlineContainer.innerHTML += '<p>No headings found</p>';
                }
            } else if (document.type === 'pdf') {
                this.outlineContainer.innerHTML += '<p>PDF outline not implemented</p>';
            } else {
                this.outlineContainer.innerHTML += '<p>No outline available</p>';
            }
        }
        
        /**
         * Scroll to element by ID
         * @param {string} elementId - Element ID
         */
        scrollToElement(elementId) {
            const element = document.getElementById(elementId);
            if (element && this.container) {
                this.container.scrollTo({
                    top: element.offsetTop - 20,
                    behavior: 'smooth'
                });
                
                // Highlight element temporarily
                element.classList.add('highlight-element');
                setTimeout(() => {
                    element.classList.remove('highlight-element');
                }, 2000);
            }
        }
        
        /**
         * Print current document
         * @param {object} doc - Document to print
         */
        printDocument(doc) {
            if (!doc) return;
            
            console.log('Printing document:', doc.title);
            
            // Create a new window for printing
            const printWindow = window.open('', '_blank');
            
            if (printWindow) {
                printWindow.document.write(`
                    <html>
                        <head>
                            <title>Print: ${doc.title}</title>
                            <style>
                                body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
                                pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; }
                                .hljs { background: #f5f5f5; }
                                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                                th { background-color: #f2f2f2; }
                                h1, h2, h3 { color: #333; }
                                code { background-color: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
                            </style>
                        </head>
                        <body>
                            ${this.container?.innerHTML || `<h1>${doc.title}</h1><pre>${doc.content}</pre>`}
                        </body>
                    </html>
                `);
                
                printWindow.document.close();
                printWindow.focus();
                setTimeout(() => {
                    printWindow.print();
                }, 250);
            } else {
                alert('Unable to open print window. Please check your browser settings.');
            }
        }
        
        /**
         * Create a document visualization using D3.js
         */
        visualizeDocument() {
            if (!this.activeDocument) return;
            
            // Get visualizer modal
            const modal = document.getElementById('document-preview-modal');
            if (!modal) return;
            
            // Set modal title
            const titleElement = modal.querySelector('#preview-document-title');
            if (titleElement) {
                titleElement.textContent = `Visualize: ${this.activeDocument.title}`;
            }
            
            // Get container
            const container = modal.querySelector('#document-preview-container');
            if (!container) return;
            
            // Clear container
            container.innerHTML = '';
            
            // Create visualization based on document type
            if (this.activeDocument.type === 'csv' || this.activeDocument.type === 'json') {
                // Create visualization options
                container.innerHTML = `
                    <div class="visualization-options">
                        <div class="form-group">
                            <label for="vis-type">Visualization Type:</label>
                            <select id="vis-type">
                                <option value="bar">Bar Chart</option>
                                <option value="line">Line Chart</option>
                                <option value="pie">Pie Chart</option>
                                <option value="scatter">Scatter Plot</option>
                            </select>
                        </div>
                        <div class="vis-config-container"></div>
                        <button id="create-visualization-btn" class="modal-btn">Create Visualization</button>
                    </div>
                    <div class="visualization-preview" id="visualization-preview"></div>
                `;
                
                // Initialize data visualizer
                if (window.DataVisualizer) {
                    const visualizer = new DataVisualizer('visualization-preview');
                    
                    // Setup visualization creation
                    const createButton = container.querySelector('#create-visualization-btn');
                    if (createButton) {
                        createButton.addEventListener('click', () => {
                            const visType = container.querySelector('#vis-type').value;
                            const config = {
                                width: 800,
                                height: 500
                            };
                            
                            visualizer.createVisualization(visType, config);
                        });
                    }
                } else {
                    container.innerHTML = '<p>Data Visualizer not available</p>';
                }
            } else if (this.activeDocument.type === 'markdown' || this.activeDocument.type === 'text') {
                // Create word frequency analysis
                container.innerHTML = '<div id="word-freq-chart"></div>';
                this.createWordFrequencyChart(this.activeDocument.content);
            } else {
                container.innerHTML = '<p>Visualization not available for this document type</p>';
            }
            
            // Show modal
            modal.style.display = 'block';
        }
        
        /**
         * Create word frequency chart for text document
         * @param {string} text - Text content
         */
        createWordFrequencyChart(text) {
            // Get chart container
            const container = document.getElementById('word-freq-chart');
            if (!container) return;
            
            // Process text
            const words = text.toLowerCase()
                .replace(/[^\w\s]/g, '')
                .split(/\s+/)
                .filter(word => word.length > 3);
            
            // Count word frequency
            const wordCount = {};
            words.forEach(word => {
                if (wordCount[word]) {
                    wordCount[word]++;
                } else {
                    wordCount[word] = 1;
                }
            });
            
            // Convert to array and sort
            const wordArray = Object.entries(wordCount)
                .map(([word, count]) => ({ word, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, 20);
            
            // Create chart with D3.js
            if (d3) {
                const margin = { top: 30, right: 30, bottom: 70, left: 60 };
                const width = 800 - margin.left - margin.right;
                const height = 400 - margin.top - margin.bottom;
                
                // Create SVG
                const svg = d3.select(container)
                    .append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                    .attr("transform", `translate(${margin.left},${margin.top})`);
                
                // Set up X axis
                const x = d3.scaleBand()
                    .range([0, width])
                    .domain(wordArray.map(d => d.word))
                    .padding(0.2);
                
                svg.append("g")
                    .attr("transform", `translate(0,${height})`)
                    .call(d3.axisBottom(x))
                    .selectAll("text")
                    .attr("transform", "translate(-10,0)rotate(-45)")
                    .style("text-anchor", "end");
                
                // Set up Y axis
                const y = d3.scaleLinear()
                    .domain([0, d3.max(wordArray, d => d.count) * 1.1])
                    .range([height, 0]);
                
                svg.append("g")
                    .call(d3.axisLeft(y));
                
                // Add bars
                svg.selectAll("mybar")
                    .data(wordArray)
                    .enter()
                    .append("rect")
                    .attr("x", d => x(d.word))
                    .attr("y", d => y(d.count))
                    .attr("width", x.bandwidth())
                    .attr("height", d => height - y(d.count))
                    .attr("fill", "#4285F4");
                
                // Add title
                svg.append("text")
                    .attr("x", width / 2)
                    .attr("y", -10)
                    .attr("text-anchor", "middle")
                    .text("Word Frequency Analysis");
            } else {
                container.innerHTML = '<p>D3.js not available for visualization</p>';
            }
        }
    }
    
    // Create global instance of DocumentViewer
    window.documentViewer = new DocumentViewer();
    
    // Document ready function
    function onDocumentReady() {
        // Initialize the document viewer with sample documents if available
        const viewer = window.documentViewer;
        
        // Initialize events
        viewer.initEvents();
        
        // Sample Markdown document
        fetch('data/d3_visualization.md')
            .then(response => response.text())
            .then(content => {
                viewer.openDocument('d3_visualization', 'markdown', 'D3.js Visualization Guide', content);
            })
            .catch(error => console.error('Error loading sample document:', error));
        
        // Initialize tabs functionality for main dashboard tabs
        const tabs = document.querySelectorAll('.tabs .tab');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.getAttribute('data-tab');
                
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Hide all tab contents
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Show clicked tab content
                document.getElementById(tabId)?.classList.add('active');
                
                // If document view tab is activated, ensure explorer is initialized
                if (tabId === 'document-view' && window.documentExplorer) {
                    window.documentExplorer.init();
                }
            });
        });
    }
    
    // Initialize document viewer when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', onDocumentReady);
    } else {
        onDocumentReady();
    }
})(); 