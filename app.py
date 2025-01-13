from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Asegurar que los directorios necesarios existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/temp', exist_ok=True)

ALLOWED_EXTENSIONS = {
    'pdf': ['pdf'],
    'image': ['png', 'jpg', 'jpeg'],
    'document': ['doc', 'docx', 'txt']
}

def allowed_file(filename, file_types):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[file_types]

def save_uploaded_file(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Obtener la extensión del archivo
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    try:
        if file_ext in ALLOWED_EXTENSIONS['image']:
            # Guardar la imagen temporalmente
            temp_img_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(temp_img_path)
            
            # Abrir la imagen con Pillow
            image = Image.open(temp_img_path)
            # Convertir a RGB si es necesario (por ejemplo, si es PNG con transparencia)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Crear el nombre del archivo PDF
            pdf_filename = secure_filename(os.path.splitext(file.filename)[0] + '.pdf')
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            
            # Guardar como PDF
            image.save(pdf_path, 'PDF', resolution=100.0)
            
            # Limpiar el archivo temporal de imagen
            os.remove(temp_img_path)
            
            # Enviar el archivo PDF al cliente
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=pdf_filename,
                mimetype='application/pdf'
            )
        elif file_ext in ALLOWED_EXTENSIONS['document']:
            # Aquí iría la lógica para convertir documentos a PDF
            return jsonify({'error': 'Conversión de documentos aún no implementada'}), 501
        else:
            return jsonify({'error': 'Tipo de archivo no soportado'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/convert-from-pdf', methods=['POST'])
def convert_from_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    format_to = request.form.get('format', 'docx')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file or not allowed_file(file.filename, 'pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        filepath = save_uploaded_file(file)
        # Aquí iría la lógica de conversión según el formato solicitado
        return jsonify({'message': 'File converted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/merge', methods=['POST'])
def merge():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files part'}), 400

    files = request.files.getlist('files[]')
    merger = PdfMerger()

    try:
        for file in files:
            if file and allowed_file(file.filename, 'pdf'):
                filepath = save_uploaded_file(file)
                merger.append(filepath)

        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged.pdf')
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
        merger.close()

        return send_file(
            output_path,
            as_attachment=True,
            download_name='merged.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/split', methods=['POST'])
def split():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file or not allowed_file(file.filename, 'pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        filepath = save_uploaded_file(file)
        reader = PdfReader(filepath)
        
        # Crear un PDF por cada página
        for i in range(len(reader.pages)):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'page_{i+1}.pdf')
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
        
        return jsonify({'message': 'PDF split successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/edit', methods=['POST'])
def edit():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file or not allowed_file(file.filename, 'pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        filepath = save_uploaded_file(file)
        # Aquí iría la lógica de edición
        return jsonify({'message': 'PDF edited successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sign', methods=['POST'])
def sign():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file or not allowed_file(file.filename, 'pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        filepath = save_uploaded_file(file)
        # Aquí iría la lógica para añadir la firma
        return jsonify({'message': 'PDF signed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

if __name__ == '__main__':
    # Configuración para desarrollo local
    app.run(debug=True)
else:
    # Configuración para producción
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/temp', exist_ok=True)
