document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('drawings-container');
    const addBtn = document.querySelector('.order-add-drawing-btn');
    const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');

    container.addEventListener('click', function (e) {
        if (e.target.classList.contains('order-collapse-btn')) {
            toggleCollapse(e.target);
        } else if (e.target.classList.contains('order-delete-btn')) {
            deleteDrawing(e.target);
        }
    });

    container.addEventListener('change', function (e) {
        if (e.target.classList.contains('material-type-select')) {
            updateMaterialOptions(e.target);
        }
        
        if (e.target.name && e.target.name.includes('form-')) {
            if (e.target.name.includes('-material') && e.target.value) {
                const block = e.target.closest('.order-drawing-block');
                const priceDiv = block.querySelector('.order-form-price-result');
                if (priceDiv) {
                    sendHtmxRequest(priceDiv, block);
                }
            }
        }
    });
    
    container.addEventListener('input', function (e) {
        if (e.target.type === 'number' && e.target.name && e.target.name.includes('form-')) {
            const block = e.target.closest('.order-drawing-block');
            const priceDiv = block.querySelector('.order-form-price-result');
            if (priceDiv) {
                clearTimeout(priceDiv._timeout);
                priceDiv._timeout = setTimeout(() => {
                    sendHtmxRequest(priceDiv, block);
                }, 500);
            }
        }
    });
    
    addBtn.addEventListener('click', addDrawing);
    
    function sendHtmxRequest(priceDiv, block) {
        const url = priceDiv.getAttribute('hx-get');
        
        const params = new URLSearchParams();
        params.append('index', block.getAttribute('data-index'));
        
        block.querySelectorAll('select, input').forEach(el => {
            if (el.name && el.value) {
                params.append(el.name, el.value);
            }
        });
        
        let fullUrl = url;
        if (url.includes('?')) {
            fullUrl += '&' + params.toString();
        } else {
            fullUrl += '?' + params.toString();
        }

        fetch(fullUrl)
            .then(response => response.text())
            .then(html => {
                priceDiv.innerHTML = html;
            })
            .catch(error => {
                console.error('Error sending HTMX request:', error);
            });
    }

    function toggleCollapse(button) {
    const content = button.closest('.order-drawing-block').querySelector('.order-drawing-content');
    content.classList.toggle('collapsed');
    button.classList.toggle('collapsed');
}

function deleteDrawing(button) {
    const drawingBlock = button.closest('.order-drawing-block');
    if (container.children.length > 1) {
        drawingBlock.remove();
        updateDrawingNumbers();
        updateFormIndexes();
    } else {
        alert('Неможливо видалити останнє креслення');
    }
}

function updateDrawingNumbers() {
    const blocks = container.querySelectorAll('.order-drawing-block');
    blocks.forEach((block, index) => {
        const label = block.querySelector('.order-drawing-number-label');
        label.textContent = `№${index + 1}`;
    });
}

function updateFormIndexes() {
    const blocks = container.querySelectorAll('.order-drawing-block');
    blocks.forEach((block, index) => {
        block.setAttribute('data-index', index);
        const priceDiv = block.querySelector('.order-form-price-result');
        if (priceDiv) {
            priceDiv.setAttribute('data-index', index);
            priceDiv.setAttribute('hx-get', detailPriceUrl + "?index=" + index);
            priceDiv.setAttribute('hx-target', 'this');
            priceDiv.setAttribute('hx-trigger', 'change from:select,input delay:300ms');
            priceDiv.setAttribute('hx-include', 'closest .order-drawing-block');
            priceDiv.setAttribute('hx-swap', 'outerHTML');
        }
        block.querySelectorAll('select, input').forEach(el => {
            const name = el.name;
            if (name && name.includes('form-')) {
                const parts = name.split('-');
                const field = parts.slice(2).join('-');
                el.name = `form-${index}-${field}`;
            }
        });
    });
    totalFormsInput.value = blocks.length;
    
    blocks.forEach(block => {
        htmx.process(block);
    });
}

function updateMaterialOptions(select) {
    const block = select.closest('.order-drawing-block');
    const materialSelect = block.querySelector('.material-select');
    const selectedType = select.value;

    materialSelect.innerHTML = '<option value="">Оберіть різновид матеріалу</option>';

    if (!selectedType) {
        materialSelect.disabled = true;
        materialSelect.value = '';
        return;
    }

    allMaterials.forEach(mat => {
        if (mat.material_type == selectedType) {
            const option = document.createElement("option");
            option.value = mat.id;
            option.textContent = mat.material_name;
            materialSelect.appendChild(option);
        }
    });
    materialSelect.disabled = false;
    materialSelect.value = '';
}

function addDrawing() {
    const blocks = container.querySelectorAll('.order-drawing-block');
    const index = blocks.length;
    const firstBlock = blocks[0];
    const newBlock = firstBlock.cloneNode(true);

    newBlock.setAttribute('data-index', index);
    newBlock.querySelector('.order-drawing-number-label').textContent = `№${index + 1}`;

    newBlock.querySelectorAll('input, select').forEach(el => {
        if (el.type === 'checkbox') {
            el.checked = false;
        } else {
            el.value = '';
        }

        if (el.classList.contains('material-select')) {
            el.innerHTML = '<option value="">Спочатку оберіть вид матеріалу</option>';
            el.disabled = true;
        }

        if (el.name && el.name.includes('form-')) {
            const parts = el.name.split('-');
            const field = parts.slice(2).join('-');
            el.name = `form-${index}-${field}`;
        }
    });

    const priceDiv = newBlock.querySelector(".order-form-price-result");
    if (priceDiv) {
        priceDiv.setAttribute("data-index", index);
        priceDiv.setAttribute("hx-target", "this");
        priceDiv.setAttribute("hx-trigger", "change from:select,input delay:300ms");
        priceDiv.setAttribute("hx-include", "closest .order-drawing-block");
        priceDiv.setAttribute("hx-swap", "outerHTML");
        priceDiv.setAttribute("hx-get", detailPriceUrl + "?index=" + index);
        priceDiv.innerHTML = "Вкажіть всі поля для розрахунку";
    }

    container.appendChild(newBlock);
    totalFormsInput.value = index + 1;

    htmx.process(newBlock);
}

});