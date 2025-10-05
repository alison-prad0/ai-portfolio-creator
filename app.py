# --- 1. IMPORTACIONES CORREGIDAS (Todas al inicio) ---
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, session
import os
from werkzeug.utils import secure_filename
from fpdf import FPDF 
from PIL import Image # <-- Importación de Pillow (PIL)

# --- CONFIGURACIÓN ---
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Necesario para sesiones
# Crea una carpeta llamada 'uploads' para guardar temporalmente las imágenes
UPLOAD_FOLDER = 'uploads'
# Verifica si la carpeta 'uploads' existe, si no, la crea
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Define las extensiones de archivo permitidas (seguridad)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    """Limpia archivos antiguos de la carpeta uploads (más de 1 hora)"""
    import time
    current_time = time.time()
    image_dir = app.config['UPLOAD_FOLDER']
    
    if not os.path.exists(image_dir):
        return
    
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(image_dir, filename)
            try:
                # Si el archivo es más antiguo que 1 hora, lo elimina
                if current_time - os.path.getmtime(filepath) > 3600:
                    os.remove(filepath)
                    print(f"Archivo antiguo eliminado: {filename}")
            except Exception as e:
                print(f"Error al eliminar archivo antiguo {filename}: {e}")

# --- RUTAS DE LA APLICACIÓN ---

# 1. Ruta principal: Muestra el formulario (archivo index.html)
@app.route('/')
def index():
    # Limpiar archivos antiguos al cargar la página principal
    cleanup_old_files()
    # Esto carga el archivo HTML con el formulario de subida
    return render_template('index.html') 

# 2. Ruta de Subida: Procesa los archivos del formulario
@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file' not in request.files:
        return redirect(request.url) 

    files = request.files.getlist('file')
    uploaded_filenames = []
    
    # Generar un ID único para esta sesión de subida
    import uuid
    session_id = str(uuid.uuid4())
    session['current_upload_id'] = session_id

    for file in files:
        if file and allowed_file(file.filename):
            # Crear nombre único para evitar conflictos
            original_filename = secure_filename(file.filename)
            name, ext = os.path.splitext(original_filename)
            filename = f"{session_id}_{name}{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_filenames.append(filename)

    # Guardar la lista de archivos en la sesión
    session['uploaded_files'] = uploaded_filenames
    
    # Redirige a la página de edición (edit.html)
    return render_template('edit.html', filenames=uploaded_filenames)

# 3. Ruta para servir los archivos subidos (hace que las imágenes sean visibles al navegador)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 4. Ruta para generar el PDF
@app.route('/create-pdf', methods=['POST'])
def create_pdf():
    # Obtener las imágenes seleccionadas del formulario
    selected_images = request.form.getlist('selected_images')
    
    if not selected_images:
        return "No hay imágenes seleccionadas para generar el PDF.", 400
    
    image_dir = app.config['UPLOAD_FOLDER']
    image_files = selected_images

    # Inicializar el objeto PDF
    pdf = FPDF()
    
    # Parámetros del PDF (por ejemplo, tamaño A4)
    # 210 y 297 son las dimensiones de A4 en mm
    PDF_WIDTH = 210
    PDF_HEIGHT = 297
    
    # Procesar cada imagen
    for filename in image_files:
        filepath = os.path.join(image_dir, filename)
        
        # 1. Agregar una nueva página para cada imagen
        pdf.add_page()
        
        # 2. Insertar la imagen, ajustando el tamaño
        try:
            # Ya importamos Image arriba, así que la usamos directamente
            img = Image.open(filepath)
            img_width, img_height = img.size
            
            # Calcular la relación de aspecto y el tamaño para que quepa en el PDF
            ratio = img_width / img_height
            
            # Ajustar dimensiones para que quepa en el PDF
            if ratio > 1:
                pdf_w = PDF_WIDTH * 0.9
                pdf_h = pdf_w / ratio
            else:
                pdf_h = PDF_HEIGHT * 0.9
                pdf_w = pdf_h * ratio
                
            # Centrar la imagen
            x = (PDF_WIDTH - pdf_w) / 2
            y = (PDF_HEIGHT - pdf_h) / 2
            
            pdf.image(filepath, x=x, y=y, w=pdf_w)
            
            # Opcional: Escribir el nombre del archivo
            pdf.set_xy(10, 10)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, filename, 0, 1, 'L')
            
        except Exception as e:
            # En caso de que falle PIL/fpdf2, simplemente saltamos la imagen
            print(f"Error al procesar la imagen {filename}: {e}")
            
 # Guardar el PDF en un archivo temporal
    output_pdf_path = os.path.join('temp_portfolio.pdf')
    pdf.output(output_pdf_path)
    
    # --- CÓDIGO AÑADIDO: Limpiar solo las imágenes usadas en el PDF ---
    
    # Recorre cada nombre de archivo que se usó para el PDF
    for filename in image_files:
        filepath = os.path.join(image_dir, filename)
        try:
            # Elimina el archivo del servidor
            os.remove(filepath)
            print(f"Archivo borrado: {filename}")
        except Exception as e:
            # En caso de error (ej. el archivo ya fue borrado), no bloquea la app
            print(f"Error al borrar el archivo {filename}: {e}")
            
    # Limpiar la sesión después de generar el PDF
    session.pop('uploaded_files', None)
    session.pop('current_upload_id', None)
            
    # --- FIN DEL CÓDIGO DE LIMPIEZA ---
    
    # Enviar el archivo PDF al navegador
    # Nota: os.remove('temp_portfolio.pdf') no es necesario porque send_file se encarga de archivos temporales
    return send_file(
        output_pdf_path,
        as_attachment=True,
        download_name='Portafolio_IA.pdf',
        mimetype='application/pdf'
    )

# 5. Ruta para limpiar todas las imágenes (opcional)
@app.route('/cleanup', methods=['POST'])
def cleanup_all():
    """Limpia todas las imágenes de la carpeta uploads"""
    image_dir = app.config['UPLOAD_FOLDER']
    
    if not os.path.exists(image_dir):
        return "No hay archivos para limpiar", 200
    
    removed_count = 0
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(image_dir, filename)
            try:
                os.remove(filepath)
                removed_count += 1
            except Exception as e:
                print(f"Error al eliminar {filename}: {e}")
    
    return f"Se eliminaron {removed_count} archivos", 200

# Punto de entrada principal para ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
