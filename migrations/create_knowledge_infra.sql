-- DDL gerada para a tabela vetorial multi-tenant do subagente "infra"
CREATE TABLE IF NOT EXISTS knowledge_infra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    conteudo_original TEXT NOT NULL,
    fonte_documento TEXT,
    dado_sensivel BOOLEAN DEFAULT FALSE,
    apenas_para_si BOOLEAN DEFAULT FALSE,
    areas_liberadas TEXT[],
    nivel_hierarquico_minimo SMALLINT DEFAULT 1,
    geografias_liberadas TEXT[],
    projetos_liberados TEXT[],
    idioma VARCHAR(10),
    data_validade DATE,
    responsavel TEXT,
    aprovador TEXT,
    data_ingestao TIMESTAMPTZ DEFAULT NOW(),
    vetor VECTOR(1536) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_infra_tenant_id ON knowledge_infra (tenant_id);
CREATE INDEX IF NOT EXISTS idx_infra_fonte_documento ON knowledge_infra (fonte_documento);
CREATE INDEX IF NOT EXISTS idx_infra_data_validade ON knowledge_infra (data_validade);

CREATE INDEX IF NOT EXISTS idx_infra_vetor_hnsw
    ON knowledge_infra USING hnsw (vetor vector_cosine_ops);
