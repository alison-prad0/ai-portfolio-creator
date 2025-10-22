# AI Portfolio Creator

Una aplicación web que permite crear portafolios de imágenes con IA usando Flask y Google Gemini.

## Características

- Subida de múltiples imágenes
- Generación de títulos y descripciones con IA
- Creación de PDFs profesionales
- Interfaz web moderna
- Compatible con Render y otros servidores

## Configuración Local

1. Clona el repositorio
2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Copia `env.example` a `.env` y configura tus variables:
   ```bash
   cp env.example .env
   ```
5. Edita `.env` con tus claves reales
6. Ejecuta la aplicación:
   ```bash
   python app.py
   ```

## Despliegue en Render

### Variables de Entorno en Render

Configura estas variables en tu dashboard de Render:

- `SECRET_KEY`: Una clave secreta larga y segura para Flask
- `GEMINI_API_KEY`: Tu clave API de Google Gemini
- `FLASK_ENV`: `production`

### Pasos para Render

1. Conecta tu repositorio de GitHub a Render
2. Selecciona "Web Service"
3. Configura:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: `Python 3`
4. Agrega las variables de entorno mencionadas arriba
5. Despliega

## Obtener Clave API de Gemini

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Crea una nueva API key
4. Copia la clave y agrégala a tus variables de entorno

## Estructura del Proyecto

```
ai-portfolio-creator/
├── app.py              # Aplicación principal Flask
├── requirements.txt    # Dependencias de Python
├── Procfile           # Configuración para Render
├── env.example        # Ejemplo de variables de entorno
├── templates/         # Plantillas HTML
│   ├── index.html
│   ├── edit.html
│   └── message.html
└── uploads/           # Carpeta temporal para imágenes
```

## Funcionalidades

- **Subida de Imágenes**: Soporte para PNG, JPG, JPEG
- **IA Integrada**: Genera títulos y descripciones usando Gemini
- **Generación de PDF**: Crea portafolios profesionales
- **Limpieza Automática**: Elimina archivos temporales
- **Interfaz Responsiva**: Funciona en móviles y escritorio

## Solución de Problemas

### Error de Gemini API
- Verifica que `GEMINI_API_KEY` esté configurada correctamente
- Asegúrate de que la clave sea válida y tenga permisos

### Error de Archivos
- Verifica que la carpeta `uploads` tenga permisos de escritura
- En Render, los archivos temporales se limpian automáticamente

### Error de Puerto
- Render usa automáticamente la variable `PORT`
- Para desarrollo local, usa el puerto 5000 por defecto

## Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **IA**: Google Gemini API
- **PDF**: FPDF2
- **Imágenes**: Pillow (PIL)
- **Despliegue**: Render, Gunicorn
- **Frontend**: HTML, CSS, JavaScript
