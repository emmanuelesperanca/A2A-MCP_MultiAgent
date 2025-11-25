# Troubleshooting - Sistema de Abas

## ✅ PROBLEMA RESOLVIDO: Abas não trocavam

### Sintoma
- Apenas a aba Chat e o botão Logout funcionavam
- Clicar em "Agentes", "Criar Agente" ou "Ingerir Dados" não mostrava o conteúdo

### Causa Raiz
O HTML tinha `style="display: none;"` inline nas divs `.tab-content`, que tem **prioridade maior** que classes CSS normais. Quando o JavaScript adicionava a classe `.active`, o CSS `.tab-content.active { display: block; }` era **ignorado** devido ao style inline.

### Solução Implementada
Adicionado `!important` no CSS para sobrescrever os styles inline:

```css
.tab-content {
    display: none !important;  /* Força esconder */
    animation: fadeIn 0.3s ease;
}

.tab-content.active {
    display: block !important;  /* Força mostrar */
}
```

### Melhorias Adicionais
1. **Logs de Debug**: Adicionados console.log para rastrear cliques nas abas
2. **Auto-carregamento**: Aba "Agentes" agora carrega a árvore automaticamente ao ser clicada
3. **Validação**: JavaScript verifica se targetTab existe antes de adicionar classe

---

## 🧪 Como Testar

### 1. Login
- Acesse: http://localhost:8000/login
- Login admin: `admin` / `admin123`
- Deve redirecionar para `/` automaticamente

### 2. Verificar Abas Visíveis
**Admin deve ver**:
- ✅ Chat (aba ativa por padrão)
- ✅ Agentes
- ✅ Criar Agente
- ✅ Ingerir Dados
- ✅ Nome "Olá, admin" no topo direito
- ✅ Botão de logout

### 3. Testar Navegação
**Clicar em cada aba e verificar**:

#### Aba Chat
```
✅ Mostra interface de conversação
✅ Mostra mensagem de boas-vindas do Neoson
✅ Textarea para digitar mensagem
✅ Botão "Enviar"
```

#### Aba Agentes
```
✅ Mostra título "Arquitetura Multi-Agente"
✅ Mostra botão "Atualizar"
✅ Carrega árvore genealógica dos agentes
✅ Console mostra: "📑 Clique na aba: agents"
✅ Console mostra: "✅ Aba ativada: agents"
```

#### Aba Criar Agente (Admin Only)
```
✅ Mostra seletor: Subagente vs Coordenador
✅ Formulário de subagente visível por padrão
✅ Dropdown "Coordenador Pai" populado com coordenadores existentes
✅ Botões "Limpar" e "Criar Agente" visíveis
✅ Console mostra: "📑 Clique na aba: create-agent"
```

#### Aba Ingerir Dados (Admin Only)
```
✅ Mostra área de upload com ícone de nuvem
✅ Dropdown "Agente/Tabela Destino" populado
✅ Botão "Selecionar Arquivos"
✅ Área de drag & drop funcional
✅ Console mostra: "📑 Clique na aba: ingest-data"
```

---

## 🔍 Debug no Console

### Console Logs Esperados

**Ao carregar a página**:
```
✅ Usuário autenticado: admin - admin
🎯 Configurando abas: 4 botões, 4 conteúdos
🎯 Inicializando TabsManager...
✅ TabsManager inicializado
```

**Ao clicar em uma aba**:
```
📑 Clique na aba: agents
✅ Aba ativada: agents
```

**Se algo falhar**:
```
❌ Erro ao carregar coordenadores: [detalhes do erro]
```

---

## ⚠️ Problemas Comuns

### Problema: "Aba não muda ao clicar"
**Possíveis causas**:
1. JavaScript não carregou → Verificar console (F12) por erros
2. Token expirado → Fazer logout e login novamente
3. Cache do browser → Ctrl + Shift + R (hard refresh)

**Solução**:
```javascript
// No console do browser:
console.log('Botões:', document.querySelectorAll('.tab-btn').length);
console.log('Conteúdos:', document.querySelectorAll('.tab-content').length);
console.log('TabsManager:', window.tabsManager);
```

### Problema: "Abas admin não aparecem"
**Causa**: Login como usuário comum (não admin)

**Verificação**:
```javascript
// No console:
JSON.parse(localStorage.getItem('neoson_user'))
// Deve mostrar: { username: "admin", user_type: "admin" }
```

**Solução**: Fazer logout e login com credenciais de admin

### Problema: "CSS não atualiza"
**Causa**: Cache do browser

**Solução**:
1. Ctrl + Shift + R (hard refresh)
2. Limpar cache do browser
3. Testar em modo anônimo
4. Verificar se arquivo style_neoson.css está sendo carregado

---

## 🛠️ Ferramentas de Debug

### 1. Verificar Estado das Abas
```javascript
// No console do browser:
document.querySelectorAll('.tab-content').forEach(tab => {
    console.log(tab.id, 'active:', tab.classList.contains('active'));
});
```

### 2. Forçar Ativação de Aba
```javascript
// Ativar aba manualmente:
document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
document.getElementById('create-agent').classList.add('active');
```

### 3. Verificar Autenticação
```javascript
console.log('Token:', localStorage.getItem('neoson_token'));
console.log('User:', localStorage.getItem('neoson_user'));
```

### 4. Testar Clique Programático
```javascript
// Simular clique na aba Agentes:
document.querySelector('[data-tab="agents"]').click();
```

---

## 📝 Checklist de Validação

Após implementar a correção, validar:

- [ ] Login com admin → 4 abas visíveis
- [ ] Login com user → 2 abas visíveis (Chat, Agentes)
- [ ] Clicar em "Chat" → mostra interface de chat
- [ ] Clicar em "Agentes" → mostra árvore
- [ ] Clicar em "Criar Agente" → mostra formulários
- [ ] Clicar em "Ingerir Dados" → mostra upload
- [ ] Console mostra logs de clique
- [ ] Nenhum erro no console (F12)
- [ ] CSS !important funcionando
- [ ] Animação fadeIn funciona ao trocar abas
- [ ] Logout limpa localStorage e redireciona

---

## 📚 Referências

- **Arquivo CSS**: `static/style_neoson.css` (linhas 3084-3091)
- **Arquivo JS**: `static/script_neoson.js` (linhas 2475-2510)
- **Arquivo HTML**: `templates/index.html` (linhas 54-80)

---

**Documentação criada em**: 16/10/2025
**Problema**: Abas não trocavam devido a style inline vs CSS
**Status**: ✅ RESOLVIDO
**Solução**: CSS com !important + logs de debug
