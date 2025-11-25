# 🌳 Árvore de Agentes - Implementação Completa

## 📋 Resumo

Implementação de uma visualização hierárquica interativa da estrutura de agentes do sistema Neoson, com cards expansíveis, modais de detalhes e integração com a API de agentes.

---

## 🎯 Funcionalidades Implementadas

### ✅ 1. Visualização Hierárquica

**Estrutura em 3 Níveis:**
```
🧠 Neoson (Orquestrador)
    │
    ├── 👥 Coordenadores
    │   ├── Coordenador de TI
    │   │   ├── 💻 Carlos - Desenvolvimento
    │   │   ├── 🎧 Marina - Suporte ao Usuário
    │   │   ├── ⚖️ Ariel - Governança
    │   │   └── 📝 String Agent
    │   │
    │   └── 👥 Ana - Recursos Humanos
    │
    └── 🤖 Subagentes Independentes
```

**Características:**
- **Neoson** no topo (orquestrador principal)
- **Coordenadores** no segundo nível
- **Subagentes** subordinados a cada coordenador
- Conectores visuais entre níveis

---

### ✅ 2. Cards Interativos

#### Card do Neoson
```html
┌─────────────────────────────────────┐
│ 🧠  Neoson                          │
│     Orquestrador Multi-Agente       │
│     [Orquestrador]                  │
├─────────────────────────────────────┤
│ Sistema inteligente que analisa     │
│ perguntas e delega automaticamente  │
│ para o especialista mais adequado.  │
├─────────────────────────────────────┤
│ 👥 2 coordenadores                  │
│ 🤖 5 especialistas                  │
└─────────────────────────────────────┘
```

#### Card de Coordenador
```html
┌─────────────────────────────────────┐
│ 🖥️  Coordenador de TI        [v]   │
│     Coordenação de TI               │
│     [Coordenador]                   │
├─────────────────────────────────────┤
│ 🌐 5 subordinados                   │
│ 🏷️  4 keywords                      │
└─────────────────────────────────────┘
    │
    ├── [Carlos - Dev]
    ├── [Marina - Suporte]
    ├── [Ariel - Governança]
    └── [String Agent]
```

#### Card de Subagente
```html
┌────────────────────────────────┐
│ 💻  Carlos - Desenvolvimento   │
│     Desenvolvimento de Sistemas│
│     [Subagente]                │
├────────────────────────────────┤
│ Especialista em código, APIs,  │
│ e desenvolvimento de sistemas. │
├────────────────────────────────┤
│ [desenvolvimento] [api] [bug]  │
│ +9 keywords                    │
└────────────────────────────────┘
```

**Hover Effects:**
- ✅ Elevação do card (-4px translateY)
- ✅ Borda colorida animada (topo do card)
- ✅ Sombra mais pronunciada
- ✅ Cursor pointer

---

### ✅ 3. Expansão/Recolhimento

**Mecanismo de Toggle:**
```javascript
function toggleCoordinator(coordinatorId) {
    const wrapper = document.getElementById(`coord-${coordinatorId}`);
    wrapper.classList.toggle('expanded');
}
```

**Estados:**
- **Recolhido** (default): `max-height: 0`
- **Expandido**: `max-height: 5000px`
- **Transição**: `0.4s ease`

**Ícone Toggle:**
- Recolhido: ▼ (chevron-down)
- Expandido: ▲ (chevron rotacionado 180°)

**Layout dos Subagentes:**
- Grid responsivo: `repeat(auto-fill, minmax(320px, 1fr))`
- Gap entre cards: `var(--spacing-lg)`
- Borda lateral esquerda: `2px solid var(--border-subtle)`
- Padding esquerdo: `var(--spacing-xl)`

---

### ✅ 4. Modal de Detalhes

**Estrutura do Modal:**
```
┌─────────────────────────────────────┐
│ [X]  🧠 Neoson                      │
│      Orquestrador Multi-Agente      │
│      [Orquestrador]                 │
├─────────────────────────────────────┤
│ 📄 Descrição                        │
│ Sistema inteligente que analisa...  │
│                                     │
│ ⚙️ Informações Técnicas             │
│ ┌──────────┐ ┌──────────┐          │
│ │Identificad│ │Tipo      │          │
│ │neoson     │ │orquestrad│          │
│ └──────────┘ └──────────┘          │
│                                     │
│ 🏷️ Palavras-chave                   │
│ [orquestração] [delegação]          │
│ [análise] [roteamento]              │
├─────────────────────────────────────┤
│ [💬 Conversar] [✖️ Fechar]          │
└─────────────────────────────────────┘
```

**Campos Exibidos:**

**Para Todos:**
- Nome
- Especialidade
- Tipo (badge colorido)
- Descrição
- Identificador
- Keywords

**Para Subagentes:**
- Base de dados (table_name)

**Para Coordenadores:**
- Número de subordinados (children)

**Para Neoson:**
- Total de coordenadores
- Total de especialistas

**Ações do Modal:**
1. **Conversar**: Fecha modal, volta ao chat, preenche input com sugestão
2. **Fechar**: Fecha modal (também via `ESC` ou clique fora)

---

## 🎨 Design System

### Cores por Tipo

```css
/* Orquestrador (Neoson) */
background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(79, 209, 197, 0.1));
border: 2px solid var(--primary-color);
badge: rgba(124, 58, 237, 0.2)

/* Coordenador */
border-left: 4px solid var(--accent-color);
badge: rgba(79, 209, 197, 0.2)

/* Subagente */
border-left: 4px solid var(--text-tertiary);
badge: rgba(156, 163, 175, 0.2)
```

### Ícones por Especialidade

| Especialidade | Ícone | Trigger Keywords |
|---------------|-------|------------------|
| Desenvolvimento | 💻 | desenvolvimento, dev |
| Suporte | 🎧 | suporte, usuario |
| Governança | ⚖️ | governança, governance |
| Recursos Humanos | 👥 | recursos humanos, rh |
| TI | 🖥️ | ti, tecnologia |
| Coordenação | 🎯 | coordenação |
| String | 📝 | string |
| Default | 🤖 | (qualquer outro) |

### Animações

```css
/* Entrada do Modal */
@keyframes modalSlideIn {
    from {
        opacity: 0;
        transform: scale(0.9) translateY(20px);
    }
    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}
duration: 0.3s ease-out

/* Spinner de Loading */
@keyframes spin {
    to { transform: rotate(360deg); }
}
duration: 1s linear infinite

/* Hover do Card */
transition: all var(--transition-normal)
transform: translateY(-4px)
box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15)
```

---

## 🔌 Integração com API

### Endpoint Consumido

```http
GET /api/factory/agents
Authorization: Bearer <token>
```

**Response Schema:**
```json
{
  "total": 7,
  "subagents": 5,
  "coordinators": 2,
  "with_mcp_tools": 0,
  "agents": [
    {
      "identifier": "dev",
      "name": "Carlos - Desenvolvimento",
      "specialty": "Desenvolvimento de Sistemas",
      "type": "subagent",
      "description": "...",
      "table_name": "knowledge_dev",
      "keywords": ["desenvolvimento", "api", "bug", ...],
      "children": []
    },
    {
      "identifier": "ti_coordinator",
      "name": "Coordenador de TI",
      "specialty": "Coordenação de TI",
      "type": "coordinator",
      "keywords": ["ti", "tecnologia", ...],
      "children": ["dev", "enduser", "governance", "string", "teste"]
    }
  ]
}
```

---

## 📱 Responsividade

### Breakpoints

```css
/* Mobile (< 768px) */
- Grid: 1 coluna (320px mínimo)
- Padding reduzido
- Font-size menor
- Ícones menores

/* Tablet (768px - 1024px) */
- Grid: 2 colunas
- Padding médio
- Font-size padrão

/* Desktop (> 1024px) */
- Grid: auto-fill (320px mínimo)
- Max-width: 1400px
- Padding completo
```

---

## 🔧 Funções JavaScript

### Principais

#### 1. `showTab(tabName)`
```javascript
// Alternar entre visualizações
showTab('agents') // Mostra árvore
showTab('chat')   // Volta ao chat
showTab('logs')   // Alert (não implementado)
```

#### 2. `loadAgentsTree()`
```javascript
// Carrega dados da API e renderiza
- Fetch de /api/factory/agents
- Salva em agentsData global
- Chama renderAgentsTree()
- Tratamento de erro com empty state
```

#### 3. `renderAgentsTree(data)`
```javascript
// Renderiza estrutura completa
- Separa coordinators e subagents
- Renderiza Neoson (nível 1)
- Renderiza coordenadores (nível 2)
- Renderiza subagentes em grids
- Adiciona event listeners
```

#### 4. `toggleCoordinator(coordinatorId)`
```javascript
// Expande/recolhe coordenador
- Toggle classe 'expanded'
- Animação de max-height
- Rotação do ícone chevron
```

#### 5. `showAgentDetails(agent)`
```javascript
// Exibe modal com informações
- Popula campos do modal
- Mostra/oculta seções dinamicamente
- Renderiza keywords
- Adiciona classe 'active' ao modal
```

#### 6. `closeAgentModal()`
```javascript
// Fecha modal
- Remove classe 'active'
- Limpa currentAgentData
```

#### 7. `startChatWithAgent()`
```javascript
// Inicia conversa com agente
- Volta para tab 'chat'
- Fecha modal
- Preenche input com sugestão
- Foca no textarea
```

---

## 🎛️ Estados da Aplicação

### Variáveis Globais

```javascript
agentsData = null           // Dados dos agentes carregados
window.agentsTreeLoaded     // Flag de carregamento
currentAgentData = null     // Agente selecionado no modal
```

### Estados Visuais

**Chat:**
```javascript
chatArea.display = 'flex'
inputContainer.display = 'block'
agentsTreeView.active = false
```

**Árvore de Agentes:**
```javascript
chatArea.display = 'none'
inputContainer.display = 'none'
agentsTreeView.active = true
```

**Modal Aberto:**
```javascript
agentModal.active = true
currentAgentData = { agent object }
```

---

## 🧪 Como Testar

### 1. Navegação Básica

```
1. Login no sistema
2. Clicar em "Árvore de Agentes" no menu lateral
3. Verificar carregamento da estrutura
```

**Esperado:**
- ✅ Chat oculta
- ✅ Input oculta
- ✅ Árvore visível
- ✅ Spinner → Cards renderizados

---

### 2. Expansão de Coordenadores

```
1. Na árvore, clicar no card de um coordenador
2. Verificar animação de expansão
3. Clicar novamente para recolher
```

**Esperado:**
- ✅ Container de subagentes expande suavemente
- ✅ Ícone chevron rotaciona 180°
- ✅ Subagentes aparecem em grid
- ✅ Borda lateral esquerda visível

---

### 3. Modal de Detalhes

```
1. Clicar em qualquer card (Neoson, coordenador ou subagente)
2. Verificar abertura do modal
3. Verificar informações corretas
4. Testar fechamento (X, ESC, clique fora)
```

**Esperado:**
- ✅ Modal abre com animação (scale + fadeIn)
- ✅ Informações corretas do agente
- ✅ Keywords renderizadas
- ✅ Seções dinâmicas (table_name, children) aparecem apenas quando aplicável
- ✅ Modal fecha com todos os métodos

---

### 4. Iniciar Conversa

```
1. Abrir modal de um agente
2. Clicar em "Conversar com este agente"
3. Verificar retorno ao chat
```

**Esperado:**
- ✅ Modal fecha
- ✅ Volta para visualização de chat
- ✅ Input preenchido com texto sugerido
- ✅ Foco no textarea
- ✅ Botão de enviar habilitado

---

### 5. Voltar ao Chat

```
1. Na árvore, clicar em "Conversa Atual" no menu
2. Verificar retorno
```

**Esperado:**
- ✅ Árvore oculta
- ✅ Chat visível
- ✅ Input visível
- ✅ Estado anterior do chat preservado

---

## 🐛 Troubleshooting

### Problema: Árvore não carrega

**Sintomas:**
- Spinner infinito
- Ou mensagem de erro

**Causas possíveis:**
1. Token inválido/expirado
2. Endpoint /api/factory/agents offline
3. CORS bloqueando request

**Solução:**
```javascript
// Console do navegador (F12)
console.log('Token:', currentToken);

// Testar endpoint manualmente
fetch('/api/factory/agents', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
})
.then(r => r.json())
.then(console.log);
```

---

### Problema: Coordenador não expande

**Sintomas:**
- Clicar no toggle não faz nada

**Causas possíveis:**
1. ID do coordenador incorreto
2. JavaScript não carregado
3. Evento bloqueado

**Solução:**
```javascript
// Verificar ID
const wrapper = document.getElementById('coord-ti_coordinator');
console.log('Wrapper existe?', !!wrapper);

// Forçar toggle
wrapper.classList.toggle('expanded');
```

---

### Problema: Modal não abre

**Sintomas:**
- Clicar no card não abre modal

**Causas possíveis:**
1. Função showAgentDetails não definida
2. Escape de JSON falhou
3. Modal sem classe 'active'

**Solução:**
```javascript
// Testar manualmente
showAgentDetails({
    identifier: 'dev',
    name: 'Carlos',
    specialty: 'Dev',
    type: 'subagent'
});

// Verificar modal
const modal = document.getElementById('agentModal');
console.log('Modal existe?', !!modal);
```

---

### Problema: Estilo quebrado

**Sintomas:**
- Cards sem estilo
- Layout desorganizado

**Causas possíveis:**
1. CSS não carregado
2. Variáveis CSS não definidas
3. Classes erradas

**Solução:**
```javascript
// Verificar variáveis CSS
const styles = getComputedStyle(document.documentElement);
console.log('--primary-color:', styles.getPropertyValue('--primary-color'));

// Verificar classes aplicadas
document.querySelectorAll('.agent-tree-card').forEach(card => {
    console.log('Classes:', card.className);
});
```

---

## 📊 Estatísticas

### Código Adicionado

| Tipo | Linhas | Arquivo |
|------|--------|---------|
| CSS | ~550 | index.html |
| HTML | ~80 | index.html |
| JavaScript | ~450 | index.html |
| **Total** | **~1080** | **1 arquivo** |

### Funcionalidades

| Feature | Status |
|---------|--------|
| Visualização hierárquica | ✅ |
| Cards interativos | ✅ |
| Expansão/recolhimento | ✅ |
| Modal de detalhes | ✅ |
| Integração com API | ✅ |
| Responsividade | ✅ |
| Animações | ✅ |
| Estados de loading/erro | ✅ |
| Navegação entre tabs | ✅ |
| Ícones dinâmicos | ✅ |

---

## 🚀 Próximos Passos

### Fase 1: Melhorias Visuais
- [ ] Adicionar animações de entrada nos cards (stagger effect)
- [ ] Melhorar conectores visuais entre níveis
- [ ] Adicionar indicador de "online/offline" nos agentes
- [ ] Theme dark/light toggle

### Fase 2: Funcionalidades
- [ ] Busca/filtro de agentes
- [ ] Ordenação (alfabética, por tipo, por uso)
- [ ] Estatísticas de uso por agente
- [ ] Histórico de conversas por agente
- [ ] Drag & drop para reorganizar hierarquia

### Fase 3: Performance
- [ ] Lazy loading de subagentes
- [ ] Virtualização para muitos agentes
- [ ] Cache de dados carregados
- [ ] Debounce em toggles rápidos

### Fase 4: Avançado
- [ ] Edição inline de agentes
- [ ] Criação de novos agentes via UI
- [ ] Visualização em grafo (D3.js ou similar)
- [ ] Export da estrutura (JSON, PNG, PDF)

---

## 📚 Referências

**Design inspirado em:**
- Claude AI interface (cards e modal)
- GitHub file tree (expansão/recolhimento)
- VS Code extension marketplace (grid de cards)

**Tecnologias utilizadas:**
- Font Awesome 6.x (ícones)
- CSS Grid & Flexbox (layout)
- CSS Custom Properties (variáveis)
- Vanilla JavaScript (sem dependências)
- Fetch API (requisições)

**Arquivos relacionados:**
- `/api/factory/agents` (backend)
- `factory/agent_registry.py` (registry de agentes)
- `factory/agents_registry.json` (dados dos agentes)
- `templates/agents/*.html` (templates individuais)

---

**Documentação criada em**: 20/10/2025  
**Versão**: 1.0.0  
**Status**: ✅ Implementação Completa  
**Autor**: GitHub Copilot Assistant
