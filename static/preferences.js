// ============================================================================
// ⚙️ GERENCIAMENTO DE PREFERÊNCIAS DO USUÁRIO
// Arquivo: static/preferences.js
// ============================================================================

// Valores padrão para desenvolvimento
const defaultPreferences = {
    username: 'Usuário',
    fullName: 'Nome Completo',
    email: 'usuario@empresa.com',
    role: 'admin',
    cargo: 'Gerente',
    area: 'Tecnologia da Informação',
    departamento: 'Desenvolvimento',
    pais: 'Brasil',
    projetos: 'Neoson AI, Portal Corporativo'
};

/**
 * Carrega as preferências do localStorage e preenche o formulário
 */
function loadPreferences() {
    const saved = localStorage.getItem('userPreferences');
    const prefs = saved ? JSON.parse(saved) : defaultPreferences;
    
    // Preencher campos do formulário
    const fields = {
        'prefUsername': prefs.username,
        'prefFullName': prefs.fullName,
        'prefEmail': prefs.email,
        'prefRole': prefs.role,
        'prefCargo': prefs.cargo,
        'prefArea': prefs.area,
        'prefDepartamento': prefs.departamento,
        'prefPais': prefs.pais,
        'prefProjetos': prefs.projetos
    };
    
    for (const [id, value] of Object.entries(fields)) {
        const element = document.getElementById(id);
        if (element) element.value = value || '';
    }
}

/**
 * Salva as preferências no localStorage e atualiza a UI
 */
function savePreferences() {
    // Coletar dados do formulário
    const prefs = {
        username: document.getElementById('prefUsername').value.trim() || 'Usuário',
        fullName: document.getElementById('prefFullName').value.trim() || 'Nome Completo',
        email: document.getElementById('prefEmail').value.trim() || 'usuario@empresa.com',
        role: document.getElementById('prefRole').value || 'admin',
        cargo: document.getElementById('prefCargo').value.trim() || 'Gerente',
        area: document.getElementById('prefArea').value.trim() || 'TI',
        departamento: document.getElementById('prefDepartamento').value.trim() || 'Desenvolvimento',
        pais: document.getElementById('prefPais').value || 'Brasil',
        projetos: document.getElementById('prefProjetos').value.trim() || 'Neoson AI'
    };
    
    // Validação básica
    if (!prefs.username || !prefs.email) {
        alert('❌ Por favor, preencha pelo menos o Nome de Usuário e E-mail.');
        return;
    }
    
    // Salvar no localStorage
    localStorage.setItem('userPreferences', JSON.stringify(prefs));
    
    // Atualizar UI imediatamente
    updateUserProfile(prefs);
    
    // Feedback visual
    showSaveNotification();
    
    console.log('✅ Preferências salvas:', prefs);
}

/**
 * Restaura os valores padrão
 */
function resetPreferences() {
    if (confirm('⚠️ Tem certeza que deseja restaurar os valores padrão?\n\nIsso irá apagar todas as suas personalizações.')) {
        // Remover do localStorage
        localStorage.removeItem('userPreferences');
        
        // Recarregar formulário com padrões
        loadPreferences();
        
        // Atualizar UI com valores padrão
        updateUserProfile(defaultPreferences);
        
        alert('✅ Preferências restauradas com sucesso!');
        console.log('🔄 Preferências resetadas para valores padrão');
    }
}

/**
 * Atualiza todos os elementos da UI com as preferências
 * @param {Object} prefs - Objeto com as preferências do usuário
 */
function updateUserProfile(prefs) {
    // Avatar (primeira letra do username)
    const avatar = prefs.username.charAt(0).toUpperCase();
    
    // Atualizar sidebar
    const sidebarElements = {
        'userName': prefs.username,
        'userRole': prefs.role,
        'userAvatarSidebar': avatar
    };
    
    for (const [id, value] of Object.entries(sidebarElements)) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }
    
    // Atualizar dropdown
    const dropdownElements = {
        'dropdownUserName': prefs.fullName || prefs.username,
        'dropdownUserEmail': prefs.email,
        'userAvatarDropdown': avatar
    };
    
    for (const [id, value] of Object.entries(dropdownElements)) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }
    
    // Atualizar informações detalhadas do perfil
    const profileSpans = {
        '#dropdownCargo span': prefs.cargo,
        '#dropdownArea span': prefs.area,
        '#dropdownPais span': prefs.pais,
        '#dropdownDepartamento span': prefs.departamento,
        '#dropdownProjetos span': prefs.projetos
    };
    
    for (const [selector, value] of Object.entries(profileSpans)) {
        const element = document.querySelector(selector);
        if (element) element.textContent = value;
    }
    
    console.log('🔄 UI atualizada com preferências:', prefs);
}

/**
 * Mostra notificação de sucesso ao salvar
 */
function showSaveNotification() {
    // Criar elemento de notificação
    const notification = document.createElement('div');
    notification.className = 'save-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(90deg, #75246a 0%, #47ad8a 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        font-weight: 600;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 12px;
        animation: slideInFromRight 0.3s ease;
    `;
    
    notification.innerHTML = `
        <i class="fas fa-check-circle" style="font-size: 20px;"></i>
        <span>Preferências salvas com sucesso!</span>
    `;
    
    document.body.appendChild(notification);
    
    // Animar saída e remover após 3 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOutToRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

/**
 * Carrega preferências salvas ao iniciar a aplicação
 */
window.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando sistema de preferências...');
    
    // Verificar se há preferências salvas
    const saved = localStorage.getItem('userPreferences');
    
    if (saved) {
        try {
            const prefs = JSON.parse(saved);
            updateUserProfile(prefs);
            console.log('✅ Preferências carregadas do localStorage');
        } catch (error) {
            console.error('❌ Erro ao carregar preferências:', error);
            // Em caso de erro, usar valores padrão
            updateUserProfile(defaultPreferences);
        }
    } else {
        // Primeira vez: usar valores padrão
        console.log('ℹ️ Nenhuma preferência salva, usando valores padrão');
        updateUserProfile(defaultPreferences);
    }
});

// Adicionar animações CSS dinamicamente
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInFromRight {
        from {
            opacity: 0;
            transform: translateX(100px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutToRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100px);
        }
    }
`;
document.head.appendChild(style);

console.log('✅ Sistema de preferências carregado');
