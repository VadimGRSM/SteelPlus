// Додаємо інтерактивність
document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const action = this.textContent.trim();
        if (action === 'Замовити креслення') {
            alert('Відкривається форма замовлення креслення...');
        } else {
            alert(`Дія: ${action}`);
        }
    });
});

document.querySelector('.upload-btn').addEventListener('click', function() {
    alert('Відкривається діалог завантаження файлу...');
});

// Анімація при наведенні на картку
document.querySelector('.drawing-card').addEventListener('mouseenter', function() {
    this.style.borderColor = '#4285f4';
});

document.querySelector('.drawing-card').addEventListener('mouseleave', function() {
    this.style.borderColor = '#e8eaed';
});