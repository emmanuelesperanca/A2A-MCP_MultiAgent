# 💬 Implementação do Endpoint /api/chat

## 📋 Visão Geral

Endpoint criado para processar mensagens do chat da nova interface Claude-style.

## 🔌 Endpoint

### POST /api/chat

**Autenticação**: Requerida (Bearer Token JWT)

**Headers:**
```http
Content-Type: application/json
Authorization: Bearer <token_jwt>
```

**Request Body:**
```json
{
  "mensagem": "Qual é o horário de funcionamento da empresa?"
}
```

**Response (Sucesso - 200 OK):**
```json
{
  "success": true,
  "response": "O horário de funcionamento é...",
  "cadeia_raciocinio": "========== CADEIA DE RACIOCÍNIO ==========...",
  "agent_usado": "Agente RH",
  "classificacao": "RH",
  "especialidade": "Recursos Humanos"
}
```

**Response (Erro - 401 Unauthorized):**
```json
{
  "detail": "Token inválido ou expirado"
}
```

**Response (Erro - 500 Internal Server Error):**
```json
{
  "detail": "Erro ao processar mensagem: <detalhes>"
}
```

## 🏗️ Arquitetura

### Fluxo de Processamento

```
1. Usuário envia mensagem no chat
   ↓
2. Frontend valida token JWT
   ↓
3. POST /api/chat com { mensagem: "..." }
   ↓
4. Backend valida autenticação (get_current_user)
   ↓
5. Cria perfil do usuário baseado em dados do token
   ↓
6. neoson_sistema.processar_pergunta_async()
   ↓
7. Retorna resposta formatada
   ↓
8. Frontend exibe mensagem na interface
```

### Componentes Integrados

| Componente | Responsabilidade |
|------------|------------------|
| **FastAPI** | Roteamento e validação |
| **HTTPBearer** | Autenticação JWT |
| **ChatRequest** | Validação do payload |
| **neoson_sistema** | Processamento IA |
| **get_current_user** | Extração de dados do usuário |

## 💻 Implementação Backend

**Arquivo**: `app_fastapi.py`

**Localização**: Linha ~506 (após `/api/user`)

### Código Principal

```python
@app.post("/api/chat")
async def api_chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Endpoint de chat para a nova interface
    Processa mensagem do usuário e retorna resposta do Neoson
    """
    if neoson_sistema is None:
        raise HTTPException(status_code=500, detail='Sistema Neoson não inicializado')
    
    try:
        # Criar perfil do usuário
        perfil = {
            "Nome": current_user.get("full_name", current_user["username"]),
            "Cargo": "Gerente" if current_user["user_type"] == "admin" else "Colaborador",
            "Departamento": "Geral",
            "Nivel_Acesso": current_user["user_type"]
        }
        
        # Processar pergunta de forma assíncrona
        resultado = await neoson_sistema.processar_pergunta_async(request.mensagem, perfil)
        
        if resultado['sucesso']:
            # Separar resposta da cadeia de raciocínio
            resposta_texto = resultado['resposta']
            cadeia_separador = "="*60
            
            if cadeia_separador in resposta_texto:
                partes = resposta_texto.split(cadeia_separador, 1)
                resposta_principal = partes[0].strip()
                cadeia_raciocinio = cadeia_separador + partes[1]
            else:
                resposta_principal = resposta_texto
                cadeia_raciocinio = None
            
            return {
                "success": True,
                "response": resposta_principal,
                "cadeia_raciocinio": cadeia_raciocinio,
                "agent_usado": resultado.get('agente_usado', 'Neoson'),
                "classificacao": resultado.get('classificacao', 'Geral'),
                "especialidade": resultado.get('especialidade', 'Geral')
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=resultado.get('erro', 'Erro ao processar mensagem')
            )
    except Exception as e:
        logger.exception(f"❌ Erro inesperado no chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )
```

### Modelo de Dados (ChatRequest)

```python
class ChatRequest(BaseModel):
    """Modelo para requisição de chat"""
    mensagem: str = Field(..., min_length=1, max_length=1000)
    persona_selecionada: Optional[str] = "Gerente"
    custom_persona: Optional[Dict] = None

    @validator('mensagem')
    def validate_mensagem(cls, v):
        if not v.strip():
            raise ValueError('Mensagem não pode estar vazia')
        return v.strip()
```

## 🌐 Implementação Frontend

**Arquivo**: `templates/index.html`

**Localização**: Função `sendMessage()` (linha ~981)

### Código JavaScript

```javascript
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Animação de primeira mensagem
    if (!hasMessages) {
        animateFirstMessage();
    }

    // Adicionar mensagem do usuário
    addMessage(message, 'user');
    
    // Limpar input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Mostrar typing indicator
    const typingId = addTypingIndicator();

    try {
        // Enviar para API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({ mensagem: message })  // ✅ Corrigido: "mensagem" não "message"
        });

        const data = await response.json();

        // Remover typing indicator
        removeTypingIndicator(typingId);

        if (data.success && data.response) {
            addMessage(data.response, 'assistant');
        } else if (data.detail) {
            addMessage(`Erro: ${data.detail}`, 'assistant');
        } else {
            addMessage('Desculpe, não consegui processar sua mensagem.', 'assistant');
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('Desculpe, ocorreu um erro ao processar sua mensagem.', 'assistant');
        console.error('Erro:', error);
    }
}
```

## 🔐 Autenticação

### Extração de Dados do Usuário

```python
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency para extrair usuário autenticado do token JWT"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )
    
    username = payload.get("username")
    user_data = USUARIOS_DB.get(username)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    return user_data
```

### Perfil Dinâmico

O perfil é criado dinamicamente baseado nos dados do token:

```python
perfil = {
    "Nome": current_user.get("full_name", current_user["username"]),
    "Cargo": "Gerente" if current_user["user_type"] == "admin" else "Colaborador",
    "Departamento": "Geral",
    "Nivel_Acesso": current_user["user_type"]
}
```

| user_type | Cargo | Nível de Acesso |
|-----------|-------|-----------------|
| `admin` | Gerente | admin |
| `user` | Colaborador | user |

## 🧪 Testes

### Teste 1: Mensagem Simples

**Request:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"mensagem": "Olá, como você pode me ajudar?"}'
```

**Response Esperada:**
```json
{
  "success": true,
  "response": "Olá! Sou o Neoson, seu assistente virtual...",
  "cadeia_raciocinio": null,
  "agent_usado": "Neoson Coordenador",
  "classificacao": "Geral",
  "especialidade": "Coordenação"
}
```

### Teste 2: Sem Autenticação

**Request:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "Teste"}'
```

**Response Esperada:**
```json
{
  "detail": "Not authenticated"
}
```

**Status Code:** 403 Forbidden

### Teste 3: Token Expirado

**Request:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_expirado>" \
  -d '{"mensagem": "Teste"}'
```

**Response Esperada:**
```json
{
  "detail": "Token inválido ou expirado"
}
```

**Status Code:** 401 Unauthorized

### Teste 4: Mensagem Vazia

**Request:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"mensagem": ""}'
```

**Response Esperada:**
```json
{
  "detail": [
    {
      "loc": ["body", "mensagem"],
      "msg": "Mensagem não pode estar vazia",
      "type": "value_error"
    }
  ]
}
```

**Status Code:** 422 Unprocessable Entity

## 📊 Logs

### Log de Sucesso

```
INFO - 💬 Chat - Usuário: admin, Mensagem: 'Olá, como você pode me ajudar?...'
INFO - 🎯 App processando pergunta: 'Olá, como você pode me ajudar?...'
INFO - ✅ Resposta gerada: 256 caracteres
INFO - 127.0.0.1:50123 - "POST /api/chat HTTP/1.1" 200 OK
```

### Log de Erro (Sistema não inicializado)

```
ERROR - Sistema Neoson não inicializado
INFO - 127.0.0.1:50123 - "POST /api/chat HTTP/1.1" 500 Internal Server Error
```

### Log de Erro (Token inválido)

```
WARNING - Token inválido ou expirado
INFO - 127.0.0.1:50123 - "POST /api/chat HTTP/1.1" 401 Unauthorized
```

## 🎯 Diferenças entre Endpoints

### /chat (Antigo)

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Sem autenticação obrigatória
    # Usa persona_selecionada ou custom_persona
    # Resposta mais complexa com enrichment
```

**Uso**: Interface antiga, testes, API pública

### /api/chat (Novo)

```python
@app.post("/api/chat")
async def api_chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    # Autenticação obrigatória
    # Perfil gerado automaticamente do token
    # Resposta simplificada e rápida
```

**Uso**: Nova interface Claude-style, usuários autenticados

## 🔄 Melhorias Futuras

### Fase 1: Funcionalidades Básicas ✅
- [x] Processamento de mensagens
- [x] Autenticação JWT
- [x] Resposta simples
- [x] Tratamento de erros

### Fase 2: Enriquecimento (Futuro)
- [ ] Integrar `response_enricher`
- [ ] Documentos relacionados
- [ ] FAQs similares
- [ ] Sugestões de próximas perguntas

### Fase 3: Streaming (Futuro)
- [ ] Server-Sent Events (SSE)
- [ ] Resposta em tempo real
- [ ] Typing indicator real (baseado em streaming)

### Fase 4: Histórico (Futuro)
- [ ] Salvar conversas no banco
- [ ] Recuperar histórico por usuário
- [ ] Análise de conversas

## 📁 Arquivos Modificados

| Arquivo | Modificação | Linhas |
|---------|-------------|--------|
| `app_fastapi.py` | Adicionado endpoint `/api/chat` | ~506-570 |
| `templates/index.html` | Corrigido `message` → `mensagem` | ~993 |
| `docs/API_CHAT_ENDPOINT.md` | Documentação completa | (novo) |

## ✅ Checklist de Validação

- [x] Endpoint `/api/chat` criado
- [x] Autenticação JWT integrada
- [x] Modelo `ChatRequest` validado
- [x] Frontend envia `mensagem` (não `message`)
- [x] Resposta formatada corretamente
- [x] Tratamento de erros implementado
- [x] Logs informativos adicionados
- [x] Documentação criada

## 🚀 Como Testar

### 1. Reiniciar servidor FastAPI

```powershell
python start_fastapi.py
```

### 2. Fazer login na interface

```
http://localhost:8000/
Login: admin / admin123
```

### 3. Enviar mensagem no chat

```
Digite: "Olá, como você pode me ajudar?"
Aguarde resposta do Neoson
```

### 4. Verificar logs do servidor

```
INFO - 💬 Chat - Usuário: admin, Mensagem: 'Olá, como você pode me ajudar?...'
INFO - ✅ Resposta gerada: XXX caracteres
INFO - 127.0.0.1:XXXXX - "POST /api/chat HTTP/1.1" 200 OK
```

### 5. Verificar console do navegador

```
[Nenhum erro deve aparecer]
```

---

**Status**: ✅ Implementado  
**Data**: 20 de Outubro de 2025  
**Versão**: 1.0  
**Prioridade**: Alta (funcionalidade crítica)  
**Impacto**: Torna o chat funcional na nova interface
