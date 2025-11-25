-- Migration: Create Feedback Testers Table
-- Descrição: Estrutura dedicada para registrar feedback do programa de testers internos
-- Autor: GitHub Copilot + Desenvolvedor
-- Data: 19/11/2025
-- Versão: 1.0.0

CREATE TABLE IF NOT EXISTS feedback_testers (
    tester_feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    usuario_id VARCHAR(150) NOT NULL,
    comentario TEXT,
    nota SMALLINT NOT NULL CHECK (nota BETWEEN 0 AND 10),
    origem VARCHAR(100),
    contexto JSONB,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_feedback_testers_usuario
    ON feedback_testers (usuario_id);

CREATE INDEX IF NOT EXISTS idx_feedback_testers_timestamp
    ON feedback_testers (timestamp DESC);

COMMENT ON TABLE feedback_testers IS 'Feedback submetido por testers internos, armazenado diretamente em PostgreSQL';
COMMENT ON COLUMN feedback_testers.nota IS 'Escala de 0 a 10 utilizada no pop-up interno';
COMMENT ON COLUMN feedback_testers.contexto IS 'Metadados contextuais (rota, agente ativo, etc.) enviados pelo frontend';
COMMENT ON COLUMN feedback_testers.metadata IS 'Campos adicionais opcionais enviados pelo backend/frontend';
