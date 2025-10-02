// ===== NEOSON SISTEMA MULTI-AGENTE - JAVASCRIPT =====

class NeosonInterface {
    constructor() {
        this.selectedPersona = null;
        this.isProcessing = false;
        this.currentDelegation = null;
        this.eyeTrackingEnabled = true;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeEyeTracking();
        this.updateCharCounter();
        this.setupAgentMonitoring();
        this.startSubAgentMonitoring();
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
        this.updateSystemStatus('loading', `Delegando para ${agentInfo.name}...`);

        this.activateAgentCard(agentKey);
        this.showAgentResponseIndicator(agentInfo);

        // Se é um agente TI hierárquico, mostrar delegação específica
        if (agentKey === 'Coordenador TI') {
            await this.showHierarchicalDelegation();
        }

        await this.delay(600);

        this.isProcessing = false;
        this.updateSystemStatus('ready', 'Sistema Pronto');
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
        const overlay = document.querySelector('.processing-overlay');
        if (overlay) {
            overlay.classList.remove('show');
        }

        // Reset steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
        });

        // Hide handoff
        const handoff = document.querySelector('.agent-handoff');
        if (handoff) {
            handoff.classList.remove('show');
        }

        this.isProcessing = false;
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
            this.addMessage(data.resposta, 'bot', data.agent_usado || 'neoson');
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
        }
    }

    addMessage(content, sender, agent = null) {
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

        messageDiv.innerHTML = `
            <div class="message-avatar ${agent ? agentInfo.class : ''}">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <strong>${senderName}</strong>
                    ${agentBadge}
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="message-text">${this.formatMessage(content)}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessage(content) {
        // Convert URLs to links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        content = content.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        
        // Convert line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
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