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
    const modal = document.getElementById("deleteModal");
    modal.classList.add("show");
}

function closeModal() {
    deleteUrl = "";
    const modal = document.getElementById("deleteModal");
    modal.classList.remove("show");
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("confirmDelete").addEventListener("click", function () {
        window.location.href = deleteUrl;
    });
});