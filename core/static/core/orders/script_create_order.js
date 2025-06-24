  // Використовуємо делегування подій для кращої сумісності з динамічно створеними елементами
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.getElementById('drawings-container');
            const addBtn = document.querySelector('.order-add-drawing-btn');
            const createBtn = document.querySelector('.order-create-btn');
            const followBtn = document.querySelector('.order-follow-btn');

            // Делегування подій для кнопок у контейнері креслень
            container.addEventListener('click', function(e) {
                if (e.target.classList.contains('order-collapse-btn')) {
                    toggleCollapse(e.target);
                } else if (e.target.classList.contains('order-delete-btn')) {
                    deleteDrawing(e.target);
                } else if (e.target.classList.contains('order-processing-option') ||
                          e.target.parentElement.classList.contains('order-processing-option')) {
                    const option = e.target.classList.contains('order-processing-option') ?
                                  e.target : e.target.parentElement;
                    toggleProcessing(option);
                }
            });

            // Делегування подій для селектів
            container.addEventListener('change', function(e) {
                if (e.target.classList.contains('material-type-select')) {
                    updateMaterialOptions(e.target);
                }
            });

            // Подія для кнопки додавання креслення
            addBtn.addEventListener('click', addDrawing);

            // Події для нижніх кнопок
            createBtn.addEventListener('click', function() {
                alert('Замовлення створено!');
            });

            followBtn.addEventListener('click', function() {
                alert('Слідування увімкнено!');
            });
        });

        function toggleCollapse(button) {
            const content = button.closest('.order-drawing-block').querySelector('.order-drawing-content');
            content.classList.toggle('collapsed');
            button.classList.toggle('collapsed');
        }

        function deleteDrawing(button) {
            const drawingBlock = button.closest('.order-drawing-block');
            const container = document.getElementById('drawings-container');

            // Перевіряємо, чи залишається хоча б одне креслення
            if (container.children.length > 1) {
                drawingBlock.remove();
                // Оновлюємо нумерацію
                updateDrawingNumbers();
            } else {
                alert('Неможливо видалити останнє креслення');
            }
        }

        function updateDrawingNumbers() {
            const drawingBlocks = document.querySelectorAll('.order-drawing-block');
            drawingBlocks.forEach((block, index) => {
                const numberLabel = block.querySelector('.order-drawing-number-label');
                numberLabel.textContent = `№${index + 1}`;
            });
        }

        function toggleProcessing(option) {
            const checkbox = option.querySelector('.order-processing-checkbox');
            checkbox.checked = !checkbox.checked;
            option.classList.toggle('active', checkbox.checked);
        }

        function updateMaterialOptions(select) {
            const materialSelect = select.closest('.order-drawing-content').querySelector('.material-select');
            const value = select.value;

            materialSelect.innerHTML = '<option value="">Оберіть матеріал</option>';

            if (value === 'metal') {
                materialSelect.innerHTML += `
                    <option value="steel">Сталь</option>
                    <option value="aluminum">Алюміній</option>
                    <option value="stainless">Нержавіюча сталь</option>
                `;
            } else if (value === 'plastic') {
                materialSelect.innerHTML += `
                    <option value="abs">ABS</option>
                    <option value="pvc">ПВХ</option>
                    <option value="acrylic">Акрил</option>
                `;
            } else if (value === 'composite') {
                materialSelect.innerHTML += `
                    <option value="carbon">Карбон</option>
                    <option value="fiberglass">Скловолокно</option>
                `;
            }
        }

        function addDrawing() {
            const container = document.getElementById('drawings-container');
            const drawingCount = container.children.length + 1;

            const newDrawing = container.firstElementChild.cloneNode(true);
            newDrawing.querySelector('.order-drawing-number-label').textContent = `№${drawingCount}`;

            // Очистити значення в новому блоці
            newDrawing.querySelectorAll('input, select').forEach(element => {
                if (element.type === 'checkbox') {
                    element.checked = false;
                } else {
                    element.value = '';
                }
            });

            // Оновити стан чекбоксів (виправлений селектор)
            newDrawing.querySelectorAll('.order-processing-option').forEach(option => {
                option.classList.remove('active');
            });

            // Розгорнути новий блок, якщо він був згорнутий
            const content = newDrawing.querySelector('.order-drawing-content');
            const collapseBtn = newDrawing.querySelector('.order-collapse-btn');
            content.classList.remove('collapsed');
            collapseBtn.classList.remove('collapsed');

            container.appendChild(newDrawing);
        }