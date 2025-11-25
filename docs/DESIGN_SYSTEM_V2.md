# 🎨 Neoson Design System V2.0

## Visão Geral

O novo design do Neoson foi inspirado no estilo clean e moderno do "Mês do Sorriso - Neodent", trazendo uma estética premium com cards flutuantes, bordas brancas e um visual minimalista.

## 🌈 Paleta de Cores

### Cores Principais
- **Primary**: `#75246a` (Roxo profundo)
- **Secondary**: `#47ad8a` (Verde-azulado/Teal)
- **Accent**: `#833178` (Roxo médio)

### Background
```css
background: linear-gradient(90deg, #75246a 0%, #47ad8a 100%);
```
- Gradiente de 90° (horizontal)
- Do roxo (#75246a) ao teal (#47ad8a)
- Background fixo para efeito parallax

## 📦 Componentes

### Cards
```css
background: rgba(255, 255, 255, 0);      /* Transparente */
border: 1px solid rgba(255, 255, 255, 1); /* Borda branca sólida */
border-radius: 15px;
padding: 30px;
backdrop-filter: blur(0px);               /* Sem blur */
```

**Características:**
- Fundo completamente transparente
- Bordas brancas sólidas (1px)
- Bordas arredondadas (15px)
- Sem backdrop blur
- Animação de entrada suave

### Títulos de Cards
```css
display: inline-block;
background: white;
color: #833178;                           /* Roxo */
padding: 10px 25px;
border-radius: 50px;                      /* Pill shape */
transform: translateY(-50px);             /* Flutuante */
font-weight: bold;
```

**Estilo "Pill":**
- Fundo branco
- Texto roxo (#833178)
- Bordas arredondadas extremas (50px)
- Posicionamento flutuante (-50px)
- Uppercase automático

### Botões
```css
background: white;
color: #833178;
border: none;
padding: 15px 30px;
border-radius: 8px;
font-weight: 600;
text-transform: uppercase;
letter-spacing: 1px;
```

**Hover Effect:**
```css
transform: translateY(-2px);
box-shadow: 0 5px 15px rgba(138, 43, 226, 0.4);
```

**Características:**
- Fundo branco
- Texto roxo
- Sem bordas
- Uppercase com espaçamento
- Animação de elevação no hover
- Sombra roxa no hover

### Inputs e Textareas
```css
background: rgba(255, 255, 255, 0.1);     /* 10% opacidade */
border: 1px solid rgba(255, 255, 255, 0.3);
color: white;
border-radius: 8px;
padding: 12px 15px;
```

**Placeholder:**
```css
color: rgba(255, 255, 255, 0.6);          /* 60% opacidade */
```

**Focus State:**
```css
border-color: rgba(255, 255, 255, 0.6);
background: rgba(255, 255, 255, 0.15);    /* Aumenta opacidade */
```

### Abas de Navegação
```css
/* Estado Inativo */
background: rgba(255, 255, 255, 0.1);
border: 1px solid rgba(255, 255, 255, 0.3);
color: white;

/* Estado Ativo */
background: white;
color: #833178;
border-color: white;
```

### Área de Upload
```css
border: 2px dashed rgba(255, 255, 255, 0.3);
border-radius: 10px;
padding: 40px;
background: transparent;
```

**Estados:**
- **Hover**: Borda roxa (#8A2BE2) com fundo roxo transparente
- **Has File**: Borda verde (#00FF7F) com fundo verde transparente

## 🎭 Opacidades e Transparências

| Elemento | Opacidade | Hex/RGBA |
|----------|-----------|----------|
| Input Background | 10% | `rgba(255, 255, 255, 0.1)` |
| Input Border | 30% | `rgba(255, 255, 255, 0.3)` |
| Placeholder Text | 60% | `rgba(255, 255, 255, 0.6)` |
| Card Background | 0% | `rgba(255, 255, 255, 0)` |
| Card Border | 100% | `rgba(255, 255, 255, 1)` |

## 📱 Responsividade

### Breakpoint: 768px

**Cards:**
```css
padding: 20px;                            /* Reduz de 30px */
margin-bottom: 20px;
```

**Títulos:**
```css
font-size: 1rem;                          /* Reduz de 1.2rem */
padding: 8px 20px;                        /* Reduz de 10px 25px */
transform: translateY(-35px);             /* Menos flutuante */
```

**Botões:**
```css
padding: 12px 20px;                       /* Reduz de 15px 30px */
font-size: 0.9rem;                        /* Reduz de 1rem */
```

## 🎬 Animações

### Slide In (Cards)
```css
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Spinner (Loading)
```css
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

## 🎯 Sistema de Steps

```css
.step {
    opacity: 0.5;                         /* Inativo */
}

.step.active {
    opacity: 1;                           /* Ativo */
}
```

## 🖱️ Scrollbar Customizada

```css
::-webkit-scrollbar {
    width: 12px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: rgba(131, 49, 120, 0.6); /* Roxo */
    border-radius: 10px;
}
```

## 📝 Tipografia

### Cores de Texto
- **Primário**: `#ffffff` (Branco)
- **Secundário**: `rgba(255, 255, 255, 0.85)` (Branco 85%)
- **Discreto**: `rgba(255, 255, 255, 0.65)` (Branco 65%)
- **Em Botões**: `#75246a` (Roxo)

### Estilos de Fonte
- **Fonte Principal**: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- **Peso Normal**: 400
- **Peso Médio**: 500
- **Peso Bold**: 600-700

## 🔧 Como Usar

### Estrutura de Arquivos
```
static/
├── style_neoson.css         # CSS base com variáveis
└── theme_overrides.css      # Novo design (aplica overrides)
```

### Ordem de Importação no HTML
```html
<link rel="stylesheet" href="/static/style_neoson.css">
<link rel="stylesheet" href="/static/theme_overrides.css">
```

⚠️ **IMPORTANTE**: `theme_overrides.css` deve ser carregado **DEPOIS** do `style_neoson.css` para os overrides funcionarem corretamente.

## 🎨 Customização Rápida

Para alterar as cores, edite as variáveis CSS no arquivo `style_neoson.css`:

```css
:root {
    --color-primary: #75246a;
    --color-secondary: #47ad8a;
    --gradient-background: linear-gradient(90deg, #75246a 0%, #47ad8a 100%);
}
```

## ✅ Checklist de Implementação

- [x] Background com gradiente 90° (roxo → teal)
- [x] Cards transparentes com bordas brancas
- [x] Títulos no estilo "pill" branco com texto roxo
- [x] Botões brancos com texto roxo
- [x] Inputs com opacidade 0.1
- [x] Todos os textos em branco
- [x] Abas com estados ativos/inativos
- [x] Animações suaves
- [x] Responsividade mobile
- [x] Scrollbar customizada
- [x] Sistema de steps com opacidade

## 🚀 Próximos Passos

1. Testar no navegador
2. Verificar contraste de cores (acessibilidade)
3. Ajustar mobile se necessário
4. Documentar componentes adicionais

---

**Versão**: 2.0  
**Data**: Outubro 2025  
**Autor**: Neoson AI Team  
**Inspiração**: Mês do Sorriso - Neodent
