// Prevenir execução dupla
if (window.factoryLoaded) {
    console.warn('⚠️ Factory.js já foi carregado, ignorando segunda execução');
    throw new Error('Factory already loaded');
}
window.factoryLoaded = true;

// ====================================
// VERSÃO 1.1.3 - Factory de Agentes
// ====================================
// Correção: Uso correto do singleton get_registry()
// ====================================

console.log('🏭 Factory.js carregado - versão 1.1.3');

// Estado do formulário
let currentAgentType = 'subagent';
let availableCoordinators = [];
let availableSubagents = [];
const FLOW_STATUS_LABELS = {
    pending: 'Pendente',
    active: 'Em andamento',
    done: 'Concluído'
};

// ============================================================================
// SELEÇÃO DE TIPO DE AGENTE
// ============================================================================

function selectAgentType(type) {
    console.log('🔄 Selecionando tipo de agente:', type);
    currentAgentType = type;
    
    // Atualizar botões
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === type) {
            btn.classList.add('active');
        }
    });
    
    // Mostrar formulário apropriado
    const subagentForm = document.getElementById('subagentForm');
    const coordinatorForm = document.getElementById('coordinatorForm');
    
    if (type === 'subagent') {
        subagentForm.style.display = 'block';
        coordinatorForm.style.display = 'none';
    } else {
        subagentForm.style.display = 'none';
        coordinatorForm.style.display = 'block';
        
        // Atualizar lista de subagentes disponíveis
        populateAgentSelector();
    }
}

// ============================================================================
// CARREGAR AGENTES DISPONÍVEIS
// ============================================================================

async function loadAvailableAgents() {
    try {
        console.log('📡 Carregando agentes disponíveis...');
        const token = localStorage.getItem('token');
        const response = await fetch('/api/factory/agents', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Falha ao carregar agentes');
        }
        
        const data = await response.json();
        console.log('📊 Dados recebidos:', data);
        
        // Separar coordenadores e subagentes
        availableCoordinators = data.agents.filter(a => a.type === 'coordinator');
        availableSubagents = data.agents.filter(a => a.type === 'subagent');
        
        console.log(`✅ Coordenadores: ${availableCoordinators.length}, Subagentes: ${availableSubagents.length}`);
        
        // Popular dropdown de coordenadores
        const coordinatorSelect = document.getElementById('subagent_coordinator');
        if (coordinatorSelect) {
            coordinatorSelect.innerHTML = '<option value="">Nenhum (independente)</option>';
            availableCoordinators.forEach(coord => {
                const option = document.createElement('option');
                option.value = coord.identifier;
                option.textContent = `${coord.name} (${coord.identifier})`;
                coordinatorSelect.appendChild(option);
            });
            console.log(`✅ Dropdown de coordenadores populado com ${availableCoordinators.length} opções`);
        }
        
    } catch (error) {
        console.error('❌ Erro ao carregar agentes disponíveis:', error);
    }
}

// ============================================================================
// POPULAR SELETOR DE AGENTES (PARA COORDENADOR)
// ============================================================================

function populateAgentSelector() {
    const selector = document.getElementById('agentSelector');
    if (!selector) return;
    
    selector.innerHTML = '';
    
    if (availableSubagents.length === 0) {
        selector.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">Nenhum subagente disponível. Crie subagentes primeiro.</p>';
        return;
    }
    
    availableSubagents.forEach(agent => {
        const checkbox = document.createElement('label');
        checkbox.className = 'agent-checkbox';
        checkbox.innerHTML = `
            <input type="checkbox" value="${agent.identifier}" onchange="toggleAgentCheckbox(this)">
            <span>${agent.name}</span>
        `;
        selector.appendChild(checkbox);
    });
}

function toggleAgentCheckbox(checkbox) {
    const label = checkbox.closest('.agent-checkbox');
    if (checkbox.checked) {
        label.classList.add('selected');
    } else {
        label.classList.remove('selected');
    }
}

// ============================================================================
// TOGGLE MCP FIELDS
// ============================================================================

function toggleMCPFields() {
    const enableMCP = document.getElementById('subagent_enable_mcp').checked;
    const mcpFields = document.getElementById('mcpFields');
    
    if (enableMCP) {
        mcpFields.style.display = 'block';
    } else {
        mcpFields.style.display = 'none';
    }
}

// ============================================================================
// GUIA DE FLUXO
// ============================================================================

function setFlowStepStatus(step, status = 'pending', description = '', actions = []) {
    const stepEl = document.querySelector(`.flow-step[data-step="${step}"]`);
    if (!stepEl) return;

    stepEl.classList.remove('pending', 'active', 'done');
    stepEl.classList.add(status);

    const badge = stepEl.querySelector('.flow-step-badge');
    if (badge) {
        badge.textContent = FLOW_STATUS_LABELS[status] || FLOW_STATUS_LABELS.pending;
    }

    const descriptionEl = stepEl.querySelector('.flow-step-description');
    if (descriptionEl && description) {
        descriptionEl.textContent = description;
    }

    const actionsContainer = stepEl.querySelector('.flow-step-actions');
    if (actionsContainer) {
        actionsContainer.innerHTML = '';
        actions.forEach(actionItem => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `flow-action-btn ${actionItem.variant || 'primary'}`;
            btn.textContent = actionItem.label;
            if (typeof actionItem.action === 'function') {
                btn.addEventListener('click', actionItem.action);
            }
            actionsContainer.appendChild(btn);
        });
    }
}

function resetFlowGuide() {
    setFlowStepStatus('create', 'active', 'Preencha o formulário ao lado e clique em "Criar Subagente".');
    setFlowStepStatus('ingest', 'pending', 'Após criar, adicione documentos à base dedicada do agente.');
    setFlowStepStatus('test', 'pending', 'Depois da ingestão, teste o agente diretamente no chat.');
}

// ============================================================================
// CRIAR SUBAGENTE
// ============================================================================

async function createAgent() {
    // Validar campos obrigatórios
    const name = document.getElementById('subagent_name').value.trim();
    const identifier = document.getElementById('subagent_identifier').value.trim();
    const specialty = document.getElementById('subagent_specialty').value.trim();
    const description = document.getElementById('subagent_description').value.trim();
    const keywordsStr = document.getElementById('subagent_keywords').value.trim();
    
    if (!name || !identifier || !specialty || !description || !keywordsStr) {
        showNotification('⚠️ Preencha todos os campos obrigatórios', 'error');
        return;
    }
    
    // Validar identifier (apenas letras minúsculas)
    if (!/^[a-z_]+$/.test(identifier)) {
        showNotification('⚠️ Identificador deve conter apenas letras minúsculas e underscore', 'error');
        return;
    }
    
    // Preparar dados
    const keywords = keywordsStr.split(',').map(k => k.trim()).filter(k => k);
    
    const data = {
        name,
        identifier,
        specialty,
        description,
        keywords,
        parent_coordinator: document.getElementById('subagent_coordinator').value || null,
        table_name: document.getElementById('subagent_table').value.trim() || null,
        llm_model: document.getElementById('subagent_model').value,
        llm_temperature: parseFloat(document.getElementById('subagent_temperature').value),
        llm_max_tokens: parseInt(document.getElementById('subagent_max_tokens').value),
        enable_mcp_tools: document.getElementById('subagent_enable_mcp').checked,
        mcp_tools_category: document.getElementById('subagent_mcp_category').value.trim() || null,
        allowed_tools: []
    };
    
    // Tools MCP
    if (data.enable_mcp_tools) {
        const toolsStr = document.getElementById('subagent_allowed_tools').value.trim();
        if (toolsStr) {
            data.allowed_tools = toolsStr.split(',').map(t => t.trim()).filter(t => t);
        }
    }
    
    // Mostrar status
    showFactoryStatus('Criando subagente...');
    setFlowStepStatus('create', 'active', 'Estamos configurando o novo subagente e provisionando os recursos necessários.');
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/factory/create-subagent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        console.log('📊 Resultado da API:', result);
        console.log('   success:', result.success);
        console.log('   identifier:', result.identifier);
        console.log('   message:', result.message);
        console.log('   error:', result.error);
        
        hideFactoryStatus();
        
        if (response.ok && result.success) {
            showNotification(`✅ Subagente "${name}" criado com sucesso!`, 'success');
            
            // Resetar formulário
            resetFactoryForm();
            
            // Atualizar listas
            await loadAvailableAgents();
            await refreshAgentsList();
            
            // 🔥 ATUALIZAR ÁRVORE DE AGENTES
            if (typeof window.loadAgentsTree === 'function') {
                console.log('🔄 Atualizando Árvore de Agentes...');
                window.agentsTreeLoaded = false;
                await window.loadAgentsTree();
            }
            
            // 🔥 ATUALIZAR DROPDOWN DA BASE DE CONHECIMENTO
            if (typeof window.loadKnowledgeAgents === 'function') {
                console.log('🔄 Atualizando dropdown da Base de Conhecimento...');
                await window.loadKnowledgeAgents();
            }
            
            // Mostrar opção de adicionar conhecimento
            showAddKnowledgePrompt(result.identifier, result.table_name, name);
            
        } else {
            console.error('❌ Erro ao criar subagente:', result);
            const errorMsg = result.error || result.message || 'Erro desconhecido';
            showNotification(`❌ Erro ao criar subagente: ${errorMsg}`, 'error');
        }
        
    } catch (error) {
        hideFactoryStatus();
        console.error('Erro ao criar subagente:', error);
        showNotification(`❌ Erro ao criar subagente: ${error.message}`, 'error');
    }
}

// ============================================================================
// CRIAR COORDENADOR
// ============================================================================

async function createCoordinator() {
    // Validar campos obrigatórios
    const name = document.getElementById('coord_name').value.trim();
    const identifier = document.getElementById('coord_identifier').value.trim();
    const specialty = document.getElementById('coord_specialty').value.trim();
    const description = document.getElementById('coord_description').value.trim();
    
    if (!name || !identifier || !specialty || !description) {
        showNotification('⚠️ Preencha todos os campos obrigatórios', 'error');
        return;
    }
    
    // Validar identifier
    if (!/^[a-z_]+$/.test(identifier)) {
        showNotification('⚠️ Identificador deve conter apenas letras minúsculas e underscore', 'error');
        return;
    }
    
    // Coletar agentes selecionados
    const selectedAgents = Array.from(
        document.querySelectorAll('#agentSelector input[type="checkbox"]:checked')
    ).map(cb => cb.value);
    
    if (selectedAgents.length === 0) {
        showNotification('⚠️ Selecione pelo menos um subagente', 'error');
        return;
    }
    
    // Preparar dados
    const data = {
        name,
        identifier,
        specialty,
        description,
        children_agents: selectedAgents
    };
    
    // Mostrar status
    showFactoryStatus('Criando coordenador...');
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/factory/create-coordinator', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        hideFactoryStatus();
        
        if (response.ok && result.success) {
            showNotification(`✅ Coordenador "${name}" criado com sucesso!`, 'success');
            
            // Resetar formulário
            resetFactoryForm();
            
            // Atualizar listas
            await loadAvailableAgents();
            await refreshAgentsList();
            
            // 🔥 ATUALIZAR ÁRVORE DE AGENTES
            if (typeof window.loadAgentsTree === 'function') {
                console.log('🔄 Atualizando Árvore de Agentes...');
                window.agentsTreeLoaded = false;
                await window.loadAgentsTree();
            }
            
            // 🔥 ATUALIZAR DROPDOWN DA BASE DE CONHECIMENTO
            if (typeof window.loadKnowledgeAgents === 'function') {
                console.log('🔄 Atualizando dropdown da Base de Conhecimento...');
                await window.loadKnowledgeAgents();
            }
            
        } else {
            showNotification(`❌ Erro: ${result.error || result.message}`, 'error');
        }
        
    } catch (error) {
        hideFactoryStatus();
        console.error('Erro ao criar coordenador:', error);
        showNotification(`❌ Erro ao criar coordenador: ${error.message}`, 'error');
    }
}

// ============================================================================
// RESETAR FORMULÁRIO
// ============================================================================

function resetFactoryForm() {
    if (currentAgentType === 'subagent') {
        document.getElementById('subagent_name').value = '';
        document.getElementById('subagent_identifier').value = '';
        document.getElementById('subagent_specialty').value = '';
        document.getElementById('subagent_description').value = '';
        document.getElementById('subagent_keywords').value = '';
        document.getElementById('subagent_table').value = '';
        document.getElementById('subagent_coordinator').value = '';
        document.getElementById('subagent_model').value = 'gpt-4o-mini';
        document.getElementById('subagent_temperature').value = '0.3';
        document.getElementById('subagent_max_tokens').value = '10000';
        document.getElementById('subagent_enable_mcp').checked = false;
        document.getElementById('subagent_mcp_category').value = '';
        document.getElementById('subagent_allowed_tools').value = '';
        toggleMCPFields();
    } else {
        document.getElementById('coord_name').value = '';
        document.getElementById('coord_identifier').value = '';
        document.getElementById('coord_specialty').value = '';
        document.getElementById('coord_description').value = '';
        
        // Desmarcar checkboxes
        document.querySelectorAll('#agentSelector input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
            cb.closest('.agent-checkbox').classList.remove('selected');
        });
    }

    resetFlowGuide();
}

// ============================================================================
// ATUALIZAR LISTA DE AGENTES
// ============================================================================

async function refreshAgentsList() {
    const tbody = document.getElementById('agentsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Carregando...</td></tr>';
    
    try {
        console.log('📊 Atualizando lista de agentes...');
        const token = localStorage.getItem('token');
        const response = await fetch('/api/factory/agents', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Falha ao carregar agentes');
        }
        
        const data = await response.json();
        console.log('📈 Dados da API:', data);
        
        // Atualizar estatísticas
        document.getElementById('totalAgents').textContent = data.total || 0;
        document.getElementById('totalSubagents').textContent = data.subagents || 0;
        document.getElementById('totalCoordinators').textContent = data.coordinators || 0;
        document.getElementById('totalWithMCP').textContent = data.with_mcp_tools || 0;
        
        console.log(`📊 Stats: Total=${data.total}, Subagentes=${data.subagents}, Coordenadores=${data.coordinators}`);
        
        // Preencher tabela
        if (!data.agents || data.agents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Nenhum agente criado ainda</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        
        data.agents.forEach(agent => {
            const row = document.createElement('tr');
            
            const typeClass = agent.type === 'coordinator' ? 'coordinator' : 'subagent';
            const typeLabel = agent.type === 'coordinator' ? 'Coordenador' : 'Subagente';
            
            row.innerHTML = `
                <td><span class="agent-type-badge ${typeClass}">${typeLabel}</span></td>
                <td>${agent.name}</td>
                <td><code>${agent.identifier}</code></td>
                <td>${agent.specialty}</td>
                <td><span class="status-badge active">Ativo</span></td>
                <td>
                    <div class="table-actions">
                        <button class="table-btn view" onclick="viewAgentInTree('${agent.identifier}')">
                            <i class="fas fa-eye"></i> Ver na Árvore
                        </button>
                        ${agent.type === 'subagent' ? `
                            <button class="table-btn knowledge" onclick="addKnowledgeToAgent('${agent.identifier}', '${agent.table_name || `knowledge_${agent.identifier}`}')">
                                <i class="fas fa-book"></i> Adicionar Conhecimento
                            </button>
                        ` : ''}
                    </div>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        console.log(`✅ Tabela preenchida com ${data.agents.length} agentes`);
        
    } catch (error) {
        console.error('❌ Erro ao carregar lista de agentes:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="loading" style="color: #e74c3c;">Erro ao carregar agentes</td></tr>';
    }
}

// ============================================================================
// INTEGRAÇÃO COM OUTRAS PÁGINAS
// ============================================================================

function viewAgentInTree(agentId) {
    // Ir para a página de árvore de agentes
    showTab('agents');
    
    // Recarregar árvore se necessário
    if (window.loadAgentsTree) {
        window.agentsTreeLoaded = false;
        setTimeout(() => window.loadAgentsTree(), 300);
    }
    
    showNotification(`📊 Visualizando agente "${agentId}" na árvore`, 'info');
}

function openChatWithAgent(agentId) {
    showTab('chat');

    setTimeout(() => {
        if (typeof window.selectAgentForChat === 'function') {
            const found = window.selectAgentForChat(agentId);
            if (found) {
                setFlowStepStatus('test', 'active', 'Envie uma pergunta para validar o comportamento desse agente.');
                showNotification(`💬 Conversando diretamente com ${agentId}`, 'success');
            } else {
                showNotification('⚠️ Não encontrei esse agente no seletor do chat. Atualize os destinos e tente novamente.', 'error');
            }
        }
    }, 300);
}

function addKnowledgeToAgent(agentId, tableName) {
    // Ir para a página de Base de Conhecimento
    showTab('knowledge');

    if (agentId) {
        setFlowStepStatus('create', 'done', `Subagente ${agentId} configurado com sucesso.`);
    }
    setFlowStepStatus('ingest', 'active', 'Selecione os arquivos e clique em "Iniciar Ingestão" para alimentar a base do agente.');
    setFlowStepStatus('test', 'pending', 'Assim que a ingestão finalizar, volte ao chat para validar o comportamento.');
    
    // Pré-selecionar a tabela no dropdown
    setTimeout(() => {
        const select = document.getElementById('targetAgent');
        if (select) {
            // Procurar opção correspondente
            for (let option of select.options) {
                if (option.value === tableName) {
                    select.value = tableName;
                    break;
                }
            }
        }
    }, 300);
    
    showNotification(`📚 Adicione conhecimento ao agente "${agentId}"`, 'info');
}

function showAddKnowledgePrompt(agentId, tableName, agentName) {
    const displayName = agentName || agentId;
    const tableMessage = tableName
        ? `A base ${tableName} está pronta para receber documentos.`
        : 'A base padrão foi criada e está pronta para ingestão.';

    setFlowStepStatus('create', 'done', `Subagente ${displayName} criado com sucesso.`);
    setFlowStepStatus('ingest', 'active', tableMessage, [
        {
            label: 'Adicionar conhecimento agora',
            action: () => addKnowledgeToAgent(agentId, tableName),
            variant: 'primary'
        }
    ]);
    setFlowStepStatus('test', 'pending', 'Depois da ingestão, volte ao chat e valide o comportamento do agente.', [
        {
            label: 'Abrir chat com o agente',
            action: () => openChatWithAgent(agentId),
            variant: 'ghost'
        }
    ]);

    showNotification(`🚀 ${displayName} criado! Avance para a ingestão de conhecimento.`, 'success');
}

// ============================================================================
// NOTIFICAÇÕES E STATUS
// ============================================================================

function showFactoryStatus(message) {
    const status = document.getElementById('factoryStatus');
    const statusText = document.getElementById('factoryStatusText');
    
    if (status && statusText) {
        statusText.textContent = message;
        status.style.display = 'flex';
    }
}

function hideFactoryStatus() {
    const status = document.getElementById('factoryStatus');
    if (status) {
        status.style.display = 'none';
    }
}

function showNotification(message, type = 'info') {
    // Criar elemento de notificação
    const notification = document.createElement('div');
    notification.className = `factory-notification ${type}`;
    notification.textContent = message;
    
    // Adicionar estilos inline (será sobrescrito por CSS)
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#e74c3c' : '#2196f3'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    // Remover após 4 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Adicionar animações CSS dinamicamente
const factoryStyle = document.createElement('style');
factoryStyle.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(factoryStyle);

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

// Expor funções globalmente PRIMEIRO - antes do DOMContentLoaded
window.refreshAgentsList = refreshAgentsList;
window.loadAvailableAgents = loadAvailableAgents;
window.selectAgentType = selectAgentType;
window.createAgent = createAgent;
window.createCoordinator = createCoordinator;
window.viewAgentInTree = viewAgentInTree;
window.addKnowledgeToAgent = addKnowledgeToAgent;
window.toggleMCPFields = toggleMCPFields;
window.resetFactoryForm = resetFactoryForm;
window.openChatWithAgent = openChatWithAgent;
window.resetFlowGuide = resetFlowGuide;

console.log('✅ Funções do Factory expostas no window');

document.addEventListener('DOMContentLoaded', () => {
    console.log('🏭 Agent Factory carregado');
    
    // Carregar lista de agentes existentes
    loadAvailableAgents();
    
    // Carregar lista de agentes criados
    refreshAgentsList();

    // Resetar guia de fluxo
    resetFlowGuide();
});

console.log('✅ Agent Factory pronto!');
