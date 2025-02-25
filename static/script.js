let isDrawing = false;
let isRightDrawing = false;

function uploadImage() {
    const fileInput = document.getElementById('imageInput');
    const formData = new FormData();
    formData.append('image', fileInput.files[0]);

    fetch('/upload', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => updateImage())
        .catch(error => console.error('Ошибка:', error));
}

function updateImage() {
    const data = {
        width: parseInt(document.getElementById('width').value),
        height: parseInt(document.getElementById('height').value),
        threshold: parseInt(document.getElementById('threshold').value),
        grayscale: document.getElementById('grayscale').checked,
        invert: document.getElementById('invert').checked
    };

    fetch('/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('processedImage').src = data.image_url + '?t=' + new Date().getTime(); // Предотвращаем кэширование
        document.getElementById('result').textContent = `Enclosed Pixels: ${data.enclosed_pixels.toFixed(2)}`;
    })
    .catch(error => console.error('Ошибка:', error));
}

function moveRectangle(dx, dy) {
    fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dx, dy })
    }).then(() => updateImage());
}

function drawOnImage(x, y, brushSize, color) {
    fetch('/draw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y, brush_size: brushSize, color })
    }).then(() => updateImage());
}

// Слушатели для ползунков и чекбоксов
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('change', updateImage);
});

// Рисование на изображении
const img = document.getElementById('processedImage');
img.addEventListener('mousedown', (e) => {
    if (e.button === 0) isDrawing = true;
    if (e.button === 2) isRightDrawing = true;
});
img.addEventListener('mousemove', (e) => {
    if (isDrawing || isRightDrawing) {
        const rect = img.getBoundingClientRect();
        const x = Math.round((e.clientX - rect.left) * (img.naturalWidth / rect.width));
        const y = Math.round((e.clientY - rect.top) * (img.naturalHeight / rect.height));
        const brushSize = parseInt(document.getElementById('brushSize').value);
        const color = isDrawing ? 'white' : 'black';
        drawOnImage(x, y, brushSize, color);
    }
});
img.addEventListener('mouseup', () => {
    isDrawing = false;
    isRightDrawing = false;
});
img.addEventListener('contextmenu', (e) => e.preventDefault()); // Отключаем контекстное меню