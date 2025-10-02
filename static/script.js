// === SISTEMA DE MOVIMENTO DOS OLHOS DO ROBÔ ===
function iniciarMovimentoOlhos() {
    const leftPupil = document.querySelector('.left-pupil');
    const rightPupil = document.querySelector('.right-pupil');
    const robotHead = document.querySelector('.robot-head');
    
    if (!leftPupil || !rightPupil || !robotHead) return;
    
    let isThinking = false;
    
    // Função para mover os olhos baseado na posição do mouse
    function moverOlhos(mouseX, mouseY) {
        if (isThinking) return; // Não mover se estiver "pensando"
        
        const robotRect = robotHead.getBoundingClientRect();
        const robotCenterX = robotRect.left + robotRect.width / 2;
        const robotCenterY = robotRect.top + robotRect.height / 2;
        
        // Calcular direção do mouse em relação ao centro do robô
        const deltaX = mouseX - robotCenterX;
        const deltaY = mouseY - robotCenterY;
        
        // Limitar o movimento dos olhos dentro dos limites naturais
        const maxMove = 6; // pixels
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        const limitedDistance = Math.min(distance / 50, 1); // Normalizar
        
        const moveX = (deltaX / distance) * maxMove * limitedDistance || 0;
        const moveY = (deltaY / distance) * maxMove * limitedDistance || 0;
        
        // Aplicar movimento suave
        leftPupil.style.transform = `translate(calc(-50% + ${moveX}px), calc(-50% + ${moveY}px))`;
        rightPupil.style.transform = `translate(calc(-50% + ${moveX}px), calc(-50% + ${moveY}px))`;
    }
    
    // Piscar dos olhos ocasionalmente
    function piscarOlhos() {
        const eyes = document.querySelectorAll('.eye');
        eyes.forEach(eye => {
            eye.style.transform = 'scaleY(0.1)';
            setTimeout(() => {
                eye.style.transform = 'scaleY(1)';
            }, 150);
        });
    }
    
    // Animação de "pensamento"
    function olhosPensando(ativo) {
        isThinking = ativo;
        if (ativo) {
            // Olhos olham para cima e se movem levemente
            leftPupil.style.transform = 'translate(-50%, -80%)';
            rightPupil.style.transform = 'translate(-50%, -80%)';
            
            // Adicionar movimento sutil de "processamento"
            const interval = setInterval(() => {
                if (!isThinking) {
                    clearInterval(interval);
                    return;
                }
                const randomX = (Math.random() - 0.5) * 4;
                leftPupil.style.transform = `translate(calc(-50% + ${randomX}px), -80%)`;
                rightPupil.style.transform = `translate(calc(-50% + ${-randomX}px), -80%)`;
            }, 200);
        }
    }
    
    // Event listeners
    document.addEventListener('mousemove', (e) => {
        moverOlhos(e.clientX, e.clientY);
    });
    
    // Piscar automaticamente
    setInterval(() => {
        if (Math.random() < 0.3) { // 30% de chance a cada intervalo
            piscarOlhos();
        }
    }, 3000);
    
    // Expor funções globalmente para usar com o chat
    window.robotEyes = {
        pensar: olhosPensando,
        piscar: piscarOlhos
    };
}

// Variáveis globais
let perfis = [];
let perfilSelecionado = null;
let agenteOnline = false;

// Elementos DOM
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const personaGrid = document.getElementById('personaGrid');
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const perguntaInput = document.getElementById('perguntaInput');
const submitBtn = document.getElementById('submitBtn');
const charCount = document.getElementById('charCount');
const loadingOverlay = document.getElementById('loadingOverlay');

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    iniciarMovimentoOlhos(); // Iniciar movimento dos olhos
    carregarPerfis();
    verificarStatus();
    configurarEventos();
    
    // Verifica status periodicamente
    setInterval(verificarStatus, 10000); // A cada 10 segundos
});

// Configurar eventos
function configurarEventos() {
    // Contador de caracteres
    perguntaInput.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = count;
        
        // Atualizar classes do contador
        charCount.parentElement.classList.remove('warning', 'danger');
        if (count > 150) {
            charCount.parentElement.classList.add('warning');
        }
        if (count > 180) {
            charCount.parentElement.classList.add('danger');
        }
        
        // Habilitar/desabilitar botão
        atualizarBotaoSubmit();
    });
    
    // Submit do formulário
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        enviarPergunta();
    });
    
    // Teclas de atalho
    perguntaInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            enviarPergunta();
        }
    });
}

// Carregar perfis disponíveis
async function carregarPerfis() {
    try {
        const response = await fetch('/api/perfis');
        const data = await response.json();
        
        if (data.success) {
            perfis = data.perfis;
            renderizarPerfis();
        } else {
            console.error('Erro ao carregar perfis:', data.error);
            mostrarErro('Erro ao carregar perfis');
        }
    } catch (error) {
        console.error('Erro na requisição de perfis:', error);
        mostrarErro('Erro de conexão ao carregar perfis');
    }
}

// Renderizar cards de perfis
function renderizarPerfis() {
    personaGrid.innerHTML = '';
    
    perfis.forEach(perfil => {
        const card = document.createElement('div');
        card.className = 'persona-card';
        card.dataset.perfil = perfil;
        
        // Informações dos perfis (você pode expandir isso)
        const info = getPerfilInfo(perfil);
        
        card.innerHTML = `
            <h3>${info.nome}</h3>
            <p>${info.descricao}</p>
        `;
        
        card.addEventListener('click', () => selecionarPerfil(perfil, card));
        personaGrid.appendChild(card);
    });
}

// Informações dos perfis
function getPerfilInfo(perfil) {
    const infos = {
        'Ana (Analista Jr.)': {
            nome: 'Ana - Analista Júnior',
            descricao: 'Analista júnior com acesso limitado a informações básicas'
        },
        'Carlos (Gerente de Projetos Sr.)': {
            nome: 'Carlos - Gerente Sênior',
            descricao: 'Gerente sênior com acesso amplo a projetos e documentos'
        },
        'Maria (Diretora Global)': {
            nome: 'Maria - Diretora Global',
            descricao: 'Diretora com acesso completo a todas as informações'
        }
    };
    
    return infos[perfil] || {
        nome: perfil,
        descricao: 'Perfil de usuário'
    };
}

// Selecionar perfil
function selecionarPerfil(perfil, cardElement) {
    // Remove seleção anterior
    document.querySelectorAll('.persona-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Adiciona seleção atual
    cardElement.classList.add('selected');
    perfilSelecionado = perfil;
    
    // Habilita o input se o agente estiver online
    atualizarBotaoSubmit();
    
    // Adiciona mensagem de confirmação
    adicionarMensagem('system', `Perfil selecionado: ${getPerfilInfo(perfil).nome}`);
}

// Verificar status do agente
async function verificarStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.success) {
            atualizarStatus(data.agente_pronto);
        }
    } catch (error) {
        console.error('Erro ao verificar status:', error);
        atualizarStatus(false);
    }
}

// Atualizar indicador de status
function atualizarStatus(online) {
    agenteOnline = online;
    
    statusIndicator.className = `status-indicator ${online ? 'online' : 'offline'}`;
    statusText.textContent = online ? 'Ana Online! 😊' : 'Ana inicializando...';
    
    // Fazer Ana piscar quando ficar online
    if (online && window.robotEyes) {
        setTimeout(() => {
            window.robotEyes.piscar();
        }, 500);
    }
    
    atualizarBotaoSubmit();
}

// Atualizar estado do botão submit
function atualizarBotaoSubmit() {
    const perguntaValida = perguntaInput.value.trim().length > 0 && 
                          perguntaInput.value.length <= 200;
    const podeEnviar = agenteOnline && perfilSelecionado && perguntaValida;
    
    submitBtn.disabled = !podeEnviar;
    perguntaInput.disabled = !agenteOnline || !perfilSelecionado;
    
    if (!agenteOnline) {
        perguntaInput.placeholder = 'Aguarde o agente inicializar...';
    } else if (!perfilSelecionado) {
        perguntaInput.placeholder = 'Selecione uma persona acima...';
    } else {
        perguntaInput.placeholder = 'Digite sua pergunta aqui... (máx. 200 caracteres)';
    }
}

// Enviar pergunta
async function enviarPergunta() {
    const pergunta = perguntaInput.value.trim();
    
    if (!pergunta || !perfilSelecionado || !agenteOnline) {
        return;
    }
    
    // Adiciona mensagem do usuário
    adicionarMensagem('user', pergunta);
    
    // Limpa input
    perguntaInput.value = '';
    charCount.textContent = '0';
    atualizarBotaoSubmit();
    
    // Mostra loading e ativa olhos pensando
    mostrarLoading(true);
    if (window.robotEyes) {
        window.robotEyes.pensar(true);
    }
    
    try {
        const response = await fetch('/api/pergunta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pergunta: pergunta,
                perfil: perfilSelecionado
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Piscar antes de responder
            if (window.robotEyes) {
                window.robotEyes.piscar();
                setTimeout(() => {
                    adicionarMensagem('bot', data.resposta, {
                        perfil: data.perfil_usado,
                        caracteres: data.caracteres
                    });
                }, 200);
            } else {
                adicionarMensagem('bot', data.resposta, {
                    perfil: data.perfil_usado,
                    caracteres: data.caracteres
                });
            }
        } else {
            adicionarMensagem('error', `Erro: ${data.error}`);
        }
        
    } catch (error) {
        console.error('Erro ao enviar pergunta:', error);
        adicionarMensagem('error', 'Erro de conexão. Tente novamente.');
    } finally {
        // Remove loading e para de pensar
        mostrarLoading(false);
        if (window.robotEyes) {
            window.robotEyes.pensar(false);
        }
    }
}

// Adicionar mensagem ao chat
function adicionarMensagem(tipo, conteudo, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${tipo}-message`;
    
    let header = '';
    let icon = '';
    
    switch (tipo) {
        case 'user':
            header = `Você (${getPerfilInfo(perfilSelecionado).nome})`;
            icon = '<i class="fas fa-user"></i>';
            break;
        case 'bot':
            header = 'Agente de IA';
            icon = '<i class="fas fa-robot"></i>';
            break;
        case 'system':
            header = 'Sistema';
            icon = '<i class="fas fa-info-circle"></i>';
            break;
        case 'error':
            header = 'Erro';
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            break;
    }
    
    messageDiv.innerHTML = `
        <div class="message-header">
            ${icon}
            <strong>${header}</strong>
            <span class="timestamp">${new Date().toLocaleTimeString()}</span>
        </div>
        <div class="message-content">${conteudo}</div>
    `;
    
    // Remove mensagem de boas-vindas se existir
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage && tipo !== 'system') {
        welcomeMessage.remove();
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Mostrar/ocultar loading
function mostrarLoading(show) {
    loadingOverlay.classList.toggle('show', show);
}

// Mostrar erro
function mostrarErro(mensagem) {
    // Você pode implementar um toast ou modal de erro aqui
    console.error(mensagem);
    adicionarMensagem('error', mensagem);
}