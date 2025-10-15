// ===== NEOSON SISTEMA MULTI-AGENTE - JAVASCRIPT =====

class NeosonInterface {
    constructor() {
        this.selectedPersona = null;
        this.isProcessing = false;
        this.currentDelegation = null;
        this.eyeTrackingEnabled = true;
        this.currentStep = 0;
        this.progressInterval = null;
        
        // Elementos para o indicador sutil de processamento
        this.processingIndicator = null;
        this.processingText = null;
        this.sendBtn = null;
        this.processingSteps = [
            '🔍 Avaliando agentes disponíveis para resposta...',
            '📊 Pesquisando na base de dados o melhor conteúdo...',
            '🎯 Avaliando se a resposta está dentro das diretrizes...',
            '🧠 Processando informações encontradas...',
            '✅ Finalizando resposta personalizada...'
        ];
        
        // Sistema de Feedback
        this.feedbackContext = {}; // Armazena contexto das mensagens para feedback
        this.currentUserId = 'user_' + Date.now(); // ID único do usuário
        this.currentFeedbackId = null;
        this.currentRating = null;
        this.lastUserQuestion = null; // Armazena última pergunta do usuário
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeEyeTracking();
        this.updateCharCounter();
        this.setupAgentMonitoring();
        this.startSubAgentMonitoring();
        
        // Inicializar elementos do indicador de processamento
        this.processingIndicator = document.getElementById('processingIndicator');
        this.processingText = document.getElementById('processingText');
        this.sendBtn = document.getElementById('sendBtn');
        
        console.log('🤖 Neoson System Interface Initialized');
        console.log('👥 Sub-agentes TI monitoramento iniciado');
    }

    // ===== EVENT LISTENERS =====
    setupEventListeners() {
        // Form submission
        const chatForm = document.getElementById('chatForm');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        }

        // Character counter
        const messageInput = document.getElementById('mensagem');
        if (messageInput) {
            messageInput.addEventListener('input', () => this.updateCharCounter());
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    this.handleChatSubmit(e);
                }
            });
        }

        // Clear memory button
        const clearBtn = document.getElementById('clearMemoryBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearMemory());
        }

        // Persona selection
        document.querySelectorAll('.persona-card').forEach(card => {
            card.addEventListener('click', (e) => this.selectPersona(e));
        });

        // Toggle buttons for persona creator
        const presetToggle = document.getElementById('presetToggle');
        const customToggle = document.getElementById('customToggle');
        if (presetToggle && customToggle) {
            presetToggle.addEventListener('click', () => this.showPresetPersonas());
            customToggle.addEventListener('click', () => this.showCustomCreator());
        }

        // Custom persona creator
        const createBtn = document.getElementById('createPersonaBtn');
        const clearFormBtn = document.getElementById('clearFormBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.createCustomPersona());
        }
        if (clearFormBtn) {
            clearFormBtn.addEventListener('click', () => this.clearPersonaForm());
        }

        // Form inputs for live preview
        const formInputs = document.querySelectorAll('#customName, #customRole, #customDepartment, #customLevel, #customGeography');
        formInputs.forEach(input => {
            input.addEventListener('input', () => this.updatePersonaPreview());
        });

        // Checkbox for "All Projects"
        const allProjectsCheck = document.getElementById('allProjects');
        if (allProjectsCheck) {
            allProjectsCheck.addEventListener('change', (e) => this.handleAllProjectsCheck(e));
        }

        // Mouse tracking for eyes
        if (this.eyeTrackingEnabled) {
            document.addEventListener('mousemove', (e) => this.updateEyeTracking(e));
        }
    }

    // ===== EYE TRACKING SYSTEM =====
    initializeEyeTracking() {
        const pupils = document.querySelectorAll('.pupil');
        if (pupils.length === 0) return;

        this.pupils = pupils;
        this.eyeCenter = this.calculateEyeCenter();
    }

    calculateEyeCenter() {
        const neosonFace = document.querySelector('.neoson-face');
        if (!neosonFace) return { x: 0, y: 0 };

        const rect = neosonFace.getBoundingClientRect();
        return {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2 - 20
        };
    }

    updateEyeTracking(event) {
        if (!this.pupils || this.isProcessing) return;

        const mouseX = event.clientX;
        const mouseY = event.clientY;
        
        this.pupils.forEach(pupil => {
            const eye = pupil.parentElement;
            const eyeRect = eye.getBoundingClientRect();
            const eyeCenterX = eyeRect.left + eyeRect.width / 2;
            const eyeCenterY = eyeRect.top + eyeRect.height / 2;

            const angle = Math.atan2(mouseY - eyeCenterY, mouseX - eyeCenterX);
            const distance = Math.min(6, Math.sqrt(
                Math.pow(mouseX - eyeCenterX, 2) + 
                Math.pow(mouseY - eyeCenterY, 2)
            ) / 10);

            const pupilX = Math.cos(angle) * distance;
            const pupilY = Math.sin(angle) * distance;

            pupil.style.transform = `translate(calc(-50% + ${pupilX}px), calc(-50% + ${pupilY}px))`;
        });
    }

    centerEyes() {
        if (!this.pupils) return;
        
        this.pupils.forEach(pupil => {
            pupil.style.transform = 'translate(-50%, -50%)';
        });
    }

    // ===== NEOSON ANIMATIONS =====
    startThinking() {
        const indicator = document.querySelector('.thinking-indicator');
        if (indicator) {
            indicator.classList.add('active');
        }
        this.centerEyes();
    }

    stopThinking() {
        const indicator = document.querySelector('.thinking-indicator');
        if (indicator) {
            indicator.classList.remove('active');
        }
    }

    showNeosonExpression(type) {
        const neosonFace = document.querySelector('.neoson-face');
        if (!neosonFace) return;

        // Remove previous expressions
        neosonFace.classList.remove('happy', 'thinking', 'processing', 'surprised');
        
        // Add new expression
        neosonFace.classList.add(type);
        
        // Auto-remove after animation
        setTimeout(() => {
            neosonFace.classList.remove(type);
        }, 2000);
    }

    // ===== AGENT DELEGATION SYSTEM =====
    async showDelegationProcess(agentKey) {
        this.isProcessing = true;
        this.currentDelegation = agentKey;

        const agentInfo = this.getAgentInfo(agentKey);
        
        // Mostrar indicador sutil de processamento
        this.showSubtleProcessing();

        this.activateAgentCard(agentKey);
        this.showAgentResponseIndicator(agentInfo);

        // Se é um agente TI hierárquico, mostrar delegação específica
        if (agentKey === 'Coordenador TI') {
            await this.showHierarchicalDelegation();
        }

        await this.delay(600);
    }

    showSubtleProcessing() {
        console.log('🔄 Iniciando indicador de processamento sutil...');
        
        // Re-obter elementos se necessário (caso não foram inicializados)
        if (!this.processingIndicator) {
            this.processingIndicator = document.getElementById('processingIndicator');
        }
        if (!this.processingText) {
            this.processingText = document.getElementById('processingText');
        }
        if (!this.sendBtn) {
            this.sendBtn = document.getElementById('sendBtn');
        }
        
        if (!this.processingIndicator || !this.processingText || !this.sendBtn) {
            console.error('❌ Elementos do indicador não encontrados');
            return;
        }
        
        // Marcar como processando
        this.isProcessing = true;
        
        // Desabilitar botão e mostrar indicador
        this.sendBtn.disabled = true;
        this.processingIndicator.classList.add('active');
        
        console.log('✅ Botão desabilitado e indicador ativado');
        
        // Reset e configuração inicial
        this.currentStep = 0;
        
        // Iniciar rotação das mensagens de processamento
        this.startSubtleProgress();
    }
    
    startSubtleProgress() {
        if (!this.processingText) return;
        
        // Mostrar primeira mensagem
        this.processingText.textContent = this.processingSteps[this.currentStep];
        
        // Configurar intervalo para trocar mensagens
        this.progressInterval = setInterval(() => {
            this.currentStep = (this.currentStep + 1) % this.processingSteps.length;
            if (this.processingText) {
                this.processingText.textContent = this.processingSteps[this.currentStep];
            }
        }, 2000); // Trocar a cada 2 segundos
    }

    startProgressSequence() {
        const messages = [
            "Avaliando agentes disponíveis para resposta",
            "Pesquisando na base de dados o conteúdo para a melhor resposta", 
            "Avaliando se a resposta se encontra dentro das diretrizes da empresa",
            "Finalizando resposta"
        ];

        const icons = ["fas fa-users", "fas fa-database", "fas fa-shield-alt", "fas fa-check-circle"];
        
        const updateMessage = (step) => {
            const titleEl = document.querySelector('.progress-title');
            const subtitleEl = document.querySelector('.progress-subtitle');
            const iconEl = document.querySelector('.progress-icon');
            const progressEl = document.querySelector('.progress-ring__progress');
            
            if (titleEl && subtitleEl && iconEl && progressEl) {
                titleEl.textContent = "Neoson está pensando";
                subtitleEl.innerHTML = `${messages[step]}<span class="progress-dots"></span>`;
                iconEl.className = `progress-icon ${icons[step]}`;
                
                // Atualizar progresso (25% por step)
                const progress = ((step + 1) / messages.length) * 283;
                const offset = 283 - progress;
                progressEl.style.strokeDashoffset = offset;
            }
        };

        // Iniciar sequência
        updateMessage(0);
        
        // Atualizar a cada 1.5 segundos
        this.progressInterval = setInterval(() => {
            this.currentStep++;
            if (this.currentStep < messages.length) {
                updateMessage(this.currentStep);
            } else {
                clearInterval(this.progressInterval);
            }
        }, 1500);
    }

    async showHierarchicalDelegation() {
        // Simular análise hierárquica
        this.showHierarchyMessage('🔍 Analisando pergunta...');
        await this.delay(800);
        
        this.showHierarchyMessage('🎯 Selecionando sub-especialista...');
        await this.delay(600);
        
        // Buscar informações da hierarquia TI
        try {
            const response = await fetch('/api/ti-hierarchy');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.showHierarchyMessage('✅ Delegação hierárquica ativa');
                }
            }
        } catch (error) {
            console.log('Info da hierarquia não disponível:', error);
        }
    }

    showHierarchyMessage(message) {
        const messagesContainer = document.querySelector('.chat-messages');
        if (!messagesContainer) return;

        const indicator = document.createElement('div');
        indicator.className = 'hierarchy-indicator';
        indicator.innerHTML = `
            <div class="hierarchy-icon">🎯</div>
            <span>${message}</span>
        `;

        messagesContainer.appendChild(indicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Auto-remove after delay
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.classList.add('fade-out');
                setTimeout(() => indicator.remove(), 300);
            }
        }, 1500);
    }

    showAgentResponseIndicator(agentInfo) {
        const messagesContainer = document.querySelector('.chat-messages');
        if (!messagesContainer) return;

        const indicator = document.createElement('div');
        indicator.className = `agent-indicator agent-${agentInfo.class}-indicator`;
        indicator.innerHTML = `
            <i class="fas fa-microchip"></i>
            <span>${agentInfo.name} está preparando a resposta...</span>
        `;

        messagesContainer.appendChild(indicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        setTimeout(() => {
            indicator.classList.add('fade-out');
        }, 2200);

        setTimeout(() => {
            indicator.remove();
        }, 2800);
    }

    async animateProcessingSteps() {
        const steps = [
            'step-analyzing',
            'step-classifying', 
            'step-delegating'
        ];

        for (let i = 0; i < steps.length; i++) {
            const step = document.getElementById(steps[i]);
            if (!step) continue;

            // Activate current step
            step.classList.add('active');
            
            // Wait for animation
            await this.delay(1500);
            
            // Complete current step
            step.classList.remove('active');
            step.classList.add('completed');
            
            // Small delay between steps
            await this.delay(300);
        }
    }

    showAgentHandoff(agentKey) {
        const handoff = document.querySelector('.agent-handoff');
        const targetAgent = document.querySelector('.target-agent');
        
        if (!handoff || !targetAgent) return;

        // Update target agent info
        const agentInfo = this.getAgentInfo(agentKey);
        const avatar = targetAgent.querySelector('.agent-avatar');
        const name = targetAgent.querySelector('h4');
        
        if (avatar) {
            avatar.className = `agent-avatar ${agentInfo.class}`;
            avatar.textContent = agentInfo.icon;
        }
        
        if (name) {
            name.textContent = agentInfo.name;
        }

        // Show handoff animation
        handoff.classList.add('show');
        
        // Activate target agent card
        this.activateAgentCard(agentKey);
    }

    hideDelegationProcess() {
        console.log('🔄 Ocultando indicador de processamento...');
        
        // Marcar como não processando
        this.isProcessing = false;
        
        // Ocultar indicador sutil e habilitar botão
        if (this.processingIndicator) {
            this.processingIndicator.classList.remove('active');
        }
        
        if (this.sendBtn) {
            this.sendBtn.disabled = false;
        }

        // Limpar intervalos de progresso
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        console.log('✅ Indicador ocultado e botão habilitado');

        // Hide handoff (manter funcionalidade existente)
        const handoff = document.querySelector('.agent-handoff');
        if (handoff) {
            handoff.classList.remove('show');
        }

        this.isProcessing = false;
        this.currentStep = 0;
        this.updateSystemStatus('ready', 'Sistema Pronto');
    }

    activateAgentCard(agentKey) {
        // Remove active from all cards
        document.querySelectorAll('.agent-card').forEach(card => {
            card.classList.remove('active');
        });

        // Add active to current agent
        const targetCard = document.querySelector(`[data-agent="${agentKey}"]`);
        if (targetCard) {
            targetCard.classList.add('active');
            
            // Remove after delay
            setTimeout(() => {
                targetCard.classList.remove('active');
            }, 3000);
        }
    }

    getAgentInfo(agentKey) {
        const agents = {
            // Agentes principais
            'ana': { name: 'Ana (RH)', icon: '👩‍💼', class: 'ana' },
            'Coordenador TI': { name: 'Sistema TI Hierárquico', icon: '🎯', class: 'ti-system' },
            'alex': { name: 'Alex (TI)', icon: '👨‍💻', class: 'alex' },
            'neoson': { name: 'Neoson', icon: '🤖', class: 'neoson' },
            
            // Sub-agentes TI
            'Ariel': { name: 'Ariel (Governança)', icon: '🏛️', class: 'governance' },
            'Alice': { name: 'Alice (Infraestrutura)', icon: '🖥️', class: 'infrastructure' },
            'Carlos': { name: 'Carlos (Desenvolvimento)', icon: '⚡', class: 'development' },
            'Marina': { name: 'Marina (Usuário Final)', icon: '🎧', class: 'enduser' },
            
            // Aliases para compatibilidade
            'governance': { name: 'Ariel (Governança)', icon: '🏛️', class: 'governance' },
            'infrastructure': { name: 'Alice (Infraestrutura)', icon: '🖥️', class: 'infrastructure' },
            'development': { name: 'Carlos (Desenvolvimento)', icon: '⚡', class: 'development' },
            'enduser': { name: 'Marina (Usuário Final)', icon: '🎧', class: 'enduser' }
        };
        return agents[agentKey] || agents['neoson'];
    }

    // ===== SYSTEM STATUS =====
    updateSystemStatus(status, message) {
        const statusElement = document.querySelector('.status-indicator');
        if (!statusElement) return;

        // Remove all status classes
        statusElement.classList.remove('ready', 'loading', 'error');
        
        // Add current status
        statusElement.classList.add(status);
        
        // Update text
        const statusText = statusElement.querySelector('span');
        if (statusText) {
            statusText.textContent = message;
        }
    }

    setupAgentMonitoring() {
        // Monitor main agent cards and update status
        document.querySelectorAll('.agent-card').forEach(card => {
            const statusIcon = card.querySelector('.agent-status');
            if (statusIcon) {
                // Default to ready
                statusIcon.innerHTML = '<i class="fas fa-check-circle" style="color: #27ae60;"></i>';
            }
        });

        // Monitor sub-agent cards
        document.querySelectorAll('.sub-agent-card').forEach(card => {
            const statusIcon = card.querySelector('.sub-agent-status');
            if (statusIcon) {
                // Default to ready
                statusIcon.innerHTML = '<i class="fas fa-check-circle" style="color: #27ae60;"></i>';
            }
        });

        // Setup click handlers for sub-agents
        document.querySelectorAll('.sub-agent-card').forEach(card => {
            card.addEventListener('click', (e) => this.selectSubAgent(e));
        });
    }

    selectSubAgent(event) {
        const card = event.currentTarget;
        const subAgent = card.dataset.subagent;
        
        // Remove active class from all sub-agents
        document.querySelectorAll('.sub-agent-card').forEach(c => c.classList.remove('active'));
        
        // Add active class to selected sub-agent
        card.classList.add('active');
        
        console.log(`🎯 Sub-agente selecionado: ${subAgent}`);
        
        // Show info about the selected sub-agent
        this.showSubAgentInfo(subAgent);
    }

    showSubAgentInfo(subAgent) {
        const subAgentNames = {
            'governance': 'Ariel (Governança TI)',
            'infrastructure': 'Alice (Infraestrutura)', 
            'development': 'Carlos (Desenvolvimento)',
            'enduser': 'Marina (Usuário Final)'
        };

        const subAgentExpertise = {
            'governance': 'Especialista em LGPD, Compliance e Delivery Methods',
            'infrastructure': 'Especialista em Servidores, Redes e Monitoramento',
            'development': 'Especialista em APIs, Deploy e Arquitetura',
            'enduser': 'Especialista em Senhas, Acessos e Suporte'
        };

        const name = subAgentNames[subAgent] || 'Sub-agente';
        const expertise = subAgentExpertise[subAgent] || 'Especialista TI';

        // Show temporary notification
        this.showNotification(`📋 ${name}`, `${expertise}`, 3000);
    }

    // ===== CHAT SYSTEM =====
    async handleChatSubmit(event) {
        event.preventDefault();
        
        if (this.isProcessing) return;

        const messageInput = document.getElementById('mensagem');
        const message = messageInput.value.trim();

        if (!message) return;

        // Armazenar última pergunta do usuário para o feedback
        this.lastUserQuestion = message;

        // IMEDIATAMENTE mostrar indicador de processamento
        this.showSubtleProcessing();

        // Clear input and show user message
        messageInput.value = '';
        this.updateCharCounter();
        this.addMessage(message, 'user');

        // Start processing
        this.startThinking();
        this.showNeosonExpression('thinking');

        try {
            // Send to backend
            const requestBody = {
                mensagem: message,
                persona_selecionada: this.selectedPersona
            };

            // If using custom persona, include the full persona data
            if (this.selectedPersona === 'custom' && this.customPersona) {
                requestBody.custom_persona = this.customPersona;
            }

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            console.log('📡 Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ HTTP error response:', errorText);
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }

            console.log('✅ Response received, parsing JSON...');
            
            // Try to parse JSON with error handling
            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                const responseText = await response.text();
                console.error('❌ JSON parsing failed. Raw response:', responseText);
                throw new Error(`Invalid JSON response: ${jsonError.message}`);
            }
            
            console.log('📊 Parsed data:', data);
            console.log('🤖 Agent used:', data.agent_usado);
            console.log('📝 Response length:', data.resposta ? data.resposta.length : 'undefined');

            // Check if response is valid
            if (!data.resposta) {
                throw new Error('Response data is missing or invalid');
            }

            // Show delegation if agent was used
            if (data.agent_usado && data.agent_usado !== 'neoson') {
                await this.showDelegationProcess(data.agent_usado);
            }

            // Show response
            this.addMessage(data.resposta, 'bot', data.agent_usado || 'neoson', data.cadeia_raciocinio, data.enriched || null);
            this.showNeosonExpression('happy');

        } catch (error) {
            console.error('❌ Chat error details:', error);
            console.error('Error stack:', error.stack);
            
            let errorMessage = 'Desculpe, ocorreu um erro ao processar sua mensagem.';
            
            // Try to get more specific error info
            if (error.message) {
                errorMessage += ` (${error.message})`;
            }
            
            this.addMessage(errorMessage, 'bot', 'error');
            this.updateSystemStatus('error', 'Erro de Comunicação');
            this.showNeosonExpression('surprised');
        } finally {
            this.stopThinking();
            this.hideDelegationProcess();
        }
    }

    addMessage(content, sender, agent = null, cadeiaRaciocinio = null, enrichedData = null) {
        const messagesContainer = document.querySelector('.chat-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        if (sender === 'bot' && agent) {
            // Sanitizar nome do agente para uso como classe CSS
            const sanitizedAgent = agent.toLowerCase().replace(/\s+/g, '-');
            messageDiv.classList.add(`agent-${sanitizedAgent}`);
        }

        const agentInfo = agent ? this.getAgentInfo(agent) : null;
        const shouldShowBadge = sender === 'bot' && agentInfo && agent !== 'error';
        const agentBadge = shouldShowBadge
            ? `<span class="agent-badge">${agentInfo.name}</span>`
            : '';
        const avatar = sender === 'user' ? '👤' : (agentInfo ? agentInfo.icon : '🤖');
        const senderName = sender === 'user' ? 'Você' : (agentInfo ? agentInfo.name : 'Sistema');

        // Gerar ID único para esta mensagem
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        // Botão de cadeia de raciocínio (apenas para respostas do bot com cadeia)
        const cadeiaButton = (sender === 'bot' && cadeiaRaciocinio) 
            ? `<button class="chain-button" onclick="neosonInterface.toggleChain('${messageId}')">
                 <i class="fas fa-brain"></i> Ver Cadeia de Raciocínio
               </button>` 
            : '';

        // Cadeia de raciocínio colapsada
        const cadeiaSection = (sender === 'bot' && cadeiaRaciocinio)
            ? `<div class="reasoning-chain collapsed" id="chain_${messageId}">
                 <div class="chain-content">
                   <h4><i class="fas fa-brain"></i> Cadeia de Decisão e Raciocínio</h4>
                   <div class="chain-text">${this.formatChainContent(cadeiaRaciocinio)}</div>
                 </div>
               </div>`
            : '';

        // NOVO: Seções enriquecidas (documentos, FAQs, contatos, sugestões, glossário)
        const enrichedSections = (sender === 'bot' && enrichedData) 
            ? this.renderEnrichedSections(enrichedData, messageId)
            : '';

        // Botões de feedback (apenas para respostas do bot que não são erro)
        const feedbackButtons = (sender === 'bot' && agent !== 'error')
            ? `<div class="feedback-buttons" data-response-id="${messageId}">
                 <button class="feedback-btn feedback-positive" onclick="neosonInterface.submitFeedback(5, '${messageId}', event)">
                   <i class="fas fa-thumbs-up"></i>
                   <span>Útil</span>
                 </button>
                 <button class="feedback-btn feedback-negative" onclick="neosonInterface.submitFeedback(1, '${messageId}', event)">
                   <i class="fas fa-thumbs-down"></i>
                   <span>Não Útil</span>
                 </button>
               </div>`
            : '';

        messageDiv.innerHTML = `
            <div class="message-avatar ${agent ? agentInfo.class : ''}">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <strong>${senderName}</strong>
                    ${agentBadge}
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="message-text markdown-content" id="${messageId}_text">${this.formatMessage(content)}</div>
                <div class="message-actions">
                    <button class="copy-button" onclick="neosonInterface.copyMessage('${messageId}_text')">
                        <i class="fas fa-copy"></i> Copiar
                    </button>
                    ${cadeiaButton}
                </div>
                ${cadeiaSection}
                ${enrichedSections}
                ${feedbackButtons}
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Aplicar formatação markdown
        this.renderMarkdown(messageId + '_text');
        
        // Armazenar contexto da mensagem para feedback
        if (sender === 'bot' && agent !== 'error') {
            this.storeMessageContext(messageId, content, agent);
        }
    }

    renderEnrichedSections(enrichedData, messageId) {
        if (!enrichedData) return '';
        
        let html = '<div class="enriched-sections">';
        
        // 1. Documentos Relacionados
        if (enrichedData.documentos_relacionados && enrichedData.documentos_relacionados.length > 0) {
            html += `
                <div class="enriched-section">
                    <button class="enriched-header" onclick="neosonInterface.toggleEnrichedSection('docs_${messageId}')">
                        <i class="fas fa-file-alt"></i>
                        <span>Documentos Relacionados (${enrichedData.documentos_relacionados.length})</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </button>
                    <div class="enriched-content collapsed" id="docs_${messageId}">
                        ${enrichedData.documentos_relacionados.map(doc => `
                            <div class="doc-card">
                                <div class="doc-title">${doc.titulo}</div>
                                <div class="doc-preview">${doc.preview}</div>
                                <div class="doc-relevance">
                                    <span class="relevance-badge">${doc.relevancia}% relevante</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // 2. FAQs Similares
        if (enrichedData.faqs_similares && enrichedData.faqs_similares.length > 0) {
            html += `
                <div class="enriched-section">
                    <button class="enriched-header" onclick="neosonInterface.toggleEnrichedSection('faqs_${messageId}')">
                        <i class="fas fa-question-circle"></i>
                        <span>Perguntas Similares (${enrichedData.faqs_similares.length})</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </button>
                    <div class="enriched-content collapsed" id="faqs_${messageId}">
                        ${enrichedData.faqs_similares.map(faq => `
                            <div class="faq-card">
                                <div class="faq-question"><strong>P:</strong> ${faq.pergunta}</div>
                                <div class="faq-answer"><strong>R:</strong> ${faq.resposta}</div>
                                <div class="faq-meta">
                                    <span class="rating-badge">⭐ ${faq.rating}</span>
                                    <span class="similarity-badge">${faq.similaridade}% similar</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // 3. Contatos de Especialistas
        if (enrichedData.especialistas_contato && enrichedData.especialistas_contato.length > 0) {
            html += `
                <div class="enriched-section">
                    <button class="enriched-header" onclick="neosonInterface.toggleEnrichedSection('contacts_${messageId}')">
                        <i class="fas fa-user-friends"></i>
                        <span>Especialistas para Contato (${enrichedData.especialistas_contato.length})</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </button>
                    <div class="enriched-content collapsed" id="contacts_${messageId}">
                        ${enrichedData.especialistas_contato.map(contact => `
                            <div class="contact-card">
                                <div class="contact-name">${contact.nome}</div>
                                <div class="contact-info">
                                    <span><i class="fas fa-envelope"></i> ${contact.email}</span>
                                    <span><i class="fas fa-phone"></i> ${contact.telefone}</span>
                                </div>
                                <div class="contact-specialties">
                                    ${contact.especialidades.map(esp => `<span class="specialty-tag">${esp}</span>`).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // 4. Sugestões de Próximas Perguntas
        if (enrichedData.proximas_sugestoes && enrichedData.proximas_sugestoes.length > 0) {
            html += `
                <div class="enriched-section">
                    <button class="enriched-header" onclick="neosonInterface.toggleEnrichedSection('suggestions_${messageId}')">
                        <i class="fas fa-lightbulb"></i>
                        <span>Você também pode perguntar (${enrichedData.proximas_sugestoes.length})</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </button>
                    <div class="enriched-content collapsed" id="suggestions_${messageId}">
                        <div class="suggestions-list">
                            ${enrichedData.proximas_sugestoes.map(suggestion => `
                                <button class="suggestion-button" onclick="neosonInterface.askSuggestion('${suggestion.replace(/'/g, "\\'")}')">
                                    <i class="fas fa-arrow-right"></i>
                                    ${suggestion}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        // 5. Glossário de Termos
        if (enrichedData.glossario && Object.keys(enrichedData.glossario).length > 0) {
            html += `
                <div class="enriched-section">
                    <button class="enriched-header" onclick="neosonInterface.toggleEnrichedSection('glossary_${messageId}')">
                        <i class="fas fa-book"></i>
                        <span>Glossário de Termos (${Object.keys(enrichedData.glossario).length})</span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </button>
                    <div class="enriched-content collapsed" id="glossary_${messageId}">
                        <div class="glossary-list">
                            ${Object.entries(enrichedData.glossario).map(([termo, definicao]) => `
                                <div class="glossary-term">
                                    <div class="term-name">${termo}</div>
                                    <div class="term-definition">${definicao}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }

    toggleEnrichedSection(sectionId) {
        const section = document.getElementById(sectionId);
        const header = section.previousElementSibling;
        
        if (section.classList.contains('collapsed')) {
            section.classList.remove('collapsed');
            header.querySelector('.toggle-icon').style.transform = 'rotate(180deg)';
        } else {
            section.classList.add('collapsed');
            header.querySelector('.toggle-icon').style.transform = 'rotate(0deg)';
        }
    }

    askSuggestion(suggestion) {
        // Preencher o campo de mensagem com a sugestão
        const messageInput = document.getElementById('mensagem');
        if (messageInput) {
            messageInput.value = suggestion;
            messageInput.focus();
            this.updateCharCounter();
        }
    }

    formatMessage(content) {
        // Para mensagens de usuário, apenas converter quebras de linha
        if (!content.includes('**') && !content.includes('###') && !content.includes('```')) {
            // Convert URLs to links
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            content = content.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
            
            // Convert line breaks
            content = content.replace(/\n/g, '<br>');
            
            return content;
        }

        // Para mensagens com markdown, retornar como está para processamento posterior
        return content;
    }

    renderMarkdown(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const content = element.textContent || element.innerText;
        
        try {
            // Configurar marked para segurança
            marked.setOptions({
                breaks: true,
                gfm: true,
                sanitize: false, // Vamos permitir HTML para melhor formatação
                smartLists: true,
                smartypants: true
            });

            const htmlContent = marked.parse(content);
            element.innerHTML = htmlContent;

            // Aplicar syntax highlighting se houver código
            if (element.querySelector('code')) {
                Prism.highlightAllUnder(element);
            }
        } catch (error) {
            console.error('Erro ao renderizar markdown:', error);
            // Fallback para formatação simples
            element.innerHTML = this.formatMessage(content);
        }
    }

    formatChainContent(chainContent) {
        if (!chainContent) return '';
        
        try {
            // Processar a cadeia de raciocínio com markdown
            const htmlContent = marked.parse(chainContent);
            return htmlContent;
        } catch (error) {
            console.error('Erro ao formatar cadeia:', error);
            return chainContent.replace(/\n/g, '<br>');
        }
    }

    toggleChain(messageId) {
        const chainElement = document.getElementById(`chain_${messageId}`);
        const button = document.querySelector(`[onclick="neosonInterface.toggleChain('${messageId}')"]`);
        
        if (!chainElement || !button) return;

        chainElement.classList.toggle('collapsed');
        
        const isCollapsed = chainElement.classList.contains('collapsed');
        const icon = button.querySelector('i');
        const text = button.childNodes[1]; // Nó de texto após o ícone
        
        if (isCollapsed) {
            icon.className = 'fas fa-brain';
            text.textContent = ' Ver Cadeia de Raciocínio';
        } else {
            icon.className = 'fas fa-eye-slash';
            text.textContent = ' Ocultar Cadeia de Raciocínio';
        }
    }

    copyMessage(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        // Obter o texto markdown original ou o texto processado
        const textToCopy = element.textContent || element.innerText;
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            // Feedback visual
            const button = event.target.closest('.copy-button');
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copiado!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('Erro ao copiar:', err);
        });
    }

    async clearMemory() {
        if (this.isProcessing) return;

        if (!confirm('Tem certeza de que deseja limpar toda a memória de conversas?')) {
            return;
        }

        this.updateSystemStatus('loading', 'Limpando memória...');

        try {
            const response = await fetch('/limpar_memoria', { method: 'POST' });
            
            if (response.ok) {
                // Clear chat messages
                const messagesContainer = document.querySelector('.chat-messages');
                if (messagesContainer) {
                    messagesContainer.innerHTML = this.getWelcomeMessage();
                }
                
                this.updateSystemStatus('ready', 'Memória limpa com sucesso!');
                this.showNeosonExpression('happy');
                
                // Reset status after delay
                setTimeout(() => {
                    this.updateSystemStatus('ready', 'Sistema Pronto');
                }, 2000);
                
            } else {
                throw new Error('Falha ao limpar memória');
            }
        } catch (error) {
            console.error('Erro ao limpar memória:', error);
            this.updateSystemStatus('error', 'Erro ao limpar memória');
            this.showNeosonExpression('surprised');
        }
    }

    getWelcomeMessage() {
        return `
            <div class="welcome-message">
                <div class="message-avatar neoson-avatar">🤖</div>
                <div class="message-content">
                    <h3>Bem-vindo ao Sistema Neoson!</h3>
                    <p>Sou o Neoson, seu assistente inteligente multi-agente. Posso ajudar você com:</p>
                    <ul>
                        <li><strong>Questões de RH:</strong> Delegarei para a Ana, especialista em recursos humanos</li>
                        <li><strong>Questões de TI:</strong> Delegarei para o Alex, especialista em tecnologia</li>
                        <li><strong>Coordenação Geral:</strong> Posso gerenciar suas solicitações e escolher o melhor especialista</li>
                    </ul>
                    <p>Como posso ajudá-lo hoje?</p>
                </div>
            </div>
        `;
    }

    // ===== PERSONA SYSTEM =====
    selectPersona(event) {
        const card = event.currentTarget;
        const persona = card.dataset.persona;

        // Remove selection from all cards
        document.querySelectorAll('.persona-card').forEach(c => {
            c.classList.remove('selected');
        });

        // Select current card
        card.classList.add('selected');
        this.selectedPersona = persona;

        console.log(`Persona selecionada: ${persona}`);
        this.showNeosonExpression('happy');
    }

    showPresetPersonas() {
        const presetToggle = document.getElementById('presetToggle');
        const customToggle = document.getElementById('customToggle');
        const presetPersonas = document.getElementById('presetPersonas');
        const customCreator = document.getElementById('customPersonaCreator');

        // Update toggle buttons
        presetToggle.classList.add('active');
        customToggle.classList.remove('active');

        // Show/hide sections
        presetPersonas.style.display = 'grid';
        customCreator.style.display = 'none';
    }

    showCustomCreator() {
        const presetToggle = document.getElementById('presetToggle');
        const customToggle = document.getElementById('customToggle');
        const presetPersonas = document.getElementById('presetPersonas');
        const customCreator = document.getElementById('customPersonaCreator');

        // Update toggle buttons
        presetToggle.classList.remove('active');
        customToggle.classList.add('active');

        // Show/hide sections
        presetPersonas.style.display = 'none';
        customCreator.style.display = 'block';

        // Initialize preview
        this.updatePersonaPreview();
    }

    createCustomPersona() {
        const name = document.getElementById('customName').value.trim();
        const role = document.getElementById('customRole').value.trim();
        const department = document.getElementById('customDepartment').value;
        const level = document.getElementById('customLevel').value;
        const geography = document.getElementById('customGeography').value;

        // Validation
        if (!name || !role || !department || !level || !geography) {
            alert('Por favor, preencha todos os campos obrigatórios.');
            return;
        }

        // Get selected projects
        const projects = this.getSelectedProjects();

        // Create persona object
        const customPersona = {
            Nome: name,
            Cargo: role,
            Departamento: department,
            Nivel_Hierarquico: parseInt(level),
            Geografia: geography,
            Projetos: projects,
            isCustom: true
        };

        // Store custom persona
        this.customPersona = customPersona;
        this.selectedPersona = 'custom';

        // Update UI
        this.showPersonaCreatedSuccess(customPersona);
        this.showNeosonExpression('happy');

        console.log('Persona personalizada criada:', customPersona);
    }

    getSelectedProjects() {
        const checkboxes = document.querySelectorAll('#customProjects input[type="checkbox"]:checked');
        const projects = Array.from(checkboxes).map(cb => cb.value);

        // If "ALL" is selected, return only ["ALL"]
        if (projects.includes('ALL')) {
            return ['ALL'];
        }

        return projects.length > 0 ? projects : ['ALL'];
    }

    handleAllProjectsCheck(event) {
        const allCheckbox = event.target;
        const otherCheckboxes = document.querySelectorAll('#customProjects input[type="checkbox"]:not(#allProjects)');

        if (allCheckbox.checked) {
            // Uncheck all other project checkboxes
            otherCheckboxes.forEach(cb => cb.checked = false);
        }

        this.updatePersonaPreview();
    }

    updatePersonaPreview() {
        const name = document.getElementById('customName').value.trim();
        const role = document.getElementById('customRole').value.trim();
        const department = document.getElementById('customDepartment').value;
        const level = document.getElementById('customLevel').value;
        const geography = document.getElementById('customGeography').value;

        const preview = document.getElementById('personaPreview');
        const previewName = document.getElementById('previewName');
        const previewDetails = document.getElementById('previewDetails');
        const previewPermissions = document.getElementById('previewPermissions');

        if (!name && !role) {
            preview.style.display = 'none';
            return;
        }

        preview.style.display = 'block';

        // Update preview content
        previewName.textContent = name || 'Nome da Persona';
        
        const levelText = this.getLevelText(level);
        const geoText = this.getGeographyText(geography);
        const deptText = department || 'Departamento';
        
        previewDetails.innerHTML = `
            <strong>Cargo:</strong> ${role || 'Cargo não definido'}<br>
            <strong>Departamento:</strong> ${deptText}<br>
            <strong>Nível:</strong> ${levelText}<br>
            <strong>Localização:</strong> ${geoText}
        `;

        // Update permissions preview
        this.updatePermissionsPreview(department, level, geography, previewPermissions);
    }

    updatePermissionsPreview(department, level, geography, container) {
        const permissions = [];
        const levelNum = parseInt(level) || 1;

        // Department permissions
        if (department) {
            permissions.push(`<span class="permission-tag">${department}</span>`);
        }

        // Level-based permissions
        if (levelNum >= 4) {
            permissions.push('<span class="permission-tag high-level">Informações Sensíveis</span>');
        }
        if (levelNum >= 5) {
            permissions.push('<span class="permission-tag high-level">Dados Confidenciais</span>');
        }

        // Geography permissions
        if (geography) {
            permissions.push(`<span class="permission-tag">${this.getGeographyText(geography)}</span>`);
        }

        // Basic permissions
        permissions.push('<span class="permission-tag">Informações Básicas</span>');

        if (levelNum < 3) {
            permissions.push('<span class="permission-tag restricted">Acesso Limitado</span>');
        }

        container.innerHTML = permissions.join('');
    }

    getLevelText(level) {
        const levels = {
            '1': 'Nível 1 - Estagiário',
            '2': 'Nível 2 - Junior', 
            '3': 'Nível 3 - Pleno/Supervisor',
            '4': 'Nível 4 - Sênior/Gerente',
            '5': 'Nível 5 - Diretor/Executivo'
        };
        return levels[level] || 'Nível não definido';
    }

    getGeographyText(geo) {
        const geos = {
            'BR': 'Brasil',
            'USA': 'Estados Unidos',
            'EU': 'Europa',
            'ASIA': 'Ásia'
        };
        return geos[geo] || 'Localização não definida';
    }

    showPersonaCreatedSuccess(persona) {
        // Show success message
        const successMessage = document.createElement('div');
        successMessage.className = 'success-message';
        successMessage.innerHTML = `
            <div class="success-content">
                <i class="fas fa-check-circle"></i>
                <h4>Persona Criada com Sucesso!</h4>
                <p><strong>${persona.Nome}</strong> foi criada e está pronta para uso.</p>
                <button onclick="this.parentElement.parentElement.remove()" class="close-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Insert after creator
        const creator = document.getElementById('customPersonaCreator');
        creator.parentNode.insertBefore(successMessage, creator.nextSibling);

        // Remove after 5 seconds
        setTimeout(() => {
            if (successMessage.parentNode) {
                successMessage.remove();
            }
        }, 5000);
    }

    clearPersonaForm() {
        // Clear all form fields
        document.getElementById('customName').value = '';
        document.getElementById('customRole').value = '';
        document.getElementById('customDepartment').value = '';
        document.getElementById('customLevel').value = '';
        document.getElementById('customGeography').value = '';

        // Uncheck all project checkboxes
        document.querySelectorAll('#customProjects input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
        });

        // Check "All Projects" by default
        document.getElementById('allProjects').checked = true;

        // Update preview
        this.updatePersonaPreview();

        this.showNeosonExpression('happy');
    }

    // ===== UTILITY FUNCTIONS =====
    updateCharCounter() {
        const messageInput = document.getElementById('mensagem');
        const counter = document.querySelector('.char-counter');
        
        if (messageInput && counter) {
            const length = messageInput.value.length;
            const maxLength = 1000;
            counter.textContent = `${length}/${maxLength}`;
            
            if (length > maxLength * 0.9) {
                counter.style.color = '#e74c3c';
            } else {
                counter.style.color = 'rgba(255, 255, 255, 0.7)';
            }
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ===== NOTIFICATIONS =====
    showNotification(title, message, duration = 3000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'sub-agent-notification';
        notification.innerHTML = `
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        `;

        // Add to document
        document.body.appendChild(notification);

        // Auto-remove after duration
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    // ===== SUB-AGENTS MONITORING =====
    async updateSubAgentsStatus() {
        try {
            const response = await fetch('/api/ti-hierarchy');
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.ti_system) {
                    this.displaySubAgentsStats(data.ti_system);
                }
            }
        } catch (error) {
            console.log('Não foi possível obter status dos sub-agentes:', error);
        }
    }

    displaySubAgentsStats(tiSystem) {
        const stats = tiSystem.hierarchy_stats || {};
        const subAgents = tiSystem.sub_agents || [];

        // Update sub-agents count indicator
        const indicator = document.querySelector('.sub-agents-indicator span');
        if (indicator) {
            indicator.textContent = `${subAgents.length} sub-especialistas ativos`;
        }

        // Show recent delegations if any
        if (stats.recent_delegations && stats.recent_delegations.length > 0) {
            const lastDelegation = stats.recent_delegations[stats.recent_delegations.length - 1];
            console.log('🔄 Última delegação:', lastDelegation);
        }
    }

    // Inicializar monitoramento automático dos sub-agentes
    startSubAgentMonitoring() {
        // Update immediately
        this.updateSubAgentsStatus();
        
        // Update every 30 seconds
        setInterval(() => {
            this.updateSubAgentsStatus();
        }, 30000);
    }

    // ===== RESPONSIVE ADJUSTMENTS =====
    adjustForMobile() {
        const isMobile = window.innerWidth <= 768;
        
        if (isMobile) {
            this.eyeTrackingEnabled = false;
            this.centerEyes();
        } else {
            this.eyeTrackingEnabled = true;
        }
    }

    // ===== SISTEMA DE FEEDBACK =====
    
    /**
     * Armazena contexto da mensagem para posterior envio de feedback
     */
    storeMessageContext(messageId, responseText, agentName) {
        this.feedbackContext[messageId] = {
            question: this.lastUserQuestion,
            response: responseText,
            agent: agentName,
            timestamp: new Date().toISOString(),
            classification: this.getAgentClassification(agentName)
        };
        
        console.log(`💾 Contexto armazenado para ${messageId}:`, this.feedbackContext[messageId]);
    }
    
    /**
     * Obtém classificação do agente
     */
    getAgentClassification(agentName) {
        const classifications = {
            'ana': 'rh',
            'Coordenador TI': 'ti',
            'alex': 'ti',
            'Ariel': 'ti_governance',
            'Alice': 'ti_infrastructure',
            'Carlos': 'ti_development',
            'Marina': 'ti_enduser',
            'neoson': 'geral'
        };
        
        return classifications[agentName] || 'outro';
    }
    
    /**
     * Submete feedback do usuário
     */
    async submitFeedback(rating, responseId, event) {
        // Prevenir clique múltiplo
        const button = event.target.closest('.feedback-btn');
        if (button.disabled) return;
        
        console.log(`👍👎 Feedback ${rating} para resposta ${responseId}`);
        
        this.currentFeedbackId = responseId;
        this.currentRating = rating;
        
        // Desabilitar todos os botões de feedback desta mensagem
        const buttonsContainer = document.querySelector(`.feedback-buttons[data-response-id="${responseId}"]`);
        if (buttonsContainer) {
            const allButtons = buttonsContainer.querySelectorAll('.feedback-btn');
            allButtons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            });
        }
        
        // Marcar botão clicado visualmente
        button.classList.add('selected');
        
        // Se positivo, enviar direto
        if (rating === 5) {
            await this.sendFeedbackToAPI(rating, responseId, null);
            this.showThankYouToast('Obrigado pelo feedback positivo! 👍');
        } else {
            // Se negativo, abrir modal para comentário
            this.openFeedbackModal();
        }
    }
    
    /**
     * Abre modal de feedback
     */
    openFeedbackModal() {
        let modal = document.getElementById('feedbackModal');
        
        // Criar modal se não existir
        if (!modal) {
            modal = this.createFeedbackModal();
            document.body.appendChild(modal);
        }
        
        modal.style.display = 'flex'; // Usar flex para centralizar
        const textarea = document.getElementById('feedbackComment');
        if (textarea) {
            textarea.value = '';
            textarea.focus();
            document.getElementById('charCount').textContent = '0';
        }
    }
    
    /**
     * Cria modal de feedback
     */
    createFeedbackModal() {
        const modal = document.createElement('div');
        modal.id = 'feedbackModal';
        modal.className = 'modal feedback-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-comment-dots"></i> Obrigado pelo feedback!</h3>
                    <button class="modal-close" onclick="neosonInterface.closeFeedbackModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <p>Quer nos contar mais sobre sua experiência? (opcional)</p>
                    <textarea id="feedbackComment" 
                              placeholder="Como podemos melhorar esta resposta?"
                              maxlength="2000"
                              rows="4"></textarea>
                    <div class="char-counter-feedback">
                        <span id="charCount">0</span>/2000 caracteres
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="neosonInterface.closeFeedbackModal()">
                        Pular
                    </button>
                    <button class="btn-primary" onclick="neosonInterface.submitComment()">
                        <i class="fas fa-paper-plane"></i>
                        Enviar
                    </button>
                </div>
            </div>
        `;
        
        // Adicionar event listener para contador de caracteres
        setTimeout(() => {
            const textarea = document.getElementById('feedbackComment');
            const charCount = document.getElementById('charCount');
            
            if (textarea && charCount) {
                textarea.addEventListener('input', () => {
                    const count = textarea.value.length;
                    charCount.textContent = count;
                    
                    if (count > 1900) {
                        charCount.style.color = '#f44336';
                    } else {
                        charCount.style.color = '#999';
                    }
                });
            }
        }, 100);
        
        // Fechar modal ao clicar fora
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeFeedbackModal();
            }
        });
        
        return modal;
    }
    
    /**
     * Fecha modal de feedback
     */
    closeFeedbackModal() {
        const modal = document.getElementById('feedbackModal');
        if (!modal) return;
        
        modal.style.display = 'none';
        
        // Se já selecionou rating negativo mas não enviou comentário, enviar sem comentário
        if (this.currentFeedbackId && this.currentRating === 1) {
            this.sendFeedbackToAPI(this.currentRating, this.currentFeedbackId, null);
            this.showThankYouToast('Obrigado pelo seu feedback! Vamos melhorar! 💪');
            
            // Limpar estado
            this.currentFeedbackId = null;
            this.currentRating = null;
        }
    }
    
    /**
     * Submete comentário do modal
     */
    async submitComment() {
        const comment = document.getElementById('feedbackComment').value.trim();
        
        await this.sendFeedbackToAPI(this.currentRating, this.currentFeedbackId, comment || null);
        
        this.closeFeedbackModal();
        this.showThankYouToast('Obrigado pelo seu feedback detalhado! Vamos melhorar! 💪');
        
        // Limpar estado
        this.currentFeedbackId = null;
        this.currentRating = null;
    }
    
    /**
     * Envia feedback para API
     */
    async sendFeedbackToAPI(rating, feedbackId, comment) {
        const context = this.feedbackContext[feedbackId];
        
        if (!context) {
            console.error('❌ Contexto não encontrado para', feedbackId);
            return;
        }
        
        try {
            console.log('📤 Enviando feedback para API...');
            
            const requestBody = {
                usuario_id: this.currentUserId,
                feedback_id: feedbackId,
                pergunta: context.question || '',
                resposta: context.response || '',
                agente: context.agent || 'desconhecido',
                classificacao: context.classification || 'outro',
                rating: rating,
                comentario: comment,
                tempo_resposta_ms: 0, // Pode ser calculado se necessário
                contexto: {
                    persona: this.selectedPersona,
                    timestamp: context.timestamp
                }
            };
            
            console.log('📦 Request body:', requestBody);
            
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ erro: 'Erro desconhecido' }));
                console.error('❌ Erro na API de feedback:', errorData);
                throw new Error(errorData.erro || errorData.detail || 'Erro ao enviar feedback');
            }
            
            const data = await response.json();
            console.log('✅ Feedback enviado com sucesso:', data);
            
        } catch (error) {
            console.error('❌ Erro ao enviar feedback:', error);
            this.showErrorToast('Erro ao enviar feedback. Tente novamente mais tarde.');
        }
    }
    
    /**
     * Mostra toast de agradecimento
     */
    showThankYouToast(message) {
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
    showErrorToast(message) {
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
}

// ===== ADDITIONAL FEATURES =====

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus message input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const messageInput = document.getElementById('mensagem');
        if (messageInput) {
            messageInput.focus();
        }
    }
    
    // Escape to close overlays
    if (e.key === 'Escape') {
        const overlay = document.querySelector('.processing-overlay.show');
        if (overlay && !window.neoson.isProcessing) {
            overlay.classList.remove('show');
        }
    }
});

// Initialize system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.neoson = new NeosonInterface();
    window.neosonInterface = window.neoson; // Para compatibilidade com os novos métodos
    
    // Handle responsive changes
    window.addEventListener('resize', () => {
        window.neoson.adjustForMobile();
    });
    
    // Initial responsive check
    window.neoson.adjustForMobile();
});

// ===== ERROR HANDLING =====
window.addEventListener('error', function(e) {
    console.error('Sistema Neoson - Erro:', e.error);
    
    if (window.neoson) {
        window.neoson.updateSystemStatus('error', 'Erro no Sistema');
        window.neoson.showNeosonExpression('surprised');
    }
});

// Service worker registration (for offline support)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Register service worker if available
        // navigator.serviceWorker.register('/sw.js');
    });
}

console.log('🚀 Neoson Multi-Agent System - JavaScript Loaded Successfully');