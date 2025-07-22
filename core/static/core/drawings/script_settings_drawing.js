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

// =================== Валідація ===================

function validateLayerSelection() {
    const cuttingLayers = Array.from(document.querySelectorAll('select[name="cutting"] option:checked')).map(option => option.value);
    const bendingLayers = Array.from(document.querySelectorAll('select[name="bending"] option:checked')).map(option => option.value);

    const overlapping = cuttingLayers.filter(layer => bendingLayers.includes(layer));
    if (overlapping.length > 0) {
        return false;
    }

    return true;
}

function validateBendingConfiguration() {
    const bendingLayers = Array.from(document.querySelectorAll('select[name="bending"] option:checked')).map(option => option.value);

    if (bendingLayers.length === 0) {
        return { valid: true, errors: [] };
    }

    const errors = [];
    const rows = document.querySelectorAll('.corner-table tbody tr');

    if (rows.length === 0 || (rows.length === 1 && rows[0].cells.length === 1)) {
        errors.push('Немає налаштованих кутів для вибраних шарів згинання.');
        return { valid: false, errors };
    }

    rows.forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells.length === 4) {
            const pointButton = cells[0].querySelector('button');
            const degreeInput = cells[1].querySelector('input');
            const radiusButton = cells[3].querySelector('button');

            if (pointButton && degreeInput && radiusButton) {
                const pointText = pointButton.textContent.trim();
                const degreeValue = degreeInput.value.trim();
                const radiusText = radiusButton.textContent.trim();

                if (!pointText || pointText === 'Обрати' || pointText.includes('Клікніть на зображення')) {
                    errors.push(`Угол ${index + 1}: не выбрана точка на изображении.`);
                }

                if (!degreeValue) {
                    errors.push(`Угол ${index + 1}: не задан градус изгиба.`);
                } else {
                    const degree = parseFloat(degreeValue);
                    if (isNaN(degree) || degree < 0 || degree > 360) {
                        errors.push(`Угол ${index + 1}: градус должен быть от 0 до 360.`);
                    }
                }

                if (!radiusText || radiusText === 'Обрати') {
                    errors.push(`Угол ${index + 1}: не задан радиус изгиба.`);
                }
            }
        }
    });

    return { valid: errors.length === 0, errors };
}

function updateSaveButtonState() {
    const saveButton = document.querySelector('.save-button');
    if (!saveButton) return;

    const selectedProcessIds = Array.from(document.querySelectorAll('#process-multiselect option:checked')).map(opt => opt.value);
    if (selectedProcessIds.length === 0) {
        saveButton.disabled = true;
        saveButton.style.opacity = '0.5';
        saveButton.style.cursor = 'not-allowed';
        saveButton.title = 'Оберіть хоча б один процес';
        return;
    }

    let isValid = true;
    let errorMessage = '';

    selectedProcessIds.forEach(pid => {
        if (pid == '1') { // Різка
            const cuttingSelect = document.querySelector('.process-section[data-process-id="1"] select[name="cutting"]');
            if (cuttingSelect && cuttingSelect.selectedOptions.length === 0) {
                isValid = false;
                errorMessage += 'Оберіть хоча б один шар для різки.\n';
            }
        }
        if (pid == '2') { // Гибка
            const bendingSelect = document.querySelector('.process-section[data-process-id="2"] select[name="bending"]');
            if (bendingSelect && bendingSelect.selectedOptions.length === 0) {
                isValid = false;
                errorMessage += 'Оберіть хоча б один шар для згинання.\n';
            }
            const bendingValidation = validateBendingConfiguration();
            if (!bendingValidation.valid) {
                isValid = false;
                errorMessage += bendingValidation.errors.join('\n');
            }
        }
        // Можно додати перевірки і для інших процесів
    });

    const isLayerSelectionValid = validateLayerSelection();
    if (!isLayerSelectionValid) {
        isValid = false;
        errorMessage += 'Шари для різання та згинання не повинні перетинатися.\n';
    }

    saveButton.disabled = !isValid;
    saveButton.style.opacity = isValid ? '1' : '0.5';
    saveButton.style.cursor = isValid ? 'pointer' : 'not-allowed';
    saveButton.title = isValid ? '' : errorMessage;
}

document.addEventListener('DOMContentLoaded', function() {
    updateSaveButtonState();

    const selects = document.querySelectorAll('.dropdown-multiselect');
    selects.forEach(select => {
        select.addEventListener('change', updateSaveButtonState);
    });

    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('corner-input')) {
            updateSaveButtonState();
        }
    });

    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('pick-point-btn') || e.target.classList.contains('action-button')) {
            setTimeout(updateSaveButtonState, 100);
        }
    });

    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                updateSaveButtonState();
            }
        });
    });

    const tableBends = document.getElementById('table-bends');
    if (tableBends) {
        observer.observe(tableBends, { childList: true, subtree: true });
    }
});

document.querySelector("form").addEventListener("submit", function (e) {
    const isLayerSelectionValid = validateLayerSelection();
    const bendingValidation = validateBendingConfiguration();

    if (!isLayerSelectionValid) {
        e.preventDefault();
        alert('Помилка: Шари для різання та згинання не повинні перетинатися.');
        return;
    }

    if (!bendingValidation.valid) {
        e.preventDefault();
        alert('Помилки у налаштуванні кутів:\n' + bendingValidation.errors.join('\n'));
        return;
    }

    const cuttingLengthLabel = document.querySelector("#cutting-length-container .info-label");
    const cuttingLengthText = cuttingLengthLabel ? cuttingLengthLabel.textContent.trim() : "0";
    const lengthValue = cuttingLengthText.match(/[\d\.]+/);
    if (document.getElementById("id_length_of_cuts")) {
        document.getElementById("id_length_of_cuts").value = lengthValue ? lengthValue[0] : "0";
    }

    const rows = document.querySelectorAll(".corner-table tbody tr");
    const bendsData = [];

    rows.forEach(row => {
        const cells = row.querySelectorAll("td");
        if (cells.length === 4) {
            const pointButton = cells[0].querySelector("button");
            const degreeInput = cells[1].querySelector("input");
            const orientationCheckbox = cells[2].querySelector("input");
            const radiusButton = cells[3].querySelector("button");

            if (pointButton && degreeInput && orientationCheckbox && radiusButton) {
                 bendsData.push({
                    point: pointButton.textContent.trim(),
                    degree: degreeInput.value,
                    orientation: orientationCheckbox.checked ? "Вверх" : "Вниз",
                    radius: radiusButton.textContent.trim() === "Обрати" ? "" : radiusButton.textContent.trim()
                });
            }
        }
    });

    var anglesInput = document.getElementById("id_angles_2");
    if (anglesInput) {
        anglesInput.value = JSON.stringify(bendsData);
    }
});

const originalConfirmRadius = confirmRadius;
confirmRadius = function() {
    originalConfirmRadius();
    updateSaveButtonState();
};

targetImages.forEach(image => {
    image.addEventListener("click", function (event) {
        if (!activeButton) return;

        const rect = this.getBoundingClientRect();
        const naturalWidth = this.naturalWidth;
        const naturalHeight = this.naturalHeight;
        const displayedWidth = rect.width;
        const displayedHeight = rect.height;

        const scale = Math.min(
            displayedWidth / naturalWidth,
            displayedHeight / naturalHeight
        );

        const fittedWidth = naturalWidth * scale;
        const fittedHeight = naturalHeight * scale;

        const offsetX = (displayedWidth - fittedWidth) / 2;
        const offsetY = (displayedHeight - fittedHeight) / 2;

        const clickX = event.clientX - rect.left - offsetX;
        const clickY = event.clientY - rect.top - offsetY;

        if (clickX < 0 || clickY < 0 || clickX > fittedWidth || clickY > fittedHeight) {
            console.log("Клік поза зображенням");
            return;
        }

        const scaledX = Math.round(clickX / scale);
        const scaledY = Math.round(clickY / scale);

        activeButton.textContent = `${this.alt} [${scaledX}; ${scaledY}]`;
        activeButton.classList.add("picked");
        activeButton = null;

        updateSaveButtonState();
    });
});
