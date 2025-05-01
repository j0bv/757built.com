/**
 * Document Explorer Component
 * Handles the document file system and navigation
 */
(function() {
    // Document explorer class
    class DocumentExplorer {
        constructor() {
            // DOM elements
            this.container = document.getElementById('document-explorer');
            
            // Document structure
            this.documentTree = [];
            
            // Initialize
            this.init();
        }
        
        /**
         * Initialize the explorer
         */
        init() {
            // Load document structure
            this.loadDocumentStructure()
                .then(() => {
                    // Render the explorer
                    this.renderExplorer();
                    
                    // Setup event listeners
                    this.setupEventListeners();
                })
                .catch(error => {
                    console.error('Error initializing document explorer:', error);
                    if (this.container) {
                        this.container.innerHTML = `<div class="error-message">Error loading documents: ${error.message}</div>`;
                    }
                });
        }
        
        /**
         * Load document structure from server
         * @returns {Promise} - Promise resolving to document structure
         */
        async loadDocumentStructure() {
            try {
                // Try to load document structure from server
                const response = await fetch('data/documents.json');
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                
                this.documentTree = await response.json();
                return this.documentTree;
            } catch (error) {
                console.error('Error loading document structure:', error);
                
                // If unable to load from server, use sample structure
                this.documentTree = [
                    {
                        id: 'documents',
                        name: 'Documents',
                        type: 'folder',
                        children: [
                            {
                                id: 'd3_visualization',
                                name: 'D3.js Visualization Guide',
                                type: 'markdown',
                                path: 'data/d3_visualization.md'
                            },
                            {
                                id: 'data',
                                name: 'Data Files',
                                type: 'folder',
                                children: [
                                    {
                                        id: 'sample_data',
                                        name: 'Country Data',
                                        type: 'csv',
                                        path: 'data/sample_data.csv'
                                    },
                                    {
                                        id: 'network_data',
                                        name: 'Network Data',
                                        type: 'json',
                                        path: 'data/network_data.json'
                                    }
                                ]
                            },
                            {
                                id: 'samples',
                                name: 'Sample Documents',
                                type: 'folder',
                                children: [
                                    {
                                        id: 'sample1',
                                        name: 'JavaScript Sample',
                                        type: 'code',
                                        language: 'javascript',
                                        path: 'data/sample_code.js'
                                    },
                                    {
                                        id: 'sample2',
                                        name: 'HTML Template',
                                        type: 'code',
                                        language: 'html',
                                        path: 'data/sample_template.html'
                                    }
                                ]
                            }
                        ]
                    }
                ];
                
                return this.documentTree;
            }
        }
        
        /**
         * Render the explorer
         */
        renderExplorer() {
            if (!this.container) return;
            
            // Clear container
            this.container.innerHTML = '';
            
            // Create file tree
            const fileTree = document.createElement('div');
            fileTree.className = 'file-tree';
            
            // Create root level
            const rootList = document.createElement('ul');
            rootList.className = 'tree-root';
            
            // Add each root item
            this.documentTree.forEach(item => {
                const rootItem = this.createTreeItem(item);
                rootList.appendChild(rootItem);
            });
            
            fileTree.appendChild(rootList);
            this.container.appendChild(fileTree);
        }
        
        /**
         * Create a tree item
         * @param {object} item - Item to create
         * @returns {HTMLElement} - Tree item element
         */
        createTreeItem(item) {
            const treeItem = document.createElement('li');
            treeItem.className = 'tree-item';
            treeItem.dataset.id = item.id;
            treeItem.dataset.type = item.type;
            if (item.path) treeItem.dataset.path = item.path;
            
            // Create item content
            const itemContent = document.createElement('div');
            itemContent.className = 'tree-item-content';
            
            // Add icon
            const icon = document.createElement('i');
            icon.className = 'fas';
            
            // Set icon based on item type
            if (item.type === 'folder') {
                icon.className += ' fa-folder';
                treeItem.classList.add('folder');
            } else {
                // Set icon based on file type
                switch (item.type) {
                    case 'markdown':
                        icon.className += ' fa-file-markdown';
                        break;
                    case 'pdf':
                        icon.className += ' fa-file-pdf';
                        break;
                    case 'code':
                        icon.className += ' fa-file-code';
                        break;
                    case 'image':
                        icon.className += ' fa-file-image';
                        break;
                    case 'csv':
                        icon.className += ' fa-file-csv';
                        break;
                    case 'json':
                        icon.className += ' fa-file-code';
                        break;
                    default:
                        icon.className += ' fa-file-alt';
                }
            }
            
            // Add name
            const name = document.createElement('span');
            name.className = 'tree-item-name';
            name.textContent = item.name;
            
            // Add to item content
            itemContent.appendChild(icon);
            itemContent.appendChild(name);
            treeItem.appendChild(itemContent);
            
            // Add children if folder
            if (item.type === 'folder' && item.children && item.children.length > 0) {
                const childList = document.createElement('ul');
                childList.className = 'tree-children';
                
                // Create child items
                item.children.forEach(child => {
                    const childItem = this.createTreeItem(child);
                    childList.appendChild(childItem);
                });
                
                treeItem.appendChild(childList);
                
                // Add expand/collapse
                const toggle = document.createElement('span');
                toggle.className = 'tree-toggle';
                toggle.innerHTML = '<i class="fas fa-caret-right"></i>';
                itemContent.insertBefore(toggle, icon);
            }
            
            return treeItem;
        }
        
        /**
         * Setup event listeners
         */
        setupEventListeners() {
            if (!this.container) return;
            
            // Folder toggle
            this.container.addEventListener('click', event => {
                const toggle = event.target.closest('.tree-toggle');
                if (toggle) {
                    const treeItem = toggle.closest('.tree-item');
                    if (treeItem) {
                        treeItem.classList.toggle('expanded');
                        
                        // Update toggle icon
                        const icon = toggle.querySelector('i');
                        if (icon) {
                            if (treeItem.classList.contains('expanded')) {
                                icon.className = 'fas fa-caret-down';
                                // Update folder icon
                                const folderIcon = toggle.nextElementSibling;
                                if (folderIcon && folderIcon.classList.contains('fa-folder')) {
                                    folderIcon.className = 'fas fa-folder-open';
                                }
                            } else {
                                icon.className = 'fas fa-caret-right';
                                // Update folder icon
                                const folderIcon = toggle.nextElementSibling;
                                if (folderIcon && folderIcon.classList.contains('fa-folder-open')) {
                                    folderIcon.className = 'fas fa-folder';
                                }
                            }
                        }
                    }
                }
            });
            
            // File click
            this.container.addEventListener('click', event => {
                const itemContent = event.target.closest('.tree-item-content');
                if (itemContent) {
                    const treeItem = itemContent.parentElement;
                    if (treeItem && treeItem.dataset.type !== 'folder') {
                        // Open document
                        this.openDocument(treeItem.dataset.id, treeItem.dataset.type, treeItem.querySelector('.tree-item-name').textContent, treeItem.dataset.path);
                    }
                }
            });
        }
        
        /**
         * Open a document
         * @param {string} id - Document ID
         * @param {string} type - Document type
         * @param {string} name - Document name
         * @param {string} path - Document path
         */
        openDocument(id, type, name, path) {
            // Check if document viewer exists
            if (window.documentViewer) {
                // Fetch document content
                fetch(path)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                        }
                        return response.text();
                    })
                    .then(content => {
                        // Open document in viewer
                        window.documentViewer.openDocument(id, type, name, content);
                    })
                    .catch(error => {
                        console.error('Error opening document:', error);
                        alert(`Error opening document: ${error.message}`);
                    });
            } else {
                console.error('Document viewer not available');
            }
        }
    }
    
    // Create global instance of DocumentExplorer
    window.documentExplorer = new DocumentExplorer();
})(); 