"""
BAERA Chatbot Backend con Google Gemini (Versión Simplificada)
Sistema de chatbot para información de becas UMSA usando Gemini AI directamente
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
import pandas as pd
import google.generativeai as genai
import logging
from datetime import datetime
import unicodedata
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask
# Inicializar Flask apuntando a la carpeta frontend para archivos estáticos
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, '..', 'frontend')
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# Configuración
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    logger.warning("⚠️  GOOGLE_API_KEY no encontrada. Por favor configura tu .env")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Variables globales
knowledge_base = ""
chat_histories = {}  # Almacenar historiales por sesión
documentos_imagenes = {}  # Almacenar imágenes de documentos requeridos (mapa rápido)
documentos_catalogo = []  # Catálogo detallado de documentos con palabras clave
comunicados_media = {}  # Almacenar comunicados con imágenes por ID
ubicaciones_map = {} # Almacenar ubicaciones con imágenes

IMAGE_REQUEST_KEYWORDS = [
    'muestra', 'mostrar', 'ver imagen', 'ver imágenes', 'ver imagenes', 'imagen', 'imágenes', 'imagenes',
    'foto', 'fotos', 'fotografía', 'fotografías', 'fotografia', 'fotografias', 'dame imagen', 'quiero ver',
    'puedo ver', 'muéstrame', 'muestrame', 'enseña', 'enseñame', 'ensename', 'ver ejemplo', 'ejemplo visual',
    'darme', 'pasame', 'dame', 'tienes'
]

# Palabras de confirmación para mostrar imágenes
CONFIRMATION_KEYWORDS = [
    'si', 'sí', 'por favor', 'porfavor', 'claro', 'por supuesto', 'adelante', 'ok', 'okay',
    'vale', 'perfecto', 'bueno', 'bien', 'dale', 'vamos', 'empieza', 'comienza'
]

DOCUMENT_REFERENCE_KEYWORDS = [
    'documento', 'documentos', 'folder', 'carpeta', 'presentación', 'presentacion',
    'boleta', 'inscripción', 'inscripcion', 'plan de estudios', 'croquis', 'fotografía', 'fotografia'
]

COMUNICADO_REFERENCE_KEYWORDS = [
    'comunicado', 'comunicados', 'ultimo comunicado', 'último comunicado', 'ultimos comunicados', 'últimos comunicados',
    'pago', 'pagos', 'pagaron', 'pagado', 'abonado', 'abonaron',
    'fecha de pago', 'fecha de pagos', 'cuando pagan', 'cuando pagaron', 'ya pagaron', 'ya pagaron este mes',
    'cronograma', 'aviso', 'avisos', 'anuncio', 'anuncios', 'publicación', 'publicacion',
    'boleta de pago', 'recoger boleta', 'reciente', 'recientes'
]


def normalize_text(text: str) -> str:
    if not text:
        return ''
    normalized = unicodedata.normalize('NFD', text.lower())
    return ''.join(
        ch for ch in normalized
        if unicodedata.category(ch) != 'Mn'
    )


def build_section_images(answer_text: str, include_all_docs=False):
    """
    Determina qué imágenes pertenecen a cada sección mencionada en la respuesta.
    
    Args:
        answer_text: Texto de la respuesta del bot
        include_all_docs: Si es True, incluye TODAS las imágenes de cada categoría mencionada,
                        sin filtrar por coincidencias en el texto. Útil cuando el usuario
                        confirma que quiere ver todas las imágenes.
    """
    if not documentos_catalogo or not answer_text:
        return []
    normalized_answer = normalize_text(answer_text)
    category_positions = {}
    
    # Orden de prioridad de categorías (para cuando include_all_docs=True)
    category_order = {
        'PRESENTACIÓN': 1,
        'ACADÉMICO': 2,
        'SOCIO-ECONÓMICO': 3,
        'Socio-Económico': 3,
        'SOCIOECONÓMICO': 3
    }
    
    for doc in documentos_catalogo:
        category = doc.get('category')
        cat_norm = doc.get('category_normalized')
        if not category or not cat_norm:
            continue
        
        # Usar regex para buscar la categoría seguida de dos puntos (ej. "presentacion:")
        # Esto evita falsos positivos cuando se menciona la palabra en el texto normal
        pattern = re.escape(cat_norm) + r'\s*:'
        match = re.search(pattern, normalized_answer)
        
        if match:
            idx = match.start()
            if category not in category_positions or idx < category_positions[category]:
                category_positions[category] = idx
                
    # Si no se encontraron categorías en la respuesta, no devolver imágenes
    if not category_positions:
        return []
    
    # Ordenar categorías: primero por posición en el texto, luego por orden de prioridad
    ordered_categories = sorted(
        category_positions.items(), 
        key=lambda item: (item[1], category_order.get(item[0], 999))
    )
    
    sections = []
    for category, _ in ordered_categories:
        seen_urls = set()
        images = []
        category_docs = [doc for doc in documentos_catalogo if doc.get('category') == category]
        
        # Si include_all_docs es True, incluir TODAS las imágenes de la categoría
        if include_all_docs:
            for doc in category_docs:
                url = doc.get('imagen_url')
                if url and url not in seen_urls:
                    images.append(url)
                    seen_urls.add(url)
        else:
            # Lógica original: solo incluir documentos mencionados en la respuesta
            for doc in category_docs:
                url = doc.get('imagen_url')
                if not url or url in seen_urls:
                    continue
                name_norm = doc.get('name_normalized', '')
                keywords = doc.get('keywords', set())
                
                include = False
                if name_norm and name_norm in normalized_answer:
                    include = True
                elif keywords and any(kw in normalized_answer for kw in keywords):
                    include = True
                
                if include:
                    images.append(url)
                    seen_urls.add(url)
        
        if images:
            # Crear lista de documentos con sus imágenes y descripciones
            documents_with_images = []
            for doc in category_docs:
                url = doc.get('imagen_url')
                if url and url in images:
                    documents_with_images.append({
                        'nombre': doc.get('nombre', ''),
                        'imagen_url': url,
                        'name_normalized': doc.get('name_normalized', '')
                    })
            
            # Ordenar documentos para mantener el orden de las imágenes
            ordered_documents = []
            for url in images:
                for doc_info in documents_with_images:
                    if doc_info['imagen_url'] == url and doc_info not in ordered_documents:
                        ordered_documents.append(doc_info)
                        break
            
            sections.append({
                'title': category,
                'images': images,
                'documents': ordered_documents
            })
    
    return sections

LOCATION_KEYWORDS = ['donde', 'dónde', 'ubicacion', 'ubicación', 'queda', 'llegar', 'direccion', 'dirección', 'lugar']

IMAGE_REQUEST_KEYWORDS = [
    'muestra', 'mostrar', 'ver imagen', 'ver imágenes', 'ver imagenes', 'imagen', 'imágenes', 'imagenes',
    'foto', 'fotos', 'fotografía', 'fotografías', 'fotografia', 'fotografias', 'dame imagen', 'quiero ver',
    'puedo ver', 'muéstrame', 'muestrame', 'enseña', 'enseñame', 'ensename', 'ver ejemplo', 'ejemplo visual',
    'darme', 'pasame', 'dame', 'tienes'
]

# Palabras de confirmación para mostrar imágenes
CONFIRMATION_KEYWORDS = [
    'si', 'sí', 'por favor', 'porfavor', 'claro', 'por supuesto', 'adelante', 'ok', 'okay',
    'vale', 'perfecto', 'bueno', 'bien', 'dale', 'vamos', 'empieza', 'comienza'
]

DOCUMENT_REFERENCE_KEYWORDS = [
    'documento', 'documentos', 'folder', 'carpeta', 'presentación', 'presentacion',
    'boleta', 'inscripción', 'inscripcion', 'plan de estudios', 'croquis', 'fotografía', 'fotografia'
]

COMUNICADO_REFERENCE_KEYWORDS = [
    'comunicado', 'comunicados', 'ultimo comunicado', 'último comunicado', 'ultimos comunicados', 'últimos comunicados',
    'pago', 'pagos', 'pagaron', 'pagado', 'abonado', 'abonaron',
    'fecha de pago', 'fecha de pagos', 'cuando pagan', 'cuando pagaron', 'ya pagaron', 'ya pagaron este mes',
    'cronograma', 'aviso', 'avisos', 'anuncio', 'anuncios', 'publicación', 'publicacion',
    'boleta de pago', 'recoger boleta', 'reciente', 'recientes'
]

REQUISITOS_KEYWORDS = ['requisito', 'requisitos']

from supabase_client import fetch_table_data

def load_supabase_data():
    """Cargar datos desde Supabase y crear base de conocimiento"""
    global knowledge_base, documentos_imagenes, documentos_catalogo, comunicados_media, ubicaciones_map
    
    # Definir las tablas (nombres basados en los archivos CSV originales)
    tables = {
        'becas': 'Información general de la beca',
        'requisitos': 'Requisitos para aplicar a la beca',
        'documentos_requeridos': 'Documentos necesarios para la postulación',
        'proceso_postulacion': 'Pasos del proceso de postulación',
        'servicios': 'Servicios incluidos en la beca',
        'contactos': 'Información de contacto',
        'compromiso_beca': 'Compromiso del becario',
        'comunicados': 'Comunicados y avisos oficiales',
        'ubicaciones': 'Ubicaciones y referencias visuales'
    }
    
    knowledge_parts = []
    documentos_imagenes = {}  # Reiniciar diccionario de imágenes
    documentos_catalogo = []  # Reiniciar catálogo de documentos
    comunicados_media = {}  # Reiniciar comunicados con imágenes (Diccionario por ID)
    ubicaciones_map = {} # Reiniciar mapa de ubicaciones
    
    for table_name, description in tables.items():
        try:
            # Obtener datos de Supabase
            data = fetch_table_data(table_name)
            
            # Si no hay datos en Supabase, intentar cargar desde CSV local
            if not data:
                logger.warning(f"⚠️  Tabla {table_name} vacía en Supabase, intentando CSV local...")
                try:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    csv_path = os.path.normpath(os.path.join(current_dir, '..', 'data', f'{table_name}.csv'))
                    if os.path.exists(csv_path):
                        df = pd.read_csv(csv_path)
                        # Reemplazar NaN con None o string vacío para compatibilidad
                        df = df.fillna('')
                        data = df.to_dict('records')
                        logger.info(f"📂 Cargado {table_name} desde CSV local")
                except Exception as e_csv:
                    logger.error(f"❌ Error cargando CSV {table_name}: {str(e_csv)}")

            if not data:
                logger.warning(f"⚠️  Tabla {table_name} está vacía o no se pudo leer")
            # Si es la tabla de documentos_requeridos, guardar las imágenes
            if table_name == 'documentos_requeridos':
                for row in data:
                    nombre_doc = row.get('nombre_documento', '')
                    # Ignorar entradas genéricas o placeholders
                    if not nombre_doc or nombre_doc.strip() == "Documento requerido":
                        continue
                        
                    imagen_url = row.get('imagen_url', '')
                    
                    if nombre_doc and imagen_url:
                        # Extraer categoría si existe (formato "CATEGORIA: Nombre")
                        parts = nombre_doc.split(':', 1)
                        if len(parts) > 1:
                            categoria = parts[0].strip()
                            nombre_limpio = parts[1].strip()
                        else:
                            categoria = "General"
                            nombre_limpio = nombre_doc
                            
                        categoria_norm = normalize_text(categoria)
                        
                        # También guardar por palabras clave
                        palabras = nombre_doc.lower().split()
                        doc_keywords = set()
                        for palabra in palabras:
                            palabra_limpia = palabra.strip()
                            # Solo palabras significativas (más de 3 caracteres y no comunes)
                            palabras_comunes = ['del', 'de', 'la', 'en', 'con', 'para', 'por', 'los', 'las', 'una', 'un']
                            if len(palabra_limpia) > 3 and palabra_limpia not in palabras_comunes:
                                palabra_norm = normalize_text(palabra_limpia)
                                if palabra_norm not in documentos_imagenes:
                                    documentos_imagenes[palabra_norm] = imagen_url
                                doc_keywords.add(palabra_norm)

                        documentos_catalogo.append({
                            'nombre': nombre_doc,
                            'name_normalized': normalize_text(nombre_doc),
                            'imagen_url': imagen_url,
                            'category': categoria,
                            'category_normalized': categoria_norm,
                            'keywords': doc_keywords
                        })

            # Si es la tabla de ubicaciones, guardar mapa de ubicaciones
            if table_name == 'ubicaciones':
                for row in data:
                    nombre = row.get('nombre', '')
                    imagen_url = row.get('imagen_url', '')
                    direccion = row.get('direccion', '')
                    
                    if nombre and imagen_url:
                        # Guardar por nombre completo normalizado
                        nombre_norm = normalize_text(nombre)
                        if nombre_norm not in ubicaciones_map:
                            ubicaciones_map[nombre_norm] = []
                        
                        ubicaciones_map[nombre_norm].append({
                            'nombre': nombre,
                            'imagen_url': imagen_url,
                            'direccion': direccion
                        })
                        
                        # También guardar por palabras clave
                        palabras = nombre.lower().split()
                        for palabra in palabras:
                            if len(palabra) > 3:
                                palabra_norm = normalize_text(palabra)
                                if palabra_norm not in ubicaciones_map:
                                    ubicaciones_map[palabra_norm] = []
                                
                                # Evitar duplicados exactos en la lista
                                ya_existe = False
                                for item in ubicaciones_map[palabra_norm]:
                                    if item['imagen_url'] == imagen_url:
                                        ya_existe = True
                                        break
                                
                                if not ya_existe:
                                    ubicaciones_map[palabra_norm].append({
                                        'nombre': nombre,
                                        'imagen_url': imagen_url,
                                        'direccion': direccion
                                    })

            # Si es la tabla de comunicados, guardar comunicados con imágenes
            # La tabla tiene: id, fecha, contenido, imagen_url
            if table_name == 'comunicados':
                for row in data:
                    comunicado_id = row.get('id')
                    imagen_url = row.get('imagen_url', '')
                    fecha = row.get('fecha', '')
                    contenido = row.get('contenido', '')
                    
                    # Guardar comunicado si tiene ID (aunque no tenga imagen_url, para poder responder preguntas)
                    if comunicado_id:
                        # Convertir ID a string para usar como clave
                        id_str = str(comunicado_id)
                        
                        # Guardar la información del comunicado (solo campos que existen)
                        comunicados_media[id_str] = {
                            'id': comunicado_id,
                            'imagen_url': imagen_url if imagen_url else '',
                            'fecha': fecha,
                            'contenido': contenido
                        }
                        
                        if imagen_url:
                            logger.debug(f"📰 Cargado comunicado ID {id_str} con imagen: {imagen_url[:50]}...")
                        else:
                            logger.debug(f"📰 Cargado comunicado ID {id_str} sin imagen_url")
                    else:
                        logger.warning(f"⚠️  Fila de comunicados sin ID: {row}")

            # Crear sección de conocimiento
            section = f"\n## {description}\n\n"
            
            # Convertir cada fila en texto
            for row in data:
                row_text = []
                for col, value in row.items():
                    if col not in ['id', 'beca_id', 'created_at', 'embedding', 'imagen_url']:
                        val_str = str(value)
                        # Filtrar valores nulos o vacíos
                        if val_str and val_str != 'nan' and val_str != 'None' and val_str.strip():
                            row_text.append(f"{col}: {val_str}")
                
                # Inyectar ID explícitamente para comunicados para referencia
                if table_name == 'comunicados' and 'id' in row:
                    row_text.insert(0, f"[ID: {row['id']}]")
                
                if row_text:
                    section += "- " + ", ".join(row_text) + "\n"
            
            if section.strip() != f"## {description}":
                knowledge_parts.append(section)
                logger.info(f"✅ Cargado {table_name}: {len(data)} registros")
            else:
                logger.warning(f"⚠️  {table_name} no tiene datos válidos")
            
        except Exception as e:
            logger.error(f"❌ Error cargando {table_name}: {str(e)}")
    
    knowledge_base = "\n".join(knowledge_parts)
    logger.info(f"📸 Cargadas {len(documentos_imagenes)} referencias de imágenes de documentos")
    if comunicados_media:
        logger.info(f"📰 Cargados {len(comunicados_media)} comunicados con imágenes")
        # Mostrar los IDs cargados para debug
        ids_cargados = list(comunicados_media.keys())
        logger.info(f"📰 IDs de comunicados cargados: {ids_cargados}")
    if ubicaciones_map:
        logger.info(f"📍 Cargadas {len(ubicaciones_map)} referencias de ubicaciones")
    return len(knowledge_parts) > 0

def initialize_chatbot():
    """Inicializar el chatbot con Gemini"""
    try:
        logger.info("🚀 Inicializando chatbot con Gemini...")
        
        # Cargar documentos desde Supabase
        if not load_supabase_data():
            logger.error("❌ No se cargaron documentos")
            return False
        
        logger.info(f"📚 Base de conocimiento creada ({len(knowledge_base)} caracteres)")
        logger.info("✅ Chatbot inicializado correctamente con Gemini 2.0 Flash")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando chatbot: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_bot_response(user_message, session_id="default"):
    """Obtener respuesta del bot usando Gemini directamente"""
    
    if not knowledge_base:
        return {
            "response": "Lo siento, el sistema no está disponible en este momento. Por favor, intenta más tarde.",
            "sources": []
        }
    
    # Crear el prompt del sistema con contexto (definido antes del try para que esté disponible en except)
    system_instruction = f"""Eres un asistente virtual en la beca de apoyo económico por rendimiento académico de la UMSA (Universidad Mayor de San Andrés). 
Tu trabajo es ayudar a los estudiantes con información sobre la ex beca COMEDOR.

Usa SOLO la siguiente información para responder:

{knowledge_base}

Instrucciones CRÍTICAS:
- Responde de manera amigable, profesional y CONCISA
- NO repitas información ni subdividas en exceso
- Cuando enumeres documentos, agrúpalos en las categorías principales (PRESENTACIÓN, ACADÉMICO, SOCIO-ECONÓMICO, etc.) y numera los ítems dentro de cada categoría usando 1., 2., 3., etc.
- Los nombres de las categorías deben ir en **negritas** seguidos de dos puntos (ej. **PRESENTACIÓN:**).
- Para comunicados, fechas de pago o avisos, usa igualmente un único encabezado en negritas (ej. **COMUNICADOS:**) y enumera los puntos clave.
- Ejemplo CORRECTO:
  "PRESENTACIÓN:
   1. Folder color crema tamaño oficio con datos de domicilio
   2. Croquis de ubicación (13x16 cm) en la tapa
   3. Fotografía del frontis del domicilio (10x15 cm, a color)
   4. Plan de estudios o certificado de conclusión
   5. Datos en el borde derecho interno de la contratapa

   ACADÉMICO:
   1. Boleta de inscripción original gestión 2025
   2. Boleta de retiro y adición de materias (si corresponde)
   3. Historial académico original con sello de Kardex
   4. Fotocopia de matrícula universitaria vigente"

- Nunca repitas el nombre de la categoría más de una vez consecutiva; si necesitas añadir un elemento extra (por ejemplo, fotografía 4x4), agrégalo al final de la misma categoría o, si es un recordatorio especial, usa una nota breve como "Nota: ...".
- Si la pregunta no está relacionada con la beca, indica amablemente que solo puedes ayudar con información sobre la BECA COMEDOR BAERA
- Si no tienes la información específica, dilo honestamente
- Usa la información exacta de la base de conocimiento
- Responde en español
- Sé DIRECTO y EVITA repeticiones innecesarias
- Usa formato Markdown solo cuando sea necesario:
  * Usa **negritas** para resaltar conceptos clave
  * Usa listas simples numeradas por categoría
  * Evita múltiples niveles de encabezados
- IMPORTANTE SOBRE COMUNICADOS:
  * Cuando menciones un comunicado específico que encontraste en la base de conocimiento, DEBES incluir su ID al final de la mención en el formato `[ID: <id>]`.
  * Ejemplo: "El pago se realizará el 20 de enero [ID: 5]."
  * Esto es CRÍTICO para que el sistema pueda mostrar la imagen correcta.
  * NO inventes IDs. Usa solo los que están en la base de conocimiento.

- IMPORTANTE SOBRE IMÁGENES DE DOCUMENTOS: 
  * Cuando el usuario pregunte sobre documentos requeridos, SIEMPRE pregunta al final: "¿Te gustaría que te muestre imágenes de ejemplo de alguno de estos documentos?"
  * Si el usuario responde "sí", "por favor", "claro", o similar, el sistema mostrará automáticamente las imágenes organizadas por categorías (PRESENTACIÓN, ACADÉMICO, SOCIO-ECONÓMICO).
  * Las imágenes se mostrarán en orden: primero PRESENTACIÓN, luego ACADÉMICO, luego SOCIO-ECONÓMICO.
  * Cada imagen irá acompañada de su descripción correspondiente para guiar paso a paso al estudiante.

- IMPORTANTE SOBRE UBICACIONES:
  * Si el usuario pregunta "dónde queda", "cómo llegar" o "dónde es" alguna oficina o lugar, USA la información de la tabla de ubicaciones.
  * Menciona la dirección exacta que tienes en la base de datos.
  * El sistema mostrará automáticamente la imagen del lugar si está disponible, así que puedes decir "Aquí tienes una imagen de referencia" o similar.

- IMPORTANTE SOBRE CONTINUIDAD (MEMORIA):
  * Si el usuario pregunta "¿qué sigue?", "¿qué más?", o "continuar" después de que le hayas dado una lista parcial de requisitos (ej. solo PRESENTACIÓN), DEBES asumir que quiere continuar con la SIGUIENTE categoría de requisitos (ej. ACADÉMICO).
  * NO cambies de tema al "Proceso de Postulación" general a menos que el usuario lo pida explícitamente.
  * Tu objetivo es guiar al estudiante paso a paso en el armado de su carpeta. Si ya cubriste PRESENTACIÓN, sigue con ACADÉMICO, luego SOCIO-ECONÓMICO, etc.
"""
    
    try:
        logger.info(f"Procesando mensaje: {user_message[:50]}...")
        
        # Obtener historial de la sesión
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        
        # Crear el modelo con system_instruction (usando modelo gratuito gemini-2.0-flash)
        logger.info("Creando modelo Gemini 2.0 Flash...")
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=system_instruction
        )
        
        # Construir el historial de conversación para Gemini (formato correcto)
        history = []
        for q, a in chat_histories[session_id][-5:]:  # Últimas 5 conversaciones
            history.append({
                "role": "user",
                "parts": [q]
            })
            history.append({
                "role": "model",
                "parts": [a]
            })
        
        # Si hay historial, crear chat con historial, sino usar modelo directamente
        if history:
            chat = model.start_chat(history=history)
            logger.info("Generando respuesta con Gemini (con historial)...")
            response = chat.send_message(user_message)
        else:
            # Primera conversación sin historial
            logger.info("Generando respuesta con Gemini (sin historial)...")
            response = model.generate_content(user_message)
        
        answer = response.text
        logger.info(f"Respuesta generada: {answer[:100]}...")
        
        # Gestión de imágenes (documentos y comunicados)
        imagenes = []
        imagenes_set = set()
        user_message_lower = user_message.lower()
        answer_lower = answer.lower()
        user_message_normalized = normalize_text(user_message)
        answer_normalized = normalize_text(answer)

        def append_images(urls):
            for url in urls:
                if url and url not in imagenes_set:
                    imagenes.append(url)
                    imagenes_set.add(url)

        def obtener_imagenes_documentos(contexto_usuario_norm, contexto_respuesta_norm, limite=15):
            """Obtiene imágenes SOLO de documentos_requeridos, no de otras secciones"""
            imgs = []
            vistos = set()
            # SOLO usar documentos_catalogo (contiene solo documentos_requeridos de la tabla documentos_requeridos)
            for doc in documentos_catalogo:
                url = doc.get('imagen_url')
                if not url:
                    continue
                nombre = doc.get('nombre', '').lower()
                name_norm = doc.get('name_normalized', '')
                keywords = doc.get('keywords', set())
                
                # SOLO buscar en el contexto del usuario, ignorar la respuesta del bot
                # Esto asegura que solo se muestren imágenes cuando el usuario realmente pregunta sobre ese documento
                coincide_nombre = nombre and (nombre in contexto_usuario_norm)
                coincide_keyword = keywords and any(
                    kw in contexto_usuario_norm for kw in keywords
                )
                
                # Solo agregar si hay coincidencia real con la consulta del usuario
                if coincide_nombre or coincide_keyword:
                    if url not in vistos:
                        imgs.append(url)
                        vistos.add(url)
                if len(imgs) >= limite:
                    break
            return imgs

        def obtener_imagenes_comunicados_por_id(respuesta_texto):
            """Extrae IDs de la respuesta y devuelve las imágenes correspondientes SOLO de comunicados"""
            if not comunicados_media:
                logger.warning("⚠️  comunicados_media está vacío - no hay comunicados cargados")
                return []
            
            # Buscar patrones [ID: <numero>] en la respuesta
            ids_encontrados = re.findall(r'\[ID:\s*(\d+)\]', respuesta_texto)
            
            if not ids_encontrados:
                logger.debug(f"🔍 No se encontraron IDs en la respuesta: {respuesta_texto[:200]}")
                return []
            
            logger.info(f"🔍 IDs encontrados en respuesta: {ids_encontrados}")
            logger.info(f"📊 Comunicados disponibles en memoria: {list(comunicados_media.keys())}")
            
            imagenes_seleccionadas = []
            vistos = set()
            
            # SOLO usar imágenes de comunicados_media (no de otras secciones)
            for id_str in ids_encontrados:
                logger.debug(f"🔎 Buscando comunicado con ID: '{id_str}' (tipo: {type(id_str)})")
                
                if id_str in comunicados_media:
                    data = comunicados_media[id_str]
                    url = data.get('imagen_url', '')
                    # Validar que la URL existe, no está vacía y pertenece a un comunicado
                    if url and str(url).strip() and url not in vistos:
                        imagenes_seleccionadas.append(url)
                        vistos.add(url)
                        logger.info(f"✅ Imagen encontrada para comunicado ID {id_str}: {url[:80]}...")
                    elif not url or not str(url).strip():
                        logger.debug(f"ℹ️  Comunicado ID {id_str} no tiene imagen_url (es válido, solo no tiene imagen)")
                else:
                    logger.warning(f"⚠️  Comunicado ID '{id_str}' no encontrado en comunicados_media")
                    logger.debug(f"   Claves disponibles: {list(comunicados_media.keys())}")
            
            logger.info(f"📸 Total de imágenes encontradas: {len(imagenes_seleccionadas)}")
            return imagenes_seleccionadas

        def obtener_imagenes_ubicaciones(texto_usuario, texto_respuesta):
            """Busca imágenes SOLO de ubicaciones (tabla ubicaciones), no de otras secciones"""
            imgs = []
            if not ubicaciones_map:
                return []
            
            texto_usuario_norm = normalize_text(texto_usuario)
            texto_respuesta_norm = normalize_text(texto_respuesta)
            texto_combinado = texto_usuario_norm + " " + texto_respuesta_norm
            
            # Palabras clave para contacto/información general
            keywords_contacto = ['mas informacion', 'informacion', 'contacto', 'contactar', 'oficinas', 'donde preguntar']
            es_consulta_contacto = any(kw in texto_usuario_norm for kw in keywords_contacto)
            
            # Si es consulta de contacto, agregar imágenes de Trabajo Social por defecto
            if es_consulta_contacto:
                trabajo_social_keys = ['oficinas de trabajo social', 'trabajo social']
                for key in trabajo_social_keys:
                    key_norm = normalize_text(key)
                    if key_norm in ubicaciones_map:
                        for item in ubicaciones_map[key_norm]:
                            url = item.get('imagen_url')
                            if url and url not in imgs:
                                imgs.append(url)
            
            # Mapeo de palabras clave a ubicaciones (para búsquedas semánticas)
            keywords_ubicaciones = {
                'nutricion': ['revision nutricional', 'nutricional', 'control nutricional', 'carnet nutricional'],
                'trabajo social': ['oficinas de trabajo social', 'trabajo social'],
                'compromiso': ['fotocopia de compromiso', 'compromiso del estudiante']
            }
            
            # Búsqueda por palabras clave relacionadas
            for keyword, ubicaciones_relacionadas in keywords_ubicaciones.items():
                keyword_norm = normalize_text(keyword)
                if keyword_norm in texto_combinado:
                    for ubicacion_rel in ubicaciones_relacionadas:
                        ubicacion_rel_norm = normalize_text(ubicacion_rel)
                        if ubicacion_rel_norm in ubicaciones_map:
                            for item in ubicaciones_map[ubicacion_rel_norm]:
                                url = item.get('imagen_url')
                                if url and url not in imgs:
                                    imgs.append(url)
            
            # Búsqueda PRECISA por nombre de ubicación en el texto del usuario o respuesta
            # Priorizar coincidencias en el texto del usuario
            ubicaciones_encontradas = set()
            for nombre_norm, lista_items in ubicaciones_map.items():
                # Verificar si el nombre de la ubicación está en el texto
                # Priorizar el texto del usuario sobre la respuesta
                if nombre_norm in texto_usuario_norm or nombre_norm in texto_respuesta_norm:
                    for item in lista_items:
                        nombre_ubicacion = item.get('nombre', '')
                        url = item.get('imagen_url')
                        direccion = item.get('direccion', '')
                        
                        if url and url not in imgs:
                            # Verificar que la ubicación mencionada realmente coincida
                            nombre_ubicacion_norm = normalize_text(nombre_ubicacion)
                            direccion_norm = normalize_text(direccion) if direccion else ''
                            
                            # Coincidencia por nombre
                            coincide_nombre = nombre_ubicacion_norm in texto_usuario_norm or nombre_ubicacion_norm in texto_respuesta_norm
                            
                            # Coincidencia por dirección (si la respuesta menciona la dirección)
                            # Buscar palabras clave de la dirección en la respuesta
                            coincide_direccion = False
                            if direccion_norm:
                                palabras_direccion = [p for p in direccion_norm.split() if len(p) > 4]
                                # Si hay al menos 2 palabras clave de la dirección en la respuesta, es coincidencia
                                coincidencias_direccion = sum(1 for palabra in palabras_direccion if palabra in texto_respuesta_norm)
                                coincide_direccion = coincidencias_direccion >= 2
                            
                            # Coincidencia por palabras clave del nombre
                            palabras_nombre = nombre_ubicacion_norm.split()
                            coincide_palabras = any(
                                palabra in texto_combinado 
                                for palabra in palabras_nombre 
                                if len(palabra) > 4  # Solo palabras significativas
                            )
                            
                            if coincide_nombre or coincide_direccion or coincide_palabras:
                                imgs.append(url)
                                ubicaciones_encontradas.add(nombre_ubicacion_norm)
            
            return imgs

        # Detectar qué tipo de consulta es
        # IMPORTANTE: Cada sección debe usar SOLO sus propias imágenes
        
        # Verificar si la respuesta anterior era sobre documentos (para detectar confirmaciones)
        respuesta_anterior_sobre_documentos = False
        if chat_histories.get(session_id) and len(chat_histories[session_id]) > 0:
            ultima_respuesta = chat_histories[session_id][-1][1].lower()
            respuesta_anterior_sobre_documentos = any(
                palabra in ultima_respuesta for palabra in ['presentación', 'académico', 'socio-económico', 'documento']
            ) or '¿te gustaría' in ultima_respuesta or 'imágenes' in ultima_respuesta
        
        # Detectar confirmación del usuario
        user_message_lower_clean = user_message_lower.strip()
        confirma_ver_imagenes = any(
            palabra in user_message_lower_clean for palabra in CONFIRMATION_KEYWORDS
        )
        
        # Detección PRECISA de documentos requeridos
        # Solo cuando se pregunta específicamente sobre documentos para la postulación
        palabras_documentos_requeridos = [
            'documento requerido', 'documentos requeridos', 'documentos para postular', 
            'documentos necesarios', 'documentos de postulacion', 'documentos de postulación',
            'que documentos', 'qué documentos', 'que debo presentar', 'qué debo presentar',
            'documentos que debo', 'documentos que necesito', 'carpeta de postulacion', 'carpeta de postulación'
        ]
        menciona_documentos_requeridos = any(
            frase in user_message_lower for frase in palabras_documentos_requeridos
        ) or (
            any(palabra in user_message_lower for palabra in ['documento', 'documentos']) and
            any(palabra in user_message_lower for palabra in ['requerido', 'necesario', 'presentar', 'postular', 'postulacion', 'postulación'])
        ) or (confirma_ver_imagenes and respuesta_anterior_sobre_documentos)
        
        # Para ubicaciones, SOLO verificar el mensaje del usuario para evitar falsos positivos en respuestas largas
        # (ej. si la respuesta de requisitos dice "ir a...", no debería mostrar mapa a menos que el usuario pregunte dónde)
        # IMPORTANTE: Definir esto PRIMERO porque se usa más adelante
        keywords_ubicacion_extra = [
            'contacto', 'contactar', 'oficinas', 'donde preguntar', 'mas informacion', 'más información',
            'adquirir', 'obtener', 'conseguir', 'solicitar', 'retirar', 'recoger', 'perdi', 'perdí', 'perdido'
        ]
        menciona_ubicacion = any(
            palabra in user_message_lower for palabra in LOCATION_KEYWORDS + keywords_ubicacion_extra
        )
        
        # IMPORTANTE: Si la pregunta es sobre ubicación (dónde obtener, adquirir, etc.), 
        # NO debe considerarse como pregunta sobre documentos, incluso si menciona palabras relacionadas
        # Ejemplo: "donde adquirir carnet" es una pregunta de ubicación, NO de documentos
        # También detectar casos como "perdi mi carnet" (pregunta implícita de dónde obtener)
        tiene_palabras_ubicacion_explicitas = any(
            palabra in user_message_lower for palabra in ['donde', 'dónde', 'adquirir', 'obtener', 'conseguir', 'solicitar']
        )
        tiene_perdida = any(
            palabra in user_message_lower for palabra in ['perdi', 'perdí', 'perdido']
        )
        es_pregunta_ubicacion = menciona_ubicacion and (
            tiene_palabras_ubicacion_explicitas or tiene_perdida
        )
        
        # Detección PRECISA de comunicados
        # IMPORTANTE: Verificar primero si la respuesta tiene IDs de comunicados (más preciso)
        # Luego verificar si el usuario pregunta sobre comunicados/pagos
        respuesta_tiene_id_comunicado = bool(re.search(r'\[ID:\s*\d+\]', answer))
        
        # Detectar si el usuario pregunta sobre comunicados/pagos
        usuario_pregunta_comunicados = any(
            palabra in user_message_lower for palabra in COMUNICADO_REFERENCE_KEYWORDS
        )
        
        # Si la respuesta tiene ID de comunicado, ES una pregunta sobre comunicados
        # O si el usuario pregunta explícitamente sobre comunicados/pagos
        # IMPORTANTE: Si hay ID en la respuesta, SIEMPRE es sobre comunicados (aunque el usuario no lo mencione explícitamente)
        menciona_comunicados = (
            usuario_pregunta_comunicados or respuesta_tiene_id_comunicado
        ) and not es_pregunta_ubicacion  # Excluir si es pregunta de ubicación
        
        # Log para debug
        if respuesta_tiene_id_comunicado or usuario_pregunta_comunicados:
            logger.info(f"📰 Detectada pregunta sobre comunicados. Usuario pregunta: {usuario_pregunta_comunicados}, Respuesta tiene ID: {respuesta_tiene_id_comunicado}")
            logger.info(f"📰 menciona_comunicados = {menciona_comunicados}, es_pregunta_ubicacion = {es_pregunta_ubicacion}")
        
        # IMPORTANTE: Si es pregunta de ubicación, excluir de detección de documentos y comunicados
        # PERO: Si la respuesta tiene ID de comunicado, NO excluir (es un comunicado válido)
        if es_pregunta_ubicacion and not respuesta_tiene_id_comunicado:
            menciona_documentos_requeridos = False
            menciona_comunicados = False
            logger.info(f"📍 Pregunta de ubicación detectada. Excluyendo documentos y comunicados.")
        elif respuesta_tiene_id_comunicado:
            # Si hay ID de comunicado en la respuesta, SIEMPRE es sobre comunicados
            menciona_comunicados = True
            logger.info(f"📰 ID de comunicado encontrado en respuesta. Forzando menciona_comunicados = True")
        
        # SOLO enviar imágenes si se pregunta específicamente sobre comunicados O documentos_requeridos O ubicaciones
        # En cualquier otro caso (requisitos, servicios, contactos, etc.) NO enviar imágenes
        section_images = []
        
        # IMPORTANTE: Usar if-elif-elif para evitar que se mezclen imágenes de diferentes secciones
        # Solo una sección puede activarse a la vez para evitar confusión
        # PRIORIDAD: ubicaciones primero (para evitar falsos positivos con documentos)
        if menciona_ubicacion or es_pregunta_ubicacion:
            # Si pregunta sobre ubicaciones, buscar SOLO imágenes de ubicaciones
            # Solo mostrar si realmente hay imágenes relacionadas con la consulta
            logger.info(f"📍 Procesando pregunta de ubicación. menciona_ubicacion={menciona_ubicacion}, es_pregunta_ubicacion={es_pregunta_ubicacion}")
            imagenes_ubi = obtener_imagenes_ubicaciones(user_message, answer)
            if imagenes_ubi:
                append_images(imagenes_ubi)
                logger.info(f"📍 ✅ Enviando {len(imagenes_ubi)} imagen(es) de ubicación")
            else:
                logger.warning(f"📍 ⚠️  No se encontraron imágenes de ubicación para: {user_message}")
            
        elif menciona_comunicados:
            # Si pregunta sobre comunicados, buscar SOLO imágenes de comunicados
            # IMPORTANTE: Si la respuesta tiene IDs de comunicados, SIEMPRE buscar las imágenes
            logger.info(f"📰 Procesando comunicados. Respuesta original: {answer[:200]}")
            imagenes_com = obtener_imagenes_comunicados_por_id(answer)
            
            # Si hay IDs en la respuesta, DEBE haber imágenes (validar que se encontraron)
            if respuesta_tiene_id_comunicado and not imagenes_com:
                logger.warning(f"⚠️  Se encontró ID de comunicado en la respuesta pero no se obtuvo imagen. Respuesta: {answer[:200]}")
                logger.warning(f"⚠️  Comunicados disponibles: {list(comunicados_media.keys())}")
            
            # Enviar imágenes si se encontraron (SIEMPRE enviar si hay IDs en la respuesta)
            if imagenes_com:
                append_images(imagenes_com)
                logger.info(f"📰 ✅ Enviando {len(imagenes_com)} imagen(es) de comunicado(s)")
            elif respuesta_tiene_id_comunicado:
                # Si hay ID pero no se encontró imagen, intentar buscar de nuevo con más detalle
                logger.warning(f"⚠️  No se encontraron imágenes para los IDs en la respuesta. Revisando...")
                logger.warning(f"⚠️  Respuesta completa: {answer}")
            
            # IMPORTANTE: Limpiar los tags de ID de la respuesta visible al usuario
            # SOLO al final, después de obtener imágenes, para que el texto se mantenga intacto
            answer_original = answer
            answer = re.sub(r'\s*\[ID:\s*\d+\]', '', answer).strip()
            logger.info(f"📝 Texto final (sin IDs): {answer[:200]}")
            
        elif menciona_documentos_requeridos and documentos_catalogo and not es_pregunta_ubicacion:
            # IMPORTANTE: NO procesar documentos si es pregunta de ubicación
            # Solo mostrar imágenes si:
            # 1. El usuario confirma que quiere ver imágenes Y la respuesta anterior era sobre documentos, O
            # 2. El usuario pregunta explícitamente sobre documentos requeridos Y la respuesta menciona categorías
            debe_mostrar_imagenes = (
                confirma_ver_imagenes and respuesta_anterior_sobre_documentos
            ) or (
                menciona_documentos_requeridos and any(
                    cat in answer_lower for cat in ['presentación', 'académico', 'socio-económico']
                )
            )
            
            if debe_mostrar_imagenes:
                # Si el usuario confirma que quiere ver imágenes Y la respuesta anterior era sobre documentos,
                # incluir TODAS las imágenes de cada categoría mencionada
                include_all = confirma_ver_imagenes and respuesta_anterior_sobre_documentos
                
                # Generar section_images para documentos
                section_images = build_section_images(answer, include_all_docs=include_all)
                
                # Si no se generaron secciones pero el usuario confirmó ver imágenes, 
                # usar la respuesta anterior para construir las secciones
                if not section_images and confirma_ver_imagenes and respuesta_anterior_sobre_documentos:
                    if chat_histories.get(session_id) and len(chat_histories[session_id]) > 0:
                        respuesta_anterior = chat_histories[session_id][-1][1]
                        # Construir secciones basadas en la respuesta anterior que mencionaba los documentos
                        section_images = build_section_images(respuesta_anterior, include_all_docs=True)
                
                # Solo agregar imágenes al nivel superior si NO se generaron secciones
                # Esto evita duplicar imágenes que ya se muestran en las secciones
                if not section_images:
                    imagenes_doc = obtener_imagenes_documentos(user_message_normalized, answer_normalized)
                    # Solo agregar si realmente hay imágenes relacionadas con la consulta
                    if imagenes_doc:
                        append_images(imagenes_doc)
            
        # Si NO menciona comunicados NI documentos NI ubicaciones, NO se envían imágenes (section_images ya está vacío)
        
        # Actualizar historial
        chat_histories[session_id].append((user_message, answer))
        
        return {
            "response": answer,
            "sources": ["Base de conocimiento BAERA"],
            "images": imagenes,
            "section_images": section_images
        }
        
    except Exception as e:
        logger.error(f"ERROR generando respuesta: {str(e)}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Mensaje de error más específico
        error_msg = "Lo siento, ocurrió un error procesando tu mensaje."
        if "API key" in str(e) or "authentication" in str(e).lower():
            error_msg = "Error de autenticación. Por favor, verifica tu API key de Google."
        elif "quota" in str(e).lower() or "limit" in str(e).lower():
            error_msg = "Se ha alcanzado el límite de uso. Por favor, intenta más tarde."
        elif "model" in str(e).lower() and "not found" in str(e).lower():
            error_msg = "Error: El modelo no está disponible. Verificando modelo alternativo..."
            # Intentar con modelo alternativo
            try:
                logger.info("Intentando con modelo gemini-2.5-flash...")
                model_alt = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    system_instruction=system_instruction
                )
                response_alt = model_alt.generate_content(user_message)
                answer_alt = response_alt.text
                chat_histories[session_id].append((user_message, answer_alt))
                # Buscar imágenes para respuesta alternativa también
                imagenes_alt = []
                answer_alt_lower = answer_alt.lower()
                user_message_lower_alt = user_message.lower()
                
                # Detectar qué tipo de consulta es (mismo criterio que el flujo principal)
                menciona_documentos_alt = any(
                    palabra in user_message_lower_alt or palabra in answer_alt_lower for palabra in DOCUMENT_REFERENCE_KEYWORDS
                )
                menciona_comunicados_alt = any(
                    palabra in user_message_lower_alt or palabra in answer_alt_lower for palabra in COMUNICADO_REFERENCE_KEYWORDS
                )
                menciona_ubicacion_alt = any(
                    palabra in user_message_lower_alt for palabra in LOCATION_KEYWORDS + ['contacto', 'contactar', 'oficinas', 'donde preguntar', 'mas informacion', 'más información']
                )
                user_message_norm_alt = normalize_text(user_message)
                answer_alt_norm = normalize_text(answer_alt)
                
                imagenes_alt = []
                imagenes_alt_set = set()

                def append_alt(urls):
                    """Agrega URLs válidas de imágenes (solo de documentos_requeridos y comunicados)."""
                    for url in urls:
                        # Verificar que la URL existe y tiene un valor válido
                        if url and str(url).strip() and url not in imagenes_alt_set:
                            imagenes_alt.append(url)
                            imagenes_alt_set.add(url)

                # SOLO enviar imágenes si se pregunta específicamente sobre comunicados O documentos_requeridos
                section_images_alt = []
                
                if menciona_comunicados_alt:
                    # Si pregunta sobre comunicados, buscar imágenes de comunicados
                    imagenes_com_alt = obtener_imagenes_comunicados_por_id(answer_alt)
                    append_alt(imagenes_com_alt)
                    answer_alt = re.sub(r'\s*\[ID:\s*\d+\]', '', answer_alt).strip()
                    
                elif menciona_documentos_alt and documentos_catalogo:
                    # Si pregunta sobre documentos_requeridos, buscar imágenes de documentos
                    imagenes_doc_alt = obtener_imagenes_documentos(user_message_norm_alt, answer_alt_norm)
                    append_alt(imagenes_doc_alt)
                    # Generar section_images solo para documentos
                    section_images_alt = build_section_images(answer_alt)
                    
                if menciona_ubicacion_alt:
                    # Si pregunta sobre ubicaciones, buscar imágenes de ubicaciones
                    imagenes_ubi_alt = obtener_imagenes_ubicaciones(user_message, answer_alt)
                    append_alt(imagenes_ubi_alt)
                
                # Si NO menciona comunicados NI documentos NI ubicaciones, NO se envían imágenes (section_images_alt ya está vacío)
                
                return {
                    "response": answer_alt,
                    "sources": ["Base de conocimiento BAERA"],
                    "images": imagenes_alt,
                    "section_images": section_images_alt
                }
            except Exception as e2:
                logger.error(f"Error con modelo alternativo: {str(e2)}")
        
        return {
            "response": error_msg + " Por favor, intenta de nuevo.",
            "sources": [],
            "images": [],
            "section_images": []
        }

# ===== RUTAS API =====

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado del servidor"""
    return jsonify({
        "status": "ok",
        "chatbot_ready": bool(knowledge_base),
        "ai_model": "Google Gemini 2.0 Flash"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal del chat"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({"error": "Mensaje vacío"}), 400
        
        # Obtener respuesta del bot
        result = get_bot_response(user_message, session_id)
        
        return jsonify({
            "success": True,
            "message": result["response"],
            "sources": result["sources"],
            "images": result.get("images", []),
            "section_images": result.get("section_images", [])
        })
        
    except Exception as e:
        logger.error(f"❌ Error en /api/chat: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reiniciar conversación de una sesión"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        
        if session_id in chat_histories:
            chat_histories[session_id] = []
        
        return jsonify({
            "success": True,
            "message": "Conversación reiniciada"
        })
        
    except Exception as e:
        logger.error(f"❌ Error en /api/reset: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/data/summary', methods=['GET'])
def data_summary():
    """Obtener resumen de los datos cargados"""
    try:
        summary = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.normpath(os.path.join(current_dir, '..', 'data'))
        
        csv_files = [
            'becas.csv', 'requisitos.csv', 'documentos_requeridos.csv',
            'proceso_postulacion.csv', 'servicios.csv', 'horarios.csv', 'contactos.csv'
        ]
        
        for filename in csv_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                summary[filename] = {
                    "rows": len(df),
                    "columns": list(df.columns)
                }
        
        return jsonify({
            "success": True,
            "summary": summary,
            "knowledge_base_size": len(knowledge_base),
            "documentos_catalogo_size": len(documentos_catalogo)
        })
        
    except Exception as e:
        logger.error(f"❌ Error en /api/data/summary: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===== INICIALIZACIÓN =====

if __name__ == '__main__':
    # Inicializar chatbot al arrancar
    if initialize_chatbot():
        logger.info("🎉 Servidor listo para recibir peticiones con Gemini 2.0 Flash")
    else:
        logger.warning("⚠️  Servidor iniciado pero chatbot no está disponible")
    
    # Iniciar servidor
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )
