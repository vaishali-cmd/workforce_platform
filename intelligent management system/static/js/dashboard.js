// Draggable panel with header handle and position persistence
(function(){
    const panel = document.querySelector('.draggable-panel');
    if (!panel) return;
    const header = document.createElement('div');
    header.className = 'drag-handle';
    header.style = 'cursor: move; padding: 8px; background: rgba(0,0,0,0.05); border-bottom: 1px solid #ccc;';
    header.innerHTML = '<strong>Drag Panel</strong>';
    panel.prepend(header);
    let isDragging = false;
    let offsetX = 0, offsetY = 0;
    // Load saved position
    const saved = localStorage.getItem('dashboardPanelPos');
    if (saved) {
        const pos = JSON.parse(saved);
        panel.style.left = pos.left + 'px';
        panel.style.top = pos.top + 'px';
    }
    header.addEventListener('mousedown', e => {
        isDragging = true;
        offsetX = panel.offsetLeft - e.clientX;
        offsetY = panel.offsetTop - e.clientY;
        panel.style.transition = 'none';
    });
    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            // Save position
            localStorage.setItem('dashboardPanelPos', JSON.stringify({left: panel.offsetLeft, top: panel.offsetTop}));
            panel.style.transition = '';
        }
    });
    document.addEventListener('mousemove', e => {
        if (!isDragging) return;
        panel.style.left = (e.clientX + offsetX) + 'px';
        panel.style.top = (e.clientY + offsetY) + 'px';
    });
})();
