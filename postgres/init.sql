-- ====================================================================
-- HUBFÓLIO - DATABASE SCHEMA
-- Sistema de Avaliação de Qualidade de Portfólios
-- ====================================================================

-- Criar extensão para UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================================================
-- TABELA: users
-- Armazena informações dos usuários/estudantes
-- ====================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS 'Usuários da plataforma HubFólio';
COMMENT ON COLUMN users.user_id IS 'ID único do usuário';
COMMENT ON COLUMN users.nome IS 'Nome completo do usuário';

-- ====================================================================
-- TABELA: portfolios
-- Armazena dados brutos dos portfólios
-- ====================================================================
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Seções Preenchidas (features binárias/numéricas)
    bio BOOLEAN NOT NULL DEFAULT FALSE,
    projetos_min INTEGER NOT NULL DEFAULT 0,
    habilidades_min INTEGER NOT NULL DEFAULT 0,
    contatos BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Palavras-chave de Clareza (features numéricas)
    kw_contexto INTEGER NOT NULL DEFAULT 0,
    kw_processo INTEGER NOT NULL DEFAULT 0,
    kw_resultado INTEGER NOT NULL DEFAULT 0,
    
    -- Consistência Visual (0-100)
    consistencia_visual_score FLOAT NOT NULL DEFAULT 0,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_projetos_min CHECK (projetos_min >= 0),
    CONSTRAINT check_habilidades_min CHECK (habilidades_min >= 0),
    CONSTRAINT check_kw_contexto CHECK (kw_contexto >= 0),
    CONSTRAINT check_kw_processo CHECK (kw_processo >= 0),
    CONSTRAINT check_kw_resultado CHECK (kw_resultado >= 0),
    CONSTRAINT check_consistencia_visual CHECK (consistencia_visual_score >= 0 AND consistencia_visual_score <= 100)
);

COMMENT ON TABLE portfolios IS 'Dados brutos dos portfólios dos usuários';
COMMENT ON COLUMN portfolios.bio IS 'Se o usuário preencheu a bio (true/false)';
COMMENT ON COLUMN portfolios.projetos_min IS 'Número de projetos no portfólio';
COMMENT ON COLUMN portfolios.habilidades_min IS 'Número de habilidades listadas';
COMMENT ON COLUMN portfolios.contatos IS 'Se o usuário incluiu informações de contato';
COMMENT ON COLUMN portfolios.kw_contexto IS 'Quantidade de palavras-chave de contexto nos projetos';
COMMENT ON COLUMN portfolios.kw_processo IS 'Quantidade de palavras-chave de processo nos projetos';
COMMENT ON COLUMN portfolios.kw_resultado IS 'Quantidade de palavras-chave de resultado nos projetos';
COMMENT ON COLUMN portfolios.consistencia_visual_score IS 'Score de consistência visual (0-100)';

-- ====================================================================
-- TABELA: portfolio_metrics
-- Armazena métricas calculadas (Completude, Clareza, IQ)
-- ====================================================================
CREATE TABLE IF NOT EXISTS portfolio_metrics (
    metric_id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    
    -- Métricas Calculadas
    completude_score FLOAT NOT NULL DEFAULT 0,
    clareza_score FLOAT NOT NULL DEFAULT 0,
    indice_qualidade FLOAT NOT NULL DEFAULT 0,
    
    -- Metadados
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_completude CHECK (completude_score >= 0 AND completude_score <= 100),
    CONSTRAINT check_clareza CHECK (clareza_score >= 0 AND clareza_score <= 100),
    CONSTRAINT check_indice_qualidade CHECK (indice_qualidade >= 0 AND indice_qualidade <= 100)
);

COMMENT ON TABLE portfolio_metrics IS 'Métricas calculadas dos portfólios';
COMMENT ON COLUMN portfolio_metrics.completude_score IS 'Score de completude (0-100)';
COMMENT ON COLUMN portfolio_metrics.clareza_score IS 'Score de clareza (0-100)';
COMMENT ON COLUMN portfolio_metrics.indice_qualidade IS 'Índice de Qualidade final (0-100)';

-- ====================================================================
-- TABELA: predictions
-- Armazena predições do modelo de ML
-- ====================================================================
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    
    -- Resultado da Predição
    predicted_iq FLOAT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    
    -- Classificação
    classification VARCHAR(50),
    
    -- Feedback Gerado
    feedback_suggestions TEXT[],
    
    -- Metadados
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_predicted_iq CHECK (predicted_iq >= 0 AND predicted_iq <= 100)
);

COMMENT ON TABLE predictions IS 'Predições do modelo de Machine Learning';
COMMENT ON COLUMN predictions.predicted_iq IS 'Índice de Qualidade previsto pelo modelo';
COMMENT ON COLUMN predictions.model_name IS 'Nome do modelo usado (ex: LinearRegression, DecisionTree)';
COMMENT ON COLUMN predictions.classification IS 'Classificação (Excelente, Bom, Regular, Precisa Melhorar)';
COMMENT ON COLUMN predictions.feedback_suggestions IS 'Array de sugestões de melhoria';

-- ====================================================================
-- VIEWS: Queries úteis pré-computadas
-- ====================================================================

-- View: Sumário completo de portfólios com métricas
CREATE OR REPLACE VIEW portfolio_summary AS
SELECT 
    u.user_id,
    u.nome,
    p.portfolio_id,
    p.bio,
    p.projetos_min,
    p.habilidades_min,
    p.contatos,
    p.kw_contexto,
    p.kw_processo,
    p.kw_resultado,
    p.consistencia_visual_score,
    m.completude_score,
    m.clareza_score,
    m.indice_qualidade,
    p.created_at
FROM users u
JOIN portfolios p ON u.user_id = p.user_id
LEFT JOIN portfolio_metrics m ON p.portfolio_id = m.portfolio_id;

COMMENT ON VIEW portfolio_summary IS 'Visão consolidada de portfólios com métricas';

-- View: Estatísticas gerais dos portfólios
CREATE OR REPLACE VIEW portfolio_stats AS
SELECT 
    COUNT(*) as total_portfolios,
    AVG(m.indice_qualidade) as avg_iq,
    MIN(m.indice_qualidade) as min_iq,
    MAX(m.indice_qualidade) as max_iq,
    STDDEV(m.indice_qualidade) as stddev_iq,
    AVG(p.projetos_min) as avg_projects,
    AVG(p.habilidades_min) as avg_skills,
    AVG(p.consistencia_visual_score) as avg_visual_score
FROM portfolios p
LEFT JOIN portfolio_metrics m ON p.portfolio_id = m.portfolio_id;

COMMENT ON VIEW portfolio_stats IS 'Estatísticas agregadas dos portfólios';

-- View: Top portfólios por IQ
CREATE OR REPLACE VIEW top_portfolios AS
SELECT 
    u.nome,
    m.indice_qualidade,
    p.projetos_min,
    p.habilidades_min,
    p.consistencia_visual_score
FROM users u
JOIN portfolios p ON u.user_id = p.user_id
JOIN portfolio_metrics m ON p.portfolio_id = m.portfolio_id
ORDER BY m.indice_qualidade DESC
LIMIT 20;

COMMENT ON VIEW top_portfolios IS 'Top 20 portfólios com maior Índice de Qualidade';

-- ====================================================================
-- ÍNDICES para otimização de queries
-- ====================================================================

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolio_metrics_portfolio_id ON portfolio_metrics(portfolio_id);
CREATE INDEX idx_predictions_portfolio_id ON predictions(portfolio_id);
CREATE INDEX idx_predictions_model_name ON predictions(model_name);
CREATE INDEX idx_portfolio_metrics_iq ON portfolio_metrics(indice_qualidade DESC);

-- ====================================================================
-- FUNÇÕES UTILITÁRIAS
-- ====================================================================

-- Função para calcular métricas automaticamente
CREATE OR REPLACE FUNCTION calculate_portfolio_metrics(p_portfolio_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_bio INTEGER;
    v_projetos INTEGER;
    v_habilidades INTEGER;
    v_contatos INTEGER;
    v_kw_contexto INTEGER;
    v_kw_processo INTEGER;
    v_kw_resultado INTEGER;
    v_visual_score FLOAT;
    v_completude FLOAT;
    v_clareza FLOAT;
    v_iq FLOAT;
    v_total_kw INTEGER;
BEGIN
    -- Buscar dados do portfólio
    SELECT 
        CASE WHEN bio THEN 1 ELSE 0 END,
        projetos_min,
        habilidades_min,
        CASE WHEN contatos THEN 1 ELSE 0 END,
        kw_contexto,
        kw_processo,
        kw_resultado,
        consistencia_visual_score
    INTO 
        v_bio, v_projetos, v_habilidades, v_contatos,
        v_kw_contexto, v_kw_processo, v_kw_resultado, v_visual_score
    FROM portfolios
    WHERE portfolio_id = p_portfolio_id;
    
    -- Calcular Completude (0-100%)
    v_completude := (
        (v_bio * 25) +
        (CASE WHEN v_projetos >= 1 THEN 25 ELSE 0 END) +
        (CASE WHEN v_habilidades >= 5 THEN 25 ELSE 0 END) +
        (v_contatos * 25)
    );
    
    -- Calcular Clareza (0-100%)
    v_total_kw := v_kw_contexto + v_kw_processo + v_kw_resultado;
    v_clareza := LEAST(100, (v_total_kw::FLOAT / 15.0) * 100);
    
    -- Calcular Índice de Qualidade (0-100)
    v_iq := (v_completude * 0.4) + (v_clareza * 0.4) + (v_visual_score * 0.2);
    
    -- Inserir ou atualizar métricas
    INSERT INTO portfolio_metrics (portfolio_id, completude_score, clareza_score, indice_qualidade)
    VALUES (p_portfolio_id, v_completude, v_clareza, v_iq)
    ON CONFLICT (portfolio_id) 
    DO UPDATE SET 
        completude_score = EXCLUDED.completude_score,
        clareza_score = EXCLUDED.clareza_score,
        indice_qualidade = EXCLUDED.indice_qualidade,
        calculated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Adicionar UNIQUE constraint para evitar duplicatas
ALTER TABLE portfolio_metrics ADD CONSTRAINT unique_portfolio_id UNIQUE (portfolio_id);

COMMENT ON FUNCTION calculate_portfolio_metrics IS 'Calcula e atualiza métricas de um portfólio';

-- ====================================================================
-- DADOS DE EXEMPLO (opcional - será populado pelo ETL)
-- ====================================================================

-- Seed data será inserido via ETL (etl_minio_postgres.py)

-- ====================================================================
-- CONCLUSÃO
-- ====================================================================

-- Verificar tabelas criadas
SELECT 
    table_name, 
    table_type 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
