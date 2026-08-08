document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('templateCanvas');
    const ctx = canvas.getContext('2d');
    const fileInput = document.getElementById('blankSheetInput');
    const saveBtn = document.getElementById('saveTemplateBtn');
    const templateNameInput = document.getElementById('templateName');
    
    let currentImage = null;
    let isDrawing = false;
    let startX, startY;
    let regions = [];

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const img = new Image();
            img.onload = () => {
                currentImage = img;
                canvas.width = img.width;
                canvas.height = img.height;
                redraw();
            };
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
    });

    canvas.addEventListener('mousedown', (e) => {
        if (!currentImage) return;
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        startX = (e.clientX - rect.left) * scaleX;
        startY = (e.clientY - rect.top) * scaleY;
    });

    canvas.addEventListener('mousemove', (e) => {
        if (!isDrawing || !currentImage) return;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const currentX = (e.clientX - rect.left) * scaleX;
        const currentY = (e.clientY - rect.top) * scaleY;
        
        redraw();
        
        // Draw temporary rectangle
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
    });

    canvas.addEventListener('mouseup', (e) => {
        if (!isDrawing || !currentImage) return;
        isDrawing = false;
        
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const endX = (e.clientX - rect.left) * scaleX;
        const endY = (e.clientY - rect.top) * scaleY;
        
        const width = endX - startX;
        const height = endY - startY;
        
        if (Math.abs(width) > 10 && Math.abs(height) > 10) {
            const name = prompt("Enter field name (e.g., 'q1' or 'rollNumber'):", "field" + (regions.length + 1));
            if (name) {
                regions.push({
                    name: name,
                    x: Math.min(startX, endX),
                    y: Math.min(startY, endY),
                    w: Math.abs(width),
                    h: Math.abs(height)
                });
            }
        }
        redraw();
    });

    function redraw() {
        if (!currentImage) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(currentImage, 0, 0);
        
        // Draw regions
        regions.forEach(region => {
            ctx.strokeStyle = '#6366f1';
            ctx.lineWidth = 3;
            ctx.strokeRect(region.x, region.y, region.w, region.h);
            
            ctx.fillStyle = 'rgba(99, 102, 241, 0.7)';
            ctx.fillRect(region.x, region.y, region.w, 30);
            
            ctx.fillStyle = '#ffffff';
            ctx.font = '20px Arial';
            ctx.fillText(region.name, region.x + 5, region.y + 22);
        });
    }

    saveBtn.addEventListener('click', async () => {
        if (regions.length === 0) {
            alert("No regions drawn!");
            return;
        }
        const tname = templateNameInput.value || "custom_template";
        
        // Constructing basic layout structure compatible with OMRChecker
        const templateData = {
            "dimensions": [canvas.width, canvas.height],
            "bubbleDimensions": [30, 30],
            "customLabels": {},
            "fieldBlocks": {}
        };
        
        regions.forEach(r => {
            // Very simplified approximation for visual creator.
            // OMRChecker usually takes a grid of bubbles.
            templateData.fieldBlocks[r.name] = {
                "origin": [r.x, r.y],
                "bubblesGap": 40,
                "labelsGap": 40,
                "fieldType": "QTYPE_INT",
                "direction": "horizontal",
                "labels": ["A", "B", "C", "D"]
            };
        });

        try {
            const res = await fetch('/api/templates/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: tname,
                    template_data: templateData
                })
            });
            const data = await res.json();
            alert(data.message);
        } catch(err) {
            console.error(err);
            alert("Error saving template.");
        }
    });
});
