# 👤 Dropdown de Perfil do Usuário

## ✨ Funcionalidade Implementada

Ao clicar no perfil do usuário na sidebar, um dropdown elegante é exibido com:
- ✅ Informações completas do usuário
- ✅ Cargo, Área, País, Departamento, Projetos
- ✅ Botão de Logout destacado
- ✅ Design moderno com glassmorphism

## 🎨 Design

### Estilo Visual
- **Card flutuante** com backdrop blur
- **Gradiente sutil** no avatar
- **Ícones** para cada informação
- **Animação suave** ao abrir/fechar
- **Botão de logout vermelho** para destaque

### Responsividade
- Posiciona-se acima do perfil na sidebar
- Adapta-se quando sidebar está colapsada
- Fecha automaticamente ao clicar fora

## 📋 Estrutura

### HTML
```html
<div class="sidebar-footer">
    <!-- Perfil clicável -->
    <div class="user-profile" id="userProfile">
        <div class="user-avatar">U</div>
        <div class="user-info">...</div>
    </div>
    
    <!-- Dropdown -->
    <div class="user-profile-dropdown" id="userDropdown">
        <div class="dropdown-header">
            <!-- Avatar + Nome + Email -->
        </div>
        <div class="dropdown-body">
            <!-- Cargo, Área, País, etc -->
        </div>
        <div class="dropdown-footer">
            <!-- Botão Logout -->
        </div>
    </div>
</div>
```

### CSS Classes

| Classe | Função |
|--------|--------|
| `.user-profile-dropdown` | Container principal do dropdown |
| `.user-profile-dropdown.active` | Estado aberto |
| `.dropdown-header` | Cabeçalho com avatar e nome |
| `.dropdown-body` | Corpo com informações |
| `.profile-info-group` | Grupo de informação (label + value) |
| `.dropdown-logout-btn` | Botão de logout |

### JavaScript

**Toggle Dropdown:**
```javascript
userProfile.addEventListener('click', (e) => {
    e.stopPropagation();
    userDropdown.classList.toggle('active');
});
```

**Fechar ao clicar fora:**
```javascript
document.addEventListener('click', (e) => {
    if (!userDropdown.contains(e.target) && !userProfile.contains(e.target)) {
        userDropdown.classList.remove('active');
    }
});
```

**Logout:**
```javascript
dropdownLogoutBtn.addEventListener('click', () => {
    if (confirm('Deseja sair da sua conta?')) {
        localStorage.removeItem('token');
        window.location.href = '/login';
    }
});
```

## 📊 Informações Exibidas

### Dados do Usuário
1. **Nome Completo** - Do token JWT
2. **Email** - Gerado: `{username}@empresa.com`
3. **Cargo** - Admin: "Gerente de TI" | User: "Analista"
4. **Área** - Tecnologia da Informação
5. **País** - Brasil
6. **Departamento** - Admin: "Desenvolvimento & Inovação" | User: "Suporte"
7. **Projetos** - "Neoson AI, Automações Corporativas"

### Dados Dinâmicos vs Estáticos

| Campo | Tipo | Fonte |
|-------|------|-------|
| Nome | Dinâmico | API `/api/user` |
| Email | Dinâmico | Gerado do username |
| Avatar | Dinâmico | Primeira letra do username |
| Cargo | Semi-dinâmico | Baseado no role |
| Área | Estático | Hardcoded |
| País | Estático | Hardcoded |
| Departamento | Semi-dinâmico | Baseado no role |
| Projetos | Estático | Hardcoded |

## 🔮 Melhorias Futuras

### Fase 1: Dados Reais do Backend
```javascript
// Expandir /api/user para retornar mais campos
{
    "username": "admin",
    "full_name": "Emmanuel Silva",
    "email": "emmanuel.silva@empresa.com",
    "role": "admin",
    "cargo": "Gerente de TI",
    "area": "Tecnologia",
    "pais": "Brasil",
    "departamento": "Desenvolvimento",
    "projetos": ["Neoson AI", "Portal Corporativo"]
}
```

### Fase 2: Edição de Perfil
- Modal para editar informações
- Upload de avatar
- Alterar senha
- Preferências (tema, idioma)

### Fase 3: Estatísticas
- Total de conversas
- Tempo de uso
- Agentes mais utilizados
- Gráfico de atividade

## 🎯 Como Usar

### 1. Abrir Dropdown
```
Clique no perfil (parte inferior da sidebar)
```

### 2. Visualizar Informações
```
- Avatar grande
- Nome completo
- Email
- Cargo, Área, País, Departamento, Projetos
```

### 3. Fazer Logout
```
Clique em "Sair da Conta"
Confirme no dialog
→ Token removido
→ Redireciona para /login
```

### 4. Fechar Dropdown
```
Opção 1: Clique novamente no perfil
Opção 2: Clique em qualquer lugar fora do dropdown
```

## 🎨 Customização

### Alterar Cores do Botão Logout
```css
.dropdown-logout-btn {
    background: rgba(244, 67, 54, 0.1);  /* Fundo vermelho suave */
    color: #f44336;                       /* Texto vermelho */
    border: 1px solid rgba(244, 67, 54, 0.3);
}

.dropdown-logout-btn:hover {
    background: rgba(244, 67, 54, 0.2);  /* Mais intenso no hover */
    border-color: rgba(244, 67, 54, 0.5);
}
```

### Adicionar Mais Campos
```html
<div class="profile-info-group">
    <div class="profile-info-label">Seu Campo</div>
    <div class="profile-info-value" id="dropdownSeuCampo">
        <i class="fas fa-seu-icone"></i>
        <span>Valor do Campo</span>
    </div>
</div>
```

### Posição do Dropdown
```css
.user-profile-dropdown {
    bottom: 80px;  /* Distância do fundo */
    left: 10px;    /* Margem esquerda */
    right: 10px;   /* Margem direita */
}
```

## 🐛 Troubleshooting

### Dropdown não abre
**Verificar:**
1. ID `userProfile` existe no HTML
2. ID `userDropdown` existe no HTML
3. JavaScript foi carregado
4. Console do navegador sem erros

### Dropdown não fecha ao clicar fora
**Verificar:**
1. Event listener do document está registrado
2. `e.stopPropagation()` no clique do perfil

### Informações não aparecem
**Verificar:**
1. `/api/user` retorna 200 OK
2. IDs dos elementos estão corretos
3. `data.username` existe na resposta

## 📱 Comportamento Mobile (Futuro)

```css
@media (max-width: 768px) {
    .user-profile-dropdown {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        border-radius: 12px 12px 0 0;
        max-height: 80vh;
        overflow-y: auto;
    }
}
```

## ✅ Checklist de Implementação

- [x] CSS do dropdown adicionado
- [x] HTML do dropdown criado
- [x] JavaScript toggle implementado
- [x] Fechar ao clicar fora
- [x] Botão de logout funcional
- [x] Dados do usuário integrados
- [x] Avatar atualizado
- [x] Animações suaves
- [x] Responsivo com sidebar colapsada
- [x] Documentação criada

---

**Status**: ✅ Implementado  
**Data**: 20 de Outubro de 2025  
**Arquivo**: `templates/index.html`  
**Linhas Adicionadas**: ~200  
**Complexidade**: Média  
**Teste**: Clicar no perfil na sidebar
