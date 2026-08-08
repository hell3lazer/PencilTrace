document.addEventListener('DOMContentLoaded', () => {
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

    // File Upload handling
    const folderInput = document.getElementById('folderInput');
    const startProcessBtn = document.getElementById('startProcessBtn');
    const dropZone = document.getElementById('folderDropZone');
    let selectedFiles = [];

    folderInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

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
        // For simplicity, falling back to input click for directory structure, 
        // but handling basic file drops here:
        if (e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });

    function handleFiles(files) {
        selectedFiles = Array.from(files).filter(f => f.type.startsWith('image/') || f.type === 'application/pdf');
        if (selectedFiles.length > 0) {
            dropZone.querySelector('h3').textContent = `${selectedFiles.length} files selected`;
            startProcessBtn.disabled = false;
        }
    }

    // Processing
    startProcessBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;
        
        const templateName = document.getElementById('templateSelect').value;
        const progressSection = document.getElementById('progressSection');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const resultsTableBody = document.querySelector('#resultsTable tbody');
        
        progressSection.style.display = 'block';
        startProcessBtn.disabled = true;
        
        if (resultsTableBody.querySelector('.empty-state')) {
            resultsTableBody.innerHTML = '';
        }

        let processed = 0;
        
        for (const file of selectedFiles) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('template_name', templateName);
            
            try {
                const res = await fetch('/api/process', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                
                // Add to results table (mocking score for now)
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${data.filename}</td>
                    <td>Pending Evaluation</td>
                    <td><span style="color:var(--text-muted)">Processing...</span></td>
                `;
                resultsTableBody.appendChild(tr);
            } catch (err) {
                console.error(err);
            }
            
            processed++;
            progressFill.style.width = `${(processed / selectedFiles.length) * 100}%`;
            progressText.textContent = `${processed} / ${selectedFiles.length} files processed`;
        }
        
        progressText.textContent = "Processing complete! Check Results tab.";
        startProcessBtn.disabled = false;
        
        // Auto switch to results
        setTimeout(() => {
            document.querySelector('[data-view="results"]').click();
        }, 1000);
    });
});
