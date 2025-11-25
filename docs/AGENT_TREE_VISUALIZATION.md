# 🌳 Visualização em Árvore Genealógica - Sistema de Agentes

## 📋 Resumo Executivo

Sistema completo de visualização hierárquica dos agentes do Neoson implementado com:
- **Geração automática de HTMLs** para cada agente (coordenadores e subagentes)
- **Árvore genealógica dinâmica** no index.html mostrando relações pai-filho
- **Hot-reload automático** detectando novos agentes a cada 5 segundos
- **Interface interativa** com cards clicáveis linkando para páginas individuais

---

## 🎯 Objetivos Alcançados

### ✅ 1. Geração de HTMLs Retroativa

**Script:** `generate_existing_agent_htmls.py`

**Função:** Gera HTMLs para agentes já existentes no sistema:
- **Subagentes:** dev, enduser, governance, rh
- **Coordenadores:** ti_coordinator

**Como usar:**
```bash
python generate_existing_agent_htmls.py
```

**O que faz:**
1. Inicializa AgentFactory
2. Cria AgentConfig para cada agente existente
3. Chama `_generate_agent_html()` para gerar HTML
4. Salva em `templates/agents/{identifier}.html`
5. Registra/atualiza no `agents_registry.json` com `html_path`

**Resultado:**
```
✅ dev.html       → Carlos - Desenvolvimento
✅ enduser.html   → Marina - Suporte ao Usuário Final
✅ governance.html → Ariel - Governança de TI
✅ rh.html        → Ana - Recursos Humanos
✅ ti_coordinator.html → Coordenador de TI
```

---

### ✅ 2. Árvore Genealógica no Index.html

**Localização:** Seção adicionada após o header, antes dos agentes

**Estrutura HTML:**
```html
<div class="agents-tree-section">
    <div class="tree-header">
        <h2>🌳 Arquitetura Multi-Agente</h2>
        <button id="refreshTreeBtn">🔄 Atualizar</button>
    </div>
    <div class="agents-tree" id="agentsTree">
        <!-- Conteúdo carregado dinamicamente -->
    </div>
</div>
```

**Renderização Hierárquica:**

```
┌─────────────────────────────────────────┐
│     🤖 SISTEMA PRINCIPAL                │
├─────────────────────────────────────────┤
│            [NEOSON]                     │
│    (Orquestrador - Avô de Todos)       │
└─────────┬───────────────────────────────┘
          │
          ↓ (conector visual)
┌─────────────────────────────────────────┐
│     👨‍✈️ COORDENADORES                     │
├─────────────────────────────────────────┤
│  [Coordenador TI]  [Coordenador RH]    │
│     (4 subs)                            │
└─────────┬───────────────────────────────┘
          │
          ↓ (conector visual)
┌─────────────────────────────────────────┐
│     🤖 AGENTES ESPECIALIZADOS           │
├─────────────────────────────────────────┤
│  ↳ Subordinados a Coordenador TI:      │
│     [Dev] [EndUser] [Governance]       │
│                                         │
│  ↳ Agentes Independentes:              │
│     [RH]                                │
└─────────────────────────────────────────┘
```

---

### ✅ 3. Sistema de Hot-Reload

**Classe JavaScript:** `AgentsTreeManager`

**Polling Inteligente:**
```javascript
setInterval(() => {
    fetch('/api/factory/stats')
    .then(res => res.json())
    .then(stats => {
        if (stats.total !== lastAgentCount) {
            console.log('🆕 Novos agentes detectados!');
            loadAgentsTree(); // Recarrega automaticamente
        }
    });
}, 5000); // A cada 5 segundos
```

**Fluxo:**
1. ⏰ Timer dispara a cada 5 segundos
2. 📡 Faz request para `/api/factory/stats`
3. 🔍 Compara total de agentes com cache local
4. 🆕 Se houver mudança → recarrega árvore
5. ✨ Animação suave ao adicionar novos cards

---

## 🎨 Design Visual

### Card do Neoson (Avô)
- **Gradiente:** Roxo principal (`#667eea` → `#764ba2`)
- **Tamanho:** Maior que todos (350-400px)
- **Borda:** 3px sólida branca transparente
- **Efeitos:** Glow pulsante contínuo + animação de ícone
- **Badge:** Total de coordenadores + especialistas
- **Hover:** Elevação 10px + escala 1.02

### Cards de Coordenadores
- **Gradiente:** Rosa/Vermelho (`#f093fb` → `#f5576c`)
- **Badge:** Círculo vermelho com número de subordinados
- **Ícone:** 40px, fundo transparente branco
- **Hover:** Elevação 8px com sombra aumentada

### Cards de Subagentes
- **Gradiente:** Azul claro (`#4facfe` → `#00f2fe`)
- **Tags:** Keywords limitadas a 3 + contador
- **Tamanho:** Menor que coordenadores (220px vs 250px)
- **Agrupamento:** Por coordenador ou "independentes"

### Conectores Visuais
- **Linha vertical:** Gradiente roxo entre níveis
- **Altura:** 50px (responsivo para 30px em mobile)
- **Estilo:** 2px sólido com degradê

---

## 🔧 Arquivos Modificados

### 1. `templates/index.html`
**Linha ~53:** Adicionada seção `agents-tree-section`
```html
<div class="agents-tree-section">...</div>
```

### 2. `static/style_neoson.css`
**Linhas finais:** ~400 linhas de CSS para árvore
- `.agents-tree-section`
- `.tree-agent-card` (coordinator/subagent)
- `.tree-connector`
- Animações e responsividade

### 3. `static/script_neoson.js`
**Linhas finais:** ~400 linhas de JavaScript
- Classe `AgentsTreeManager`
- Métodos: `loadAgentsTree()`, `renderTree()`, `startPolling()`
- Event handlers e animações

### 4. `factory/agent_factory.py`
**Linhas 734-872:** Método `_generate_agent_html()`
- Lê template de `templates/agent_template.html`
- Substitui variáveis parametrizadas
- Gera ícone automático por especialidade
- Salva em `templates/agents/{identifier}.html`

### 5. `app_fastapi.py`
**Linha ~1365:** Endpoint `GET /agents/{identifier}`
- Serve HTMLs dos agentes via FileResponse
- Validação de existência
- Headers no-cache para hot-reload

---

## 📡 APIs Utilizadas

### 1. `GET /api/factory/frontend-config`
**Retorna:**
```json
{
    "coordinators": [
        {
            "identifier": "ti_coordinator",
            "name": "Coordenador de TI",
            "specialty": "Coordenação de TI",
            "description": "...",
            "children": ["dev", "enduser", "governance"]
        }
    ],
    "subagents": [
        {
            "identifier": "dev",
            "name": "Carlos - Desenvolvimento",
            "specialty": "Desenvolvimento de Sistemas",
            "description": "...",
            "keywords": ["desenvolvimento", "api", ...]
        }
    ]
}
```

### 2. `GET /api/factory/stats`
**Retorna:**
```json
{
    "total": 5,
    "coordinators": 1,
    "subagents": 4
}
```

### 3. `GET /agents/{identifier}`
**Retorna:** HTML completo da página do agente
**Exemplo:** `/agents/dev` → Carlos - Desenvolvimento

---

## 🚀 Como Usar

### Passo 1: Gerar HTMLs dos Agentes Existentes
```bash
# No diretório raiz do projeto
python generate_existing_agent_htmls.py
```

**Saída esperada:**
```
============================================================
🏭 GERADOR DE HTMLs PARA AGENTES EXISTENTES
============================================================

📍 Base path: C:\...\agente_ia_poc
📁 Templates path: C:\...\templates
📁 Agents HTML path: C:\...\templates\agents

============================================================
📄 Gerando HTML para: Carlos - Desenvolvimento
   Tipo: subagent
   Identificador: dev
   ✅ HTML gerado: templates\agents\dev.html
   ✅ Registro atualizado com sucesso!
...
============================================================
📊 RESUMO DA GERAÇÃO
============================================================
✅ Sucesso: 5/5
❌ Falhas: 0/5

🎉 Todos os HTMLs foram gerados com sucesso!
```

### Passo 2: Iniciar o FastAPI
```bash
python start_fastapi.py
```

### Passo 3: Acessar o Sistema
```
http://127.0.0.1:8000
```

**Você verá:**
1. 🌳 **Seção Árvore Genealógica** no topo
2. 👨‍✈️ **Coordenadores** com badge de filhos
3. 🤖 **Subagentes** agrupados por coordenador
4. 🔄 **Botão "Atualizar"** manual
5. ⏰ **Atualização automática** a cada 5s

### Passo 4: Criar Novo Agente
```bash
# Via API
POST http://127.0.0.1:8000/api/factory/create-subagent
{
    "name": "Pedro - CRM",
    "identifier": "crm",
    "specialty": "Customer Relationship Management",
    ...
}
```

**Resultado:**
- ✅ Agente criado
- ✅ HTML gerado automaticamente
- ✅ Aparece na árvore em até 5 segundos
- ✅ Acessível via `/agents/crm`

---

## 🎯 Funcionalidades Principais

### 1. **Carregamento Dinâmico**
- Busca agentes da API
- Não há hardcoding de agentes
- Totalmente data-driven

### 2. **Agrupamento Inteligente**
- Subagentes organizados por coordenador
- Seção "Independentes" para órfãos
- Contadores de subordinados

### 3. **Navegação Integrada**
- Click em qualquer card → página individual
- Links diretos: `/agents/{identifier}`
- FileResponse serve HTMLs gerados

### 4. **Hot-Reload Automático**
- Polling não-invasivo (5s)
- Detecção de mudanças silenciosa
- Console.log apenas em updates

### 5. **Visual Premium**
- Gradientes diferenciados (coordenador vs subagente)
- Animações de entrada escalonadas
- Hover effects com elevação
- Responsive design completo

---

## 📊 Mapeamento de Ícones

| Especialidade | Ícone | Tipo |
|--------------|-------|------|
| TI / Tecnologia | 💻 | Geral |
| Desenvolvimento | 👨‍💻 | Subagente |
| Infraestrutura | 🖥️ | Subagente |
| Governança | ⚖️ | Subagente |
| Suporte / End-User | 🎧 | Subagente |
| RH / Recursos Humanos | 👥 | Subagente |
| Coordenação | 👨‍✈️ | Coordenador |
| Financeiro | 💰 | Subagente |
| Vendas / CRM | 📈 | Subagente |
| Marketing | 📢 | Subagente |
| Segurança | 🔒 | Subagente |
| Dados / Analytics | 📊 | Subagente |
| Default | 🤖 | Qualquer |

---

## 🐛 Tratamento de Erros

### Cenário 1: API Indisponível
```javascript
// Exibe mensagem de erro
showError(error) {
    innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Erro ao carregar agentes</h3>
        <button>Tentar Novamente</button>
    `;
}
```

### Cenário 2: Nenhum Agente Cadastrado
```javascript
showEmpty() {
    innerHTML = `
        <i class="fas fa-robot"></i>
        <h3>Nenhum agente encontrado</h3>
        <p>Crie novos agentes usando a Agent Factory API</p>
    `;
}
```

### Cenário 3: Polling Falha
```javascript
// Silencioso - não interrompe UX
console.debug('Polling error:', error);
```

---

## 📱 Responsividade

### Desktop (> 1024px)
- Cards em grid horizontal
- 3-4 coordenadores por linha
- 4-5 subagentes por linha
- Padding generoso

### Tablet (768-1024px)
- 2-3 cards por linha
- Padding reduzido
- Fontes mantidas

### Mobile (< 768px)
- **Layout vertical completo**
- 1 card por linha
- Tree header em coluna
- Conectores menores (30px)
- Botão refresh alinhado à direita

---

## 🔮 Melhorias Futuras

### 1. WebSocket Real-Time
Substituir polling por push notifications:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agents');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'agent_created') {
        loadAgentsTree();
    }
};
```

### 2. Drag & Drop para Reorganização
Permitir reatribuir subagentes a coordenadores:
```javascript
card.addEventListener('dragstart', handleDragStart);
coordinator.addEventListener('drop', handleDrop);
```

### 3. Filtros e Busca
```html
<input type="search" placeholder="Buscar agente...">
<select>
    <option>Todos</option>
    <option>Coordenadores</option>
    <option>Subagentes</option>
</select>
```

### 4. Métricas em Tempo Real
Mostrar status de cada agente (online/offline, última consulta, etc.)

### 5. Visualização em Grafo
Usar D3.js ou Cytoscape.js para visualização avançada

---

## 📝 Checklist de Implementação

- [x] Criar método `_generate_agent_html()` na AgentFactory
- [x] Adicionar campo `html_path` no AgentRegistry
- [x] Criar endpoint `GET /agents/{identifier}`
- [x] Criar script `generate_existing_agent_htmls.py`
- [x] Adicionar seção de árvore no `index.html`
- [x] Implementar CSS completo para árvore
- [x] Criar classe JavaScript `AgentsTreeManager`
- [x] Implementar sistema de polling (hot-reload)
- [x] Testar responsividade (desktop/tablet/mobile)
- [x] Documentar sistema completo

---

## 🎉 Conclusão

O sistema de visualização em árvore genealógica está **100% funcional** e oferece:

1. ✅ **Geração automática** de HTMLs para todos os agentes
2. ✅ **Visualização hierárquica** clara e intuitiva
3. ✅ **Hot-reload automático** sem intervenção do usuário
4. ✅ **Navegação integrada** com páginas individuais
5. ✅ **Design premium** com animações e responsividade

**Zero configuração manual necessária!** 🚀

Ao criar um novo agente via Agent Factory:
- HTML é gerado automaticamente ✅
- Aparece na árvore em até 5 segundos ✅
- Pode ser acessado via link direto ✅
- Totalmente integrado ao sistema ✅

---

**Data:** 16 de Outubro de 2025  
**Versão:** Neoson v3.0 + Agent Factory + Tree Visualization  
**Status:** ✅ Implementado e Testado
