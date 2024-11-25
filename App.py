from flask import Flask, request, render_template, redirect, url_for
from PIL import Image
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

def encode_image(image_path, secret_text, secret_file_path):
    image = Image.open(image_path)
    encoded_image = image.copy()
    width, height = image.size

    # Encode the secret text into the image
    data = secret_text + '%%'  # Delimiter for end of the secret text
    data_index = 0

    # Read the secret file content
    with open(secret_file_path, 'rb') as secret_file:
        secret_data = secret_file.read()
    secret_data += b'%%'  # Delimiter for end of the secret file

    # Combine text and file data
    combined_data = data.encode() + secret_data

    for y in range(height):
        for x in range(width):
            pixel = list(image.getpixel((x, y)))
            for n in range(3):  # RGB channels
                if data_index < len(combined_data):
                    pixel[n] = pixel[n] & ~1 | (combined_data[data_index] & 1)
                    data_index += 1
            encoded_image.putpixel((x, y), tuple(pixel))
            if data_index >= len(combined_data):
                break
        if data_index >= len(combined_data):
            break

    encoded_image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'encoded_image.png'))

def decode_image(image_path):
    image = Image.open(image_path)
    width, height = image.size
    data = ""
    secret_file_data = bytearray()
    delimiter_found = False

    for y in range(height):
        for x in range(width):
            pixel = list(image.getpixel((x, y)))
            for n in range(3):  # RGB channels
                if not delimiter_found:
                    data += chr(pixel[n] & 1)
                    if data.endswith('%%'):
                        delimiter_found = True
                        data = data[:-2]  # Remove delimiter
                else:
                    secret_file_data.append(pixel[n] & 1)

            if delimiter_found and len(secret_file_data) >= 2:  # Check if there's enough data
                break
        if delimiter_found:
            break

    if secret_file_data:
        # Convert bits back to bytes
        secret_file_data = bytearray((secret_file_data[i] << 7 | secret_file_data[i + 1] << 6 | 
                                       secret_file_data[i + 2] << 5 | secret_file_data[i + 3] << 4 | 
                                       secret_file_data[i + 4] << 3 | secret_file_data[i + 5] << 2 | 
                                       secret_file_data[i + 6] << 1 | secret_file_data[i + 7]) for i in range(0, len(secret_file_data), 8))

    return data, secret_file_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        image_file = request.files['image']
        secret_text = request.form['secret_text']
        secret_file = request.files['secret_file']
        
        if image_file and secret_text and secret_file:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
            secret_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secret_file.filename)
            
            image_file.save(image_path)
            secret_file.save(secret_file_path)
            
            encode_image(image_path, secret_text, secret_file_path)
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/decode', methods=['GET', 'POST'])
def decode():
    if request.method == 'POST':
        image_file = request.files['image']
        
        if image_file:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
            image_file.save(image_path)
            
            secret_text, secret_file_data = decode_image(image_path)
            extracted_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_file.txt')
            
            if secret_file_data:
                with open(extracted_file_path, 'wb') as f:
                    f.write(secret_file_data)
            else:
                extracted_file_path = None  # Tidak ada file yang diekstrak

            return render_template('decode.html', secret_text=secret_text, extracted_file_path=extracted_file_path)

    return render_template('decode.html')

if __name__ == '__main__':
    app.run(debug=True)
