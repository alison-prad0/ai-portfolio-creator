# --- 1. IMPORTACIONES CORREGIDAS (Todas al inicio) ---
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, session
import os
from werkzeug.utils import secure_filename
from fpdf import FPDF 
from PIL import Image # <-- Importación de Pillow (PIL)
# Importaciones para IA
from google import genai
from dotenv import load_dotenv
# Inicializar el cliente de Gemini a None
gemini_client = None
try:
   # Esto busca la clave del .env (local) o de las variables de entorno (Render)
    gemini_client = genai.Client()
except Exception:
 # Si falla (clave no encontrada), gemini_client sigue siendo None
    pass
except Exception:
    # Permite que la aplicación corra sin la clave si está en el servidor de Render
    pass 

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
    # Obtener el ID de sesión único del usuario
    session_id = session.get('current_upload_id')
    if not session_id:
        return "Error: No se encontró la sesión de subida.", 400

    # Obtener las imágenes seleccionadas del formulario (solo nombres originales sin ID)
    selected_images = request.form.getlist('selected_images')
    if not selected_images:
        return "No hay imágenes seleccionadas para generar el PDF.", 400

    image_dir = app.config['UPLOAD_FOLDER']
    image_files_to_process = [] # Lista de nombres de archivos completos (con ID)

    # 1. Reconstruir los nombres de archivos REALES usando el ID de sesión
    for original_name in selected_images:
        # El nombre del archivo en el servidor es: ID_original.ext
        # No usamos secure_filename porque el original_name ya está seguro (viene del formulario)
        full_filename = f"{session_id}_{original_name}"
        image_files_to_process.append(full_filename)

    # Inicializar el objeto PDF
    pdf = FPDF()
    PDF_WIDTH = 210
    PDF_HEIGHT = 297

    # 2. Procesar cada imagen
    for filename in image_files_to_process: # Usamos la lista REAL de archivos
        filepath = os.path.join(image_dir, filename)
        
        # Obtener el nombre base del archivo (sin el ID de sesión)
        base_filename = filename.split('_', 1)[1] if '_' in filename else filename
        
        # 1. Obtener el título que el usuario escribió para esta imagen
        title_field_name = f'title_{base_filename}'
        user_title = request.form.get(title_field_name, "Portafolio de Imágenes (Sin Título)") # Obtiene el texto del formulario
        
        # Intenta agregar la imagen y el título al PDF
        try:
            # 2. Lógica de Redimensionamiento (similar a la que tenías)
            img = Image.open(filepath)
            img_width, img_height = img.size
            ratio = img_width / img_height
            
            if ratio > 1:
                pdf_w = PDF_WIDTH * 0.9
                pdf_h = pdf_w / ratio
            else:
                pdf_h = PDF_HEIGHT * 0.9
                pdf_w = pdf_h * ratio
                
            x = (PDF_WIDTH - pdf_w) / 2
            y = (PDF_HEIGHT - pdf_h) / 2
            
            # 3. Agregar la página y la imagen
            pdf.add_page()
            
            # 4. Agregar el TÍTULO (fijado en la parte superior)
            pdf.set_xy(10, 10) # Fija la posición muy cerca de la esquina superior izquierda
            pdf.set_font('Arial', 'B', 16) 
            pdf.set_text_color(20, 20, 20)
            pdf.cell(0, 10, user_title, 0, 1, 'C') # 0: ancho total, C: CENTRADO

            # AGREGAR SALTO DE LÍNEA GRANDE para que la imagen no toque el título
            pdf.ln(15) 
            
            # Resto de la lógica de la imagen
            pdf.image(filepath, x, pdf.get_y(), pdf_w, pdf_h) # Usamos pdf.get_y() para la coordenada y
            
        except Exception as e:
            # MANTENER: El bloque de error original
            print(f"Error al procesar la imagen {base_filename}: {e}")
            
    # 3. Guardar el PDF en un archivo temporal
    output_pdf_path = os.path.join('temp_portfolio.pdf')
    pdf.output(output_pdf_path)
    
    # --- CÓDIGO DE LIMPIEZA FINAL: Solo borra los archivos usados por ESTA sesión ---
    for filename in image_files_to_process:
        filepath = os.path.join(image_dir, filename)
        try:
            os.remove(filepath)
            print(f"Archivo borrado: {filename}")
        except Exception as e:
            print(f"Error al borrar el archivo {filename}: {e}")
            
    # Limpiar la sesión después de generar el PDF
    session.pop('uploaded_files', None)
    session.pop('current_upload_id', None)
            
    # Enviar el archivo PDF al navegador
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

# 6. Ruta de Edición con IA: Genera título y descripción
@app.route('/generate-ia', methods=['POST'])
def generate_ia():
    user_prompt = request.form.get('ia_prompt')
    current_filenames = session.get('uploaded_files', [])

    if not user_prompt:
        return render_template('edit.html', filenames=current_filenames, ia_result="Por favor, escribe tu instrucción para la IA.")
    
    # VERIFICACIÓN CRÍTICA: Si el cliente no se inicializó, devuelve el error CLARO
    if gemini_client is None:
        error_msg = "Error: El Asistente de IA no se pudo conectar. Verifica que la variable GEMINI_API_KEY esté correctamente configurada en Render."
        return render_template('edit.html', filenames=current_filenames, ia_result=error_msg)

    # 1. Definir la instrucción precisa (el "prompt") para Gemini
    prompt = f"""
    Eres un experto en branding y diseño de portafolios.
    Genera un título muy llamativo y elegante, y una breve descripción
    para un portafolio de imágenes. El usuario ha dado la siguiente instrucción:
    "{user_prompt}"

    Asegúrate de que el título sea corto y de alto impacto.
    
    Formato de Salida Requerido (DEBES usar este formato exacto):
    Título: [Título generado aquí]
    Descripción: [Descripción generada aquí]
    """
    
    # 2. Llamar a la API de Gemini
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        ia_result = response.text.strip()
        
    except Exception as e:
        ia_result = f"Error de IA: Falló la comunicación con Gemini. Detalles: {e}"

    # 3. Regresar a la página de edición con el resultado
    return render_template('edit.html', filenames=current_filenames, ia_result=ia_result)

# Punto de entrada principal para ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)