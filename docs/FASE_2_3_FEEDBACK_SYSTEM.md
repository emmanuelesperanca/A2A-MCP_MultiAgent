# Fase 2.3: Sistema de Feedback e Métricas

**Status:** 🔄 EM IMPLEMENTAÇÃO  
**Data Início:** 09/01/2025  
**Duração Estimada:** 2-3 semanas  
**Prioridade:** Alta

---

## 🎯 Objetivos

1. **Coletar Feedback Explícito** dos usuários (thumbs up/down)
2. **Rastrear Métricas** de performance por agente
3. **Criar Dashboard** de observabilidade (Grafana)
4. **Habilitar Melhoria Contínua** baseada em dados reais

---

## 📊 Componentes do Sistema

### 1. Backend: FeedbackSystem (`core/feedback_system.py`)

```python
class FeedbackSystem:
    """
    Sistema centralizado de feedback e métricas.
    
    Funcionalidades:
    - Armazenar feedback do usuário (thumbs, comments)
    - Calcular métricas por agente
    - Gerar relatórios agregados
    - Integração com Prometheus
    """
```

#### Esquema de Dados

```python
@dataclass
class FeedbackEntry:
    feedback_id: str          # UUID único
    timestamp: str            # ISO format
    usuario_id: str           # ID do usuário
    pergunta: str             # Pergunta original
    resposta: str             # Resposta fornecida (truncada)
    agente_usado: str         # Nome do agente
    classificacao: str        # ti, rh, geral
    
    # Feedback Explícito
    rating: int               # 1 (👎) ou 5 (👍)
    comentario: Optional[str] # Feedback textual
    
    # Métricas Implícitas
    tempo_resposta_ms: int    # Latência
    score_qualidade: float    # 0-1 (validação)
    num_fallbacks: int        # Quantos agentes tentaram
    contexto_usado: bool      # Usou histórico?
```

#### Métodos Principais

```python
# Salvar feedback
await feedback_system.save_feedback(
    usuario_id="user_123",
    pergunta="Como funciona backup?",
    resposta="O backup é...",
    agente_usado="Alice - Infrastructure",
    classificacao="ti",
    rating=5,  # 👍
    comentario="Muito útil!",
    tempo_resposta_ms=1250,
    score_qualidade=0.91,
    num_fallbacks=0
)

# Obter métricas de um agente
stats = await feedback_system.get_agent_stats("Alice - Infrastructure")
# Retorna: {
#     "total_respostas": 1542,
#     "rating_medio": 4.2,
#     "taxa_positiva": 0.84,
#     "tempo_medio_ms": 1830,
#     "score_qualidade_medio": 0.87,
#     "taxa_fallback": 0.15
# }

# Obter tendências (últimos 7 dias)
trends = await feedback_system.get_trends(days=7)

# Exportar métricas para Prometheus
metrics = feedback_system.export_prometheus_metrics()
```

### 2. Database Schema (PostgreSQL)

```sql
-- Tabela de Feedback
CREATE TABLE feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    usuario_id VARCHAR(100) NOT NULL,
    pergunta TEXT NOT NULL,
    resposta TEXT,  -- Truncada para 1000 chars
    agente_usado VARCHAR(100) NOT NULL,
    classificacao VARCHAR(50),
    
    -- Feedback Explícito
    rating INTEGER CHECK (rating IN (1, 5)),  -- 1=👎, 5=👍
    comentario TEXT,
    
    -- Métricas Implícitas
    tempo_resposta_ms INTEGER,
    score_qualidade FLOAT CHECK (score_qualidade BETWEEN 0 AND 1),
    num_fallbacks INTEGER DEFAULT 0,
    contexto_usado BOOLEAN DEFAULT FALSE,
    
    -- Índices
    INDEX idx_timestamp (timestamp),
    INDEX idx_agente_usado (agente_usado),
    INDEX idx_rating (rating),
    INDEX idx_usuario_id (usuario_id)
);

-- Tabela de Métricas Agregadas (cache)
CREATE TABLE agent_metrics_daily (
    metric_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    agente_nome VARCHAR(100) NOT NULL,
    
    total_respostas INTEGER,
    rating_medio FLOAT,
    taxa_positiva FLOAT,
    tempo_medio_ms INTEGER,
    score_qualidade_medio FLOAT,
    taxa_fallback FLOAT,
    
    UNIQUE (date, agente_nome)
);
```

### 3. API Endpoints (FastAPI)

#### POST /feedback
```python
@app.post("/feedback")
async def submit_feedback(
    usuario_id: str,
    feedback_id: str,  # ID da resposta original
    rating: int,       # 1 ou 5
    comentario: Optional[str] = None
):
    """
    Submete feedback do usuário para uma resposta.
    
    Returns:
        {"status": "success", "feedback_id": "uuid"}
    """
```

#### GET /stats/agent/{agent_name}
```python
@app.get("/stats/agent/{agent_name}")
async def get_agent_stats(
    agent_name: str,
    days: int = 7
):
    """
    Retorna estatísticas de um agente específico.
    
    Returns:
        {
            "agent_name": "Alice - Infrastructure",
            "period": "7 days",
            "stats": {
                "total_respostas": 342,
                "rating_medio": 4.3,
                "taxa_positiva": 0.86,
                "tempo_medio_ms": 1650,
                "score_qualidade_medio": 0.89,
                "taxa_fallback": 0.12
            }
        }
    """
```

#### GET /stats/dashboard
```python
@app.get("/stats/dashboard")
async def get_dashboard_stats(days: int = 7):
    """
    Retorna métricas agregadas para dashboard.
    
    Returns:
        {
            "period": "7 days",
            "global": {
                "total_respostas": 2145,
                "rating_medio": 4.1,
                "taxa_positiva": 0.82
            },
            "by_agent": [...],
            "by_classification": {...},
            "trends": [...]
        }
    """
```

#### GET /metrics (Prometheus)
```python
@app.get("/metrics")
async def prometheus_metrics():
    """
    Exporta métricas no formato Prometheus.
    
    Returns (text/plain):
        # HELP neoson_responses_total Total de respostas
        # TYPE neoson_responses_total counter
        neoson_responses_total{agent="Alice"} 1542
        
        # HELP neoson_rating_average Rating médio (1-5)
        # TYPE neoson_rating_average gauge
        neoson_rating_average{agent="Alice"} 4.2
        
        # HELP neoson_response_time_ms Tempo de resposta (ms)
        # TYPE neoson_response_time_ms histogram
        ...
    """
```

### 4. Frontend UI Components

#### Thumbs Up/Down Buttons
```html
<!-- Após cada resposta -->
<div class="feedback-buttons">
    <button class="thumb-up" onclick="submitFeedback(5)">
        👍 Útil
    </button>
    <button class="thumb-down" onclick="submitFeedback(1)">
        👎 Não Útil
    </button>
</div>

<!-- Modal para comentário (opcional) -->
<div id="feedback-modal" style="display:none">
    <h3>Obrigado pelo feedback!</h3>
    <textarea placeholder="Quer nos contar mais? (opcional)"></textarea>
    <button onclick="submitComment()">Enviar</button>
    <button onclick="closeModal()">Pular</button>
</div>
```

#### JavaScript
```javascript
async function submitFeedback(rating) {
    const response = await fetch('/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            usuario_id: currentUserId,
            feedback_id: currentResponseId,
            rating: rating
        })
    });
    
    if (rating === 1) {
        // Se negativo, pedir comentário
        showFeedbackModal();
    } else {
        showThankYouMessage();
    }
}
```

### 5. Dashboard Grafana

#### Painéis Principais

**Painel 1: Visão Geral**
- Total de respostas (últimos 7 dias)
- Rating médio global
- Taxa de satisfação (👍/total)
- Tempo médio de resposta

**Painel 2: Performance por Agente**
- Gráfico de barras: Respostas por agente
- Heatmap: Rating médio por agente e dia
- Line chart: Tempo de resposta ao longo do tempo

**Painel 3: Qualidade das Respostas**
- Score de qualidade médio (validação)
- Taxa de fallback por agente
- Distribuição de ratings (1 vs 5)

**Painel 4: Tendências**
- Rating médio nos últimos 30 dias
- Volume de perguntas por classificação
- Top 5 agentes mais usados

**Painel 5: Alertas**
- Agentes com rating < 3.0
- Tempos de resposta > 5s
- Taxa de fallback > 50%

#### Configuração Grafana

```yaml
# docker-compose.yml (adicionar)
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=neoson123
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - postgres
      - prometheus

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-storage:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

volumes:
  grafana-storage:
  prometheus-storage:
```

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'neoson'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
```

---

## 🔧 Implementação (Faseada)

### Sprint 1 (Dias 1-5): Backend Core

**Tarefas:**
1. ✅ Criar `core/feedback_system.py`
2. ✅ Implementar `FeedbackEntry` dataclass
3. ✅ Implementar `FeedbackSystem` class
4. ✅ Métodos: `save_feedback()`, `get_agent_stats()`
5. ✅ Criar migration SQL (`migrations/create_feedback_tables.sql`)
6. ✅ Testes: `test_feedback_system.py` (15+ testes)

**Entregáveis:**
- Sistema funcionando com PostgreSQL
- Testes passando
- Documentação básica

### Sprint 2 (Dias 6-10): API Integration

**Tarefas:**
1. ✅ Adicionar endpoints em `app_fastapi.py`
2. ✅ POST `/feedback`
3. ✅ GET `/stats/agent/{name}`
4. ✅ GET `/stats/dashboard`
5. ✅ Integrar com TICoordinatorAsync
6. ✅ Testes de integração

**Entregáveis:**
- API funcionando
- Testes de endpoints
- Postman collection

### Sprint 3 (Dias 11-15): Frontend UI

**Tarefas:**
1. ✅ Adicionar botões 👍👎 em `templates/chat.html`
2. ✅ JavaScript para submit assíncrono
3. ✅ Modal de comentário
4. ✅ Animações e feedback visual
5. ✅ Testes manuais

**Entregáveis:**
- UI funcional e responsiva
- UX polida
- Documentação de uso

### Sprint 4 (Dias 16-21): Observability

**Tarefas:**
1. ✅ Configurar Prometheus
2. ✅ Implementar `/metrics` endpoint
3. ✅ Configurar Grafana
4. ✅ Criar dashboards
5. ✅ Configurar alertas
6. ✅ Docker Compose completo

**Entregáveis:**
- Grafana rodando
- 5 dashboards configurados
- Alertas funcionando

---

## 📈 Métricas de Sucesso

| Métrica | Meta | Como Medir |
|---------|------|------------|
| **Taxa de Feedback** | >30% | (feedbacks / respostas) |
| **Rating Médio** | >4.0 | Média de ratings |
| **Tempo de Resposta** | <2s | P95 latência |
| **Taxa de Satisfação** | >80% | (👍 / total feedbacks) |
| **Cobertura de Testes** | 100% | pytest --cov |

---

## 🧪 Plano de Testes

### Unit Tests (`test_feedback_system.py`)

```python
class TestFeedbackEntry:
    def test_create_feedback_entry()
    def test_to_dict()
    def test_from_dict()
    def test_truncate_resposta()

class TestFeedbackSystemSave:
    def test_save_feedback_postgres()
    def test_save_feedback_redis_cache()
    def test_save_feedback_validation()
    def test_save_feedback_duplicate()

class TestFeedbackSystemStats:
    def test_get_agent_stats()
    def test_get_agent_stats_empty()
    def test_get_dashboard_stats()
    def test_get_trends()

class TestFeedbackSystemPrometheus:
    def test_export_metrics()
    def test_metrics_format()
    def test_metrics_labels()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_submit_feedback_endpoint():
    response = await client.post("/feedback", json={...})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_agent_stats_endpoint():
    response = await client.get("/stats/agent/Alice")
    assert response.status_code == 200
    assert "rating_medio" in response.json()
```

---

## 🚀 Deploy e Rollout

### Fase 1: Staging (Semana 1)
- Deploy em ambiente de homologação
- Testes com usuários internos
- Coleta de 50+ feedbacks
- Ajustes finos

### Fase 2: Canary (Semana 2)
- 10% do tráfego de produção
- Monitoramento intensivo
- Validação de métricas

### Fase 3: Full Rollout (Semana 3)
- 100% do tráfego
- Anúncio para usuários
- Documentação publicada

---

## 📚 Documentação

### Para Desenvolvedores
- `docs/FEEDBACK_SYSTEM_API.md` - Referência da API
- `docs/FEEDBACK_SYSTEM_SCHEMA.md` - Esquema de dados
- `docs/GRAFANA_SETUP.md` - Setup de dashboards

### Para Usuários
- `docs/COMO_DAR_FEEDBACK.md` - Guia do usuário
- Tooltips na UI
- FAQ no chat

---

## 🔮 Futuro (Pós-Sprint 4)

### Melhorias Planejadas
1. **ML para Análise de Sentimento**
   - Analisar comentários automaticamente
   - Detectar padrões em feedbacks negativos

2. **A/B Testing**
   - Testar diferentes prompts
   - Comparar performance de agentes

3. **Notificações Proativas**
   - Email quando rating cai abaixo de 3.0
   - Slack alerts para admins

4. **Relatórios Automáticos**
   - Weekly summary por email
   - Monthly business review

---

## 📊 ROI Esperado

### Ganhos Quantitativos
- **-40% tempo de troubleshooting** (feedback direto)
- **+25% taxa de melhoria contínua** (dados reais)
- **-30% custos operacionais** (identificação rápida de problemas)

### Ganhos Qualitativos
- **Maior confiança** dos usuários no sistema
- **Tomada de decisão baseada em dados**
- **Cultura de melhoria contínua**

---

## ✅ Checklist de Implementação

### Sprint 1: Backend Core
- [ ] `core/feedback_system.py` criado
- [ ] `FeedbackEntry` dataclass implementada
- [ ] `FeedbackSystem` class implementada
- [ ] Migration SQL criada
- [ ] 15+ testes passando
- [ ] Documentação básica

### Sprint 2: API Integration
- [ ] Endpoints implementados
- [ ] Integração com TICoordinatorAsync
- [ ] Testes de integração
- [ ] Postman collection

### Sprint 3: Frontend UI
- [ ] Botões 👍👎 funcionando
- [ ] Modal de comentário
- [ ] UX polida
- [ ] Testes manuais

### Sprint 4: Observability
- [ ] Prometheus configurado
- [ ] Grafana rodando
- [ ] 5 dashboards criados
- [ ] Alertas configurados
- [ ] Docker Compose completo

---

**Próximo Passo:** Implementar Sprint 1 (Backend Core)

**Comando:** `Vamos começar com core/feedback_system.py!`
