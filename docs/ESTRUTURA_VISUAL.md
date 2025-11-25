# 🗂️ Estrutura Visual do Projeto - Neoson v3.0

```
agente_ia_poc/
│
├── 📱 APLICAÇÃO PRINCIPAL
│   ├── app_fastapi.py                    # Backend FastAPI + Auth JWT
│   ├── start_fastapi.py                  # Script de inicialização
│   ├── postgres_vector_store.py          # Gerenciamento de vetores
│   ├── requirements.txt                  # Dependências Python
│   └── requirements_fastapi.txt          # Dependências FastAPI
│
├── 🤖 AGENTES (NOVA ESTRUTURA)
│   ├── agentes/
│   │   ├── __init__.py
│   │   ├── README.md                     # Documentação completa
│   │   │
│   │   ├── neoson/                       # 🎯 ORQUESTRADOR PRINCIPAL
│   │   │   ├── __init__.py
│   │   │   └── neoson_async.py           # Neoson - Coordenador Geral
│   │   │
│   │   ├── coordenadores/                # 👥 COORDENADORES
│   │   │   ├── __init__.py
│   │   │   ├── ti_coordinator_async.py   # Coord. TI (4 subagentes)
│   │   │   └── agente_rh_async.py        # Ana - RH
│   │   │
│   │   └── subagentes/                   # 🎯 ESPECIALISTAS
│   │       ├── __init__.py
│   │       ├── agente_dev_async.py       # Carlos - Dev
│   │       ├── agente_enduser_async.py   # Marina - Suporte
│   │       ├── agente_governance_async.py # Ariel - Governança
│   │       ├── agente_string_async.py    # String Agent
│   │       └── agente_teste_async.py     # Agente de Teste
│
├── 🏭 FACTORY (CRIAÇÃO DE AGENTES)
│   ├── factory/
│   │   ├── __init__.py
│   │   ├── agent_factory.py              # Gerador de agentes
│   │   ├── agent_registry.py             # Gerenciador de registro
│   │   └── agents_registry.json          # ✅ Paths atualizados
│
├── ⚙️ CORE (LÓGICA DE NEGÓCIO)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent_classifier.py           # Classificação de perguntas
│   │   ├── config.py                     # Configurações globais
│   │   ├── conversation_memory.py        # Memória de conversas
│   │   ├── enrichment_system.py          # Enriquecimento de respostas
│   │   ├── feedback_system.py            # Sistema de feedback
│   │   ├── glossario_corporativo.py      # Glossário de termos
│   │   └── security_instructions.py      # Instruções de segurança
│
├── 💾 DAL (DATA ACCESS LAYER)
│   ├── dal/
│   │   ├── __init__.py
│   │   ├── base_dal.py                   # Classe base
│   │   ├── manager.py                    # Gerenciador de conexões
│   │   ├── postgres_dal.py               # DAL síncrono
│   │   └── postgres_dal_async.py         # DAL assíncrono
│
├── 🌐 FRONTEND
│   ├── templates/
│   │   ├── login.html                    # ✅ Página de login (JWT)
│   │   ├── index.html                    # ✅ App principal (4 abas)
│   │   ├── dashboard.html                # Dashboard analytics
│   │   └── agents/                       # HTMLs dos agentes
│   │       ├── dev.html
│   │       ├── enduser.html
│   │       ├── governance.html
│   │       └── ...
│   │
│   └── static/
│       ├── style_neoson.css              # ✅ CSS completo (3600+ linhas)
│       └── script_neoson.js              # ✅ JS com TabsManager
│
├── 📊 DADOS E INGESTÃO
│   ├── ingest_data/
│   │   ├── ingest_data.py                # Script de ingestão
│   │   ├── ingest_data.spec             # Spec para build
│   │   └── requirements.txt              # Deps da ingestão
│   │
│   └── migrations/
│       ├── create_feedback_tables.sql    # Tabelas de feedback
│       ├── create_knowledge_governance.sql
│       └── create_knowledge_infra.sql
│
├── 🔧 FERRAMENTAS
│   ├── tools/                            # Ferramentas dos agentes
│   ├── tests/                            # Testes automatizados
│   └── hooks/                            # PyInstaller hooks
│
├── 📚 DOCUMENTAÇÃO
│   └── docs/
│       ├── INDEX.md                      # Índice geral
│       ├── SISTEMA_AUTH_TABS_COMPLETO.md # ✅ Auth + Tabs (hoje)
│       ├── TROUBLESHOOTING_TABS.md       # ✅ Debug tabs (hoje)
│       ├── REORGANIZACAO_AGENTES.md      # ✅ Reorganização (hoje)
│       ├── AGENT_FACTORY_GUIDE.md        # Guia da Factory
│       ├── AGENT_TREE_VISUALIZATION.md   # Árvore genealógica
│       ├── FLUXO_PENSAMENTO_NEOSON.md    # Como Neoson pensa
│       ├── ROADMAP.md                    # Plano de desenvolvimento
│       └── ...                           # 25+ docs
│
├── 🗑️ OBSOLETO
│   └── obsoleto/
│       ├── agente_dev.py                 # Versões antigas (não async)
│       ├── agente_enduser.py
│       ├── agente_governance.py
│       ├── agente_rh.py
│       ├── ti_coordinator.py
│       ├── app.py                        # App antigo (Streamlit)
│       └── ...
│
└── 🔐 CONFIGURAÇÃO
    ├── .env                              # Variáveis de ambiente
    ├── .gitignore                        # Git ignore
    └── CHANGELOG.md                      # Log de mudanças
```

---

## 📈 Estatísticas do Projeto

### Código
- **Python Files**: ~50 arquivos
- **HTML Templates**: 10+ templates
- **CSS**: 3600+ linhas (style_neoson.css)
- **JavaScript**: 2850+ linhas (script_neoson.js)

### Agentes
- **Total**: 7 agentes ativos
  - 1 Orquestrador (Neoson)
  - 2 Coordenadores (TI, RH)
  - 4 Subagentes (Dev, EndUser, Governance, String)

### Documentação
- **Total de Docs**: 25+ arquivos .md
- **Linhas Totais**: ~5000+ linhas de documentação

### Features
- ✅ Autenticação JWT
- ✅ Sistema de tabs
- ✅ Agent Factory
- ✅ RAG com PostgreSQL + pgvector
- ✅ Dashboard Analytics
- ✅ Sistema de Feedback
- ✅ Enriquecimento de Respostas
- ✅ Árvore Genealógica Visual

---

## 🎯 Hierarquia de Agentes

```
                        USUÁRIO
                           │
                           ▼
                    ┌──────────────┐
                    │   NEOSON     │ ← Orquestrador Principal
                    │ (neoson/)    │
                    └──────┬───────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
    ┌───────────────┐           ┌────────────────┐
    │ TI COORDINATOR│           │   ANA (RH)     │
    │(coordenadores)│           │ (coordenadores)│
    └───────┬───────┘           └────────────────┘
            │
    ┌───────┼───────┬───────┬────────┐
    ▼       ▼       ▼       ▼        ▼
┌────────┬────────┬──────────┬────────┬────────┐
│ CARLOS │ MARINA │  ARIEL   │ STRING │ TESTE  │
│  (Dev) │(Support│(Governance│        │        │
│        │)       │)         │        │        │
└────────┴────────┴──────────┴────────┴────────┘
         (todos em subagentes/)
```

---

## 🚀 Fluxo de Execução

### 1. **Inicialização**
```
start_fastapi.py
    ↓
app_fastapi.py (inicia servidor)
    ↓
Carrega agents_registry.json
    ↓
Importa agentes de agentes/*
    ↓
Sistema pronto! 🚀
```

### 2. **Login de Usuário**
```
/login (templates/login.html)
    ↓
POST /api/auth/login
    ↓
Gera JWT token (8h validade)
    ↓
Salva no localStorage
    ↓
Redireciona para /
```

### 3. **Navegação por Abas**
```
index.html carrega
    ↓
script_neoson.js → TabsManager.init()
    ↓
Verifica localStorage (token + user)
    ↓
Se admin: mostra 4 abas
Se user: mostra 2 abas
    ↓
Usuário navega entre abas
```

### 4. **Conversa com Neoson**
```
Usuário digita pergunta
    ↓
POST /chat (app_fastapi.py)
    ↓
NeosonAgent.process_request()
    ↓
Classifica pergunta (core/agent_classifier.py)
    ↓
Delega para coordenador/subagente
    ↓
Busca em knowledge base (RAG)
    ↓
Enriquece resposta (core/enrichment_system.py)
    ↓
Retorna para usuário
```

### 5. **Criar Novo Agente (Admin)**
```
Aba "Criar Agente"
    ↓
Preenche formulário
    ↓
POST /api/factory/create-subagent
    ↓
agent_factory.py gera código
    ↓
Salva em agentes/subagentes/
    ↓
Atualiza agents_registry.json
    ↓
Árvore atualizada automaticamente
```

---

## 🔑 Arquivos Críticos

### 1. **app_fastapi.py** (1400+ linhas)
- Backend principal
- Endpoints de chat, auth, factory
- Inicialização de agentes
- Middlewares e CORS

### 2. **agents_registry.json**
- Registro de todos os agentes
- Paths, keywords, tabelas
- Hierarquia (children)

### 3. **style_neoson.css** (3600+ linhas)
- Todo o design do sistema
- Tabs, forms, upload, chat
- Animações e responsividade

### 4. **script_neoson.js** (2850+ linhas)
- Lógica de frontend
- TabsManager, AuthManager
- AgentsTreeManager
- Form handlers

### 5. **neoson_async.py**
- Agente orquestrador principal
- Classificação e delegação
- Orquestração de respostas

---

## 📦 Dependências Principais

- **FastAPI**: Backend async
- **PostgreSQL + pgvector**: RAG database
- **LangChain**: LLM orchestration
- **OpenAI API**: GPT-4o-mini
- **PyJWT**: Autenticação JWT
- **asyncpg**: Async PostgreSQL
- **Pydantic**: Validação de dados

---

**Estrutura atualizada em**: 16/10/2025  
**Versão**: 3.0  
**Status**: ✅ Organizado e Documentado
