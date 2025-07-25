const dropZone = document.getElementById('fileDropZone');
const fileInput = document.getElementById('id_file_path');
const selectedFilesContainer = document.getElementById('selectedFilesContainer');

const defaultIcon = document.getElementById('defaultFileIcon');
const successIcon = document.getElementById('successIcon');
const uploadText = document.getElementById('uploadText');
const uploadDetailsText = document.getElementById('uploadDetailsText');

function updateFileList(files) {
    selectedFilesContainer.innerHTML = '';
    if (files.length > 0) {
        defaultIcon.style.display = 'none';
        successIcon.style.display = 'block';

        const file = files[0]; 
        uploadText.textContent = file.name;
        uploadDetailsText.textContent = `${(file.size / 1024 / 1024).toFixed(2)} МБ`;

        const p = document.createElement('p');
        p.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        selectedFilesContainer.appendChild(p);
    } else {
        defaultIcon.style.display = 'block';
        successIcon.style.display = 'none';
        uploadText.textContent = "Перетягніть файли сюди або клікніть для вибору";
        uploadDetailsText.textContent = "Підтримуються формати: DWG, PDF, DXF (макс. 10 МБ)";
    }
}

fileInput.addEventListener('change', () => {
    updateFileList(fileInput.files);
});

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
    });
});

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.classList.add('drop-zone-hover');
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.classList.remove('drop-zone-hover');
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