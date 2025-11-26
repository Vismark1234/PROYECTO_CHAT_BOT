-- ============================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS
-- Sistema de Becas UMSA - BAERA
-- Base de datos para Supabase (PostgreSQL)
-- Información extraída de la presentación oficial
-- ============================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- TABLA PRINCIPAL: becas
-- ============================================
CREATE TABLE IF NOT EXISTS becas (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(255) NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE becas IS 'Tabla principal que almacena información general de las becas';

-- ============================================
-- TABLA: requisitos
-- ============================================
CREATE TABLE IF NOT EXISTS requisitos (
    id BIGSERIAL PRIMARY KEY,
    beca_id BIGINT NOT NULL REFERENCES becas(id) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_requisitos_beca_id ON requisitos(beca_id);

COMMENT ON TABLE requisitos IS 'Requisitos para aplicar a la beca';

-- ============================================
-- TABLA: documentos_requeridos
-- ============================================
CREATE TABLE IF NOT EXISTS documentos_requeridos (
    id BIGSERIAL PRIMARY KEY,
    beca_id BIGINT NOT NULL REFERENCES becas(id) ON DELETE CASCADE,
    nombre_documento VARCHAR(255) NOT NULL,
    imagen_url TEXT,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documentos_beca_id ON documentos_requeridos(beca_id);

COMMENT ON TABLE documentos_requeridos IS 'Documentos necesarios para la postulación';

-- ============================================
-- TABLA: proceso_postulacion
-- ============================================
CREATE TABLE IF NOT EXISTS proceso_postulacion (
    id BIGSERIAL PRIMARY KEY,
    beca_id BIGINT NOT NULL REFERENCES becas(id) ON DELETE CASCADE,
    paso INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_proceso_beca_id ON proceso_postulacion(beca_id);

COMMENT ON TABLE proceso_postulacion IS 'Pasos del proceso de postulación a la beca';

-- ============================================
-- TABLA: servicios
-- ============================================
CREATE TABLE IF NOT EXISTS servicios (
    id BIGSERIAL PRIMARY KEY,
    beca_id BIGINT NOT NULL REFERENCES becas(id) ON DELETE CASCADE,
    servicio VARCHAR(255) NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_servicios_beca_id ON servicios(beca_id);

COMMENT ON TABLE servicios IS 'Servicios incluidos en la beca';

-- ============================================
-- TABLA: horarios
-- ============================================
CREATE TABLE IF NOT EXISTS horarios (
    id BIGSERIAL PRIMARY KEY,
    beca_id BIGINT NOT NULL REFERENCES becas(id) ON DELETE CASCADE,
    servicio VARCHAR(100) NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_horarios_beca_id ON horarios(beca_id);

COMMENT ON TABLE horarios IS 'Horarios de atención de los servicios';

-- ============================================
-- TABLA: contactos
-- ============================================
CREATE TABLE IF NOT EXISTS contactos (
    id BIGSERIAL PRIMARY KEY,
    beca_id BIGINT NOT NULL REFERENCES becas(id) ON DELETE CASCADE,
    contacto VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contactos_beca_id ON contactos(beca_id);

COMMENT ON TABLE contactos IS 'Información de contacto relacionada con la beca';

-- ============================================
-- TABLA: compromiso_beca
-- ============================================
CREATE TABLE IF NOT EXISTS compromiso_beca (
    id BIGSERIAL PRIMARY KEY,
    beca_id BIGINT NOT NULL REFERENCES becas(id) ON DELETE CASCADE,
    seccion VARCHAR(255),
    articulo VARCHAR(255),
    contenido TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_compromiso_beca_id ON compromiso_beca(beca_id);

COMMENT ON TABLE compromiso_beca IS 'Compromiso y obligaciones del estudiante becado';

-- ============================================
-- VISTA: Información completa de beca
-- ============================================
CREATE OR REPLACE VIEW vista_beca_completa AS
SELECT 
    b.id,
    b.nombre,
    b.tipo,
    COUNT(DISTINCT r.id) as total_requisitos,
    COUNT(DISTINCT d.id) as total_documentos,
    COUNT(DISTINCT s.id) as total_servicios,
    b.created_at
FROM becas b
LEFT JOIN requisitos r ON b.id = r.beca_id
LEFT JOIN documentos_requeridos d ON b.id = d.beca_id
LEFT JOIN servicios s ON b.id = s.beca_id
GROUP BY b.id;

COMMENT ON VIEW vista_beca_completa IS 'Vista con información resumida de cada beca';

-- ============================================
-- TABLA: comunicados
-- ============================================
CREATE TABLE IF NOT EXISTS comunicados (
    id BIGSERIAL PRIMARY KEY,
    beca_id BIGINT REFERENCES becas(id) ON DELETE CASCADE,
    titulo VARCHAR(255),
    descripcion TEXT,
    fecha DATE,
    fecha_pago DATE,
    contenido TEXT,
    imagen_url TEXT,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comunicados_beca_id ON comunicados(beca_id);
CREATE INDEX idx_comunicados_fecha ON comunicados(fecha);

COMMENT ON TABLE comunicados IS 'Comunicados y avisos oficiales con imágenes';

-- ============================================
-- TABLA: ubicaciones
-- ============================================
CREATE TABLE IF NOT EXISTS ubicaciones (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    imagen_url TEXT NOT NULL,
    direccion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ubicaciones IS 'Ubicaciones y sus imágenes correspondientes';

-- ============================================
-- FIN DEL SCRIPT
-- ============================================
