# 🔧 Correção de Exceções JWT - PyJWT 2.x

## 🐛 Problema

### Erro Completo
```
AttributeError: module 'jwt' has no attribute 'JWTError'. Did you mean: 'PyJWTError'?
```

### Traceback Relevante
```python
File "app_fastapi.py", line 386, in verify_token
    except jwt.JWTError:
           ^^^^^^^^^^^^
AttributeError: module 'jwt' has no attribute 'JWTError'
```

### Causa Raiz
O código estava usando `jwt.JWTError`, que **não existe** nas versões modernas do PyJWT (2.x+).

Na versão PyJWT 2.0+, a hierarquia de exceções mudou:
- ❌ `jwt.JWTError` - NÃO EXISTE MAIS
- ❌ `jwt.PyJWTError` - DEPRECATED
- ✅ `jwt.exceptions.InvalidTokenError` - Exceção base moderna
- ✅ `jwt.exceptions.ExpiredSignatureError` - Token expirado
- ✅ `jwt.exceptions.DecodeError` - Erro de decodificação

## ✅ Solução Implementada

### 1. Atualização de Imports

**ANTES:**
```python
import jwt
import secrets
```

**DEPOIS:**
```python
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
import secrets
```

### 2. Correção da Função `verify_token()`

**ANTES (CÓDIGO QUEBRADO):**
```python
def verify_token(token: str) -> Optional[dict]:
    """Verifica e decodifica um token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:  # ✅ Existe
        return None
    except jwt.JWTError:  # ❌ NÃO EXISTE!
        return None
```

**DEPOIS (CÓDIGO CORRIGIDO):**
```python
def verify_token(token: str) -> Optional[dict]:
    """Verifica e decodifica um token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("Token expirado")
        return None
    except DecodeError as e:
        logger.warning(f"Erro ao decodificar token: {e}")
        return None
    except InvalidTokenError as e:
        logger.warning(f"Token inválido: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao verificar token: {e}")
        return None
```

## 📋 Hierarquia de Exceções PyJWT 2.x

```
Exception
└── InvalidTokenError (base para todas exceções JWT)
    ├── DecodeError
    │   ├── InvalidSignatureError
    │   ├── ExpiredSignatureError
    │   ├── InvalidAudienceError
    │   ├── InvalidIssuerError
    │   ├── InvalidIssuedAtError
    │   ├── ImmatureSignatureError
    │   └── InvalidKeyError
    ├── InvalidAlgorithmError
    └── MissingRequiredClaimError
```

## 🎯 Exceções Capturadas

### 1. `ExpiredSignatureError`
**Quando ocorre**: Token JWT expirado (campo `exp` no passado)

**Exemplo**:
```python
# Token criado com expiração de 8 horas
exp = datetime.utcnow() + timedelta(hours=8)

# Após 8 horas, ao decodificar:
# ExpiredSignatureError: Signature has expired
```

**Tratamento**: Retorna `None`, força novo login

### 2. `DecodeError`
**Quando ocorre**: 
- Token malformado
- Número incorreto de segmentos
- Base64 inválido
- JSON inválido

**Exemplo**:
```python
# Token malformado (faltando partes)
token = "eyJhbGc.eyJzdWI"  # Só 2 partes, precisa de 3

# DecodeError: Not enough segments
```

**Tratamento**: Log do erro, retorna `None`

### 3. `InvalidTokenError`
**Quando ocorre**:
- Assinatura inválida
- Algoritmo não permitido
- Claims obrigatórios faltando
- Qualquer outro erro de validação

**Exemplo**:
```python
# Token com assinatura inválida
token = "header.payload.invalid_signature"

# InvalidTokenError: Signature verification failed
```

**Tratamento**: Log do erro, retorna `None`

### 4. `Exception` (Catch-all)
**Quando ocorre**: Erros inesperados não relacionados ao JWT

**Tratamento**: Log de erro crítico, retorna `None`

## 🔍 Fluxo de Validação

```
1. Requisição chega com header Authorization
   ↓
2. FastAPI extrai token via HTTPBearer
   ↓
3. get_current_user() chama verify_token()
   ↓
4. jwt.decode() tenta decodificar
   ↓
5a. SUCESSO → Retorna payload (dict)
   ↓
6a. Verifica username no USUARIOS_DB
   ↓
7a. Retorna dados do usuário

5b. ERRO (ExpiredSignatureError) → Log + return None
   ↓
6b. HTTPException 401: "Token inválido ou expirado"
   ↓
7b. Front-end redireciona para /login

5c. ERRO (DecodeError) → Log + return None
   ↓
6c. HTTPException 401: "Token inválido ou expirado"
   ↓
7c. Front-end redireciona para /login

5d. ERRO (InvalidTokenError) → Log + return None
   ↓
6d. HTTPException 401: "Token inválido ou expirado"
   ↓
7d. Front-end redireciona para /login
```

## 🧪 Testes

### Teste 1: Token Válido
```python
# Login
response = requests.post('/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['access_token']

# Usar token
response = requests.get('/api/user', headers={
    'Authorization': f'Bearer {token}'
})

assert response.status_code == 200
assert response.json()['username'] == 'admin'
```

### Teste 2: Token Expirado
```python
# Criar token com expiração no passado
old_token = create_access_token({
    'username': 'admin',
    'exp': datetime.utcnow() - timedelta(hours=1)
})

# Tentar usar
response = requests.get('/api/user', headers={
    'Authorization': f'Bearer {old_token}'
})

assert response.status_code == 401
assert 'expirado' in response.json()['detail'].lower()
```

### Teste 3: Token Malformado
```python
# Token inválido
bad_token = "not.a.valid.token"

# Tentar usar
response = requests.get('/api/user', headers={
    'Authorization': f'Bearer {bad_token}'
})

assert response.status_code == 401
```

### Teste 4: Sem Token
```python
# Requisição sem Authorization header
response = requests.get('/api/user')

assert response.status_code == 403  # Forbidden (FastAPI HTTPBearer)
```

## 📊 Logs Melhorados

### Antes (Sem logs)
```
500 Internal Server Error
(Nenhuma informação útil)
```

### Depois (Com logs informativos)
```
WARNING: Token expirado
INFO: 127.0.0.1:51267 - "GET /api/user HTTP/1.1" 401 Unauthorized

WARNING: Erro ao decodificar token: Not enough segments
INFO: 127.0.0.1:51268 - "GET /api/user HTTP/1.1" 401 Unauthorized

WARNING: Token inválido: Signature verification failed
INFO: 127.0.0.1:51269 - "GET /api/user HTTP/1.1" 401 Unauthorized
```

## 🎓 Boas Práticas Implementadas

### 1. Exceções Específicas Primeiro
```python
# ✅ CORRETO - Do mais específico para o mais genérico
try:
    jwt.decode(...)
except ExpiredSignatureError:  # Mais específico
    ...
except DecodeError:            # Específico
    ...
except InvalidTokenError:      # Genérico (base)
    ...
except Exception:              # Catch-all
    ...
```

### 2. Logging Adequado
```python
# ✅ CORRETO - Log em cada exceção
except DecodeError as e:
    logger.warning(f"Erro ao decodificar token: {e}")
    return None
```

### 3. Não Expor Detalhes Internos
```python
# ❌ MAU - Expõe erro interno
raise HTTPException(401, detail=str(e))

# ✅ BOM - Mensagem genérica
raise HTTPException(401, detail="Token inválido ou expirado")
```

## 🔄 Compatibilidade de Versões

| PyJWT | JWTError | InvalidTokenError | Status |
|-------|----------|-------------------|--------|
| 1.x   | ✅ Existe | ❌ Não existe | Legacy |
| 2.0+  | ❌ Removido | ✅ Existe | Atual |

**Versão Usada**: PyJWT 2.x (moderna)

## 📁 Arquivos Modificados

- ✅ `app_fastapi.py` - Linha 21 (imports) e linha 381-395 (verify_token)

## ✅ Resultado

**ANTES:**
```
❌ AttributeError: module 'jwt' has no attribute 'JWTError'
❌ 500 Internal Server Error
❌ Aplicação quebrada
```

**DEPOIS:**
```
✅ Exceções tratadas corretamente
✅ 401 Unauthorized (comportamento esperado)
✅ Logs informativos
✅ Aplicação funcional
```

## 🚀 Como Testar

```bash
# 1. Reiniciar servidor
python start_fastapi.py

# 2. Fazer login
# POST /api/auth/login
# { "username": "admin", "password": "admin123" }

# 3. Copiar o access_token

# 4. Testar endpoint protegido
# GET /api/user
# Header: Authorization: Bearer <token>

# 5. Verificar:
✅ Status 200 OK
✅ Dados do usuário retornados
✅ Sem erros no console
```

---

**Status**: ✅ Corrigido  
**Data**: 20 de Outubro de 2025  
**Impacto**: Crítico (quebrava autenticação)  
**Complexidade**: Baixa (atualização de imports)  
**Referência**: [PyJWT 2.0 Migration](https://pyjwt.readthedocs.io/en/stable/changelog.html)
