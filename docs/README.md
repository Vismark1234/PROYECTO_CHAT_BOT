# Chatbot BAERA - UMSA

Sistema de chatbot inteligente para información sobre la Beca Comedor BAERA de la Universidad Mayor de San Andrés (UMSA), construido con LangChain y conectado a datos reales en formato CSV.

## 🚀 Características

- ✅ Backend Python con Flask y LangChain
- ✅ Integración con OpenAI GPT-3.5-turbo
- ✅ Datos cargados desde archivos CSV
- ✅ Vector store con ChromaDB para búsqueda semántica
- ✅ Memoria conversacional
- ✅ Frontend moderno con interfaz de chat
- ✅ Iframe integrado con portal BECATS

## 📋 Requisitos Previos

- Python 3.8 o superior
- Node.js (opcional, solo para desarrollo frontend)
- API Key de OpenAI

## 🛠️ Instalación

### 1. Clonar o descargar el proyecto

```bash
cd "C:\Users\Vismark Choque\Documents\PROYECTO CHAT BOT"
```

### 2. Crear entorno virtual de Python

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Copia el archivo `.env.example` a `.env`:

```bash
copy .env.example .env
```

Edita el archivo `.env` y agrega tu API Key de OpenAI:

```
OPENAI_API_KEY=tu_api_key_aqui
```

**¿Dónde obtener la API Key?**
1. Ve a https://platform.openai.com/api-keys
2. Inicia sesión o crea una cuenta
3. Crea una nueva API key
4. Cópiala y pégala en el archivo `.env`

## 🎯 Uso

### Iniciar el backend

```bash
python app.py
```

El servidor se iniciará en `http://localhost:5000`

### Abrir el frontend

Simplemente abre el archivo `index.html` en tu navegador:

```bash
start index.html
```

O usa un servidor local (recomendado):

```bash
# Con Python
python -m http.server 8000

# Luego abre http://localhost:8000 en tu navegador
```

## 📁 Estructura del Proyecto

```
PROYECTO CHAT BOT/
├── app.py                      # Backend Flask con LangChain
├── index.html                  # Frontend HTML
├── script.js                   # Lógica del chatbot frontend
├── styles.css                  # Estilos CSS
├── requirements.txt            # Dependencias Python
├── .env                        # Variables de entorno (no incluido en git)
├── .env.example               # Plantilla de variables de entorno
├── README.md                   # Este archivo
├── becas.csv                   # Datos de becas
├── requisitos.csv              # Requisitos
├── documentos_requeridos.csv   # Documentos necesarios
├── proceso_postulacion.csv     # Proceso de postulación
├── servicios.csv               # Servicios ofrecidos
├── horarios.csv                # Horarios de atención
├── contactos.csv               # Información de contacto
└── create_database.sql         # Script SQL para Supabase (opcional)
```

## 🔧 API Endpoints

### `POST /api/chat`
Enviar un mensaje al chatbot

**Request:**
```json
{
  "message": "¿Cuáles son los requisitos para la beca?",
  "session_id": "session_123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Los requisitos para la beca BAERA son...",
  "sources": [...]
}
```

### `GET /api/health`
Verificar estado del servidor

**Response:**
```json
{
  "status": "ok",
  "chatbot_ready": true
}
```

### `POST /api/reset`
Reiniciar conversación

**Request:**
```json
{
  "session_id": "session_123"
}
```

### `GET /api/data/summary`
Obtener resumen de datos cargados

## 📊 Datos

Los datos del chatbot se cargan desde archivos CSV que contienen información sobre:

- **Becas**: Información general de la beca BAERA
- **Requisitos**: Condiciones para aplicar
- **Documentos**: Documentación necesaria
- **Proceso**: Pasos de postulación
- **Servicios**: Desayuno, almuerzo, cena
- **Horarios**: Horarios de atención
- **Contactos**: Información de contacto

## 🤖 Cómo Funciona

1. **Carga de Datos**: Al iniciar, el backend carga todos los archivos CSV
2. **Embeddings**: Convierte los datos en vectores usando OpenAI Embeddings
3. **Vector Store**: Almacena los vectores en ChromaDB para búsqueda rápida
4. **Conversación**: Cuando el usuario envía un mensaje:
   - Se buscan los documentos más relevantes
   - Se envía el contexto + pregunta a GPT-3.5
   - GPT genera una respuesta basada en los datos reales
   - Se mantiene el historial de conversación

## 🎨 Personalización

### Cambiar el modelo de IA

En `app.py`, línea ~120:

```python
llm = ChatOpenAI(
    model_name="gpt-4",  # Cambiar a gpt-4 para mejor calidad
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY
)
```

### Modificar el número de documentos recuperados

En `app.py`, línea ~130:

```python
retriever=vectorstore.as_retriever(search_kwargs={"k": 5})  # Cambiar k
```

### Cambiar la URL del backend

En `script.js`, línea 11:

```javascript
const API_URL = 'http://tu-servidor.com/api/chat';
```

## 🐛 Solución de Problemas

### El chatbot no responde

1. Verifica que el backend esté ejecutándose
2. Revisa la consola del navegador (F12) para errores
3. Verifica que la API Key de OpenAI sea válida

### Error "OPENAI_API_KEY no encontrada"

Asegúrate de haber creado el archivo `.env` y agregado tu API key.

### Error de CORS

Si el frontend y backend están en diferentes puertos, asegúrate de que CORS esté habilitado en `app.py` (ya está configurado).

### ChromaDB no se crea

Verifica que tengas permisos de escritura en la carpeta del proyecto.

## 📝 Notas

- El chatbot usa GPT-3.5-turbo por defecto (más económico)
- Los datos se cargan en memoria al iniciar el servidor
- El vector store se guarda en `./chroma_db`
- Las conversaciones se mantienen en memoria (se pierden al reiniciar)

## 🚀 Próximos Pasos

- [ ] Implementar persistencia de conversaciones en base de datos
- [ ] Agregar autenticación de usuarios
- [ ] Conectar a Supabase en lugar de CSV
- [ ] Agregar más fuentes de datos
- [ ] Implementar rate limiting
- [ ] Agregar analytics y métricas

## 📄 Licencia

Este proyecto es de uso interno para la UMSA.

## 👥 Contacto

Para soporte o consultas sobre el chatbot, contacta al equipo de desarrollo.
