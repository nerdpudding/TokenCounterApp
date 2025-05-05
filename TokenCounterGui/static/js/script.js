document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const directoryBrowser = document.getElementById('directory-browser');
    const drivesBrowser = document.getElementById('drives-browser');
    const drivesList = document.getElementById('drives-list');
    // const currentPathInput = document.getElementById('current-path'); // Removed this element
    const selectedPathInput = document.getElementById('selected-path');
    const analyzeBtn = document.getElementById('analyze-btn');
    const refreshDirBtn = document.getElementById('refresh-dir');
    const showDrivesBtn = document.getElementById('show-drives-btn');
    const drivesInitBtn = document.getElementById('drives-init-btn');
    const pathApplyBtn = document.getElementById('path-apply-btn');
    const pathBreadcrumb = document.getElementById('path-breadcrumb');
    const breadcrumbList = document.querySelector('#path-breadcrumb ol');
    const themeToggle = document.getElementById('theme-toggle');
    
    // Results containers
    const welcomeContainer = document.getElementById('welcome-container');
    const loadingContainer = document.getElementById('loading-container');
    const resultsContainer = document.getElementById('results-container');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    
    // Result display elements
    const totalTokensElement = document.getElementById('total-tokens');
    const extensionsTable = document.getElementById('extensions-table');
    const technologiesTable = document.getElementById('technologies-table');
    
    // Advanced options
    const excludeTests = document.getElementById('exclude-tests');
    const excludeDocs = document.getElementById('exclude-docs');
    const excludeDependencies = document.getElementById('exclude-dependencies');
    
    // Theme handling
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeToggle.checked = true;
    }
    
    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Event listeners
    showDrivesBtn.addEventListener('click', toggleDrivesBrowser);
    drivesInitBtn.addEventListener('click', toggleDrivesBrowser);
    refreshDirBtn.addEventListener('click', refreshCurrentDirectory);
    
    // Apply manually entered path
    pathApplyBtn.addEventListener('click', function() {
        const manualPath = selectedPathInput.value.trim();
        if (manualPath) {
            // Enable analyze button
            analyzeBtn.disabled = false;
            
            // Check if this is a directory and navigate to it if possible
            fetch('/browse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: manualPath })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    // If it's a valid directory, navigate to it
                    loadDirectory(manualPath);
                }
            })
            .catch(() => {
                // Even if it fails (might be a file path), we still allow analysis
                console.log("Manually entered path will be used for analysis");
            });
        }
    });
    
    // Allow pressing Enter in the path input to apply the path
    selectedPathInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            pathApplyBtn.click();
        }
    });
    
    analyzeBtn.addEventListener('click', function() {
        if (selectedPathInput.value) {
            analyzeRepository(selectedPathInput.value);
        }
    });
    
    // Toggle drives browser visibility
    function toggleDrivesBrowser() {
        if (drivesBrowser.style.display === 'none') {
            drivesBrowser.style.display = 'block';
            loadDrives();
        } else {
            drivesBrowser.style.display = 'none';
        }
    }
    
    // Load available drives
    function loadDrives() {
        drivesList.innerHTML = `
            <div class="text-center p-3">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading drives...</span>
            </div>
        `;
        
        fetch('/get-drives')
            .then(response => response.json())
            .then(drives => {
                drivesList.innerHTML = '';
                
                if (drives.length === 0) {
                    drivesList.innerHTML = '<div class="alert alert-warning">No drives found</div>';
                    return;
                }
                
                drives.forEach(drive => {
                    const driveItem = document.createElement('button');
                    driveItem.className = 'list-group-item list-group-item-action d-flex align-items-center';
                    driveItem.innerHTML = `
                        <i class="bi bi-${drive.icon} me-2"></i>
                        <span>${drive.name}</span>
                    `;
                    
                    driveItem.addEventListener('click', function() {
                        loadDirectory(drive.path);
                        drivesBrowser.style.display = 'none'; // Hide drives after selection
                    });
                    
                    drivesList.appendChild(driveItem);
                });
            })
            .catch(error => {
                drivesList.innerHTML = `<div class="alert alert-danger">Error loading drives: ${error.message}</div>`;
            });
    }
    
    // Refresh current directory (Now refreshes based on selected path if available, else root)
    function refreshCurrentDirectory() {
        const path_to_refresh = selectedPathInput.value || '/'; // Use selected path or default to root
        loadDirectory(path_to_refresh);
    }
    
    // Load directory contents
    function loadDirectory(path) {
        directoryBrowser.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        fetch('/browse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                directoryBrowser.innerHTML = `
                    <div class="alert alert-danger m-3">
                        <i class="bi bi-exclamation-triangle me-2"></i>${data.error}
                    </div>`;
                return;
            }

            // currentPathInput.value = data.current_path; // Removed reference
            displayDirectoryContents(data);
            updateBreadcrumbs(data.current_path, data.path_parts);
        })
        .catch(error => {
            directoryBrowser.innerHTML = `
                <div class="alert alert-danger m-3">
                    <i class="bi bi-exclamation-triangle me-2"></i>Error: ${error.message}
                </div>`;
        });
    }
    
    // Display directory contents
    function displayDirectoryContents(data) {
        // Clear the directory browser
        directoryBrowser.innerHTML = '';
        
        // Create a list to hold all the items
        const itemsList = document.createElement('div');
        itemsList.className = 'list-group list-group-flush';
        
        // No items found
        if (data.items.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'text-center p-3';
            emptyMessage.innerHTML = `
                <i class="bi bi-folder2-open fs-4 mb-2 d-block"></i>
                <p>This directory is empty</p>
            `;
            directoryBrowser.appendChild(emptyMessage);
            return;
        }
        
        // Add each item to the list
        data.items.forEach(item => {
            const itemElement = document.createElement('button');
            itemElement.type = 'button';
            
            // Different styling based on item type
            if (item.is_dir) {
                if (item.is_parent) {
                    // Parent directory
                    itemElement.className = 'list-group-item list-group-item-action d-flex align-items-center parent-dir';
                    itemElement.innerHTML = `
                        <i class="bi bi-arrow-up-circle me-2"></i>
                        <span>Parent Directory</span>
                    `;
                } else {
                    // Regular directory
                    // Regular directory - Simplified: No separate select button
                    itemElement.className = 'list-group-item list-group-item-action d-flex align-items-center';
                    itemElement.innerHTML = `
                        <i class="bi bi-folder me-2"></i>
                        <span>${item.name}</span>
                    `;
                }

                // Directory click: Selects AND navigates
                itemElement.addEventListener('click', function(e) {
                    e.preventDefault(); // Prevent any default button behavior
                    if (!item.is_parent) { // Don't select parent dir, just navigate
                        selectDirectory(item.path, item.name);
                    }
                    loadDirectory(item.path); // Navigate into dir (or parent)
                });

                // Removed contextmenu listener for directories
            } else {
                // Regular file (now selectable)
                itemElement.className = 'list-group-item list-group-item-action d-flex align-items-center';
                
                // Try to determine file type by extension
                const extension = item.name.split('.').pop().toLowerCase();
                let icon = 'file';
                
                // File type icons based on extension
                if (['js', 'ts', 'jsx', 'tsx'].includes(extension)) icon = 'filetype-js';
                else if (['py', 'ipynb'].includes(extension)) icon = 'filetype-py';
                else if (['html', 'htm'].includes(extension)) icon = 'filetype-html';
                else if (['css', 'scss', 'sass'].includes(extension)) icon = 'filetype-css';
                else if (['json'].includes(extension)) icon = 'filetype-json';
                else if (['md', 'markdown'].includes(extension)) icon = 'filetype-md';
                else if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(extension)) icon = 'file-image';
                else if (['pdf'].includes(extension)) icon = 'file-pdf';
                else if (['doc', 'docx'].includes(extension)) icon = 'file-word';
                else if (['xls', 'xlsx'].includes(extension)) icon = 'file-excel';
                else if (['ppt', 'pptx'].includes(extension)) icon = 'file-ppt';
                
                itemElement.innerHTML = `
                    <i class="bi bi-${icon} me-2"></i>
                    <span>${item.name}</span>
                `;
                
                // File selection with click or right-click
                itemElement.addEventListener('click', function(e) {
                    e.preventDefault();
                    selectFile(item.path, item.name);
                });
                
                // Removed contextmenu listener for files
            }
            
            itemsList.appendChild(itemElement);
        });
        
        directoryBrowser.appendChild(itemsList);
    }
    
    // Update breadcrumb navigation
    function updateBreadcrumbs(currentPath, pathParts) {
        if (currentPath === '') {
            pathBreadcrumb.style.display = 'none';
            return;
        }
        
        pathBreadcrumb.style.display = 'block';
        breadcrumbList.innerHTML = '';
        
        // Add root
        const rootItem = document.createElement('li');
        rootItem.className = 'breadcrumb-item';
        const rootLink = document.createElement('a');
        rootLink.href = '#';
        rootLink.textContent = 'Root';
        rootLink.addEventListener('click', function(e) {
            e.preventDefault();
            loadDirectory('/');
        });
        rootItem.appendChild(rootLink);
        breadcrumbList.appendChild(rootItem);
        
        // Build the path incrementally
        let buildPath = '';
        pathParts.filter(part => part).forEach((part, index, parts) => {
            buildPath += '/' + part;
            
            const item = document.createElement('li');
            item.className = 'breadcrumb-item';
            
            // Last item is active
            if (index === parts.length - 1) {
                item.classList.add('active');
                item.textContent = part;
            } else {
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = part;
                // Capture the correct path for this specific link
                const pathToLoad = buildPath;
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    console.log('Navigating to breadcrumb path:', pathToLoad); // Debugging line
                    loadDirectory(pathToLoad);
                });
                item.appendChild(link);
            }
            
            breadcrumbList.appendChild(item);
        });
    }
    
    // Select directory for analysis
    function selectDirectory(path, name) {
        selectedPathInput.value = path;
        analyzeBtn.disabled = false;
        
        // Highlight the selected item visually
        document.querySelectorAll('.list-group-item').forEach(item => {
            item.classList.remove('active');
            if (item.querySelector('span').textContent === name) {
                item.classList.add('active');
            }
        });
        // Removed toast notification
    }

    // Select file for analysis
    function selectFile(path, name) {
        selectedPathInput.value = path;
        analyzeBtn.disabled = false;

        // Highlight the selected item visually
        document.querySelectorAll('.list-group-item').forEach(item => {
            item.classList.remove('active');
            // Ensure item has a span before trying to access textContent
            const span = item.querySelector('span');
            if (span && span.textContent === name) {
                item.classList.add('active');
            }
        });
        // Removed toast notification
    }
    
    // Analyze repository
    function analyzeRepository(path) {
        // Show loading indicator
        welcomeContainer.style.display = 'none';
        resultsContainer.style.display = 'none';
        errorContainer.style.display = 'none';
        loadingContainer.style.display = 'block';
        
        // Get advanced options
        const options = {
            excludeTests: excludeTests.checked,
            excludeDocs: excludeDocs.checked,
            excludeDependencies: excludeDependencies.checked
        };
        
        // Call API to analyze repository
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                directory: path,
                options: options
            }),
        })
        .then(response => response.json())
        .then(data => {
            loadingContainer.style.display = 'none';
            
            if (data.error) {
                errorMessage.textContent = data.error;
                errorContainer.style.display = 'block';
                return;
            }
            
            displayResults(data);
            resultsContainer.style.display = 'block';
        })
        .catch(error => {
            loadingContainer.style.display = 'none';
            errorMessage.textContent = `Error: ${error.message}`;
            errorContainer.style.display = 'block';
        });
    }
    
    // Display analysis results
    function displayResults(data) {
        // Update total tokens
        totalTokensElement.textContent = data.total_tokens_formatted;
        
        // Update extensions table
        extensionsTable.innerHTML = '';
        data.extensions.forEach(ext => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ext.extension}</td>
                <td>${ext.tokens_formatted}</td>
                <td>${ext.files_text}</td>
            `;
            extensionsTable.appendChild(row);
        });
        
        // Update technologies table
        technologiesTable.innerHTML = '';
        data.technologies.forEach(tech => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${tech.technology}</td>
                <td>${tech.tokens_formatted}</td>
                <td>${tech.files_text}</td>
            `;
            technologiesTable.appendChild(row);
        });
        
        // Update model percentages
        document.querySelectorAll('.model-progress').forEach(progress => {
            const modelName = progress.dataset.model;
            const modelData = data.models[modelName];
            
            if (modelData) {
                const progressBar = progress.querySelector('.progress-bar');
                progressBar.style.width = `${Math.min(100, modelData.percentage)}%`;
                progressBar.textContent = `${modelData.percentage}%`;
                progressBar.classList.add(`bg-${modelData.color}`);
                progressBar.setAttribute('aria-valuenow', modelData.percentage);
            }
        });
    }
});