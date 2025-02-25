import cv2
import numpy as np
from flask import Flask, request, render_template, jsonify, send_from_directory
import os
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Инициализация глобальных переменных
current_image = None
rect_x, rect_y = 0, 0


def count_enclosed_pixels(image, width_divisor=1, height_divisor=1, gray_threshold=127, grayscale=False, invert=False):
    if grayscale:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Всё равно нужен grayscale для анализа
    if invert:
        gray = cv2.bitwise_not(gray)
    _, binary = cv2.threshold(gray, gray_threshold, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(binary)
    cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)
    enclosed_pixels = np.sum(mask == 255)
    if width_divisor > 0 and height_divisor > 0:
        enclosed_pixels /= (width_divisor * height_divisor)
    return enclosed_pixels, mask


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    global current_image
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    file = request.files['image']
    img_array = np.frombuffer(file.read(), np.uint8)
    current_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'original.png')
    cv2.imwrite(filepath, current_image)
    return jsonify({'image_url': '/uploads/original.png'})


@app.route('/process', methods=['POST'])
def process_image():
    global current_image, rect_x, rect_y
    if current_image is None:
        return jsonify({'error': 'No image loaded'}), 400

    data = request.json
    width_divisor = data.get('width', 1)
    height_divisor = data.get('height', 1)
    gray_threshold = data.get('threshold', 127)
    grayscale = data.get('grayscale', False)
    invert = data.get('invert', False)

    enclosed_pixels, mask = count_enclosed_pixels(current_image, width_divisor, height_divisor, gray_threshold,
                                                  grayscale, invert)

    # Отрисовка прямоугольника
    display_image = current_image.copy()
    rect_width = min(width_divisor, current_image.shape[1])
    rect_height = min(height_divisor, current_image.shape[0])
    x1, y1 = rect_x, rect_y
    x2, y2 = rect_x + rect_width, rect_y + rect_height
    cv2.rectangle(display_image, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # Сохранение результата
    combined = np.hstack((display_image, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)))
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed.png')
    cv2.imwrite(output_path, combined)

    return jsonify({
        'image_url': '/uploads/processed.png',
        'enclosed_pixels': float(enclosed_pixels)
    })


@app.route('/move', methods=['POST'])
def move_rectangle():
    global rect_x, rect_y
    data = request.json
    dx = data.get('dx', 0)
    dy = data.get('dy', 0)
    rect_x += dx
    rect_y += dy
    return process_image()  # Повторно обрабатываем изображение с новым положением


@app.route('/draw', methods=['POST'])
def draw_on_image():
    global current_image
    if current_image is None:
        return jsonify({'error': 'No image loaded'}), 400

    data = request.json
    x = data.get('x')
    y = data.get('y')
    brush_size = data.get('brush_size', 1)
    color = data.get('color', 'white')

    color_value = (255, 255, 255) if color == 'white' else (0, 0, 0)
    cv2.circle(current_image, (x, y), brush_size, color_value, -1)
    return process_image()  # Обновляем изображение


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)