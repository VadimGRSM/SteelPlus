let currentSlide = 0;
let currentRadiusTarget = -1;

const sliderWrapper = document.querySelector('.slider-wrapper');
const slides = document.querySelectorAll('.slide');
const layerLabel = document.getElementById('layer-label');
const sliderContainer = document.querySelector('.slider-container');
const radiusModal = document.getElementById('radius-modal');
const angleSlider = document.getElementById('angle-slider');
const angleValue = document.getElementById('angle-value');
const radiusInfo = document.getElementById('radius-info');
const roundedCorner = document.getElementById('rounded-corner');
const radiusText = document.getElementById('radius-text');
const radiusLine = document.getElementById('radius-line');
const mainHorizontal = document.getElementById('main-horizontal');
const mainVertical = document.getElementById('main-vertical');

const allowedAngles = [1, 2, 6, 10];

// =================== Слайди ===================
function showSlide(index) {
    if (index >= slides.length) {
        index = 0;
    }
    if (index < 0) {
        index = slides.length - 1;
    }

    const offset = index * 100;
    sliderWrapper.style.transform = `translateX(-${offset}%)`;

    layerLabel.textContent = `Шар ${index + 1}`;
    currentSlide = index;
}

function nextSlide() {
    showSlide(currentSlide + 1);
}

function previousSlide() {
    showSlide(currentSlide - 1);
}

// =================== Валідація кутів ===================
document.querySelectorAll('.corner-input').forEach(input => {
    input.addEventListener('input', function () {
        const value = parseFloat(this.value);
        this.style.borderColor = (isNaN(value) || value < 0 || value > 360) ? '#ff3b30' : '#d2d2d7';
    });
});

document.querySelector('.save-button').addEventListener('click', function () {
    let isValid = true;
    let isLayerSelectionValid = validateLayerSelection();

    document.querySelectorAll('.corner-input').forEach(input => {
        const value = parseFloat(input.value);
        if (isNaN(value) || value < 0 || value > 360) {
            input.style.borderColor = '#ff3b30';
            isValid = false;
        } else {
            input.style.borderColor = '#d2d2d7';
        }
    });

    if (!isValid) {
        alert('Деякі значення кутів недійсні! Допустимий діапазон: 0–360°.');
        return;
    }

    if (!isLayerSelectionValid) {
        alert('Помилка вибору шарів! Шари для різки та згинання не повинні перетинатися.');
        return;
    }

    alert('Зміни збережено успішно!');
});

// =================== Модальне вікно ===================
function openRadiusModal(targetIndex) {
    currentRadiusTarget = targetIndex;
    radiusModal.style.display = 'flex';
    angleSlider.value = 0;
    updateRoundedCornerVisualization(0);
}

function closeRadiusModal() {
    radiusModal.style.display = 'none';
}

function confirmRadius() {
    const selectedRadius = allowedAngles[parseInt(angleSlider.value)];
    const table = document.querySelector('.corner-table tbody');

    if (currentRadiusTarget === -1) { // "Обрати для всіх"
        const buttons = table.querySelectorAll('button.action-button');
        buttons.forEach(button => {
            button.textContent = `${selectedRadius}px`;
            button.classList.add('transparent');
        });
    } else { // Конкретний рядок
        const row = table.rows[currentRadiusTarget];
        if (row) {
            const button = row.querySelector('button.action-button');
            if (button) {
                button.textContent = `${selectedRadius}px`;
                button.classList.add('transparent');
            }
        }
    }
    closeRadiusModal();
}

function updateRoundedCornerVisualization(sliderIndex) {
    const radius = allowedAngles[sliderIndex];
    angleValue.textContent = `${radius}px`;
    radiusInfo.textContent = `Радіус заокруглення: ${radius}px`;

    const centerX = 160;
    const centerY = 160;
    const visualRadius = radius * 8;

    const startX = centerX - visualRadius;
    const endY = centerY - visualRadius;

    const roundedPath = `M ${startX} ${centerY} Q ${centerX} ${centerY} ${centerX} ${endY}`;

    roundedCorner.setAttribute('d', roundedPath);
    mainHorizontal.setAttribute('x2', startX);
    mainVertical.setAttribute('y1', endY);
    radiusText.textContent = '';

    const arcCenterX = centerX - visualRadius / Math.sqrt(2);
    const arcCenterY = centerY - visualRadius / Math.sqrt(2);
    radiusLine.setAttribute('x1', centerX);
    radiusLine.setAttribute('y1', centerY);
    radiusLine.setAttribute('x2', arcCenterX);
    radiusLine.setAttribute('y2', arcCenterY);
}

angleSlider.addEventListener('input', function () {
    updateRoundedCornerVisualization(parseInt(this.value));
});

radiusModal.addEventListener('click', (e) => {
    if (e.target === radiusModal) closeRadiusModal();
});


// =================== Глобальні слухачі подій ===================

document.addEventListener('keydown', function (e) {
    switch (e.key) {
        case 'ArrowLeft': previousSlide(); e.preventDefault(); break;
        case 'ArrowRight': nextSlide(); e.preventDefault(); break;
    }
});

document.addEventListener('DOMContentLoaded', function () {
    showSlide(0);
});


