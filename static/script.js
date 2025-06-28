// Pivot Codex V5 - Frontend JavaScript
// Modern, responsive interface for advanced pivot table creation

class PivotCodex {
    constructor() {
        this.sessionId = 'default';
        this.currentData = null;
        this.pivotConfigs = [];
        this.activePivotId = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupKeyboardShortcuts();
        this.loadSavedState();
    }
    
    setupEventListeners() {
        // File upload
        document.getElementById('selectFileBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        
        document.getElementById('fileInput').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadFile(e.target.files[0]);
            }
        });
        
        // Header actions
        document.getElementById('saveViewsBtn').addEventListener('click', () => {
            this.saveViews();
        });
        
        document.getElementById('loadViewsBtn').addEventListener('click', () => {
            this.loadViews();
        });
        
        // Pivot management
        document.getElementById('addPivotBtn').addEventListener('click', () => {
            this.addNewPivot();
        });
        
        // Copy filters
        document.getElementById('copyFiltersBtn').addEventListener('click', () => {
            this.copyFilters();
        });
        
        // Pivot configuration
        document.getElementById('pivotNameInput').addEventListener('input', () => {
            this.updateActivePivotName();
        });
        
        document.getElementById('generatePivotBtn').addEventListener('click', () => {
            this.generatePivot();
        });
        
        document.getElementById('deletePivotBtn').addEventListener('click', () => {
            this.deleteActivePivot();
        });
        
        // Advanced options
        document.getElementById('fillValueEnabled').addEventListener('change', (e) => {
            document.getElementById('customFillValue').disabled = !e.target.checked;
        });
        
        document.getElementById('marginsEnabled').addEventListener('change', (e) => {
            document.getElementById('marginsName').disabled = !e.target.checked;
        });
        
        // Value aggregation
        document.getElementById('addValueAggBtn').addEventListener('click', () => {
            this.addValueAggregation();
        });
        
        // Filters
        document.getElementById('addFilterBtn').addEventListener('click', () => {
            this.addFilter();
        });
        
        // Download buttons
        document.getElementById('downloadCsvBtn').addEventListener('click', () => {
            this.downloadFile('pivot_csv');
        });
        
        document.getElementById('downloadCodeBtn').addEventListener('click', () => {
            this.downloadFile('python_code');
        });
        
        document.getElementById('downloadFilteredBtn').addEventListener('click', () => {
            this.downloadFile('filtered_csv');
        });
    }
    
    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });
        
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.uploadFile(files[0]);
            }
        }, false);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+S to save views
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveViews();
            }
            
            // Ctrl+O to load views
            if (e.ctrlKey && e.key === 'o') {
                e.preventDefault();
                this.loadViews();
            }
            
            // Ctrl+N to add new pivot
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                if (this.currentData) {
                    this.addNewPivot();
                }
            }
            
            // Enter to generate pivot
            if (e.key === 'Enter' && e.ctrlKey && this.activePivotId) {
                e.preventDefault();
                this.generatePivot();
            }
            
            // Delete to remove active pivot
            if (e.key === 'Delete' && e.shiftKey && this.activePivotId) {
                e.preventDefault();
                this.deleteActivePivot();
            }
        });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    async uploadFile(file) {
        if (!file.name.endsWith('.csv')) {
            this.showToast('Please upload a CSV file', 'error');
            return;
        }
        
        this.showLoading('Uploading and processing file...');
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', this.sessionId);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentData = result;
                this.updateDataInfo(result);
                this.showWelcomeScreen(false);
                this.showToast(`File uploaded successfully! ${result.shape[0]} rows, ${result.shape[1]} columns`, 'success');
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            this.showError(`Upload failed: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    updateDataInfo(data) {
        document.getElementById('fileName').textContent = data.filename;
        document.getElementById('dataRows').textContent = data.shape[0].toLocaleString();
        document.getElementById('dataColumns').textContent = data.shape[1];
        document.getElementById('dataInfo').style.display = 'block';
        document.getElementById('pivotManagement').style.display = 'block';
    }
    
    showWelcomeScreen(show = true) {
        document.getElementById('welcomeScreen').style.display = show ? 'block' : 'none';
        document.getElementById('pivotConfig').style.display = show ? 'none' : 'block';
    }
    
    async addNewPivot() {
        if (!this.currentData) {
            this.showToast('Please upload data first', 'warning');
            return;
        }
        
        this.showLoading('Creating new pivot...');
        
        try {
            const response = await fetch(`/api/pivots/${this.sessionId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                await this.loadPivots();
                this.setActivePivot(result.pivot_id);
                this.showToast('New pivot created', 'success');
            } else {
                throw new Error('Failed to create pivot');
            }
        } catch (error) {
            this.showError(`Failed to create pivot: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    async loadPivots() {
        try {
            const response = await fetch(`/api/pivots/${this.sessionId}`);
            const pivots = await response.json();
            
            this.pivotConfigs = pivots;
            this.updatePivotList();
            this.updateCopyFilterSelects();
            
            if (pivots.length > 0 && !this.activePivotId) {
                this.setActivePivot(pivots[0].id);
            }
        } catch (error) {
            console.error('Failed to load pivots:', error);
        }
    }
    
    updatePivotList() {
        const container = document.getElementById('pivotList');
        container.innerHTML = '';
        
        this.pivotConfigs.forEach(config => {
            const tab = document.createElement('div');
            tab.className = `pivot-tab ${config.id === this.activePivotId ? 'active' : ''}`;
            tab.innerHTML = `
                <div>
                    <div class="pivot-tab-name">${config.name}</div>
                    <div class="pivot-tab-info">
                        ${config.filters.length} filters, 
                        ${config.value_agg_list.length} values
                    </div>
                </div>
                <div class="pivot-tab-actions">
                    <button class="btn-danger" onclick="app.deletePivot('${config.id}')" title="Delete pivot">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            tab.addEventListener('click', (e) => {
                if (!e.target.closest('.pivot-tab-actions')) {
                    this.setActivePivot(config.id);
                }
            });
            
            container.appendChild(tab);
        });
        
        // Show bulk actions if we have multiple pivots
        document.getElementById('bulkActions').style.display = 
            this.pivotConfigs.length > 1 ? 'block' : 'none';
    }
    
    updateCopyFilterSelects() {
        const sourceSelect = document.getElementById('sourceSelect');
        const targetSelect = document.getElementById('targetSelect');
        
        sourceSelect.innerHTML = '<option value="">Select source pivot...</option>';
        targetSelect.innerHTML = '';
        
        this.pivotConfigs.forEach(config => {
            const sourceOption = document.createElement('option');
            sourceOption.value = config.id;
            sourceOption.textContent = config.name;
            sourceSelect.appendChild(sourceOption);
            
            const targetOption = document.createElement('option');
            targetOption.value = config.id;
            targetOption.textContent = config.name;
            targetSelect.appendChild(targetOption);
        });
    }
    
    setActivePivot(pivotId) {
        this.activePivotId = pivotId;
        this.updatePivotList();
        this.loadPivotConfiguration();
        this.showWelcomeScreen(false);
    }
    
    loadPivotConfiguration() {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (!config || !this.currentData) return;
        
        // Update pivot name
        document.getElementById('pivotNameInput').value = config.name;
        
        // Setup column selects
        this.setupMultiSelect('indexSelect', this.currentData.columns, config.index_cols);
        this.setupMultiSelect('columnSelect', this.currentData.columns, config.column_cols);
        
        // Setup value aggregations
        this.updateValueAggregationList(config.value_agg_list);
        
        // Setup filters
        this.updateFilterList(config.filters);
        
        // Setup advanced options
        document.getElementById('fillValueEnabled').checked = config.fill_value_enabled;
        document.getElementById('customFillValue').value = config.custom_fill_value || '';
        document.getElementById('customFillValue').disabled = !config.fill_value_enabled;
        
        document.getElementById('marginsEnabled').checked = config.margins_enabled;
        document.getElementById('marginsName').value = config.margins_name || 'All_Totals';
        document.getElementById('marginsName').disabled = !config.margins_enabled;
        
        // Show configuration
        document.getElementById('pivotConfig').style.display = 'block';
        document.getElementById('pivotResults').style.display = 'none';
    }
    
    setupMultiSelect(containerId, options, selected = []) {
        const container = document.getElementById(containerId);
        const searchInput = container.querySelector('.search-input');
        const dropdownContent = container.querySelector('.dropdown-content');
        const selectedItems = container.querySelector('.selected-items');
        const selectInput = container.querySelector('.select-input');
        const dropdownArrow = container.querySelector('.dropdown-arrow');
        
        let isOpen = false;
        
        // Clear existing content
        dropdownContent.innerHTML = '';
        selectedItems.innerHTML = '';
        
        // Add options
        options.forEach(option => {
            const optionDiv = document.createElement('div');
            optionDiv.className = `dropdown-option ${selected.includes(option) ? 'selected' : ''}`;
            optionDiv.textContent = option;
            optionDiv.addEventListener('click', () => {
                this.toggleSelection(containerId, option);
            });
            dropdownContent.appendChild(optionDiv);
        });
        
        // Add selected items
        selected.forEach(item => {
            this.addSelectedItem(containerId, item);
        });
        
        // Toggle dropdown
        selectInput.addEventListener('click', () => {
            isOpen = !isOpen;
            dropdownContent.classList.toggle('active', isOpen);
            dropdownArrow.classList.toggle('active', isOpen);
            selectInput.classList.toggle('active', isOpen);
            
            if (isOpen) {
                searchInput.focus();
            }
        });
        
        // Search functionality
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const options = dropdownContent.querySelectorAll('.dropdown-option');
            
            options.forEach(option => {
                const matches = option.textContent.toLowerCase().includes(searchTerm);
                option.style.display = matches ? 'block' : 'none';
            });
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target) && isOpen) {
                isOpen = false;
                dropdownContent.classList.remove('active');
                dropdownArrow.classList.remove('active');
                selectInput.classList.remove('active');
            }
        });
    }
    
    toggleSelection(containerId, option) {
        const container = document.getElementById(containerId);
        const optionDiv = container.querySelector(`.dropdown-option[data-value="${option}"]`) ||
                         Array.from(container.querySelectorAll('.dropdown-option'))
                             .find(div => div.textContent === option);
        
        if (optionDiv.classList.contains('selected')) {
            optionDiv.classList.remove('selected');
            this.removeSelectedItem(containerId, option);
        } else {
            optionDiv.classList.add('selected');
            this.addSelectedItem(containerId, option);
        }
        
        this.updatePivotConfiguration();
    }
    
    addSelectedItem(containerId, item) {
        const container = document.getElementById(containerId);
        const selectedItems = container.querySelector('.selected-items');
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'selected-item';
        itemDiv.innerHTML = `
            <span>${item}</span>
            <button class="remove-btn" onclick="app.removeSelectedItem('${containerId}', '${item}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        selectedItems.appendChild(itemDiv);
    }
    
    removeSelectedItem(containerId, item) {
        const container = document.getElementById(containerId);
        const selectedItems = container.querySelector('.selected-items');
        const itemDiv = Array.from(selectedItems.children)
            .find(div => div.querySelector('span').textContent === item);
        
        if (itemDiv) {
            itemDiv.remove();
        }
        
        // Update option state
        const optionDiv = Array.from(container.querySelectorAll('.dropdown-option'))
            .find(div => div.textContent === item);
        if (optionDiv) {
            optionDiv.classList.remove('selected');
        }
        
        this.updatePivotConfiguration();
    }
    
    updateValueAggregationList(valueAggList = []) {
        const container = document.getElementById('valueAggList');
        container.innerHTML = '';
        
        valueAggList.forEach((item, index) => {
            this.addValueAggregationItem(item, index);
        });
    }
    
    addValueAggregation() {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (!config) return;
        
        const newItem = { value_col: null, agg_func: 'sum' };
        config.value_agg_list.push(newItem);
        
        this.addValueAggregationItem(newItem, config.value_agg_list.length - 1);
    }
    
    addValueAggregationItem(item, index) {
        const container = document.getElementById('valueAggList');
        const itemDiv = document.createElement('div');
        itemDiv.className = 'value-agg-item';
        
        const aggFunctions = {
            'Sum': 'sum',
            'Mean': 'mean',
            'Average': 'mean',
            'Median': 'median',
            'Min': 'min',
            'Max': 'max',
            'Count': 'count',
            'Size': 'size',
            'Standard Deviation': 'std',
            'Variance': 'var',
            'Number of Unique Values': 'nunique'
        };
        
        itemDiv.innerHTML = `
            <select class="value-col-select" onchange="app.updateValueAggregation(${index}, 'value_col', this.value)">
                <option value="">Select column...</option>
                ${this.currentData.columns.map(col => 
                    `<option value="${col}" ${col === item.value_col ? 'selected' : ''}>${col}</option>`
                ).join('')}
            </select>
            <select class="agg-func-select" onchange="app.updateValueAggregation(${index}, 'agg_func', this.value)">
                ${Object.entries(aggFunctions).map(([name, func]) => 
                    `<option value="${func}" ${func === item.agg_func ? 'selected' : ''}>${name}</option>`
                ).join('')}
            </select>
            <button onclick="app.removeValueAggregation(${index})" title="Remove">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        container.appendChild(itemDiv);
    }
    
    updateValueAggregation(index, field, value) {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (config && config.value_agg_list[index]) {
            config.value_agg_list[index][field] = value;
        }
    }
    
    removeValueAggregation(index) {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (config && config.value_agg_list[index]) {
            config.value_agg_list.splice(index, 1);
            this.updateValueAggregationList(config.value_agg_list);
        }
    }
    
    updateFilterList(filters = []) {
        const container = document.getElementById('filterList');
        container.innerHTML = '';
        
        filters.forEach((filter, index) => {
            this.addFilterItem(filter, index);
        });
    }
    
    addFilter() {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (!config) return;
        
        const newFilter = { column: null, operator: '==', value: '' };
        config.filters.push(newFilter);
        
        this.addFilterItem(newFilter, config.filters.length - 1);
    }
    
    addFilterItem(filter, index) {
        const container = document.getElementById('filterList');
        const itemDiv = document.createElement('div');
        itemDiv.className = 'filter-item';
        
        const operators = {
            'Equals': '==',
            'Not Equals': '!=',
            'Greater Than': '>',
            'Less Than': '<',
            'Greater or Equal': '>=',
            'Less or Equal': '<=',
            'Contains': 'contains',
            'Not Contains': 'not_contains',
            'In List': 'in',
            'Not In List': 'not_in'
        };
        
        itemDiv.innerHTML = `
            <select class="filter-col-select" onchange="app.updateFilter(${index}, 'column', this.value)">
                <option value="">Select column...</option>
                ${this.currentData.columns.map(col => 
                    `<option value="${col}" ${col === filter.column ? 'selected' : ''}>${col}</option>`
                ).join('')}
            </select>
            <select class="filter-op-select" onchange="app.updateFilter(${index}, 'operator', this.value)">
                ${Object.entries(operators).map(([name, op]) => 
                    `<option value="${op}" ${op === filter.operator ? 'selected' : ''}>${name}</option>`
                ).join('')}
            </select>
            <input type="text" class="filter-value-input" placeholder="Filter value..." 
                   value="${filter.value || ''}" 
                   onchange="app.updateFilter(${index}, 'value', this.value)">
            <button onclick="app.removeFilter(${index})" title="Remove filter">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        container.appendChild(itemDiv);
    }
    
    updateFilter(index, field, value) {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (config && config.filters[index]) {
            config.filters[index][field] = value;
        }
    }
    
    removeFilter(index) {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (config && config.filters[index]) {
            config.filters.splice(index, 1);
            this.updateFilterList(config.filters);
        }
    }
    
    updateActivePivotName() {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (config) {
            config.name = document.getElementById('pivotNameInput').value;
            this.updatePivotList();
        }
    }
    
    updatePivotConfiguration() {
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (!config) return;
        
        // Update index columns
        const indexContainer = document.getElementById('indexSelect');
        config.index_cols = Array.from(indexContainer.querySelectorAll('.selected-item span'))
            .map(span => span.textContent);
        
        // Update column columns
        const columnContainer = document.getElementById('columnSelect');
        config.column_cols = Array.from(columnContainer.querySelectorAll('.selected-item span'))
            .map(span => span.textContent);
        
        // Update advanced options
        config.fill_value_enabled = document.getElementById('fillValueEnabled').checked;
        config.custom_fill_value = document.getElementById('customFillValue').value;
        config.margins_enabled = document.getElementById('marginsEnabled').checked;
        config.margins_name = document.getElementById('marginsName').value;
        
        this.updatePivotList();
    }
    
    async generatePivot() {
        if (!this.activePivotId) {
            this.showToast('No active pivot selected', 'warning');
            return;
        }
        
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        if (!config) return;
        
        this.showLoading('Generating pivot table...');
        
        try {
            const response = await fetch(`/api/pivots/${this.sessionId}/${this.activePivotId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            
            if (result.success) {
                await this.displayPivotTable();
                this.showToast('Pivot table generated successfully', 'success');
            } else {
                this.showError(`Failed to generate pivot: ${result.error}`);
            }
        } catch (error) {
            this.showError(`Failed to generate pivot: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    async displayPivotTable() {
        try {
            const response = await fetch(`/api/pivot-table/${this.sessionId}/${this.activePivotId}`);
            
            if (!response.ok) {
                throw new Error('Failed to load pivot table data');
            }
            
            const tableData = await response.json();
            
            // Display the pivot table
            const table = document.getElementById('pivotTable');
            table.innerHTML = '';
            
            if (tableData.data && tableData.data.length > 0) {
                // Create header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                // Add index column headers if present
                if (tableData.index && tableData.index.length > 0) {
                    const indexHeader = document.createElement('th');
                    indexHeader.textContent = '';
                    headerRow.appendChild(indexHeader);
                }
                
                // Add column headers
                tableData.columns.forEach(col => {
                    const th = document.createElement('th');
                    th.textContent = col;
                    headerRow.appendChild(th);
                });
                
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Create body
                const tbody = document.createElement('tbody');
                
                tableData.data.forEach((row, rowIndex) => {
                    const tr = document.createElement('tr');
                    
                    // Add index cell if present
                    if (tableData.index && tableData.index[rowIndex] !== undefined) {
                        const indexCell = document.createElement('td');
                        indexCell.textContent = tableData.index[rowIndex];
                        indexCell.style.fontWeight = 'bold';
                        tr.appendChild(indexCell);
                    }
                    
                    // Add data cells
                    tableData.columns.forEach(col => {
                        const td = document.createElement('td');
                        const value = row[col];
                        
                        if (typeof value === 'number') {
                            td.textContent = value.toLocaleString();
                        } else {
                            td.textContent = value || '';
                        }
                        
                        tr.appendChild(td);
                    });
                    
                    tbody.appendChild(tr);
                });
                
                table.appendChild(tbody);
                
                // Show results section
                document.getElementById('pivotResults').style.display = 'block';
                
                // Calculate and display statistics
                this.displayStatistics(tableData);
                
            } else {
                table.innerHTML = '<tr><td colspan="100%">No data to display</td></tr>';
            }
            
        } catch (error) {
            this.showError(`Failed to display pivot table: ${error.message}`);
        }
    }
    
    displayStatistics(tableData) {
        const statsContainer = document.getElementById('resultsStats');
        const config = this.pivotConfigs.find(p => p.id === this.activePivotId);
        
        if (!config || !config.value_agg_list.length) {
            statsContainer.innerHTML = '';
            return;
        }
        
        let statsHtml = '<h4><i class="fas fa-chart-bar"></i> Statistics</h4>';
        
        // Calculate basic statistics for numeric columns
        config.value_agg_list.forEach(valueAgg => {
            if (!valueAgg.value_col) return;
            
            const values = tableData.data.map(row => {
                const value = row[valueAgg.value_col];
                return typeof value === 'number' ? value : 0;
            }).filter(v => v !== 0);
            
            if (values.length > 0) {
                const sum = values.reduce((a, b) => a + b, 0);
                const avg = sum / values.length;
                const min = Math.min(...values);
                const max = Math.max(...values);
                
                statsHtml += `
                    <div class="stat-group">
                        <h5>${valueAgg.value_col}</h5>
                        <div class="stat-items">
                            <span><strong>Average:</strong> ${avg.toLocaleString(undefined, {maximumFractionDigits: 2})}</span>
                            <span><strong>Total:</strong> ${sum.toLocaleString()}</span>
                            <span><strong>Min:</strong> ${min.toLocaleString()}</span>
                            <span><strong>Max:</strong> ${max.toLocaleString()}</span>
                        </div>
                    </div>
                `;
            }
        });
        
        statsContainer.innerHTML = statsHtml;
    }
    
    async copyFilters() {
        const sourcePivotId = document.getElementById('sourceSelect').value;
        const targetSelect = document.getElementById('targetSelect');
        const targetPivotIds = Array.from(targetSelect.selectedOptions).map(option => option.value);
        
        if (!sourcePivotId) {
            this.showToast('Please select a source pivot', 'warning');
            return;
        }
        
        if (targetPivotIds.length === 0) {
            this.showToast('Please select target pivots', 'warning');
            return;
        }
        
        if (targetPivotIds.includes(sourcePivotId)) {
            this.showToast('Cannot copy filters to the same pivot', 'warning');
            return;
        }
        
        this.showLoading('Copying filters...');
        
        try {
            const response = await fetch(`/api/copy-filters/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source_pivot_id: sourcePivotId,
                    target_pivot_ids: targetPivotIds
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                await this.loadPivots();
                this.loadPivotConfiguration();
                this.showToast(`Filters copied to ${result.updated_count} pivot(s)`, 'success');
            } else {
                throw new Error('Failed to copy filters');
            }
        } catch (error) {
            this.showError(`Failed to copy filters: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    async deletePivot(pivotId) {
        if (!confirm('Are you sure you want to delete this pivot?')) {
            return;
        }
        
        this.showLoading('Deleting pivot...');
        
        try {
            const response = await fetch(`/api/pivots/${this.sessionId}/${pivotId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                await this.loadPivots();
                
                if (this.activePivotId === pivotId) {
                    if (this.pivotConfigs.length > 0) {
                        this.setActivePivot(this.pivotConfigs[0].id);
                    } else {
                        this.activePivotId = null;
                        this.showWelcomeScreen(true);
                    }
                }
                
                this.showToast('Pivot deleted', 'success');
            } else {
                throw new Error('Failed to delete pivot');
            }
        } catch (error) {
            this.showError(`Failed to delete pivot: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    deleteActivePivot() {
        if (this.activePivotId) {
            this.deletePivot(this.activePivotId);
        }
    }
    
    async saveViews() {
        this.showLoading('Saving views...');
        
        try {
            const response = await fetch(`/api/save-views/${this.sessionId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Views saved successfully', 'success');
            } else {
                throw new Error('Failed to save views');
            }
        } catch (error) {
            this.showError(`Failed to save views: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    async loadViews() {
        this.showLoading('Loading views...');
        
        try {
            const response = await fetch(`/api/load-views/${this.sessionId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                await this.loadPivots();
                this.showToast('Views loaded successfully', 'success');
            } else {
                throw new Error('Failed to load views');
            }
        } catch (error) {
            this.showError(`Failed to load views: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    async downloadFile(fileType) {
        if (!this.activePivotId) {
            this.showToast('No active pivot selected', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`/api/download/${this.sessionId}/${this.activePivotId}/${fileType}`);
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Get filename from response headers or create default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'download';
            if (contentDisposition) {
                const matches = contentDisposition.match(/filename="?([^"]+)"?/);
                if (matches) {
                    filename = matches[1];
                }
            }
            
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showToast('File downloaded successfully', 'success');
        } catch (error) {
            this.showError(`Download failed: ${error.message}`);
        }
    }
    
    loadSavedState() {
        // Try to restore session from localStorage
        const savedSessionId = localStorage.getItem('pivotCodexSessionId');
        if (savedSessionId) {
            this.sessionId = savedSessionId;
            document.getElementById('sessionId').textContent = `Session: ${savedSessionId}`;
        }
        
        // Auto-load data if available
        this.checkForExistingData();
    }
    
    async checkForExistingData() {
        try {
            const response = await fetch(`/api/data/${this.sessionId}`);
            if (response.ok) {
                const data = await response.json();
                this.currentData = data;
                this.updateDataInfo(data);
                this.showWelcomeScreen(false);
                await this.loadPivots();
            }
        } catch (error) {
            // No existing data, show welcome screen
            this.showWelcomeScreen(true);
        }
    }
    
    showLoading(message = 'Loading...') {
        document.getElementById('loadingMessage').textContent = message;
        document.getElementById('loadingOverlay').style.display = 'flex';
    }
    
    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
    
    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorDisplay').style.display = 'flex';
    }
    
    hideError() {
        document.getElementById('errorDisplay').style.display = 'none';
    }
    
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        toast.innerHTML = `
            <i class="fas ${icons[type] || icons.info}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, duration);
    }
}

// Global functions for onclick handlers
window.hideError = function() {
    app.hideError();
};

window.app = new PivotCodex();