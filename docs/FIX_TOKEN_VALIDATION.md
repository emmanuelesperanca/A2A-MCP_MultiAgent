# 🔧 Correção: "Not enough segments" - Token JWT Inválido

## 🐛 Problema

### Erro nos Logs
```
WARNING - Erro ao decodificar token: Not enough segments
INFO: 127.0.0.1:61763 - "GET /api/user HTTP/1.1" 401 Unauthorized
INFO: 127.0.0.1:54929 - "GET / HTTP/1.1" 200 OK
INFO: 127.0.0.1:54929 - "GET /login HTTP/1.1" 200 OK
```

### Loop Infinito Observado
```
GET / → GET /login → GET /api/user (401) → GET / → GET /login → ...
```

## 🔍 Causa Raiz

**Problema Principal**: Inconsistência nos nomes das chaves do `localStorage`

| Arquivo | Ação | Chave Usada | Status |
|---------|------|-------------|--------|
| `login.html` | SALVAVA | `neoson_token` | ❌ Errado |
| `index.html` | LIA | `token` | ❌ Errado |

**Resultado**: O index.html nunca encontrava o token (retornava `null` ou token antigo inválido).

**Validação Faltante**: Nenhum dos arquivos validava se o token tinha 3 segmentos (formato JWT: `header.payload.signature`)

## ✅ Soluções Implementadas

### 1. Padronização do Nome da Chave

**ANTES (login.html):**
```javascript
localStorage.setItem('neoson_token', data.token);  // ❌
```

**DEPOIS (login.html):**
```javascript
localStorage.setItem('token', token);  // ✅
```

**ANTES (index.html):**
```javascript
let currentToken = localStorage.getItem('token');  // ✅ Já estava correto
```

### 2. Validação de Token no Login

**ARQUIVO**: `templates/login.html`

**ADICIONADO:**
```javascript
const data = await response.json();

if (response.ok && data.success) {
    // Validar token JWT antes de salvar
    const token = data.token;
    if (!token || token.split('.').length !== 3) {
        showAlert('Token inválido recebido do servidor', 'error');
        setLoading(false);
        return;
    }

    // Salvar token e informações do usuário
    localStorage.setItem('token', token);  // ✅ Nome correto
    // ... resto do código
```

**Verificação ao carregar:**
```javascript
// Verificar se já está logado
const token = localStorage.getItem('token');
if (token && token.split('.').length === 3) {  // ✅ Validação
    window.location.href = '/';
}
```

### 3. Validação de Token no Index

**ARQUIVO**: `templates/index.html`

**ADICIONADO:**
```javascript
// Validar token JWT (deve ter 3 partes: header.payload.signature)
function isValidJWT(token) {
    if (!token) return false;
    const parts = token.split('.');
    return parts.length === 3;
}

// Se não tiver token ou token inválido, redirecionar
if (!currentToken || !isValidJWT(currentToken)) {
    console.warn('Token inválido ou ausente, redirecionando para login...');
    localStorage.removeItem('token');
    window.location.href = '/login';
}
```

**Tratamento de erro melhorado:**
```javascript
.then(res => {
    if (!res.ok) {
        throw new Error('Não autenticado');
    }
    return res.json();
})
.then(data => {
    if (data.username) {
        // ... atualizar UI
    } else {
        throw new Error('Dados do usuário inválidos');
    }
})
.catch((error) => {
    console.error('Erro ao buscar dados do usuário:', error);
    localStorage.removeItem('token');
    window.location.href = '/login';
});
```

### 4. Utilitário de Limpeza

**ARQUIVO**: `static/clear-old-tokens.html`

Criada página HTML para limpar tokens antigos e inválidos:

**Funcionalidades:**
- ✅ Lista todos os tokens no localStorage
- ✅ Remove `neoson_token` (nome antigo)
- ✅ Remove tokens inválidos (sem 3 segmentos)
- ✅ Mantém tokens válidos
- ✅ Redireciona para login após limpeza

**Como Usar:**
```
http://localhost:8000/static/clear-old-tokens.html
```

## 📊 Estrutura do Token JWT

### Formato Correto
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzI5NDY3NDIzfQ.Xq3KdP8jYZH9mN2vL1bR5tC7wF4eS6gA0pQ9xI8uO3k
  ────────────── HEADER ──────────────   ──────────────── PAYLOAD ───────────────   ───────────── SIGNATURE ──────────
```

### Validação
```javascript
const parts = token.split('.');
// parts[0] = header (base64)
// parts[1] = payload (base64)
// parts[2] = signature (base64)

if (parts.length !== 3) {
    // ❌ Token inválido
}
```

### Exemplos de Tokens Inválidos

| Token | Problema | Segmentos |
|-------|----------|-----------|
| `null` | Token vazio | 0 |
| `undefined` | Não definido | 0 |
| `""` | String vazia | 0 |
| `"eyJ..."` | Só header | 1 |
| `"eyJ...eyJ"` | Header + payload | 2 |
| `"a.b.c.d"` | Segmentos extras | 4 |

## 🔄 Fluxo Corrigido

### Primeira Visita (Sem Token)

```
1. Usuário acessa http://localhost:8000/
   ↓
2. index.html carrega
   ↓
3. Verifica localStorage.getItem('token')
   ↓
4. Retorna null → isValidJWT(null) = false
   ↓
5. console.warn('Token inválido ou ausente...')
   ↓
6. localStorage.removeItem('token')  // Segurança
   ↓
7. window.location.href = '/login'  // ✅ Redireciona UMA VEZ
```

### Login Bem-Sucedido

```
1. Usuário preenche formulário
   ↓
2. POST /api/auth/login
   ↓
3. Backend retorna { token: "eyJ...eyJ...abc" }
   ↓
4. Frontend valida: token.split('.').length === 3 ✅
   ↓
5. localStorage.setItem('token', token)  // ✅ Nome correto
   ↓
6. window.location.href = '/'
   ↓
7. index.html verifica token → VÁLIDO ✅
   ↓
8. GET /api/user → 200 OK ✅
   ↓
9. Exibe interface
```

### Token Expirado/Inválido

```
1. index.html carrega
   ↓
2. Token existe mas é inválido (ex: "abc.def")
   ↓
3. isValidJWT("abc.def") → false (só 2 partes)
   ↓
4. localStorage.removeItem('token')
   ↓
5. Redireciona para /login
```

```
1. index.html carrega
   ↓
2. Token válido mas expirado
   ↓
3. isValidJWT(token) → true (3 partes)
   ↓
4. GET /api/user
   ↓
5. Backend: ExpiredSignatureError
   ↓
6. Response: 401 Unauthorized
   ↓
7. Frontend: .catch() → remove token → redireciona
```

## 🧪 Testes

### Teste 1: Limpar Token Antigo

**PowerShell:**
```powershell
# Abrir console do navegador (F12) e executar:
localStorage.setItem('neoson_token', 'old_token_value')
localStorage.setItem('token', 'invalid')
location.reload()
```

**Resultado Esperado:**
- ✅ Console mostra: "Token inválido ou ausente, redirecionando para login..."
- ✅ Redireciona para /login UMA VEZ
- ✅ Sem erros "Not enough segments"

### Teste 2: Token Válido

**PowerShell (simular login):**
```powershell
# No console do navegador:
localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIn0.test')
location.reload()
```

**Resultado Esperado:**
- ✅ isValidJWT retorna true (3 partes)
- ✅ Tenta chamar /api/user
- ⚠️ Pode retornar 401 se assinatura inválida (esperado)

### Teste 3: Fluxo Completo

```
1. Acessar: http://localhost:8000/static/clear-old-tokens.html
2. Clicar em "Limpar Tokens Antigos"
3. Aguardar redirecionamento para /login
4. Fazer login com admin/admin123
5. Verificar que abre index.html sem erros
6. Verificar no console: nenhum "Not enough segments"
```

## 📋 Checklist de Verificação

- [x] Login salva token com chave `token` (não `neoson_token`)
- [x] Login valida token antes de salvar (3 segmentos)
- [x] Index valida token ao carregar (função `isValidJWT()`)
- [x] Index trata erro 401 do /api/user
- [x] Index remove token inválido antes de redirecionar
- [x] Criada página utilitária para limpar tokens antigos
- [x] Documentação completa do problema e solução

## 🎓 Boas Práticas Implementadas

### 1. Validação Client-Side
```javascript
// ✅ Sempre validar estrutura do JWT
if (token.split('.').length !== 3) {
    // Token malformado
}
```

### 2. Consistência de Nomes
```javascript
// ✅ Usar sempre a mesma chave
const TOKEN_KEY = 'token';
localStorage.setItem(TOKEN_KEY, value);
localStorage.getItem(TOKEN_KEY);
```

### 3. Tratamento de Erros Defensivo
```javascript
// ✅ Tratar todos os casos
if (!currentToken || !isValidJWT(currentToken)) {
    // Limpar e redirecionar
}
```

### 4. Logging Informativo
```javascript
// ✅ Ajuda no debug
console.warn('Token inválido ou ausente, redirecionando para login...');
```

### 5. Evitar Loops Infinitos
```javascript
// ✅ Limpar token ANTES de redirecionar
localStorage.removeItem('token');
window.location.href = '/login';  // Só redireciona UMA VEZ
```

## 📁 Arquivos Modificados

| Arquivo | Modificações | Status |
|---------|--------------|--------|
| `templates/login.html` | Mudança de `neoson_token` → `token` + validação | ✅ |
| `templates/index.html` | Função `isValidJWT()` + tratamento de erro | ✅ |
| `static/clear-old-tokens.html` | Nova página utilitária | ✅ |

## 🚀 Como Resolver Agora

### Opção 1: Limpar Manualmente (Console do Navegador)

```javascript
// Abrir DevTools (F12) → Console
localStorage.clear();
location.href = '/login';
```

### Opção 2: Usar Página de Limpeza

```
1. Acessar: http://localhost:8000/static/clear-old-tokens.html
2. Clicar em "Limpar Tokens Antigos"
3. Fazer login novamente
```

### Opção 3: Modo Anônimo

```
1. Abrir navegador em modo anônimo/privado
2. Acessar http://localhost:8000/
3. Fazer login com admin/admin123
```

## ✅ Resultado Esperado

**ANTES:**
```
❌ WARNING: Erro ao decodificar token: Not enough segments (loop infinito)
❌ GET / → GET /login → GET / → GET /login → ...
❌ Aplicação inacessível
```

**DEPOIS:**
```
✅ Token validado corretamente
✅ GET / → GET /login → Login → GET / → GET /api/user (200 OK)
✅ Aplicação funcional
✅ Sem warnings de "Not enough segments"
```

---

**Status**: ✅ Corrigido  
**Data**: 20 de Outubro de 2025  
**Impacto**: Crítico (bloqueava acesso à aplicação)  
**Complexidade**: Média (validação + padronização)  
**Relacionado**: `FIX_JWT_EXCEPTIONS.md`, `FIX_LOOP_REDIRECIONAMENTO.md`
