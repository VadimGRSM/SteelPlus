// Копіювання посилання
  document.getElementById('share-btn').addEventListener('click', function() {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
  });

// Масштабування
  let scale = 1.0;
  const step = 0.1;
  const minScale = 0.5;
  const maxScale = 3.0;

  const zoomInBtn = document.getElementById('zoom-in');
  const zoomOutBtn = document.getElementById('zoom-out');
  const zoomDisplay = document.getElementById('zoom-display');
  const drawingImg = document.querySelector('.drawing-area img');
  const drawingArea = document.querySelector('.drawing-area');

  let translate = { x: 0, y: 0 };
  let isDragging = false;
  let dragStart = { x: 0, y: 0 };

  function updateTransform() {
    drawingImg.style.transform = `translate(${translate.x}px, ${translate.y}px) scale(${scale})`;
    zoomDisplay.textContent = `${Math.round(scale * 100)}%`;
  }

  zoomInBtn.addEventListener('click', () => {
    if (scale < maxScale) {
      scale += step;
      updateTransform();
    }
  });

  zoomOutBtn.addEventListener('click', () => {
    if (scale > minScale) {
      scale -= step;
      updateTransform();
    }
  });

  // Перетягування мишкою
  drawingImg.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragStart = {
      x: e.clientX - translate.x,
      y: e.clientY - translate.y
    };
    drawingImg.style.cursor = "grabbing";
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    translate.x = e.clientX - dragStart.x;
    translate.y = e.clientY - dragStart.y;
    updateTransform();
  });

  window.addEventListener('mouseup', () => {
    isDragging = false;
    drawingImg.style.cursor = "grab";
  });

  // Масштаб колесом миші (з Ctrl)
  drawingArea.addEventListener('wheel', (e) => {
    if (!e.ctrlKey) return; // тільки якщо Ctrl натиснуто
    e.preventDefault();

    const delta = -Math.sign(e.deltaY) * step;
    const newScale = Math.min(Math.max(scale + delta, minScale), maxScale);
    if (newScale !== scale) {
      scale = newScale;
      updateTransform();
    }
  }, { passive: false });

  function resetView() {
  scale = 1.0;
  translate = { x: 0, y: 0 };
  updateTransform();
}

document.getElementById('reset-view').addEventListener('click', resetView);