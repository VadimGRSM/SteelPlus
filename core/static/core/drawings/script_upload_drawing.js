 const dropZone = document.getElementById('fileDropZone');
    const fileInput = document.getElementById('fileInput');
    const selectedFilesContainer = document.getElementById('selectedFilesContainer');
    const defaultIcon = document.getElementById('defaultFileIcon');
    const successIcon = document.getElementById('successIcon');
    const uploadText = document.getElementById('uploadText');
    const uploadDetailsText = document.getElementById('uploadDetailsText');
    const submitButton = document.getElementById('submitButton');
    const selectedProcessesInput = document.getElementById('selectedProcesses');

    let selectedProcesses = [];

    // Обработка кликов по процесам
    document.querySelectorAll('.process-button').forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('active')) return;

            const processId = this.dataset.process;

            if (this.classList.contains('selected')) {
                // Убираем выбор
                this.classList.remove('selected');
                selectedProcesses = selectedProcesses.filter(id => id !== processId);
            } else {
                // Добавляем выбор
                this.classList.add('selected');
                selectedProcesses.push(processId);
            }

            // Обновляем скрытое поле
            selectedProcessesInput.value = selectedProcesses.join(',');

            // Проверяем возможность отправки формы
            checkFormValidity();
        });
    });

    function updateFileList(files) {
        selectedFilesContainer.innerHTML = '';
        if (files.length > 0) {
            // Показываем галочку
            defaultIcon.style.display = 'none';
            successIcon.style.display = 'block';

            const file = files[0]; // Берём первый файл
            uploadText.textContent = file.name;
            uploadDetailsText.textContent = `${(file.size / 1024 / 1024).toFixed(2)} МБ`;

            const fileDiv = document.createElement('div');
            fileDiv.className = 'file-display-item';
            fileDiv.innerHTML = `
                <div class="file-display-name">${file.name}</div>
                <div class="file-display-size">${(file.size / 1024).toFixed(1)} KB</div>
            `;
            selectedFilesContainer.appendChild(fileDiv);
            selectedFilesContainer.classList.add('show-files');
        } else {
            // Возвращаем дефолт
            defaultIcon.style.display = 'block';
            successIcon.style.display = 'none';
            uploadText.textContent = "Перетягніть файли сюди або клікніть для вибору";
            uploadDetailsText.textContent = "Підтримуються формати: DWG, PDF, DXF (макс. 10 МБ)";
            selectedFilesContainer.classList.remove('show-files');
        }
        checkFormValidity();
    }

    function checkFormValidity() {
        const hasFile = fileInput.files.length > 0;
        const hasProcesses = selectedProcesses.length > 0;
        const hasName = document.getElementById('drawingName').value.trim() !== '';

        submitButton.disabled = !(hasFile && hasProcesses && hasName);
    }

    // Обработка изменения файла
    fileInput.addEventListener('change', () => {
        updateFileList(fileInput.files);
    });

    // Проверка имени креслення
    document.getElementById('drawingName').addEventListener('input', checkFormValidity);

    // Drag & Drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-active');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-active');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        const dataTransfer = new DataTransfer();
        for (const file of files) {
            dataTransfer.items.add(file);
        }
        fileInput.files = dataTransfer.files;
        updateFileList(fileInput.files);
    });

    // Клик по зоне загрузки
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // Обработка отправки формы
    document.getElementById('drawingForm').addEventListener('submit', function(e) {
        if (selectedProcesses.length === 0) {
            e.preventDefault();
            alert('Будь ласка, оберіть хоча б один процес!');
            return false;
        }

        if (fileInput.files.length === 0) {
            e.preventDefault();
            alert('Будь ласка, оберіть файл для завантаження!');
            return false;
        }

        if (document.getElementById('drawingName').value.trim() === '') {
            e.preventDefault();
            alert('Будь ласка, введіть назву креслення!');
            return false;
        }
    });

    // Инициальная проверка
    checkFormValidity();