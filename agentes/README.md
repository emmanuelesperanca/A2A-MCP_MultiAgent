# 📁 Estrutura de Agentes - Organização

## 🎯 Visão Geral

A estrutura de agentes foi reorganizada em uma hierarquia clara e intuitiva para facilitar manutenção e escalabilidade.

---

## 📂 Estrutura de Diretórios

```
agentes/
├── __init__.py                    # Pacote principal de agentes
├── neoson/                        # 🤖 Agente Principal (Orquestrador)
│   ├── __init__.py
│   └── neoson_async.py           # Neoson - Orquestrador Principal
│
├── coordenadores/                 # 👥 Agentes Coordenadores
│   ├── __init__.py
│   ├── ti_coordinator_async.py   # Coordenador de TI
│   └── agente_rh_async.py        # Ana - Recursos Humanos
│
└── subagentes/                    # 🎯 Agentes Especializados
    ├── __init__.py
    ├── agente_dev_async.py       # Carlos - Desenvolvimento
    ├── agente_enduser_async.py   # Marina - Suporte ao Usuário
    ├── agente_governance_async.py # Ariel - Governança
    ├── agente_string_async.py    # String Agent
    └── agente_teste_async.py     # Agente de Teste
```

---

## 🤖 Nível 1: Orquestrador Principal

### **Neoson** (`agentes/neoson/neoson_async.py`)
- **Papel**: Agente orquestrador principal
- **Responsabilidades**:
  - Receber todas as perguntas dos usuários
  - Classificar o tipo de pergunta
  - Delegar para o coordenador ou subagente apropriado
  - Agregar respostas quando necessário
- **Fluxo**: `Usuário → Neoson → Coordenador/Subagente → Resposta`

---

## 👥 Nível 2: Coordenadores

### 1. **Coordenador de TI** (`agentes/coordenadores/ti_coordinator_async.py`)
- **Identificador**: `ti_coordinator`
- **Especialidade**: Coordenação de Tecnologia da Informação
- **Subagentes Gerenciados**:
  - `dev` - Carlos (Desenvolvimento)
  - `enduser` - Marina (Suporte ao Usuário)
  - `governance` - Ariel (Governança)
  - `string` - String Agent
  - `teste` - Agente de Teste

### 2. **Ana - Recursos Humanos** (`agentes/coordenadores/agente_rh_async.py`)
- **Identificador**: `rh`
- **Especialidade**: Recursos Humanos
- **Responsabilidades**:
  - Férias, benefícios, contratos
  - Políticas de RH
  - Processos administrativos
- **Subagentes**: Nenhum (coordenador independente)

---

## 🎯 Nível 3: Subagentes Especializados

### 1. **Carlos - Desenvolvimento** (`agentes/subagentes/agente_dev_async.py`)
- **Identificador**: `dev`
- **Especialidade**: Desenvolvimento de Sistemas
- **Keywords**: desenvolvimento, aplicação, código, projeto, bug, feature, deploy, API
- **Tabela**: `knowledge_dev`

### 2. **Marina - Suporte ao Usuário** (`agentes/subagentes/agente_enduser_async.py`)
- **Identificador**: `enduser`
- **Especialidade**: Suporte ao Usuário Final
- **Keywords**: senha, login, acesso, reset, email, outlook, word, excel, teams
- **Tabela**: `knowledge_enduser`

### 3. **Ariel - Governança** (`agentes/subagentes/agente_governance_async.py`)
- **Identificador**: `governance`
- **Especialidade**: Governança de TI
- **Keywords**: governança, compliance, política, norma, segurança, ISO, LGPD
- **Tabela**: `knowledge_governance`

### 4. **String Agent** (`agentes/subagentes/agente_string_async.py`)
- **Identificador**: `string`
- **Especialidade**: String Processing
- **Keywords**: string
- **Tabela**: `string`

### 5. **Agente de Teste** (`agentes/subagentes/agente_teste_async.py`)
- **Identificador**: `teste`
- **Especialidade**: Testes e Validação
- **Uso**: Desenvolvimento e testes

---

## 🔄 Fluxo de Delegação

```
┌─────────────────────────────────────────────────────────────┐
│                        USUÁRIO                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    NEOSON (Orquestrador)                     │
│  - Classifica pergunta                                       │
│  - Identifica especialidade necessária                       │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   TI COORDINATOR         │  │   ANA (RH)               │
│   - Avalia sub-área      │  │   - Responde diretamente │
│   - Delega para subagente│  │                          │
└──────────────────────────┘  └──────────────────────────┘
                │
    ┌───────────┼───────────┬───────────┐
    ▼           ▼           ▼           ▼
┌──────┐   ┌─────────┐  ┌──────────┐  ┌────────┐
│CARLOS│   │ MARINA  │  │  ARIEL   │  │STRING  │
│(Dev) │   │(Suporte)│  │(Govern.) │  │(Test)  │
└──────┘   └─────────┘  └──────────┘  └────────┘
```

---

## 🗂️ Registro de Agentes

Os caminhos dos agentes foram atualizados no `factory/agents_registry.json`:

```json
{
  "dev": {
    "file_path": "agentes/subagentes/agente_dev_async.py"
  },
  "enduser": {
    "file_path": "agentes/subagentes/agente_enduser_async.py"
  },
  "governance": {
    "file_path": "agentes/subagentes/agente_governance_async.py"
  },
  "string": {
    "file_path": "agentes/subagentes/agente_string_async.py"
  },
  "rh": {
    "file_path": "agentes/coordenadores/agente_rh_async.py"
  },
  "ti_coordinator": {
    "file_path": "agentes/coordenadores/ti_coordinator_async.py"
  }
}
```

---

## 📝 Convenções de Nomenclatura

### Arquivos
- **Neoson**: `neoson_async.py` (sem prefixo "agente_")
- **Coordenadores**: `{nome}_coordinator_async.py` ou `agente_{area}_async.py`
- **Subagentes**: `agente_{especialidade}_async.py`

### Identificadores
- Sempre em minúsculas
- Sem espaços (use underscore se necessário)
- Descritivos: `dev`, `enduser`, `governance`, `ti_coordinator`

### Classes
- Padrão: `{Nome}Agent`
- Exemplos: `CarlosAgent`, `MarinaAgent`, `TICoordinatorAgent`

---

## 🔧 Impacto em Outros Arquivos

### ✅ Arquivos Atualizados
1. **`factory/agents_registry.json`**: Caminhos de file_path atualizados
2. **Estrutura de pastas**: Criada hierarquia organizada

### ⚠️ Arquivos que Podem Precisar de Atualização
1. **`app_fastapi.py`**: Verificar imports de agentes (se houver)
2. **`core/agent_classifier.py`**: Verificar referências a caminhos
3. **Scripts de deploy**: Atualizar caminhos se necessário

---

## 🚀 Benefícios da Nova Estrutura

### 1. **Organização Clara**
- ✅ Hierarquia visual (Neoson → Coordenadores → Subagentes)
- ✅ Fácil identificar papel de cada agente

### 2. **Escalabilidade**
- ✅ Adicionar novos coordenadores: `agentes/coordenadores/`
- ✅ Adicionar novos subagentes: `agentes/subagentes/`
- ✅ Não polui o diretório raiz

### 3. **Manutenção**
- ✅ Cada tipo de agente em sua pasta
- ✅ Mais fácil fazer backup/restore por categoria
- ✅ Reduz conflitos em equipes

### 4. **Desenvolvimento**
- ✅ Pacotes Python organizados com `__init__.py`
- ✅ Imports mais limpos e intuitivos
- ✅ Melhor para IDEs e autocompletar

---

## 📦 Como Adicionar Novos Agentes

### Novo Subagente
1. Criar arquivo em `agentes/subagentes/agente_{nome}_async.py`
2. Adicionar entrada no `agents_registry.json`:
   ```json
   "novo_agente": {
     "identifier": "novo_agente",
     "name": "Nome do Agente",
     "type": "subagent",
     "file_path": "agentes/subagentes/agente_novo_agente_async.py",
     ...
   }
   ```
3. Opcionalmente, adicionar aos `children` de um coordenador

### Novo Coordenador
1. Criar arquivo em `agentes/coordenadores/{nome}_coordinator_async.py`
2. Adicionar entrada no `agents_registry.json`:
   ```json
   "novo_coord": {
     "identifier": "novo_coord",
     "name": "Novo Coordenador",
     "type": "coordinator",
     "file_path": "agentes/coordenadores/novo_coord_coordinator_async.py",
     "children": ["subagente1", "subagente2"]
   }
   ```

---

## 🧪 Testando a Nova Estrutura

### 1. Verificar Imports
```python
# Teste se os agentes podem ser importados
from agentes.neoson.neoson_async import NeosonAgent
from agentes.coordenadores.ti_coordinator_async import TICoordinatorAgent
from agentes.subagentes.agente_dev_async import CarlosAgent
```

### 2. Verificar Registry
```python
from factory.agent_registry import get_registry

registry = get_registry()
print("Agentes registrados:", list(registry.agents.keys()))

# Verificar caminhos
for agent_id, agent_data in registry.agents.items():
    print(f"{agent_id}: {agent_data['file_path']}")
```

### 3. Testar Delegação
- Fazer pergunta de TI → Deve ir para TI Coordinator → Subagente apropriado
- Fazer pergunta de RH → Deve ir diretamente para Ana (RH)

---

## 📊 Estatísticas

- **Total de Agentes**: 7
  - 1 Orquestrador (Neoson)
  - 2 Coordenadores (TI, RH)
  - 5 Subagentes (Dev, EndUser, Governance, String, Teste)

- **Arquivos Movidos**: 7
- **Pastas Criadas**: 4 (agentes, neoson, coordenadores, subagentes)
- **Registry Atualizado**: 6 entradas (file_path)

---

**Documentação criada em**: 16/10/2025
**Versão**: 1.0.0
**Status**: ✅ Migração Completa
