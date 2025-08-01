// Анімація при наведенні на картку
document.querySelectorAll('.drawing-card').forEach(function(card) {
    card.addEventListener('mouseenter', function() {
        this.style.borderColor = '#4285f4';
    });
    card.addEventListener('mouseleave', function() {
        this.style.borderColor = '#e8eaed';
    });
});


// Модальне вікно видалення
let deleteUrl = "";

function openModal(url) {
    deleteUrl = url;
    const modal = document.getElementById("deleteModal");
    modal.classList.add("active");
}

function closeModal() {
    deleteUrl = "";
    const modal = document.getElementById("deleteModal");
    modal.classList.remove("active");
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("confirmDelete").addEventListener("click", function () {
        window.location.href = deleteUrl;
    });
    
    document.getElementById("deleteModal").addEventListener("click", function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
});