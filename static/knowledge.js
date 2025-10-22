// ============================================================================
// 📚 GERENCIAMENTO DE BASE DE CONHECIMENTO
// Arquivo: static/knowledge.js
// ============================================================================

let selectedFiles = [];

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando Base de Conhecimento...');
    
    // Setup drag and drop
    setupDragAndDrop();
    
    // Setup file input
    setupFileInput();
    
    console.log('✅ Base de Conhecimento carregada');
});

// ============================================================================
// DRAG AND DROP
// ============================================================================

function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    
    if (!uploadArea) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('drag-over');
        }, false);
    });
    
    uploadArea.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

// ============================================================================
// FILE INPUT
// ============================================================================

function setupFileInput() {
    const fileInput = document.getElementById('fileInput');
    
    if (!fileInput) return;
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    const validFiles = Array.from(files).filter(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        return ext === 'pdf' || ext === 'docx';
    });
    
    if (validFiles.length === 0) {
        addLog('⚠️ Nenhum arquivo válido selecionado. Apenas PDF e DOCX são aceitos.', 'warning');
        return;
    }
    
    selectedFiles = [...selectedFiles, ...validFiles];
    renderSelectedFiles();
    addLog(`✅ ${validFiles.length} arquivo(s) adicionado(s).`, 'success');
}

function renderSelectedFiles() {
    const container = document.getElementById('selectedFiles');
    
    if (!container || selectedFiles.length === 0) {
        if (container) container.innerHTML = '';
        return;
    }
    
    container.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-icon">
                    <i class="fas fa-file-${file.name.endsWith('.pdf') ? 'pdf' : 'word'}"></i>
                </div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <button class="file-remove" onclick="removeFile(${index})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderSelectedFiles();
    addLog(`🗑️ Arquivo removido.`, 'info');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ============================================================================
// LOG MANAGEMENT
// ============================================================================

function addLog(message, type = 'info') {
    const logContainer = document.getElementById('knowledgeLog');
    
    if (!logContainer) return;
    
    // Remover placeholder se existir
    const placeholder = logContainer.querySelector('.log-placeholder');
    if (placeholder) {
        placeholder.remove();
    }
    
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLog() {
    const logContainer = document.getElementById('knowledgeLog');
    
    if (!logContainer) return;
    
    logContainer.innerHTML = `
        <div class="log-placeholder">
            <i class="fas fa-info-circle"></i>
            <p>Aguardando início do processamento...</p>
        </div>
    `;
}

// ============================================================================
// FORM MANAGEMENT
// ============================================================================

function clearKnowledgeForm() {
    if (!confirm('⚠️ Tem certeza que deseja limpar o formulário?\n\nTodos os arquivos e configurações serão perdidos.')) {
        return;
    }
    
    // Limpar arquivos
    selectedFiles = [];
    renderSelectedFiles();
    
    // Reset form fields
    document.getElementById('targetAgent').value = '';
    document.getElementById('knResponsavel').value = '';
    document.getElementById('knAprovador').value = '';
    document.getElementById('knAreas').selectedIndex = -1;
    document.getElementById('knGeografias').selectedIndex = -1;
    document.getElementById('knNivelHierarquico').value = '3';
    document.getElementById('knIdioma').value = 'pt-br';
    document.getElementById('knDataValidade').value = '';
    document.getElementById('knDadoSensivel').checked = false;
    document.getElementById('knApenasSi').checked = false;
    document.getElementById('knProjetos').value = 'N/A';
    
    // Limpar log
    clearLog();
    
    addLog('🔄 Formulário limpo com sucesso.', 'info');
}

function getMetadata() {
    // Obter áreas selecionadas
    const areasSelect = document.getElementById('knAreas');
    const areas = Array.from(areasSelect.selectedOptions).map(opt => opt.value);
    
    // Obter geografias selecionadas
    const geografiasSelect = document.getElementById('knGeografias');
    const geografias = Array.from(geografiasSelect.selectedOptions).map(opt => opt.value);
    
    return {
        fonte_documento: '', // Será preenchido por arquivo
        responsavel: document.getElementById('knResponsavel').value.trim() || 'Sistema',
        aprovador: document.getElementById('knAprovador').value.trim() || 'N/A',
        areas_liberadas: areas.length > 0 ? areas : ['ALL'],
        geografias_liberadas: geografias.length > 0 ? geografias : ['ALL'],
        projetos_liberados: document.getElementById('knProjetos').value.split(',').map(p => p.trim()).filter(p => p),
        nivel_hierarquico_minimo: parseInt(document.getElementById('knNivelHierarquico').value),
        idioma: document.getElementById('knIdioma').value,
        data_validade: document.getElementById('knDataValidade').value || null,
        dado_sensivel: document.getElementById('knDadoSensivel').checked,
        apenas_para_si: document.getElementById('knApenasSi').checked
    };
}

// ============================================================================
// INGESTION
// ============================================================================

async function startIngestion() {
    // Validações
    if (selectedFiles.length === 0) {
        alert('❌ Por favor, selecione pelo menos um arquivo.');
        return;
    }
    
    const targetAgent = document.getElementById('targetAgent').value;
    if (!targetAgent) {
        alert('❌ Por favor, selecione um agente de destino.');
        return;
    }
    
    const responsavel = document.getElementById('knResponsavel').value.trim();
    if (!responsavel) {
        alert('❌ Por favor, preencha o campo Responsável.');
        return;
    }
    
    // Preparar UI
    const startBtn = document.getElementById('startIngestionBtn');
    const statusDiv = document.getElementById('ingestionStatus');
    
    startBtn.disabled = true;
    statusDiv.style.display = 'block';
    clearLog();
    
    addLog('🚀 Iniciando processo de ingestão...', 'info');
    addLog(`📋 Agente destino: ${targetAgent}`, 'info');
    addLog(`📁 Total de arquivos: ${selectedFiles.length}`, 'info');
    
    const metadata = getMetadata();
    let successCount = 0;
    let errorCount = 0;
    
    // Processar cada arquivo
    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        updateStatus(`Processando ${i + 1}/${selectedFiles.length}: ${file.name}`);
        
        addLog(`\n📄 Processando: ${file.name}`, 'info');
        
        try {
            await processFile(file, targetAgent, metadata);
            successCount++;
            addLog(`✅ ${file.name} processado com sucesso!`, 'success');
        } catch (error) {
            errorCount++;
            addLog(`❌ Erro ao processar ${file.name}: ${error.message}`, 'error');
            console.error('Erro detalhado:', error);
        }
    }
    
    // Finalizar
    addLog('\n' + '='.repeat(50), 'info');
    addLog(`✅ Processo concluído!`, 'success');
    addLog(`📊 Sucessos: ${successCount} | Erros: ${errorCount}`, 'info');
    
    startBtn.disabled = false;
    statusDiv.style.display = 'none';
    
    if (successCount > 0) {
        setTimeout(() => {
            if (confirm('✅ Ingestão concluída com sucesso!\n\nDeseja limpar o formulário?')) {
                clearKnowledgeForm();
            }
        }, 500);
    }
}

async function processFile(file, targetAgent, metadata) {
    // Criar FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_table', targetAgent);
    formData.append('metadata', JSON.stringify({
        ...metadata,
        fonte_documento: file.name
    }));
    
    addLog(`  → Enviando arquivo para o servidor...`, 'info');
    
    // Fazer upload
    const response = await fetch('/api/knowledge/ingest', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao processar arquivo');
    }
    
    const result = await response.json();
    
    addLog(`  → Texto extraído: ${result.text_length} caracteres`, 'info');
    addLog(`  → Chunks gerados: ${result.chunks_count}`, 'info');
    addLog(`  → Embeddings criados: ${result.embeddings_count}`, 'info');
    addLog(`  → Inseridos no banco: ${result.inserted_count}`, 'success');
    
    return result;
}

function updateStatus(message) {
    const statusMessage = document.getElementById('statusMessage');
    if (statusMessage) {
        statusMessage.textContent = message;
    }
}

// ============================================================================
// 🔥 CARREGAR AGENTES DINAMICAMENTE NO DROPDOWN
// ============================================================================

async function loadKnowledgeAgents() {
    console.log('📡 Carregando agentes para Base de Conhecimento...');
    
    try {
        const response = await fetch('/api/factory/agents', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) {
            console.error('Erro ao carregar agentes');
            return;
        }
        
        const data = await response.json();
        console.log('📊 Dados recebidos da API:', data);
        
        const dropdown = document.getElementById('targetAgent');
        
        if (!dropdown) {
            console.warn('Dropdown targetAgent não encontrado');
            return;
        }
        
        // Limpar opções existentes (manter apenas o placeholder)
        dropdown.innerHTML = '<option value="">Selecione um agente...</option>';
        
        // Adicionar agentes dinamicamente
        if (data.agents && data.agents.length > 0) {
            console.log(`📋 Processando ${data.agents.length} agentes...`);
            
            let addedCount = 0;
            data.agents.forEach(agent => {
                console.log(`  → Agente: ${agent.name} (tipo: ${agent.type}, tabela: ${agent.table_name})`);
                
                // Apenas subagentes têm tabelas
                if (agent.type === 'subagent' && agent.table_name) {
                    const option = document.createElement('option');
                    option.value = agent.table_name;
                    option.textContent = `${agent.name} (${agent.specialty})`;
                    dropdown.appendChild(option);
                    addedCount++;
                    console.log(`    ✅ Adicionado ao dropdown`);
                } else {
                    console.log(`    ⏭️ Ignorado (tipo: ${agent.type}, tem tabela: ${!!agent.table_name})`);
                }
            });
            
            console.log(`✅ ${addedCount} agentes adicionados ao dropdown`);
        }
        
    } catch (error) {
        console.error('Erro ao carregar agentes:', error);
    }
}

// Expor função globalmente para ser chamada pela Factory
window.loadKnowledgeAgents = loadKnowledgeAgents;

// Carregar agentes ao inicializar
document.addEventListener('DOMContentLoaded', () => {
    loadKnowledgeAgents();
});

console.log('✅ Knowledge.js carregado');
