# Sprint 3: Frontend UI - PLANEJAMENTO

**Data Início:** 09/01/2025  
**Status:** 🔄 EM DESENVOLVIMENTO  
**Duração Estimada:** 2-3 dias  
**Prioridade:** Alta

---

## 🎯 Objetivos

1. **Adicionar botões de feedback** (👍👎) após cada resposta
2. **Criar modal de comentário** para feedback negativo
3. **Implementar animações visuais** de feedback
4. **Criar página de Dashboard** com métricas
5. **Testes E2E** (opcional)

---

## 📋 Tarefas

### Task 1: Botões de Feedback na Resposta ✅

**Arquivo:** `templates/index.html`

**HTML a adicionar:**
```html
<!-- Após cada mensagem do bot -->
<div class="feedback-buttons" data-response-id="{{ response_id }}">
    <button class="feedback-btn feedback-positive" onclick="submitFeedback(5, '{{ response_id }}')">
        <i class="fas fa-thumbs-up"></i>
        <span>Útil</span>
    </button>
    <button class="feedback-btn feedback-negative" onclick="submitFeedback(1, '{{ response_id }}')">
        <i class="fas fa-thumbs-down"></i>
        <span>Não Útil</span>
    </button>
</div>
```

**CSS:**
```css
.feedback-buttons {
    display: flex;
    gap: 10px;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #e0e0e0;
}

.feedback-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 8px 16px;
    border: 1px solid #ddd;
    border-radius: 20px;
    background: white;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 14px;
}

.feedback-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.feedback-positive:hover {
    background: #4caf50;
    color: white;
    border-color: #4caf50;
}

.feedback-negative:hover {
    background: #f44336;
    color: white;
    border-color: #f44336;
}

.feedback-btn.selected {
    pointer-events: none;
    opacity: 0.6;
}

.feedback-btn.selected.feedback-positive {
    background: #4caf50;
    color: white;
}

.feedback-btn.selected.feedback-negative {
    background: #f44336;
    color: white;
}
```

---

### Task 2: Modal de Comentário

**HTML:**
```html
<!-- Modal de Feedback -->
<div id="feedbackModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Obrigado pelo feedback!</h3>
            <button class="modal-close" onclick="closeFeedbackModal()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-body">
            <p>Quer nos contar mais sobre sua experiência? (opcional)</p>
            <textarea id="feedbackComment" 
                      placeholder="Como podemos melhorar?"
                      maxlength="2000"
                      rows="4"></textarea>
            <div class="char-counter">
                <span id="charCount">0</span>/2000 caracteres
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeFeedbackModal()">
                Pular
            </button>
            <button class="btn-primary" onclick="submitComment()">
                <i class="fas fa-paper-plane"></i>
                Enviar
            </button>
        </div>
    </div>
</div>
```

**CSS:**
```css
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    animation: fadeIn 0.3s ease;
}

.modal-content {
    position: relative;
    background: white;
    margin: 10% auto;
    padding: 0;
    width: 90%;
    max-width: 500px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    animation: slideDown 0.3s ease;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
    margin: 0;
    color: #333;
}

.modal-close {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #999;
    transition: color 0.3s;
}

.modal-close:hover {
    color: #333;
}

.modal-body {
    padding: 20px;
}

.modal-body textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-family: inherit;
    font-size: 14px;
    resize: vertical;
}

.char-counter {
    text-align: right;
    font-size: 12px;
    color: #999;
    margin-top: 5px;
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 20px;
    border-top: 1px solid #e0e0e0;
}

.btn-secondary, .btn-primary {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
}

.btn-secondary {
    background: #e0e0e0;
    color: #666;
}

.btn-secondary:hover {
    background: #d0d0d0;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideDown {
    from {
        transform: translateY(-50px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}
```

---

### Task 3: JavaScript de Interação

**Adicionar em `<script>` do index.html:**

```javascript
// Variáveis globais para feedback
let currentFeedbackId = null;
let currentRating = null;
let currentUserId = 'user_' + Date.now(); // Simples para demo

/**
 * Submete feedback do usuário
 */
async function submitFeedback(rating, responseId) {
    currentFeedbackId = responseId;
    currentRating = rating;
    
    // Desabilitar botões
    const buttons = document.querySelectorAll(
        `.feedback-buttons[data-response-id="${responseId}"] .feedback-btn`
    );
    buttons.forEach(btn => {
        btn.classList.add('selected');
        btn.disabled = true;
    });
    
    // Marcar botão clicado
    const clickedBtn = event.target.closest('.feedback-btn');
    clickedBtn.classList.add('selected');
    
    // Se positivo, enviar direto
    if (rating === 5) {
        await sendFeedbackToAPI(rating, responseId, null);
        showThankYouToast('Obrigado pelo feedback positivo! 👍');
    } else {
        // Se negativo, abrir modal
        openFeedbackModal();
    }
}

/**
 * Abre modal de feedback
 */
function openFeedbackModal() {
    const modal = document.getElementById('feedbackModal');
    modal.style.display = 'block';
    document.getElementById('feedbackComment').focus();
}

/**
 * Fecha modal de feedback
 */
function closeFeedbackModal() {
    const modal = document.getElementById('feedbackModal');
    modal.style.display = 'none';
    document.getElementById('feedbackComment').value = '';
    document.getElementById('charCount').textContent = '0';
    
    // Se já enviou o rating, não precisa fazer nada
    // Se não enviou, enviar sem comentário
    if (currentFeedbackId && currentRating === 1) {
        sendFeedbackToAPI(currentRating, currentFeedbackId, null);
    }
}

/**
 * Submete comentário do modal
 */
async function submitComment() {
    const comment = document.getElementById('feedbackComment').value.trim();
    
    await sendFeedbackToAPI(currentRating, currentFeedbackId, comment || null);
    
    closeFeedbackModal();
    showThankYouToast('Obrigado pelo seu feedback! Vamos melhorar! 💪');
}

/**
 * Envia feedback para API
 */
async function sendFeedbackToAPI(rating, feedbackId, comment) {
    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                usuario_id: currentUserId,
                feedback_id: feedbackId,
                rating: rating,
                comentario: comment
            })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao enviar feedback');
        }
        
        const data = await response.json();
        console.log('Feedback enviado:', data);
        
    } catch (error) {
        console.error('Erro ao enviar feedback:', error);
        showErrorToast('Erro ao enviar feedback. Tente novamente.');
    }
}

/**
 * Mostra toast de agradecimento
 */
function showThankYouToast(message) {
    const toast = document.createElement('div');
    toast.className = 'feedback-toast success';
    toast.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Mostra toast de erro
 */
function showErrorToast(message) {
    const toast = document.createElement('div');
    toast.className = 'feedback-toast error';
    toast.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Contador de caracteres do comentário
 */
document.addEventListener('DOMContentLoaded', () => {
    const commentArea = document.getElementById('feedbackComment');
    const charCount = document.getElementById('charCount');
    
    if (commentArea) {
        commentArea.addEventListener('input', () => {
            const count = commentArea.value.length;
            charCount.textContent = count;
            
            if (count > 1900) {
                charCount.style.color = '#f44336';
            } else {
                charCount.style.color = '#999';
            }
        });
    }
    
    // Fechar modal ao clicar fora
    window.onclick = (event) => {
        const modal = document.getElementById('feedbackModal');
        if (event.target === modal) {
            closeFeedbackModal();
        }
    };
});
```

**CSS para Toast:**
```css
.feedback-toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 14px;
    z-index: 2000;
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.3s ease;
}

.feedback-toast.show {
    opacity: 1;
    transform: translateY(0);
}

.feedback-toast.success {
    background: #4caf50;
    color: white;
}

.feedback-toast.error {
    background: #f44336;
    color: white;
}

.feedback-toast i {
    font-size: 18px;
}
```

---

### Task 4: Integração com Chat Existente

**Modificar função `enviarMensagem()` para incluir feedback_id:**

```javascript
async function enviarMensagem() {
    // ... código existente ...
    
    // ADICIONAR após receber resposta do servidor:
    const responseId = 'resp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // Adicionar botões de feedback na mensagem do bot
    const botMessage = document.querySelector('.bot-message:last-child .message-text');
    if (botMessage) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-buttons';
        feedbackDiv.setAttribute('data-response-id', responseId);
        feedbackDiv.innerHTML = `
            <button class="feedback-btn feedback-positive" onclick="submitFeedback(5, '${responseId}')">
                <i class="fas fa-thumbs-up"></i>
                <span>Útil</span>
            </button>
            <button class="feedback-btn feedback-negative" onclick="submitFeedback(1, '${responseId}')">
                <i class="fas fa-thumbs-down"></i>
                <span>Não Útil</span>
            </button>
        `;
        botMessage.appendChild(feedbackDiv);
    }
}
```

---

### Task 5: Página de Dashboard (Opcional)

**Criar novo arquivo:** `templates/dashboard.html`

**Estrutura:**
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <title>Neoson - Dashboard de Métricas</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="dashboard-container">
        <h1>📊 Dashboard de Feedback</h1>
        
        <!-- Métricas Globais -->
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Total de Respostas</h3>
                <div class="metric-value" id="totalRespostas">-</div>
            </div>
            <div class="metric-card">
                <h3>Rating Médio</h3>
                <div class="metric-value" id="ratingMedio">-</div>
            </div>
            <div class="metric-card">
                <h3>Taxa de Satisfação</h3>
                <div class="metric-value" id="taxaSatisfacao">-</div>
            </div>
            <div class="metric-card">
                <h3>Tempo Médio</h3>
                <div class="metric-value" id="tempoMedio">-</div>
            </div>
        </div>
        
        <!-- Gráficos -->
        <div class="charts-grid">
            <div class="chart-container">
                <h3>Respostas por Agente</h3>
                <canvas id="agentChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Distribuição de Ratings</h3>
                <canvas id="ratingChart"></canvas>
            </div>
        </div>
        
        <!-- Top Agentes -->
        <div class="top-agents">
            <h3>🏆 Top 5 Agentes</h3>
            <div id="topAgentsList"></div>
        </div>
    </div>
    
    <script>
        // Carregar dados do dashboard
        async function loadDashboardData() {
            const response = await fetch('/api/stats/dashboard?days=7');
            const data = await response.json();
            
            // Atualizar métricas
            document.getElementById('totalRespostas').textContent = 
                data.global_stats.total_respostas;
            document.getElementById('ratingMedio').textContent = 
                data.global_stats.rating_medio.toFixed(1) + '/5';
            document.getElementById('taxaSatisfacao').textContent = 
                (data.global_stats.taxa_positiva * 100).toFixed(0) + '%';
            document.getElementById('tempoMedio').textContent = 
                (data.global_stats.tempo_medio_ms / 1000).toFixed(1) + 's';
            
            // Criar gráfico de agentes
            createAgentChart(data.by_agent);
            createRatingChart(data.global_stats);
            displayTopAgents(data.top_agents);
        }
        
        // Carregar ao abrir página
        loadDashboardData();
        
        // Atualizar a cada 30 segundos
        setInterval(loadDashboardData, 30000);
    </script>
</body>
</html>
```

---

## 📋 Checklist de Implementação

### Sprint 3: Frontend UI
- [ ] Adicionar botões 👍👎 no template
- [ ] Criar CSS para botões e animações
- [ ] Implementar modal de comentário
- [ ] Adicionar JavaScript de interação
- [ ] Integrar com endpoint /api/feedback
- [ ] Criar sistema de toasts
- [ ] Gerar response_id único para cada resposta
- [ ] Adicionar contador de caracteres
- [ ] Testar feedback positivo
- [ ] Testar feedback negativo com comentário
- [ ] Testar feedback negativo sem comentário
- [ ] Validar erro handling (503, 500)
- [ ] (Opcional) Criar página de dashboard
- [ ] (Opcional) Implementar gráficos com Chart.js
- [ ] (Opcional) Testes E2E com Selenium

---

## 🎨 Design System

### Cores
- **Positivo:** #4caf50 (verde)
- **Negativo:** #f44336 (vermelho)
- **Neutro:** #e0e0e0 (cinza)
- **Primary:** #667eea → #764ba2 (gradiente)
- **Background:** #ffffff
- **Text:** #333333

### Tipografia
- **Font Family:** System fonts (inherit)
- **Buttons:** 14px
- **Toast:** 14px
- **Modal Title:** 18px

### Animações
- **Hover:** transform translateY(-2px), 0.3s ease
- **Toast:** fadeIn + slideUp, 0.3s ease
- **Modal:** fadeIn + slideDown, 0.3s ease

---

## 🧪 Testes Manuais

### Cenário 1: Feedback Positivo
1. Fazer uma pergunta
2. Receber resposta
3. Clicar em 👍 Útil
4. Verificar toast de sucesso
5. Verificar botões desabilitados
6. Verificar no backend (logs)

### Cenário 2: Feedback Negativo com Comentário
1. Fazer uma pergunta
2. Receber resposta
3. Clicar em 👎 Não Útil
4. Modal aparece
5. Digitar comentário
6. Clicar em "Enviar"
7. Verificar toast de sucesso

### Cenário 3: Feedback Negativo sem Comentário
1. Fazer uma pergunta
2. Receber resposta
3. Clicar em 👎 Não Útil
4. Modal aparece
5. Clicar em "Pular"
6. Verificar toast de sucesso

### Cenário 4: Sistema Indisponível
1. Parar o backend
2. Tentar dar feedback
3. Verificar toast de erro

---

**Próximo Passo:** Implementar Task 1 (Botões de Feedback)
