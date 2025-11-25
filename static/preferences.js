// ============================================================================
// ⚙️ GERENCIAMENTO DE PREFERÊNCIAS DO USUÁRIO
// Arquivo: static/preferences.js
// ============================================================================

const themeOptions = [
    {
        id: 'theme-clearcorrect',
        name: 'ClearCorrect',
        variant: 'dark',
        backgroundImage: "/static/backgrounds/theme-clearcorrect.png",
        palette: {
            '--bg-primary': 'rgba(8,12,20,0.75)',
            '--gradient-bg': 'linear-gradient(180deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3))',
            '--text-primary': '#ffffff',
            '--text-secondary': 'rgba(255,255,255,0.72)',
            '--text-muted': 'rgba(255,255,255,0.55)',
            '--card-bg': 'rgba(10, 10, 20, 0.75)',
            '--card-border': 'rgba(255,255,255,0.08)',
            '--sidebar-border': 'rgba(255,255,255,0.12)',
            '--btn-primary-bg': 'linear-gradient(135deg, #7c3aed, #027d81ff)',
            '--color-primary': '#00b9be',
            '--color-accent': '#5a32c8',
            '--sidebar-glass-bg': 'rgba(0, 185, 190, 0.7)'
        }
    },
    {
        id: 'theme-neodent',
        name: 'Neodent',
        variant: 'dark',
        backgroundImage: "/static/backgrounds/theme-neodent.png",
        palette: {
            '--bg-primary': 'rgba(8,12,20,0.75)',
            '--gradient-bg': 'linear-gradient(180deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3))',
            '--text-primary': '#f4f4f5',
            '--text-secondary': 'rgba(244,244,245,0.78)',
            '--text-muted': 'rgba(244,244,245,0.55)',
            '--card-bg': 'rgba(10, 10, 20, 0.75)',
            '--card-border': 'rgba(255,255,255,0.08)',
            '--sidebar-border': 'rgba(255,255,255,0.12)',
            '--btn-primary-bg': 'linear-gradient(135deg, #5b215e, #ac79b5)',
            '--color-primary': '#843177',
            '--color-accent': '#ac79b5',
            '--sidebar-glass-bg': 'rgba(132, 49, 119, 0.78)'
        }
    },
    {
        id: 'theme-straumann',
        name: 'Straumann',
        variant: 'dark',
        backgroundImage: "/static/backgrounds/theme-straumann.png",
        palette: {
            '--bg-primary': 'rgba(8,12,20,0.75)',
            '--gradient-bg': 'linear-gradient(180deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3))',
            '--text-primary': '#ecfeff',
            '--text-secondary': 'rgba(236,254,255,0.8)',
            '--text-muted': 'rgba(236,254,255,0.55)',
            '--card-bg': 'rgba(4,20,32,0.8)',
            '--card-border': 'rgba(236,254,255,0.08)',
            '--sidebar-border': 'rgba(236,254,255,0.12)',
            '--btn-primary-bg': 'linear-gradient(135deg, #2d7662, #14b8a6)',
            '--color-primary': '#46b98c',
            '--color-accent': '#78050c',
            '--sidebar-glass-bg': 'rgba(54, 57, 58, 0.78)'
        }
    },
    {
        id: 'theme-straumann-group',
        name: 'Straumann Group',
        variant: 'dark',
        backgroundImage: "/static/backgrounds/theme-straumann_group.png",
        palette: {
            '--bg-primary': 'rgba(8,12,20,0.75)',
            '--gradient-bg': 'linear-gradient(180deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3))',
            '--text-primary': '#ffffffff',
            '--text-secondary': 'rgba(223, 248, 255, 0.94)',
            '--text-muted': 'rgba(255, 255, 255, 1)',
            '--card-bg': 'rgba(10, 10, 20, 0.75)',
            '--card-border': 'rgba(59,32,19,0.1)',
            '--sidebar-border': 'rgba(59,32,19,0.15)',
            '--btn-primary-bg': 'linear-gradient(135deg, #b98c3c, #195afa)',
            '--color-primary': '#195afa',
            '--color-accent': '#b98c3c',
            '--sidebar-glass-bg': 'rgba(25, 90, 250, 0.85)'
        }
    },
    {
        id: 'theme-midnight',
        name: 'Midnight Circuit',
        variant: 'dark',
        backgroundImage: "/static/backgrounds/theme-midnight.jpg",
        palette: {
            '--bg-primary': '#030712',
            '--gradient-bg': 'linear-gradient(160deg,rgba(132, 49, 119, 0.78),rgba(0, 185, 190, 0.7))',
            '--text-primary': '#f9fafb',
            '--text-secondary': 'rgba(249,250,251,0.78)',
            '--text-muted': 'rgba(249,250,251,0.55)',
            '--card-bg': 'rgba(8,12,20,0.85)',
            '--card-border': 'rgba(249,250,251,0.08)',
            '--sidebar-border': 'rgba(249,250,251,0.12)',
            '--btn-primary-bg': 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            '--color-primary': '#6366f1',
            '--color-accent': '#a855f7',
            '--sidebar-glass-bg': 'rgba(6, 10, 20, 0.82)'
        }
    },
    {
        id: 'theme-oneplan',
        name: 'One Plan',
        variant: 'dark',
        backgroundImage: "/static/backgrounds/theme-oneplan.png",
        palette: {
            '--bg-primary': 'rgba(8,12,20,0.75)',
            '--gradient-bg': 'linear-gradient(180deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3))',
            '--text-primary': '#ffffffff',
            '--text-secondary': 'rgba(255, 255, 255, 0.7)',
            '--text-muted': 'rgba(255, 255, 255, 0.5)',
            '--card-bg': 'rgba(8,12,20,0.85)',
            '--card-border': 'rgba(249,250,251,0.08)',
            '--sidebar-border': 'rgba(249,250,251,0.12)',
            '--btn-primary-bg': 'linear-gradient(135deg, #843177, #696B9D, #47AD8A, #00b9be)',
            '--color-primary': '#ffffffff',
            '--color-accent': '#195afa',
            '--sidebar-glass-bg': 'rgba(6, 10, 20, 0.82)'        }
    }
];

const defaultThemeId = themeOptions[0].id;
const defaultPreferences = {
    username: 'Usuário',
    fullName: 'Nome Completo',
    email: 'usuario@empresa.com',
    role: 'admin',
    cargo: 'Gerente',
    area: 'Tecnologia da Informação',
    departamento: 'Desenvolvimento',
    pais: 'Brasil',
    projetos: 'Neoson AI, Portal Corporativo',
    themeBackground: defaultThemeId,
    themeVariant: themeOptions[0].variant
};

let currentThemeId = defaultThemeId;

function getThemeById(themeId) {
    return themeOptions.find(theme => theme.id === themeId) || themeOptions[0];
}

function selectThemeCard(themeId) {
    document.querySelectorAll('.theme-card').forEach((card) => {
        const isActive = card.dataset.themeId === themeId;
        card.classList.toggle('active', isActive);
        const radio = card.querySelector('input[type="radio"]');
        if (radio) {
            radio.checked = isActive;
        }
    });
}

function applyTheme(themeId) {
    const theme = getThemeById(themeId);
    currentThemeId = theme.id;

    Object.entries(theme.palette).forEach(([token, value]) => {
        document.documentElement.style.setProperty(token, value);
    });

    const backgroundValue = theme.backgroundImage ? `url('${theme.backgroundImage}')` : 'none';
    document.documentElement.style.setProperty('--theme-background-image', backgroundValue);
    document.body.setAttribute('data-theme-variant', theme.variant);
    selectThemeCard(theme.id);
}

function initThemeSelector() {
    const inputs = document.querySelectorAll('input[name="themeBackground"]');
    if (!inputs.length) return;

    inputs.forEach((input) => {
        input.addEventListener('change', () => {
            if (input.checked) {
                applyTheme(input.value);
            }
        });
    });
}

/**
 * Carrega as preferências do localStorage e preenche o formulário
 */
function loadPreferences() {
    const saved = localStorage.getItem('userPreferences');
    let prefs;
    try {
        prefs = saved ? { ...defaultPreferences, ...JSON.parse(saved) } : { ...defaultPreferences };
    } catch (error) {
        console.warn('⚠️ Preferências inválidas no storage, usando padrão.', error);
        prefs = { ...defaultPreferences };
    }
    
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

    applyTheme(prefs.themeBackground || defaultPreferences.themeBackground);
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
        projetos: document.getElementById('prefProjetos').value.trim() || 'Neoson AI',
        themeBackground: currentThemeId || defaultPreferences.themeBackground,
        themeVariant: getThemeById(currentThemeId || defaultThemeId).variant
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
        applyTheme(defaultPreferences.themeBackground);
        
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
    initThemeSelector();

    const saved = localStorage.getItem('userPreferences');
    let prefs;
    try {
        prefs = saved ? { ...defaultPreferences, ...JSON.parse(saved) } : { ...defaultPreferences };
    } catch (error) {
        console.error('❌ Erro ao carregar preferências:', error);
        prefs = { ...defaultPreferences };
    }

    currentThemeId = prefs.themeBackground || defaultPreferences.themeBackground;
    applyTheme(currentThemeId);
    updateUserProfile(prefs);

    console.log(saved ? '✅ Preferências carregadas do localStorage' : 'ℹ️ Nenhuma preferência salva, usando valores padrão');
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
