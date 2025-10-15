-- Migration: Create Feedback Tables
-- Descrição: Tabelas para sistema de feedback e métricas
-- Autor: GitHub Copilot + Desenvolvedor
-- Data: 09/01/2025
-- Versão: 1.0.0

-- =============================================================================
-- TABELA PRINCIPAL: feedback
-- =============================================================================

CREATE TABLE IF NOT EXISTS feedback (
    -- Identificação
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    usuario_id VARCHAR(100) NOT NULL,
    
    -- Contexto da Conversa
    pergunta TEXT NOT NULL,
    resposta TEXT,  -- Truncada para 1000 caracteres
    agente_usado VARCHAR(100) NOT NULL,
    classificacao VARCHAR(50),  -- ti, rh, geral
    
    -- Feedback Explícito do Usuário
    rating INTEGER NOT NULL CHECK (rating IN (1, 5)),  -- 1=👎, 5=👍
    comentario TEXT,  -- Feedback textual opcional
    
    -- Métricas Implícitas do Sistema
    tempo_resposta_ms INTEGER,  -- Latência em milissegundos
    score_qualidade FLOAT CHECK (score_qualidade BETWEEN 0 AND 1),  -- Score de validação
    num_fallbacks INTEGER DEFAULT 0,  -- Quantos agentes tentaram
    contexto_usado BOOLEAN DEFAULT FALSE  -- Se usou histórico de conversa
);

-- =============================================================================
-- ÍNDICES PARA PERFORMANCE
-- =============================================================================

-- Índice para queries por data (mais comum)
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp 
ON feedback (timestamp DESC);

-- Índice para queries por agente
CREATE INDEX IF NOT EXISTS idx_feedback_agente_usado 
ON feedback (agente_usado);

-- Índice para queries por rating
CREATE INDEX IF NOT EXISTS idx_feedback_rating 
ON feedback (rating);

-- Índice para queries por usuário
CREATE INDEX IF NOT EXISTS idx_feedback_usuario_id 
ON feedback (usuario_id);

-- Índice composto para queries filtradas (mais eficiente)
CREATE INDEX IF NOT EXISTS idx_feedback_agente_timestamp 
ON feedback (agente_usado, timestamp DESC);

-- Índice para classificação
CREATE INDEX IF NOT EXISTS idx_feedback_classificacao 
ON feedback (classificacao);

-- =============================================================================
-- TABELA DE CACHE: agent_metrics_daily
-- =============================================================================

CREATE TABLE IF NOT EXISTS agent_metrics_daily (
    -- Identificação
    metric_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    agente_nome VARCHAR(100) NOT NULL,
    
    -- Métricas Agregadas
    total_respostas INTEGER NOT NULL,
    rating_medio FLOAT,
    taxa_positiva FLOAT CHECK (taxa_positiva BETWEEN 0 AND 1),
    tempo_medio_ms INTEGER,
    score_qualidade_medio FLOAT CHECK (score_qualidade_medio BETWEEN 0 AND 1),
    taxa_fallback FLOAT CHECK (taxa_fallback BETWEEN 0 AND 1),
    
    -- Timestamp de atualização
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraint de unicidade
    UNIQUE (date, agente_nome)
);

-- Índice para queries por data
CREATE INDEX IF NOT EXISTS idx_agent_metrics_date 
ON agent_metrics_daily (date DESC);

-- Índice para queries por agente
CREATE INDEX IF NOT EXISTS idx_agent_metrics_agente 
ON agent_metrics_daily (agente_nome);

-- =============================================================================
-- FUNÇÃO AUXILIAR: Atualizar métricas diárias
-- =============================================================================

CREATE OR REPLACE FUNCTION update_agent_metrics_daily()
RETURNS void AS $$
BEGIN
    -- Atualiza métricas do dia anterior
    INSERT INTO agent_metrics_daily (
        date,
        agente_nome,
        total_respostas,
        rating_medio,
        taxa_positiva,
        tempo_medio_ms,
        score_qualidade_medio,
        taxa_fallback
    )
    SELECT
        DATE(timestamp) as date,
        agente_usado as agente_nome,
        COUNT(*) as total_respostas,
        AVG(rating) as rating_medio,
        SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_positiva,
        AVG(tempo_resposta_ms) as tempo_medio_ms,
        AVG(score_qualidade) as score_qualidade_medio,
        SUM(CASE WHEN num_fallbacks > 0 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_fallback
    FROM feedback
    WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY DATE(timestamp), agente_usado
    ON CONFLICT (date, agente_nome) DO UPDATE SET
        total_respostas = EXCLUDED.total_respostas,
        rating_medio = EXCLUDED.rating_medio,
        taxa_positiva = EXCLUDED.taxa_positiva,
        tempo_medio_ms = EXCLUDED.tempo_medio_ms,
        score_qualidade_medio = EXCLUDED.score_qualidade_medio,
        taxa_fallback = EXCLUDED.taxa_fallback,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS ÚTEIS
-- =============================================================================

-- View: Estatísticas dos últimos 7 dias por agente
CREATE OR REPLACE VIEW v_agent_stats_7d AS
SELECT
    agente_usado,
    COUNT(*) as total_respostas,
    AVG(rating) as rating_medio,
    SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_positiva,
    AVG(tempo_resposta_ms) as tempo_medio_ms,
    AVG(score_qualidade) as score_qualidade_medio,
    SUM(CASE WHEN num_fallbacks > 0 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_fallback
FROM feedback
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY agente_usado
ORDER BY COUNT(*) DESC;

-- View: Feedbacks negativos recentes (para alertas)
CREATE OR REPLACE VIEW v_negative_feedback_recent AS
SELECT
    feedback_id,
    timestamp,
    usuario_id,
    pergunta,
    agente_usado,
    comentario,
    score_qualidade,
    tempo_resposta_ms
FROM feedback
WHERE rating = 1
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- View: Top 10 agentes por satisfação
CREATE OR REPLACE VIEW v_top_agents_by_satisfaction AS
SELECT
    agente_usado,
    COUNT(*) as total_respostas,
    AVG(rating) as rating_medio,
    SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_positiva
FROM feedback
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY agente_usado
HAVING COUNT(*) >= 10  -- Mínimo 10 respostas
ORDER BY taxa_positiva DESC, rating_medio DESC
LIMIT 10;

-- =============================================================================
-- COMENTÁRIOS (Documentação no Banco)
-- =============================================================================

COMMENT ON TABLE feedback IS 'Armazena feedback explícito e métricas implícitas de cada resposta do Neoson';
COMMENT ON COLUMN feedback.rating IS '1 = Thumbs Down (não útil), 5 = Thumbs Up (útil)';
COMMENT ON COLUMN feedback.score_qualidade IS 'Score de validação da resposta (0-1) calculado pelo sistema';
COMMENT ON COLUMN feedback.num_fallbacks IS 'Quantos agentes tentaram antes de obter resposta válida';
COMMENT ON COLUMN feedback.contexto_usado IS 'Se a resposta utilizou histórico de conversa (ConversationMemory)';

COMMENT ON TABLE agent_metrics_daily IS 'Cache de métricas diárias por agente para queries rápidas';
COMMENT ON FUNCTION update_agent_metrics_daily() IS 'Atualiza métricas agregadas do dia anterior (executar via cron)';

COMMENT ON VIEW v_agent_stats_7d IS 'Estatísticas dos últimos 7 dias por agente';
COMMENT ON VIEW v_negative_feedback_recent IS 'Feedbacks negativos das últimas 24h (para alertas)';
COMMENT ON VIEW v_top_agents_by_satisfaction IS 'Top 10 agentes com melhor taxa de satisfação (últimos 30 dias)';

-- =============================================================================
-- DADOS DE EXEMPLO (Opcional - para testes)
-- =============================================================================

-- Descomentar apenas em ambiente de desenvolvimento
/*
INSERT INTO feedback (
    usuario_id, pergunta, resposta, agente_usado, classificacao,
    rating, comentario, tempo_resposta_ms, score_qualidade, num_fallbacks, contexto_usado
) VALUES
    ('user_001', 'Como funciona o backup?', 'O backup é realizado diariamente às 02:00...', 'Alice - Infrastructure', 'ti', 5, 'Muito útil!', 1200, 0.92, 0, false),
    ('user_002', 'Qual o tamanho do storage?', 'O storage tem 10TB de capacidade...', 'Alice - Infrastructure', 'ti', 5, NULL, 850, 0.88, 0, false),
    ('user_003', 'Como resetar senha?', 'Para resetar, acesse o portal...', 'Bob - Development', 'ti', 1, 'Não resolveu meu problema', 2300, 0.65, 1, false),
    ('user_004', 'Quantos dias de férias tenho?', 'Você tem direito a 30 dias...', 'Carol - HR', 'rh', 5, 'Excelente!', 950, 0.95, 0, true),
    ('user_005', 'Como solicitar aumento?', 'O processo de revisão salarial...', 'Carol - HR', 'rh', 5, NULL, 1450, 0.91, 0, true);
*/

-- =============================================================================
-- GRANTS (Ajustar conforme ambiente)
-- =============================================================================

-- Conceder permissões ao usuário da aplicação
-- GRANT SELECT, INSERT, UPDATE ON feedback TO neoson_app;
-- GRANT SELECT ON v_agent_stats_7d, v_negative_feedback_recent, v_top_agents_by_satisfaction TO neoson_app;
-- GRANT EXECUTE ON FUNCTION update_agent_metrics_daily() TO neoson_app;

-- =============================================================================
-- QUERIES ÚTEIS PARA ANÁLISE
-- =============================================================================

-- 1. Rating médio por agente (últimos 7 dias)
-- SELECT * FROM v_agent_stats_7d;

-- 2. Feedbacks negativos para investigar
-- SELECT * FROM v_negative_feedback_recent;

-- 3. Top agentes por satisfação
-- SELECT * FROM v_top_agents_by_satisfaction;

-- 4. Distribuição de ratings por dia
-- SELECT DATE(timestamp) as dia, rating, COUNT(*) as quantidade
-- FROM feedback
-- WHERE timestamp >= NOW() - INTERVAL '30 days'
-- GROUP BY DATE(timestamp), rating
-- ORDER BY dia DESC, rating;

-- 5. Agentes com maior taxa de fallback
-- SELECT agente_usado, AVG(num_fallbacks) as fallback_medio, COUNT(*) as total
-- FROM feedback
-- WHERE timestamp >= NOW() - INTERVAL '7 days'
-- GROUP BY agente_usado
-- HAVING AVG(num_fallbacks) > 0
-- ORDER BY fallback_medio DESC;

-- 6. Impacto do contexto histórico na satisfação
-- SELECT 
--     contexto_usado,
--     COUNT(*) as total,
--     AVG(rating) as rating_medio,
--     SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_positiva
-- FROM feedback
-- WHERE timestamp >= NOW() - INTERVAL '7 days'
-- GROUP BY contexto_usado;

-- =============================================================================
-- FIM DA MIGRATION
-- =============================================================================

-- Verificar criação das tabelas
SELECT 'Tabelas criadas com sucesso!' as status;
SELECT tablename, schemaname FROM pg_tables WHERE tablename IN ('feedback', 'agent_metrics_daily');
SELECT viewname FROM pg_views WHERE viewname LIKE 'v_%';
