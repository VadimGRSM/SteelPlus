let currentSlide = 0;
        let currentZoom = 100;
        let selectedCuttingLayer = [];
        let selectedBendingLayer = [];
        let currentRadiusTarget = -1; // -1 для "всіх", інакше індекс рядка

        const slides = document.querySelectorAll('.slide');
        const progressDots = document.querySelectorAll('.progress-dot');
        const layerLabel = document.getElementById('layer-label');
        const descriptionTextbox = document.getElementById('description-textbox');
        const zoomDisplay = document.getElementById('zoom-display');
        const sliderContainer = document.querySelector('.slider-container');
        const cuttingLayerSelect = document.getElementById('cutting-layer-select');
        const bendingLayerSelect = document.getElementById('bending-layer-select');
        const cuttingLengthContainer = document.getElementById('cutting-length-container');
        const cuttingLengthInput = document.getElementById('cutting-length');
        const cornerConfig = document.getElementById('corner-config');
        const layerError = document.getElementById('layer-error');


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


        // Функція для показу слайду
        function showSlide(index) {
            slides.forEach(slide => slide.classList.remove('active-slide'));
            progressDots.forEach(dot => dot.classList.remove('current'));

            slides[index].classList.add('active-slide');
            progressDots[index].classList.add('current');

            currentSlide = index;
            layerLabel.textContent = `Слой ${index + 1}`;

            // Оновлюємо довжину різу залежно від вибраного слою
            updateCuttingLength();
        }

        // Навігація по слайдах
        function nextSlide() {
            const nextIndex = (currentSlide + 1) % slides.length;
            showSlide(nextIndex);
        }

        function previousSlide() {
            const prevIndex = (currentSlide - 1 + slides.length) % slides.length;
            showSlide(prevIndex);
        }

        // Функції масштабування
        function zoomIn() {
            if (currentZoom < 300) {
                currentZoom = Math.min(currentZoom + 25, 300);
                updateZoom();
            }
        }

        function zoomOut() {
            if (currentZoom > 25) {
                currentZoom = Math.max(currentZoom - 25, 25);
                updateZoom();
            }
        }

        function resetZoom() {
            currentZoom = 100;
            updateZoom();
        }

        function updateZoom() {
            const scale = currentZoom / 100;
            sliderContainer.style.transform = `scale(${scale})`;
            zoomDisplay.textContent = `${currentZoom}%`;

            if (currentZoom !== 100) {
                sliderContainer.style.cursor = 'move';
            } else {
                sliderContainer.style.cursor = 'default';
            }
        }

        // Функція для оновлення довжини різу
        function updateCuttingLength() {
            const lengths = {
        '1': 150,
        '2': 200,
        '3': 175
    };

    let total = selectedCuttingLayers.reduce((sum, layer) => {
        const val = lengths[layer];
        return sum + (val ? parseFloat(val) : 0);
    }, 0);

    cuttingLengthInput.value = total ? `${total}` : '';
}

        // Функція для валідації вибору слоїв
        function validateLayerSelection() {
            document.getElementById('cutting-layer-error').style.display = 'none';
    document.getElementById('bending-layer-error').style.display = 'none';

    const overlapping = selectedCuttingLayers.some(layer => selectedBendingLayers.includes(layer));
    if (overlapping) {
        document.getElementById('cutting-layer-error').style.display = 'block';
        document.getElementById('bending-layer-error').style.display = 'block';
        return false;
    }

    return true;
}

        // Обробники подій для випадаючих списків
        cuttingLayerSelect.addEventListener('change', function() {
            selectedCuttingLayers = Array.from(this.selectedOptions)
        .map(opt => opt.value)
        .filter(val => val); // відфільтрувати порожній рядок

    if (selectedCuttingLayers.length > 0) {
        cuttingLengthContainer.classList.remove('hidden');
        updateCuttingLength();
    } else {
        cuttingLengthContainer.classList.add('hidden');
        cuttingLengthInput.value = '';
    }

    validateLayerSelection();
});




    // Початкове значення - перше з доступних
    angleSlider.value = 0;
    angleValue.textContent = allowedAngles[0];







        // Обробник слайдера кута
        angleSlider.addEventListener('input', function() {
            angleValue.textContent = this.value;
        });

        // Закриття модального вікна при кліку поза ним
        radiusModal.addEventListener('click', function(e) {
            if (e.target === radiusModal) {
                closeRadiusModal();
            }
        });

        bendingLayerSelect.addEventListener('change', function() {
            selectedBendingLayers = Array.from(this.selectedOptions)
        .map(opt => opt.value)
        .filter(val => val); // фільтрувати порожній

    if (selectedBendingLayers.length > 0) {
        cornerConfig.classList.remove('hidden');
    } else {
        cornerConfig.classList.add('hidden');
    }

    validateLayerSelection();
});

        // Ініціалізація при завантаженні сторінки
        document.addEventListener('DOMContentLoaded', function() {
            updateZoom();
            showSlide(0);
        });

        document.querySelectorAll('.corner-input').forEach(input => {
    input.addEventListener('input', function () {
        const value = parseFloat(this.value);
        if (isNaN(value) || value < 0 || value > 360) {
            this.style.borderColor = '#ff3b30'; // червона рамка при помилці
        } else {
            this.style.borderColor = '#d2d2d7'; // стандартна рамка
        }
    });
});

        document.querySelector('.save-button').addEventListener('click', function () {
    let isValid = true;

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

    // тут можна додати логіку збереження
    alert('Зміни збережено успішно!');
});


        // Керування клавіатурою
        document.addEventListener('keydown', function(e) {
            switch(e.key) {
                case 'ArrowLeft':
                    previousSlide();
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                    nextSlide();
                    e.preventDefault();
                    break;
                case '+':
                case '=':
                    zoomIn();
                    e.preventDefault();
                    break;
                case '-':
                    zoomOut();
                    e.preventDefault();
                    break;
                case '0':
                    resetZoom();
                    e.preventDefault();
                    break;
            }
        });


angleSlider.addEventListener('input', function () {
    const index = parseInt(this.value);
    const angle = allowedAngles[index];
    angleValue.textContent = angle;
});




        // Функції для модального вікна радіуса
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

    if (currentRadiusTarget === -1) {
        // Обрано для всіх
        const buttons = table.querySelectorAll('button.action-button');
        buttons.forEach(button => {
            button.textContent = `${selectedRadius}px`;
            button.classList.add('transparent');
        });
    } else {
        // Обрано конкретний кут
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

            // Координати центру кута
            const centerX = 160;
            const centerY = 160;

            // Масштабуємо радіус для кращої візуалізації
            const visualRadius = radius * 8; // збільшуємо для кращого відображення

            // Точки початку заокругленого кута
            const startX = centerX - visualRadius;
            const startY = centerY;
            const endX = centerX;
            const endY = centerY - visualRadius;

            // Створюємо заокруглений кут з допомогою SVG path
            const roundedPath = [
                `M ${startX} ${centerY}`,
                `Q ${centerX} ${centerY} ${centerX} ${endY}`
            ].join(' ');

            roundedCorner.setAttribute('d', roundedPath);

            // Оновлюємо основні лінії, щоб вони не перекривались з заокругленням
            mainHorizontal.setAttribute('x2', startX);
            mainVertical.setAttribute('y1', endY);

            // Приховуємо текст радіуса
            radiusText.textContent = '';

            // Лінія радіуса (від центру до точки на дузі)
            const arcCenterX = centerX - visualRadius/2;
            const arcCenterY = centerY - visualRadius/2;
            radiusLine.setAttribute('x1', centerX);
            radiusLine.setAttribute('y1', centerY);
            radiusLine.setAttribute('x2', arcCenterX);
            radiusLine.setAttribute('y2', arcCenterY);
        }

        // Слухач змін на слайдері
        angleSlider.addEventListener('input', function () {
            const index = parseInt(this.value);
            updateRoundedCornerVisualization(index);
        });

        // Закриття по кліку поза модальним вмістом
        radiusModal.addEventListener('click', function (e) {
            if (e.target === radiusModal) {
                closeRadiusModal();
            }
        });

        // Ініціалізація початкового стану
        updateRoundedCornerVisualization(0);
