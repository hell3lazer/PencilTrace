document.addEventListener('DOMContentLoaded', () => {
    // Theme Management
    const themeSelect = document.getElementById('themeSelect');
    
    const applyTheme = (theme) => {
        if (theme === 'system') {
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', systemPrefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
    };

    const savedTheme = localStorage.getItem('pencilTraceTheme') || 'system';
    if (themeSelect) {
        themeSelect.value = savedTheme;
        themeSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            localStorage.setItem('pencilTraceTheme', val);
            applyTheme(val);
        });
    }
    
    applyTheme(savedTheme);

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (localStorage.getItem('pencilTraceTheme') === 'system' || !localStorage.getItem('pencilTraceTheme')) {
            applyTheme('system');
        }
    });

    // Navigation
    const navItems = document.querySelectorAll('nav li');
    const views = document.querySelectorAll('.view');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            
            const targetView = item.getAttribute('data-view');
            views.forEach(v => {
                v.classList.remove('active');
                if (v.id === targetView) {
                    v.classList.add('active');
                }
            });
        });
    });

    // Template Management
    const templateSelect = document.getElementById('templateSelect');
    const importBtn = document.getElementById('importBtn');
    const importInput = document.getElementById('importInput');
    const exportBtn = document.getElementById('exportBtn');

    async function loadTemplates() {
        try {
            const res = await fetch('/api/templates');
            const data = await res.json();
            templateSelect.innerHTML = '';
            data.templates.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t;
                templateSelect.appendChild(opt);
            });
        } catch (e) {
            console.error('Failed to load templates', e);
        }
    }
    
    loadTemplates();

    importInput.addEventListener('change', async (e) => {
        if (e.target.files.length === 0) return;
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        importBtn.textContent = 'Importing...';
        try {
            const res = await fetch('/api/templates/import', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.status === 'success') {
                await loadTemplates();
                templateSelect.value = data.filename;
            } else {
                alert(data.message);
            }
        } catch (err) {
            alert('Failed to import template.');
        }
        importBtn.textContent = 'Import';
        importInput.value = '';
    });

    exportBtn.addEventListener('click', () => {
        const selected = templateSelect.value;
        if (!selected) return;
        window.open(`/api/templates/export/${selected}`, '_blank');
    });

    // File Upload handling
    const folderInput = document.getElementById('folderInput');
    const fileInput = document.getElementById('fileInput');
    const startProcessBtn = document.getElementById('startProcessBtn');
    const dropZone = document.getElementById('folderDropZone');
    let selectedFiles = [];

    function handleFileSelect(e) {
        handleFiles(e.target.files);
    }
    folderInput.addEventListener('change', handleFileSelect);
    fileInput.addEventListener('change', handleFileSelect);

    // Answer Key Upload handling
    let answerKeyJson = null;
    const answerKeyInput = document.getElementById('answerKeyInput');
    const answerKeyStatus = document.getElementById('answerKeyStatus');

    if (answerKeyInput) {
        answerKeyInput.addEventListener('change', (e) => {
            if (e.target.files.length === 0) {
                answerKeyJson = null;
                answerKeyStatus.textContent = 'No answer key selected';
                answerKeyStatus.style.color = 'var(--text-muted)';
                return;
            }
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (event) => {
                const text = event.target.result;
                const lines = text.split('\n');
                const answers = [];
                lines.forEach(line => {
                    const parts = line.split(',');
                    if (parts.length >= 2) {
                        answers.push(parts[1].trim());
                    }
                });
                if (answers.length > 0) {
                    answerKeyJson = JSON.stringify(answers);
                    answerKeyStatus.textContent = `Loaded ${answers.length} answers from ${file.name}`;
                    answerKeyStatus.style.color = 'var(--success)';
                } else {
                    answerKeyJson = null;
                    answerKeyStatus.textContent = 'Invalid CSV format';
                    answerKeyStatus.style.color = '#ef4444';
                }
            };
            reader.readAsText(file);
        });
    }

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent)';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--panel-border)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--panel-border)';
        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });

    function handleFiles(files) {
        const validExts = ['.jpg', '.jpeg', '.png', '.heic', '.heif'];
        selectedFiles = Array.from(files).filter(f => {
            const name = f.name.toLowerCase();
            return validExts.some(ext => name.endsWith(ext));
        });
        if (selectedFiles.length > 0) {
            dropZone.querySelector('h3').textContent = `${selectedFiles.length} image(s) selected`;
            startProcessBtn.disabled = false;
        } else {
            dropZone.querySelector('h3').textContent = `No valid images selected.`;
            startProcessBtn.disabled = true;
        }
    }

    // Results state
    let cachedResults = JSON.parse(localStorage.getItem('pencilTraceResults') || '[]');
    const resultsList = document.getElementById('resultsList');

    function renderResults() {
        if (cachedResults.length === 0) {
            resultsList.innerHTML = `
                <div class="bento-card empty-state">
                    <div class="empty-icon">📊</div>
                    <h3>No results to display</h3>
                    <p class="text-muted">Run a batch process from the dashboard to populate this section.</p>
                </div>`;
            return;
        }
        
        resultsList.innerHTML = '';
        cachedResults.forEach((data, index) => {
            const card = document.createElement('div');
            card.className = 'result-card-modern';
            
            if (data.status === 'success') {
                const indexNum = data.responses[0] || 'N/A';
                const answers = data.responses.slice(1);
                
                const formattedAnswers = answers.map((ans, i) => {
                    const ansText = ans ? ans : '-';
                    return `<div class="answer-pill">${i+1}. <span>${ansText}</span></div>`;
                }).join('');

                card.innerHTML = `
                    <div class="result-header">
                        <div class="result-meta">
                            <input type="checkbox" class="result-checkbox" data-index="${index}" style="width: 16px; height: 16px; cursor: pointer;">
                            <span class="result-filename" style="font-weight: 600; font-size: 0.95rem;">${data.filename}</span>
                        </div>
                        <span class="score-badge">${data.score}</span>
                    </div>
                    <div class="result-body">
                        <div class="index-display">${indexNum}</div>
                        <div class="answers-grid">
                            ${formattedAnswers}
                        </div>
                    </div>
                `;
            } else {
                card.innerHTML = `
                    <div class="result-header">
                        <div class="result-meta">
                            <input type="checkbox" class="result-checkbox" data-index="${index}" style="width: 16px; height: 16px; cursor: pointer;">
                            <span class="result-filename" style="font-weight: 600; font-size: 0.95rem;">${data.filename}</span>
                        </div>
                        <span class="score-badge error">Error</span>
                    </div>
                    <div class="result-body">
                        <p style="color:var(--danger); font-size: 0.95rem; text-align: center;">${data.message}</p>
                    </div>
                `;
            }
            resultsList.appendChild(card);
        });

        // Attach event listeners to delete buttons
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(e.target.getAttribute('data-index'));
                cachedResults.splice(idx, 1);
                localStorage.setItem('pencilTraceResults', JSON.stringify(cachedResults));
                renderResults();
            });
        });
        
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }
    }

    // Select All logic
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', (e) => {
            document.querySelectorAll('.result-checkbox').forEach(cb => {
                cb.checked = e.target.checked;
            });
        });
    }

    // Delete Selected logic
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', () => {
            const checkedBoxes = document.querySelectorAll('.result-checkbox:checked');
            if (checkedBoxes.length === 0) {
                alert('Please select at least one result to delete.');
                return;
            }
            if (!confirm(`Are you sure you want to delete ${checkedBoxes.length} result(s)?`)) {
                return;
            }
            // Delete from highest index to lowest
            const indicesToDelete = Array.from(checkedBoxes).map(cb => parseInt(cb.getAttribute('data-index'))).sort((a, b) => b - a);
            indicesToDelete.forEach(idx => {
                cachedResults.splice(idx, 1);
            });
            localStorage.setItem('pencilTraceResults', JSON.stringify(cachedResults));
            renderResults();
        });
    }

    // Initial render
    renderResults();

    // Export utilities
    function exportCsv(resultsToExport) {
        if (resultsToExport.length === 0) {
            alert('No results to export.');
            return;
        }
        let csv = 'Filename,Status,Score,Index,Responses...\n';
        resultsToExport.forEach(data => {
            if (data.status === 'success') {
                const row = [data.filename, data.status, data.score, ...data.responses];
                csv += row.join(',') + '\n';
            } else {
                csv += `${data.filename},error,0,,\n`;
            }
        });
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'omr_results.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    }

    const exportAllCsvBtn = document.getElementById('exportAllCsvBtn');
    if (exportAllCsvBtn) {
        exportAllCsvBtn.addEventListener('click', () => {
            exportCsv(cachedResults);
        });
    }

    const exportSelectedCsvBtn = document.getElementById('exportSelectedCsvBtn');
    if (exportSelectedCsvBtn) {
        exportSelectedCsvBtn.addEventListener('click', () => {
            const checkedBoxes = document.querySelectorAll('.result-checkbox:checked');
            if (checkedBoxes.length === 0) {
                alert('Please select at least one result to export.');
                return;
            }
            const selectedResults = Array.from(checkedBoxes).map(cb => {
                const idx = parseInt(cb.getAttribute('data-index'));
                return cachedResults[idx];
            });
            exportCsv(selectedResults);
        });
    }

    // Processing
    startProcessBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;
        
        const templateName = document.getElementById('templateSelect').value;
        const progressSection = document.getElementById('progressSection');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        progressSection.style.display = 'block';
        startProcessBtn.disabled = true;
        
        let processed = 0;
        let batchResults = [];
        
        for (const file of selectedFiles) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('template_name', templateName);
            if (answerKeyJson) {
                formData.append('answer_key', answerKeyJson);
            }
            
            try {
                const res = await fetch('/api/process', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                batchResults.push(data);
            } catch (err) {
                console.error(err);
                batchResults.push({status: 'error', filename: file.name, message: 'Network error.'});
            }
            
            processed++;
            progressFill.style.width = `${(processed / selectedFiles.length) * 100}%`;
            progressText.textContent = `${processed} / ${selectedFiles.length} files processed`;
        }
        
        progressText.textContent = "Processing complete! Check Results tab.";
        startProcessBtn.disabled = false;
        
        // Append batch results to cached results and save to local storage
        cachedResults = [...cachedResults, ...batchResults];
        localStorage.setItem('pencilTraceResults', JSON.stringify(cachedResults));
        
        renderResults();
        
        // Auto switch to results
        setTimeout(() => {
            document.querySelector('[data-view="results"]').click();
        }, 1000);
    });
});
