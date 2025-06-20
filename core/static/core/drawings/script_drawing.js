// Анімація при наведенні на картку
document.querySelector('.drawing-card').addEventListener('mouseenter', function() {
    this.style.borderColor = '#4285f4';
});

document.querySelector('.drawing-card').addEventListener('mouseleave', function() {
    this.style.borderColor = '#e8eaed';
});


// Модальне вікно видалення
let deleteUrl = "";

function openModal(url) {
    deleteUrl = url;
    document.getElementById("deleteModal").style.display = "flex";
}

function closeModal() {
    deleteUrl = "";
    document.getElementById("deleteModal").style.display = "none";
}

document.getElementById("confirmDelete").addEventListener("click", function () {
    window.location.href = deleteUrl;
});