# 🌳 Árvore de Agentes - Guia Rápido de Uso

## 🚀 Início Rápido (30 segundos)

### Como Acessar

1. **Faça login** no sistema Neoson
2. No menu lateral esquerdo, procure a seção **"Ferramentas"**
3. Clique em **"🌐 Árvore de Agentes"**

✅ A visualização da árvore será carregada automaticamente!

---

## 📖 Navegação Básica

### Ver a Estrutura

Após abrir, você verá 3 níveis:

```
🧠 NEOSON
   ↓
👥 COORDENADORES
   ↓
🤖 ESPECIALISTAS
```

### Explorar Coordenadores

**Para ver os especialistas subordinados:**

1. Localize o card de um coordenador (ex: "Coordenador de TI")
2. Clique no card
3. A lista de especialistas aparecerá abaixo
4. Clique novamente para recolher

💡 **Dica**: O ícone ▼ vira ▲ quando expandido

---

## 🔍 Ver Detalhes de um Agente

**Para saber tudo sobre um agente:**

1. Clique em qualquer card (Neoson, coordenador ou especialista)
2. Um modal abrirá com:
   - 📄 Descrição completa
   - ⚙️ Informações técnicas
   - 🏷️ Palavras-chave
   - 💬 Botão para conversar

### Informações Disponíveis

| Agente | Info Mostrada |
|--------|---------------|
| **Neoson** | Total de coordenadores e especialistas |
| **Coordenador** | Número de subordinados |
| **Especialista** | Base de conhecimento, keywords |

---

## 💬 Iniciar Conversa com um Agente

**Duas formas:**

### Forma 1: Pelo Modal
1. Abra o modal do agente (clique no card)
2. Clique em **"💬 Conversar com este agente"**
3. Você volta ao chat com uma mensagem pré-preenchida

### Forma 2: Direta
1. Volte ao chat (menu → "Conversa Atual")
2. Digite sua pergunta normalmente
3. O Neoson delegará automaticamente para o especialista certo

---

## 🎯 Exemplos de Uso

### Cenário 1: "Preciso resetar minha senha"

```
1. Abrir árvore de agentes
2. Expandir "Coordenador de TI"
3. Clicar em "Marina - Suporte ao Usuário"
4. Ver que ela é especialista em: senha, login, acesso, reset
5. Clicar em "Conversar"
6. Chat abre com: "Olá! Gostaria de conversar com Marina"
7. Enviar sua pergunta
```

### Cenário 2: "Tenho um bug no código"

```
1. Abrir árvore de agentes
2. Expandir "Coordenador de TI"
3. Clicar em "Carlos - Desenvolvimento"
4. Ver keywords: desenvolvimento, bug, código, api
5. Clicar em "Conversar"
6. Descrever o bug
```

### Cenário 3: "Dúvida sobre política de home office"

```
1. Abrir árvore de agentes
2. Procurar "Ana - Recursos Humanos"
3. Ver que ela cobre: férias, benefícios, home office
4. Clicar em "Conversar"
5. Fazer sua pergunta
```

---

## ⌨️ Atalhos de Teclado

| Ação | Atalho |
|------|--------|
| Fechar modal | **ESC** |
| Voltar ao chat | Menu → "Conversa Atual" |

---

## 🎨 Entendendo as Cores

### Tipos de Agentes

**🧠 Neoson (Orquestrador)**
- Fundo com gradiente roxo-teal
- Borda roxa grossa
- Badge: "ORQUESTRADOR"

**👥 Coordenador**
- Borda lateral teal (4px)
- Badge: "COORDENADOR"
- Possui subordinados

**🤖 Especialista**
- Borda lateral cinza (4px)
- Badge: "SUBAGENTE"
- Ligado a um coordenador

---

## 🔄 Voltar ao Chat

**Três formas:**

1. **Menu lateral** → Clicar em "💬 Conversa Atual"
2. **Após conversar** → Automático ao clicar "Conversar com agente"
3. **Fechar modal** → ESC ou clicar fora

---

## 💡 Dicas e Truques

### Dica 1: Keywords são sua Bússola
As keywords mostram exatamente o que cada agente sabe fazer.

**Exemplo:**
- Marina: `senha`, `login`, `acesso` → Problemas de acesso
- Carlos: `bug`, `api`, `código` → Problemas técnicos
- Ariel: `política`, `compliance`, `LGPD` → Questões de governança

### Dica 2: Use o Modal para Explorar
Antes de conversar, clique no card para ver:
- Todas as keywords (não apenas 3)
- Descrição completa
- Base de conhecimento

### Dica 3: Coordenadores São Filtros
Se não tem certeza qual especialista usar:
- Expanda o coordenador relacionado
- Veja todos os especialistas
- Compare as keywords
- Escolha o mais adequado

### Dica 4: Neoson é Inteligente
Não precisa escolher manualmente! O Neoson:
- Analisa sua pergunta
- Identifica o especialista certo
- Delega automaticamente

**Mas a árvore ajuda você a:**
- Entender a estrutura
- Ver todas as capacidades
- Explorar por curiosidade

---

## ❓ FAQ

### P: A árvore demora para carregar?
**R:** Não. Carrega uma vez e fica em cache. Próximas visitas são instantâneas.

### P: Preciso escolher um agente manualmente?
**R:** Não! O Neoson faz isso automaticamente. A árvore é para você explorar e entender o sistema.

### P: Posso conversar com qualquer agente?
**R:** Sim! Mas lembre-se: cada agente só tem conhecimento da sua área. Perguntas fora do escopo serão redirecionadas.

### P: O que são "subordinados"?
**R:** São os especialistas que respondem a um coordenador. Exemplo:
- **Coordenador de TI** tem 5 subordinados:
  - Carlos (Dev)
  - Marina (Suporte)
  - Ariel (Governança)
  - String Agent
  - Agente Teste

### P: Por que alguns agentes têm mais keywords?
**R:** Porque cobrem mais tópicos. Exemplo:
- Marina (Suporte): 16 keywords → escopo amplo
- String Agent: 1 keyword → muito específico

### P: Posso criar meu próprio agente?
**R:** Em breve! Funcionalidade de criação via UI está no roadmap.

---

## 🆘 Problemas Comuns

### "Spinner girando infinito"

**Causa:** Token expirado ou API offline

**Solução:**
1. Faça logout
2. Faça login novamente
3. Tente abrir a árvore

---

### "Coordenador não expande"

**Causa:** Clique no lugar errado

**Solução:**
- Clique no **corpo do card**, não no ícone de toggle
- Ou clique diretamente no ícone ▼

---

### "Modal não abre"

**Causa:** JavaScript não carregado

**Solução:**
1. Recarregue a página (F5)
2. Limpe o cache (Ctrl+Shift+R)
3. Tente novamente

---

### "Cards estão sobrepostos"

**Causa:** Zoom do navegador muito alto/baixo

**Solução:**
- Resete o zoom (Ctrl+0)
- Ou ajuste o zoom para 100%

---

## 📱 Uso no Mobile

### Funciona?
**Sim!** Totalmente responsivo.

### Diferenças:
- Cards em **1 coluna** (em vez de grid)
- Padding reduzido
- Fonte um pouco menor
- Modal ocupa mais espaço

### Recomendação:
Use em **modo paisagem** (horizontal) para melhor experiência.

---

## 🎓 Para Iniciantes

**Nunca usou antes? Siga este tutorial:**

### Passo 1: Abrir
Menu → Ferramentas → Árvore de Agentes

### Passo 2: Ver Neoson
O card do topo mostra quantos coordenadores e especialistas existem.

### Passo 3: Expandir TI
Clique no "Coordenador de TI" para ver os 5 especialistas.

### Passo 4: Abrir Modal
Clique em "Carlos - Desenvolvimento" e explore as informações.

### Passo 5: Fechar Modal
Pressione ESC ou clique no X.

### Passo 6: Voltar
Menu → Conversa Atual → Você está de volta ao chat!

**Pronto!** Agora você sabe usar a árvore de agentes. 🎉

---

## 📊 Legenda Visual

### Ícones dos Especialistas

| Ícone | Especialidade |
|-------|---------------|
| 💻 | Desenvolvimento |
| 🎧 | Suporte ao Usuário |
| ⚖️ | Governança/Compliance |
| 👥 | Recursos Humanos |
| 🖥️ | TI/Infraestrutura |
| 📝 | String/Texto |
| 🧠 | Neoson (Orquestrador) |

### Badges de Tipo

| Badge | Significado |
|-------|-------------|
| 🟣 **ORQUESTRADOR** | Neoson - delega para todos |
| 🟢 **COORDENADOR** | Gerencia especialistas |
| ⚪ **SUBAGENTE** | Especialista em uma área |

---

## 🎯 Casos de Uso Recomendados

### 1. Onboarding
**Use para:** Novos usuários conhecerem o sistema

**Como:**
1. Mostre a estrutura completa
2. Explique cada coordenador
3. Demonstre um modal
4. Inicie uma conversa de exemplo

### 2. Troubleshooting
**Use para:** Encontrar o especialista certo

**Como:**
1. Identifique a área do problema
2. Expanda o coordenador relacionado
3. Compare keywords dos especialistas
4. Converse com o mais adequado

### 3. Exploração
**Use para:** Descobrir capacidades do sistema

**Como:**
1. Abra a árvore
2. Explore cada especialista
3. Leia as keywords
4. Descubra funcionalidades novas

---

## ✅ Checklist de Primeira Utilização

- [ ] Abri a árvore de agentes
- [ ] Vi o card do Neoson
- [ ] Expandi pelo menos 1 coordenador
- [ ] Abri o modal de um especialista
- [ ] Li as keywords e descrição
- [ ] Fechei o modal (ESC ou X)
- [ ] Recolhi o coordenador
- [ ] Voltei para o chat
- [ ] Entendi como funciona!

---

**Pronto para usar?** Comece agora! Menu → Ferramentas → 🌐 Árvore de Agentes

**Precisa de ajuda?** Pergunte ao Neoson: "Como usar a árvore de agentes?"

---

**Última atualização:** 20/10/2025  
**Versão:** 1.0.0  
**Nível:** Iniciante → Intermediário
