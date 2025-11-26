# 🚀 GUÍA RÁPIDA DE INICIO

## Pasos para ejecutar el chatbot

### 1️⃣ Crear entorno virtual
```bash
python -m venv venv
```

### 2️⃣ Activar entorno virtual
```bash
.\venv\Scripts\activate
```

### 3️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4️⃣ Configurar API Key de OpenAI

1. Copia `.env.example` a `.env`:
   ```bash
   copy .env.example .env
   ```

2. Abre `.env` y agrega tu API Key:
   ```
   OPENAI_API_KEY=sk-tu-api-key-aqui
   ```

3. Obtén tu API Key en: https://platform.openai.com/api-keys

### 5️⃣ Iniciar el backend

**Opción A - Usando el script:**
```bash
.\start_backend.bat
```

**Opción B - Manual:**
```bash
python app.py
```

### 6️⃣ Abrir el frontend

Abre `index.html` en tu navegador o usa un servidor local:

```bash
python -m http.server 8000
```

Luego ve a: http://localhost:8000

## ✅ Verificación

1. El backend debe mostrar: `✅ Chatbot inicializado correctamente`
2. El frontend debe cargar el chat flotante
3. Prueba enviando: "¿Cuáles son los requisitos de la beca?"

## 🐛 Problemas Comunes

### Error: "OPENAI_API_KEY no encontrada"
- Verifica que creaste el archivo `.env`
- Asegúrate de que la API key sea válida

### Error: "ModuleNotFoundError"
- Activa el entorno virtual: `.\venv\Scripts\activate`
- Reinstala dependencias: `pip install -r requirements.txt`

### El chatbot no responde
- Verifica que el backend esté corriendo en http://localhost:5000
- Abre la consola del navegador (F12) para ver errores

## 📞 Soporte

Si tienes problemas, revisa el archivo `README.md` para más detalles.
