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



// Анімація при наведенні на картку
document.querySelector('.drawing-card').addEventListener('mouseenter', function() {
    this.style.borderColor = '#4285f4';
});

document.querySelector('.drawing-card').addEventListener('mouseleave', function() {
    this.style.borderColor = '#e8eaed';
});

// Вибір файла
 const fileDropZone = document.getElementById('fileDropZone');
        const fileInputControl = document.getElementById('fileInputControl');
        const selectedFilesContainer = document.getElementById('selectedFilesContainer');
        let uploadedFiles = [];

        // Drag and drop event handlers
        fileDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileDropZone.classList.add('drag-active');
        });

        fileDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            fileDropZone.classList.remove('drag-active');
        });

        fileDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            fileDropZone.classList.remove('drag-active');
            processFileSelection(e.dataTransfer.files);
        });

        fileDropZone.addEventListener('click', () => {
            fileInputControl.click();
        });

        fileInputControl.addEventListener('change', (e) => {
            processFileSelection(e.target.files);
        });

        function processFileSelection(files) {
            for (let file of files) {
                if (checkFileValidity(file)) {
                    uploadedFiles.push(file);
                }
            }
            renderSelectedFiles();
        }

        function checkFileValidity(file) {
            const maximumSize = 10 * 1024 * 1024; // 10MB
            const validExtensions = ['dwg', 'pdf', 'dxf'];
            const fileExtension = file.name.split('.').pop().toLowerCase();

            if (file.size > maximumSize) {
                alert(`Файл "${file.name}" занадто великий. Максимальний розмір: 10 МБ`);
                return false;
            }

            if (!validExtensions.includes(fileExtension)) {
                alert(`Файл "${file.name}" має непідтримуваний формат. Дозволені: DWG, PDF, DXF`);
                return false;
            }

            return true;
        }

        function renderSelectedFiles() {
            if (uploadedFiles.length === 0) {
                selectedFilesContainer.classList.remove('show-files');
                return;
            }

            selectedFilesContainer.innerHTML = '';
            uploadedFiles.forEach((file, index) => {
                const fileDisplayElement = document.createElement('div');
                fileDisplayElement.className = 'file-display-item';
                fileDisplayElement.innerHTML = `
                    <div class="file-display-name">${file.name}</div>
                    <div class="file-display-size">${calculateFileSize(file.size)}</div>
                `;
                selectedFilesContainer.appendChild(fileDisplayElement);
            });
            selectedFilesContainer.classList.add('show-files');
        }

        function calculateFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function clearFormData() {
            document.getElementById('drawingNameField').value = '';
            document.getElementById('drawingDescriptionField').value = '';
            uploadedFiles = [];
            fileInputControl.value = '';
            selectedFilesContainer.classList.remove('show-files');
        }

        function processFormSubmission() {
            const drawingName = document.getElementById('drawingNameField').value.trim();

            if (!drawingName) {
                alert('Будь ласка, введіть назву креслення');
                document.getElementById('drawingNameField').focus();
                return;
            }

            if (uploadedFiles.length === 0) {
                alert('Будь ласка, виберіть файли для завантаження');
                return;
            }

            // Here you would send the data to server
            alert('Креслення успішно завантажено!');
            clearFormData();
        }