# 🧪 Guia de Teste Rápido - Correção de Token

## 🎯 Objetivo
Validar que as correções de validação de token JWT eliminaram o erro "Not enough segments" e o loop de redirecionamento.

## ⚡ Teste Rápido (2 minutos)

### 1. Limpar Estado Anterior
**Navegador: Console (F12)**
```javascript
// Executar no console:
localStorage.clear();
console.log('✅ localStorage limpo!');
```

**OU usar página de limpeza:**
```
http://localhost:8000/static/clear-old-tokens.html
```

### 2. Testar Fluxo de Login

**Passo a Passo:**
```
1. Acessar: http://localhost:8000/
2. Deve redirecionar AUTOMATICAMENTE para /login (SEM loop)
3. Fazer login:
   - Usuário: admin
   - Senha: admin123
   - Tipo: Admin
4. Clicar em "Entrar"
5. Deve redirecionar para / e mostrar interface
```

### 3. Verificar Logs do Servidor

**Resultado ESPERADO (✅ BOM):**
```
INFO: 127.0.0.1:xxxxx - "GET / HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "GET /login HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "POST /api/auth/login HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "GET / HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "GET /api/user HTTP/1.1" 200 OK
```

**Resultado RUIM (❌ SE APARECER ISSO, ALGO DEU ERRADO):**
```
WARNING - Erro ao decodificar token: Not enough segments
INFO: 127.0.0.1:xxxxx - "GET /api/user HTTP/1.1" 401 Unauthorized
INFO: 127.0.0.1:xxxxx - "GET / HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "GET /login HTTP/1.1" 200 OK
[repetindo infinitamente...]
```

### 4. Verificar Console do Navegador

**Resultado ESPERADO (✅ BOM):**
```
[Nenhum erro]
[Nenhum warning sobre token]
```

**OU (primeira visita sem token):**
```
⚠️ Token inválido ou ausente, redirecionando para login...
```

**Resultado RUIM (❌ NÃO DEVE APARECER):**
```
❌ Erro ao buscar dados do usuário: ...
❌ Not enough segments
```

## 🔬 Teste Avançado (5 minutos)

### Teste 1: Token Inválido (Menos de 3 Segmentos)

**Console do navegador:**
```javascript
localStorage.setItem('token', 'apenas.dois');
location.reload();
```

**Resultado esperado:**
- ✅ Console: "Token inválido ou ausente, redirecionando para login..."
- ✅ Redireciona para /login
- ✅ SEM erros "Not enough segments" no servidor

### Teste 2: Token Vazio

**Console do navegador:**
```javascript
localStorage.setItem('token', '');
location.reload();
```

**Resultado esperado:**
- ✅ Console: "Token inválido ou ausente, redirecionando para login..."
- ✅ Redireciona para /login

### Teste 3: Token com 4 Segmentos (Malformado)

**Console do navegador:**
```javascript
localStorage.setItem('token', 'a.b.c.d');
location.reload();
```

**Resultado esperado:**
- ✅ Console: "Token inválido ou ausente, redirecionando para login..."
- ✅ Redireciona para /login

### Teste 4: Token com Nome Antigo

**Console do navegador:**
```javascript
localStorage.setItem('neoson_token', 'eyJ.eyJ.abc');
location.reload();
```

**Resultado esperado:**
- ✅ Ignora token antigo (não é lido)
- ✅ Console: "Token inválido ou ausente, redirecionando para login..."
- ✅ Redireciona para /login

### Teste 5: Login e Persistência

**Passo a Passo:**
```
1. Fazer login com admin/admin123
2. Abrir Console (F12)
3. Verificar: localStorage.getItem('token')
4. Deve retornar string com 3 partes separadas por "."
5. Recarregar página (F5)
6. Deve permanecer logado (não redireciona para login)
```

**Verificação:**
```javascript
// Console do navegador:
const token = localStorage.getItem('token');
console.log('Token:', token);
console.log('Partes:', token ? token.split('.').length : 0);
console.log('Válido:', token && token.split('.').length === 3);
```

**Resultado esperado:**
```
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzI5NDY3NDIzfQ.Xq3KdP8...
Partes: 3
Válido: true
```

## 📊 Checklist de Validação

### Checklist Mínimo (Obrigatório)
- [ ] Acesso a / redireciona para /login (sem token)
- [ ] Login com admin/admin123 funciona
- [ ] Após login, abre interface principal
- [ ] SEM erros "Not enough segments" nos logs do servidor
- [ ] SEM loop infinito de redirecionamento

### Checklist Completo (Recomendado)
- [ ] Token inválido (2 partes) é rejeitado
- [ ] Token vazio é rejeitado
- [ ] Token com nome antigo (neoson_token) é ignorado
- [ ] Token válido persiste após reload (F5)
- [ ] Logout remove token e redireciona
- [ ] Console do navegador SEM erros
- [ ] Página de limpeza funciona corretamente

## 🐛 Troubleshooting

### Problema: Ainda vejo "Not enough segments"

**Solução:**
```javascript
// Console do navegador:
localStorage.clear();
location.href = '/login';
```

### Problema: Loop infinito de redirecionamento

**Verificar:**
1. Abrir DevTools → Application → Local Storage
2. Verificar valor da chave `token`
3. Se tiver menos de 3 partes, limpar:
```javascript
localStorage.removeItem('token');
location.reload();
```

### Problema: Login não funciona

**Verificar servidor:**
```powershell
# Verificar se FastAPI está rodando
# Deve mostrar:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Verificar credenciais:**
```
Usuário: admin
Senha: admin123
Tipo: Admin
```

### Problema: Token existe mas /api/user retorna 401

**Possíveis causas:**
1. Token expirado (8 horas após login)
2. Assinatura inválida (chave SECRET_KEY mudou)
3. Token malformado

**Solução:**
```javascript
// Fazer novo login:
localStorage.removeItem('token');
location.href = '/login';
```

## 📱 Teste em Diferentes Navegadores

### Chrome/Edge
```
1. Modo normal: Teste completo
2. Modo anônimo: Teste sem cache
3. DevTools → Application → Clear storage
```

### Firefox
```
1. Modo normal: Teste completo
2. Modo privado: Teste sem cache
3. DevTools → Storage → Clear All
```

## ✅ Critérios de Sucesso

### Funcionamento Correto
1. ✅ Login funciona e retorna token válido (3 partes)
2. ✅ Token é salvo como `token` (não `neoson_token`)
3. ✅ Token inválido é rejeitado ANTES de chamar /api/user
4. ✅ SEM erros "Not enough segments" no servidor
5. ✅ SEM loop infinito de redirecionamento
6. ✅ Console do navegador limpo (sem erros)
7. ✅ Interface principal carrega após login
8. ✅ Dados do usuário aparecem no sidebar

### Performance
- ⚡ Redirecionamento: < 500ms
- ⚡ Login: < 2s
- ⚡ Carregamento interface: < 1s

## 🎓 Entendendo os Logs

### Fluxo Normal (Primeira Visita)
```
INFO: GET / HTTP/1.1" 200 OK              # Página inicial
INFO: GET /login HTTP/1.1" 200 OK          # Redireciona login
INFO: POST /api/auth/login HTTP/1.1" 200   # Faz login
INFO: GET / HTTP/1.1" 200 OK               # Volta para home
INFO: GET /api/user HTTP/1.1" 200 OK       # Busca dados usuário ✅
```

### Fluxo com Token Inválido (ANTES DA CORREÇÃO)
```
INFO: GET / HTTP/1.1" 200 OK
INFO: GET /login HTTP/1.1" 200 OK
WARNING: Erro ao decodificar token: Not enough segments  # ❌ ERRO
INFO: GET /api/user HTTP/1.1" 401          # ❌ Falha
INFO: GET / HTTP/1.1" 200 OK               # Loop infinito
INFO: GET /login HTTP/1.1" 200 OK
[repetindo infinitamente...]
```

### Fluxo com Token Inválido (DEPOIS DA CORREÇÃO)
```
INFO: GET / HTTP/1.1" 200 OK               # Página inicial
INFO: GET /login HTTP/1.1" 200 OK          # Redireciona (token inválido detectado no frontend)
[SEM chamada para /api/user]               # ✅ Não tenta chamar API
[SEM loop]                                 # ✅ Para aqui
```

## 🚀 Próximos Passos (Se Tudo Funcionar)

1. ✅ Implementar endpoint `/api/chat`
2. ✅ Adicionar suporte a markdown nas mensagens
3. ✅ Implementar upload de arquivos
4. ✅ Criar abas de navegação (Agentes, Logs, etc)

---

**Tempo Estimado**: 2-5 minutos  
**Dificuldade**: Fácil  
**Pré-requisito**: FastAPI rodando em http://localhost:8000  
**Resultado**: Autenticação funcionando 100% sem erros
