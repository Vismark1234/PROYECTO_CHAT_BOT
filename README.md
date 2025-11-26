# Chatbot BAERA - UMSA
## Sistema de Chatbot con Google Gemini y LangChain

### 📁 Estructura del Proyecto

```
PROYECTO CHAT BOT/
├── backend/                    # Backend Python
│   ├── app.py                 # Servidor Flask con Gemini
│   └── requirements.txt       # Dependencias Python
│
├── frontend/                   # Frontend Web
│   ├── index.html             # Página principal
│   ├── script.js              # Lógica del chatbot
│   └── styles.css             # Estilos CSS
│
├── data/                       # Datos CSV
│   ├── becas.csv
│   ├── requisitos.csv
│   ├── documentos_requeridos.csv
│   ├── proceso_postulacion.csv
│   ├── servicios.csv
│   ├── horarios.csv
│   └── contactos.csv
│
├── config/                     # Configuración
│   ├── .env.example           # Plantilla de variables
│   ├── .env                   # Variables de entorno (no en git)
│   └── .gitignore             # Archivos ignorados
│
├── docs/                       # Documentación
│   ├── README.md              # Documentación completa
│   └── QUICK_START.md         # Guía rápida
│
└── start.bat                   # Script de inicio
```

### 🚀 Inicio Rápido

#### 1. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Configurar API Key de Gemini

1. Obtén tu API key en: https://makersuite.google.com/app/apikey
2. Copia `config/.env.example` a `config/.env`
3. Agrega tu API key en el archivo `.env`:

```
GOOGLE_API_KEY=tu_api_key_aqui
```

#### 3. Ejecutar el proyecto

```bash
# Opción 1: Usar el script (recomendado)
start.bat

# Opción 2: Manual
cd backend
python app.py
```

#### 4. Abrir el frontend

Abre `frontend/index.html` en tu navegador

### ✨ Características

- ✅ **Google Gemini Pro** - IA de última generación
- ✅ **LangChain** - Framework de IA conversacional
- ✅ **Vector Store** - Búsqueda semántica con ChromaDB
- ✅ **Memoria Conversacional** - Mantiene contexto
- ✅ **Datos Reales** - Conectado a CSV de BAERA
- ✅ **API REST** - Backend escalable

### 📚 Documentación

Ver `docs/README.md` para documentación completa

### 🔑 API Endpoints

- `POST /api/chat` - Enviar mensaje
- `GET /api/health` - Estado del servidor
- `POST /api/reset` - Reiniciar conversación
- `GET /api/data/summary` - Resumen de datos

### 🛠️ Tecnologías

**Backend:**
- Python 3.x
- Flask
- LangChain
- Google Gemini AI
- ChromaDB
- Pandas

**Frontend:**
- HTML5
- CSS3
- JavaScript (Vanilla)

### 📞 Soporte

Para más información, consulta la documentación en `docs/`
