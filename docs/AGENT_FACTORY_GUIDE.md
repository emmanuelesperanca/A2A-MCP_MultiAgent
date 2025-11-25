# 🏭 Agent Factory - Documentação Completa

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Como Usar](#como-usar)
4. [Exemplos Práticos](#exemplos-práticos)
5. [API Endpoints](#api-endpoints)
6. [Frontend Integration](#frontend-integration)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

A **Agent Factory** é um sistema de pipeline que permite criar **coordenadores** e **subagentes** dinamicamente, sem precisar escrever código manualmente.

### Benefícios
- ✅ **Escalabilidade**: Crie agentes sob demanda
- ✅ **Padronização**: Templates garantem consistência
- ✅ **Automação**: Criação automática de tabelas PostgreSQL
- ✅ **Integração**: Atualização automática do frontend
- ✅ **Rastreabilidade**: Registry centralizado de todos os agentes

---

## 🏗️ Arquitetura

```
factory/
├── __init__.py                 # Exports principais
├── agent_factory.py            # Fábrica principal de agentes
├── agent_registry.py           # Sistema de registro
└── agents_registry.json        # Arquivo de registro (gerado)

Agentes Gerados:
├── agente_{identifier}_async.py        # Subagentes
└── {identifier}_coordinator_async.py   # Coordenadores
```

### Componentes

#### 1. **AgentFactory**
- Gera código Python baseado em templates
- Cria tabelas PostgreSQL automaticamente
- Registra agentes no sistema

#### 2. **AgentRegistry**
- Mantém registro de todos os agentes criados
- Persiste dados em JSON
- Exporta configuração para frontend

---

## 🚀 Como Usar

### Opção 1: Via Python (Programático)

#### Criar Subagente

```python
from factory.agent_factory import create_subagent_from_config

# Criar subagente de Service Desk
result = await create_subagent_from_config(
    name="Roberto",
    identifier="servicedesk",
    specialty="Service Desk",
    description="Especialista em atendimento e suporte técnico ao usuário",
    keywords=["suporte", "ticket", "chamado", "help desk", "atendimento"],
    enable_mcp_tools=True,
    mcp_tools_category="servicedesk",
    allowed_tools=["create_ticket", "get_ticket_status", "update_ticket"]
)

print(result)
# {
#     "success": True,
#     "identifier": "servicedesk",
#     "file_path": "/path/to/agente_servicedesk_async.py",
#     "table_name": "knowledge_servicedesk",
#     "message": "Subagente Roberto criado com sucesso!"
# }
```

#### Criar Coordenador

```python
from factory.agent_factory import create_coordinator_from_config

# Criar coordenador de Vendas
result = await create_coordinator_from_config(
    name="Coordenador de Vendas",
    identifier="vendas",
    specialty="Vendas e Comercial",
    description="Coordena agentes especializados em vendas, CRM e propostas",
    children_agents=["crm", "propostas", "clientes", "contratos"]
)

print(result)
# {
#     "success": True,
#     "identifier": "vendas",
#     "file_path": "/path/to/vendas_coordinator_async.py",
#     "children": ["crm", "propostas", "clientes", "contratos"],
#     "message": "Coordenador de Vendas criado com sucesso!"
# }
```

### Opção 2: Via API REST

#### Criar Subagente

```bash
POST http://localhost:8000/api/factory/create-subagent

Content-Type: application/json

{
    "name": "Roberto",
    "identifier": "servicedesk",
    "specialty": "Service Desk",
    "description": "Especialista em atendimento e suporte técnico",
    "keywords": ["suporte", "ticket", "chamado", "help desk"],
    "enable_mcp_tools": true,
    "mcp_tools_category": "servicedesk",
    "allowed_tools": ["create_ticket", "get_ticket_status"],
    "llm_model": "gpt-4o-mini",
    "llm_temperature": 0.3,
    "llm_max_tokens": 10000
}
```

#### Criar Coordenador

```bash
POST http://localhost:8000/api/factory/create-coordinator

Content-Type: application/json

{
    "name": "Coordenador de Vendas",
    "identifier": "vendas",
    "specialty": "Vendas e Comercial",
    "description": "Coordena agentes de vendas, CRM e propostas",
    "children_agents": ["crm", "propostas", "clientes"]
}
```

### Opção 3: Via Interface Web (Planejado)

Interface visual no `index.html` para criar agentes via formulário.

---

## 💡 Exemplos Práticos

### Exemplo 1: Criar Agente de Service Desk com Ferramentas

```python
import asyncio
from factory.agent_factory import create_subagent_from_config

async def main():
    result = await create_subagent_from_config(
        name="Roberto",
        identifier="servicedesk",
        specialty="Service Desk",
        description="Especialista em service desk e atendimento ao usuário",
        keywords=[
            "servicedesk", "ticket", "chamado", "incidente", 
            "problema", "atendimento", "suporte", "help desk"
        ],
        enable_mcp_tools=True,
        mcp_tools_category="servicedesk",
        allowed_tools=[
            "create_ticket",
            "get_ticket_status", 
            "update_ticket",
            "assign_ticket",
            "close_ticket"
        ]
    )
    
    if result['success']:
        print(f"✅ Agente criado: {result['file_path']}")
        print(f"📊 Tabela criada: {result['table_name']}")
    else:
        print(f"❌ Erro: {result['error']}")

asyncio.run(main())
```

### Exemplo 2: Criar Hierarquia Completa de Vendas

```python
import asyncio
from factory.agent_factory import create_subagent_from_config, create_coordinator_from_config

async def create_sales_hierarchy():
    # 1. Criar subagentes
    subagents = [
        {
            "name": "Cristina",
            "identifier": "crm",
            "specialty": "CRM",
            "description": "Especialista em gestão de relacionamento com clientes",
            "keywords": ["crm", "cliente", "lead", "oportunidade", "pipeline"]
        },
        {
            "name": "Paula",
            "identifier": "propostas",
            "specialty": "Propostas Comerciais",
            "description": "Especialista em criação e gestão de propostas",
            "keywords": ["proposta", "orçamento", "pricing", "cotação"]
        },
        {
            "name": "Fernando",
            "identifier": "contratos",
            "specialty": "Contratos",
            "description": "Especialista em contratos e acordos comerciais",
            "keywords": ["contrato", "acordo", "sla", "termos", "condições"]
        }
    ]
    
    # Criar cada subagente
    for sub in subagents:
        result = await create_subagent_from_config(**sub)
        print(f"{'✅' if result['success'] else '❌'} Subagente {sub['identifier']}: {result['message']}")
    
    # 2. Criar coordenador
    coordinator = await create_coordinator_from_config(
        name="Coordenador de Vendas",
        identifier="vendas",
        specialty="Vendas e Comercial",
        description="Gerencia especialistas em CRM, propostas e contratos",
        children_agents=["crm", "propostas", "contratos"]
    )
    
    print(f"\n{'✅' if coordinator['success'] else '❌'} Coordenador vendas: {coordinator['message']}")
    
    return coordinator

asyncio.run(create_sales_hierarchy())
```

### Exemplo 3: Criar Agente com Prompt Customizado

```python
from textwrap import dedent

custom_prompt = dedent("""
Você é {name}, especialista em {specialty}.

REGRAS ESPECIAIS:
1. SEMPRE responda em no máximo 3 parágrafos
2. Use bullet points para listar informações
3. Termine SEMPRE com uma pergunta de follow-up

FORMATO DA RESPOSTA:
- Parágrafo 1: Resposta direta
- Parágrafo 2: Contexto adicional
- Parágrafo 3: Próximos passos + pergunta

{{historico_conversa}}CONTEXTO:
{{contexto}}

PERGUNTA:
{{pergunta}}

RESPOSTA:
""").strip()

result = await create_subagent_from_config(
    name="Juliana",
    identifier="marketing",
    specialty="Marketing Digital",
    description="Especialista em marketing digital e redes sociais",
    keywords=["marketing", "social media", "campanha", "ads"],
    prompt_template=custom_prompt
)
```

---

## 📡 API Endpoints

### 1. **POST /api/factory/create-subagent**
Cria novo subagente

**Request:**
```json
{
    "name": "Nome do Agente",
    "identifier": "id_unico",
    "specialty": "Especialidade",
    "description": "Descrição detalhada",
    "keywords": ["palavra1", "palavra2"],
    "table_name": "knowledge_custom",  // opcional
    "prompt_template": "...",           // opcional
    "enable_mcp_tools": false,
    "mcp_tools_category": "",
    "allowed_tools": [],
    "llm_model": "gpt-4o-mini",
    "llm_temperature": 0.3,
    "llm_max_tokens": 10000
}
```

**Response:**
```json
{
    "success": true,
    "identifier": "id_unico",
    "file_path": "/path/to/agente_id_unico_async.py",
    "table_name": "knowledge_id_unico",
    "message": "Subagente criado com sucesso!",
    "error": null
}
```

### 2. **POST /api/factory/create-coordinator**
Cria novo coordenador

**Request:**
```json
{
    "name": "Nome do Coordenador",
    "identifier": "coord_id",
    "specialty": "Especialidade",
    "description": "Descrição",
    "children_agents": ["filho1", "filho2", "filho3"]
}
```

**Response:**
```json
{
    "success": true,
    "identifier": "coord_id",
    "file_path": "/path/to/coord_id_coordinator_async.py",
    "children": ["filho1", "filho2", "filho3"],
    "message": "Coordenador criado com sucesso!",
    "error": null
}
```

### 3. **GET /api/factory/agents**
Lista todos os agentes

**Query Params:**
- `agent_type`: Filtrar por tipo (`coordinator` ou `subagent`)

**Response:**
```json
{
    "total": 10,
    "subagents": 8,
    "coordinators": 2,
    "with_mcp_tools": 3,
    "agents": [
        {
            "identifier": "servicedesk",
            "name": "Roberto",
            "specialty": "Service Desk",
            "type": "subagent",
            "table_name": "knowledge_servicedesk",
            "tools_enabled": true,
            "created_at": "2025-10-16T10:30:00",
            "updated_at": "2025-10-16T10:30:00"
        }
    ]
}
```

### 4. **GET /api/factory/agents/{identifier}**
Retorna dados de um agente específico

**Response:**
```json
{
    "identifier": "servicedesk",
    "name": "Roberto",
    "specialty": "Service Desk",
    "description": "Especialista em...",
    "type": "subagent",
    "table_name": "knowledge_servicedesk",
    "file_path": "/path/to/agente_servicedesk_async.py",
    "keywords": ["suporte", "ticket"],
    "tools_enabled": true,
    "tools_category": "servicedesk",
    "created_at": "2025-10-16T10:30:00",
    "updated_at": "2025-10-16T10:30:00"
}
```

### 5. **DELETE /api/factory/agents/{identifier}**
Remove agente do registry

**Response:**
```json
{
    "success": true,
    "message": "Agente 'servicedesk' removido com sucesso",
    "identifier": "servicedesk"
}
```

### 6. **GET /api/factory/stats**
Estatísticas dos agentes

**Response:**
```json
{
    "total": 10,
    "subagents": 8,
    "coordinators": 2,
    "with_mcp_tools": 3,
    "agents": ["rh", "ti", "dev", "enduser", ...]
}
```

### 7. **GET /api/factory/frontend-config**
Exporta configuração para o frontend

**Response:**
```json
{
    "coordinators": [
        {
            "id": "ti",
            "name": "Coordenador TI",
            "specialty": "Tecnologia da Informação",
            "description": "...",
            "icon": "fas fa-server",
            "children": ["dev", "enduser", "governance"]
        }
    ],
    "subagents": [
        {
            "id": "dev",
            "name": "Carlos",
            "specialty": "Desenvolvimento",
            "description": "...",
            "icon": "fas fa-code",
            "table": "knowledge_dev",
            "keywords": ["desenvolvimento", "código"]
        }
    ]
}
```

---

## 🎨 Frontend Integration

### Atualização Automática do Frontend

Quando um agente é criado, o frontend pode ser atualizado automaticamente:

```javascript
// Buscar configuração atualizada
const response = await fetch('/api/factory/frontend-config');
const config = await response.json();

// config.subagents contém todos os subagentes
// config.coordinators contém todos os coordenadores

// Atualizar UI dinamicamente
config.subagents.forEach(agent => {
    addAgentToUI(agent);
});
```

### Exemplo de Interface para Criar Agente

```html
<form id="create-agent-form">
    <h3>Criar Novo Subagente</h3>
    
    <label>Nome do Agente:</label>
    <input type="text" name="name" placeholder="Ex: Roberto" required>
    
    <label>Identificador (ID único):</label>
    <input type="text" name="identifier" placeholder="Ex: servicedesk" required>
    
    <label>Especialidade:</label>
    <input type="text" name="specialty" placeholder="Ex: Service Desk" required>
    
    <label>Descrição:</label>
    <textarea name="description" rows="3" required></textarea>
    
    <label>Palavras-chave (separadas por vírgula):</label>
    <input type="text" name="keywords" placeholder="suporte, ticket, chamado">
    
    <label>
        <input type="checkbox" name="enable_mcp_tools">
        Habilitar Ferramentas MCP
    </label>
    
    <button type="submit">Criar Agente</button>
</form>

<script>
document.getElementById('create-agent-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const keywords = formData.get('keywords').split(',').map(k => k.trim());
    
    const payload = {
        name: formData.get('name'),
        identifier: formData.get('identifier'),
        specialty: formData.get('specialty'),
        description: formData.get('description'),
        keywords: keywords,
        enable_mcp_tools: formData.get('enable_mcp_tools') === 'on'
    };
    
    const response = await fetch('/api/factory/create-subagent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (result.success) {
        alert(`✅ ${result.message}`);
        location.reload(); // Recarregar para mostrar novo agente
    } else {
        alert(`❌ Erro: ${result.error}`);
    }
});
</script>
```

---

## 🔧 Troubleshooting

### Problema: Tabela não foi criada

**Causa**: Função PostgreSQL `create_knowledge_table` pode não existir

**Solução**:
```sql
-- Executar no PostgreSQL
CREATE OR REPLACE FUNCTION create_knowledge_table(table_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            id SERIAL PRIMARY KEY,
            conteudo TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )', table_name);
    
    EXECUTE format('
        CREATE INDEX IF NOT EXISTS %I ON %I USING ivfflat (embedding vector_cosine_ops)
    ', table_name || '_embedding_idx', table_name);
END;
$$ LANGUAGE plpgsql;
```

### Problema: Agente criado mas não aparece no sistema

**Causa**: Agente não foi registrado no `neoson_async.py`

**Solução**: Adicionar manualmente ao `inicializar_agentes()`:
```python
# Em neoson_async.py
from agente_servicedesk_async import criar_agente_servicedesk_async

# No método inicializar_agentes
servicedesk_agent = criar_agente_servicedesk_async(debug=True)
if servicedesk_agent:
    self.agentes['servicedesk'] = {
        'instancia': servicedesk_agent,
        'nome': 'Roberto',
        'especialidade': 'Service Desk'
    }
```

### Problema: Arquivo gerado tem erros de sintaxe

**Causa**: Template pode ter variáveis não substituídas

**Solução**: Verificar logs e corrigir template em `agent_factory.py`

---

## 📚 Próximos Passos

### Roadmap
- [x] ✅ Sistema base de factory
- [x] ✅ Templates de subagentes e coordenadores
- [x] ✅ Registry de agentes
- [x] ✅ API REST endpoints
- [ ] 🔄 Interface web visual
- [ ] 🔄 Atualização automática do `neoson_async.py`
- [ ] 🔄 Sistema de ferramentas MCP completo
- [ ] 🔄 Validação de dependências (verificar se agentes filhos existem)
- [ ] 🔄 Testes automatizados dos agentes criados
- [ ] 🔄 Export/Import de configurações de agentes

---

## 🤝 Contribuindo

Para adicionar novas funcionalidades à factory:

1. Modificar templates em `agent_factory.py`
2. Atualizar `AgentConfig` com novos campos
3. Adicionar novos endpoints em `app_fastapi.py`
4. Documentar mudanças neste arquivo

---

## 📞 Suporte

Para dúvidas ou problemas:
- Consulte logs em `factory/agent_factory.log`
- Verifique `factory/agents_registry.json` para ver agentes registrados
- Use `/api/factory/stats` para diagnóstico

---

**Versão**: 1.0.0  
**Última atualização**: 16/10/2025  
**Autor**: Neoson Development Team
