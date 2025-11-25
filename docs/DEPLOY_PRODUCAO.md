# 🚀 Guia de Deploy para Produção

## 📋 Índice
1. [Arquitetura de Deploy](#arquitetura)
2. [Arquivos para Hospedagem Web (Frontend)](#frontend)
3. [Arquivos para VM (Backend)](#backend)
4. [Configurações CORS](#cors)
5. [Deploy do Frontend](#deploy-frontend)
6. [Deploy do Backend](#deploy-backend)
7. [Configuração de Domínio](#dominio)
8. [Segurança e SSL](#seguranca)
9. [Monitoramento](#monitoramento)

---

## 🏗️ Arquitetura {#arquitetura}

```
┌─────────────────────────────────────────┐
│  HOSPEDAGEM WEB (seu-dominio.com.br)    │
│  ├── index.html                         │
│  ├── static/                            │
│  │   ├── styles.css                     │
│  │   ├── factory.css                    │
│  │   ├── factory.js                     │
│  │   ├── knowledge.js                   │
│  │   ├── preferences.js                 │
│  │   └── images/                        │
│  └── config.js (API endpoints)          │
└─────────────────────────────────────────┘
              │ HTTPS
              ▼
┌─────────────────────────────────────────┐
│  VM (api.seu-dominio.com.br ou IP)      │
│  ├── app_fastapi.py                     │
│  ├── factory/                           │
│  ├── agentes/                           │
│  ├── dal/                               │
│  ├── core/                              │
│  ├── tools/                             │
│  └── PostgreSQL Database                │
└─────────────────────────────────────────┘
```

---

## 🌐 FRONTEND - Arquivos para Hospedagem Web {#frontend}

### **Estrutura de Pastas na Hospedagem**

```
/public_html/  (ou /www/ ou /httpdocs/)
│
├── index.html                    ✅ DEPLOY
├── config.js                     ✅ DEPLOY (NOVO - criar)
│
├── static/
│   ├── styles.css                ✅ DEPLOY (extrair do index.html)
│   ├── factory.css               ✅ DEPLOY
│   ├── factory.js                ✅ DEPLOY (modificado)
│   ├── knowledge.js              ✅ DEPLOY (modificado)
│   ├── preferences.js            ✅ DEPLOY (modificado)
│   │
│   └── images/                   ✅ DEPLOY
│       ├── logo.png
│       └── favicon.ico
│
└── .htaccess                     ✅ DEPLOY (NOVO - criar)
```

### **Arquivos que VÃO para Hospedagem:**

#### ✅ **HTML**
- `templates/index.html` → `/index.html`

#### ✅ **CSS**
- `static/factory.css` → `/static/factory.css`
- CSS inline do `index.html` → `/static/styles.css` (extrair)

#### ✅ **JavaScript**
- `static/factory.js` → `/static/factory.js` (modificar URLs de API)
- `static/knowledge.js` → `/static/knowledge.js` (modificar URLs de API)
- `static/preferences.js` → `/static/preferences.js` (modificar URLs de API)

#### ✅ **Configuração (NOVO)**
- `/config.js` (criar para centralizar endpoints)

#### ✅ **Assets**
- Imagens, ícones, fontes

---

## 🖥️ BACKEND - Arquivos para Máquina Virtual {#backend}

### **Estrutura de Pastas na VM**

```
/home/usuario/neoson/  (ou C:\Apps\neoson\)
│
├── app_fastapi.py                ✅ DEPLOY (modificado)
├── start_fastapi.py              ✅ DEPLOY
├── requirements.txt              ✅ DEPLOY
├── .env                          ✅ DEPLOY (criar com credenciais)
│
├── factory/                      ✅ DEPLOY
│   ├── __init__.py
│   ├── agent_factory.py
│   ├── agent_registry.py
│   ├── agents_registry.json
│   └── models.py
│
├── agentes/                      ✅ DEPLOY
│   ├── subagentes/
│   │   ├── agente_dev_async.py
│   │   ├── agente_enduser_async.py
│   │   ├── agente_governance_async.py
│   │   └── agente_final_test_async.py
│   └── coordenadores/
│       ├── agente_rh_async.py
│       └── ti_coordinator_async.py
│
├── dal/                          ✅ DEPLOY
│   ├── __init__.py
│   ├── base_dal.py
│   ├── manager.py
│   ├── postgres_dal_async.py
│   └── postgres_dal.py
│
├── core/                         ✅ DEPLOY
│   ├── __init__.py
│   ├── agent_classifier.py
│   ├── config.py
│   ├── conversation_memory.py
│   ├── enrichment_system.py
│   ├── feedback_system.py
│   ├── glossario_corporativo.py
│   └── security_instructions.py
│
├── tools/                        ✅ DEPLOY
│   └── (todos os arquivos .py)
│
├── templates/                    ❌ NÃO PRECISA (HTML vai para hospedagem)
│   └── agents/                   ⚠️ OPCIONAL (se backend gera HTML)
│
├── static/                       ❌ NÃO PRECISA (vai para hospedagem)
│
├── docs/                         ⚠️ OPCIONAL
├── tests/                        ⚠️ OPCIONAL
├── obsoleto/                     ❌ NÃO DEPLOY
├── __pycache__/                  ❌ NÃO DEPLOY
└── .git/                         ❌ NÃO DEPLOY
```

### **Arquivos que VÃO para VM:**

#### ✅ **Core Python**
- `app_fastapi.py` (modificado para CORS)
- `start_fastapi.py`
- `requirements.txt`
- `.env` (credenciais do banco)

#### ✅ **Módulos**
- `factory/` (completo)
- `agentes/` (completo)
- `dal/` (completo)
- `core/` (completo)
- `tools/` (completo)

#### ✅ **Dados**
- `factory/agents_registry.json`

#### ❌ **NÃO enviar para VM:**
- `templates/` (HTML vai para hospedagem)
- `static/` (CSS/JS vai para hospedagem)
- `docs/`
- `tests/`
- `obsoleto/`
- `__pycache__/`
- `.git/`

---

## 🔧 Configurações CORS {#cors}

### **1. Modificar `app_fastapi.py`**

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ⚠️ PRODUÇÃO: Substituir "*" pelo domínio real
origins = [
    "https://seu-dominio.com.br",
    "https://www.seu-dominio.com.br",
    "http://localhost:3000",  # Para testes locais
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # ⚠️ IMPORTANTE: Especificar domínios exatos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

---

## 🌐 Deploy do Frontend {#deploy-frontend}

### **Passo 1: Criar `config.js`**

Arquivo: `/config.js`

```javascript
// Configuração de API para produção
const API_CONFIG = {
    // ⚠️ ALTERAR PARA URL REAL DA VM
    BASE_URL: 'https://api.seu-dominio.com.br',  // ou 'http://IP-DA-VM:8000'
    
    ENDPOINTS: {
        // Chat
        CHAT: '/chat',
        CHAT_STREAM: '/chat/stream',
        
        // Factory
        FACTORY_AGENTS: '/api/factory/agents',
        FACTORY_CREATE_SUBAGENT: '/api/factory/create-subagent',
        FACTORY_CREATE_COORDINATOR: '/api/factory/create-coordinator',
        
        // Knowledge Base
        KNOWLEDGE_CREATE: '/api/knowledge/create',
        KNOWLEDGE_QUERY: '/api/knowledge/query',
        KNOWLEDGE_DELETE: '/api/knowledge/delete',
        KNOWLEDGE_LIST: '/api/knowledge/list',
        
        // Agent Tree
        AGENTS_TREE: '/api/agents/tree',
        
        // Preferences
        PREFERENCES_SAVE: '/api/preferences/save',
        PREFERENCES_LOAD: '/api/preferences/load'
    },
    
    // Timeout para requests (ms)
    TIMEOUT: 30000
};

// Função helper para construir URLs completas
function getApiUrl(endpoint) {
    return `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS[endpoint] || endpoint}`;
}
```

### **Passo 2: Extrair CSS do `index.html`**

Criar arquivo: `/static/styles.css`

Copiar todo o CSS inline do `<style>` tag do `index.html` para este arquivo.

### **Passo 3: Modificar `index.html`**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neoson - Sistema Multi-Agente IA</title>
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- CSS -->
    <link rel="stylesheet" href="/static/styles.css?v=1.1.3">
    <link rel="stylesheet" href="/static/factory.css?v=1.1.3">
</head>
<body>
    <!-- Conteúdo HTML completo -->
    
    <!-- Scripts -->
    <script src="/config.js"></script>  <!-- ⚠️ NOVO - PRIMEIRO -->
    <script src="/static/preferences.js"></script>
    <script src="/static/knowledge.js"></script>
    <script src="/static/factory.js?v=1.1.3"></script>
    
    <!-- Script inline do index.html -->
</body>
</html>
```

### **Passo 4: Modificar JavaScript Files**

**Em `factory.js`, `knowledge.js`, `preferences.js`:**

Substituir URLs hardcoded por chamadas ao `config.js`:

```javascript
// ❌ ANTES:
const response = await fetch('/api/factory/agents', {...});

// ✅ DEPOIS:
const response = await fetch(getApiUrl('FACTORY_AGENTS'), {...});
```

### **Passo 5: Criar `.htaccess` (se Apache)**

Arquivo: `/.htaccess`

```apache
# Habilitar rewrite
RewriteEngine On

# Redirecionar HTTP para HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
</IfModule>

# Browser Caching
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
</IfModule>

# Security Headers
<IfModule mod_headers.c>
    Header set X-Content-Type-Options "nosniff"
    Header set X-Frame-Options "SAMEORIGIN"
    Header set X-XSS-Protection "1; mode=block"
</IfModule>
```

### **Passo 6: Upload para Hospedagem**

**Via FTP/SFTP:**
1. Conectar ao servidor usando FileZilla ou WinSCP
2. Upload de todos os arquivos para `/public_html/` ou `/www/`
3. Verificar permissões (arquivos: 644, pastas: 755)

---

## 🖥️ Deploy do Backend na VM {#deploy-backend}

### **Passo 1: Preparar VM**

**Linux (Ubuntu/Debian):**
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Instalar Nginx (reverse proxy)
sudo apt install nginx -y

# Instalar supervisor (manter app rodando)
sudo apt install supervisor -y
```

**Windows Server:**
```powershell
# Instalar Python 3.11+ (baixar do python.org)
# Instalar PostgreSQL (baixar do postgresql.org)
# Instalar NSSM (para rodar como serviço)
choco install nssm -y
```

### **Passo 2: Criar Ambiente Virtual**

```bash
# Linux
cd /home/usuario
mkdir neoson
cd neoson

python3.11 -m venv venv
source venv/bin/activate

# Windows
cd C:\Apps
mkdir neoson
cd neoson

python -m venv venv
.\venv\Scripts\Activate.ps1
```

### **Passo 3: Transferir Arquivos**

**Via Git (Recomendado):**
```bash
git clone https://seu-repositorio.git
cd agente_ia_poc
```

**Via SCP/SFTP:**
```bash
# Do seu PC para VM
scp -r agente_ia_poc/ usuario@IP-VM:/home/usuario/neoson/
```

### **Passo 4: Instalar Dependências**

```bash
cd /home/usuario/neoson/agente_ia_poc
source venv/bin/activate
pip install -r requirements.txt
```

### **Passo 5: Configurar Banco de Dados**

```bash
# Criar usuário e database
sudo -u postgres psql

CREATE DATABASE neoson_db;
CREATE USER neoson_user WITH PASSWORD 'senha_super_segura';
GRANT ALL PRIVILEGES ON DATABASE neoson_db TO neoson_user;
\q
```

### **Passo 6: Criar `.env`**

Arquivo: `/home/usuario/neoson/agente_ia_poc/.env`

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=neoson_db
POSTGRES_USER=neoson_user
POSTGRES_PASSWORD=senha_super_segura

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# JWT
JWT_SECRET_KEY=gere-uma-chave-super-segura-aqui

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_RELOAD=false

# CORS (domínio do frontend)
ALLOWED_ORIGINS=https://seu-dominio.com.br,https://www.seu-dominio.com.br

# Logs
LOG_LEVEL=INFO
```

### **Passo 7: Configurar Supervisor (Linux)**

Arquivo: `/etc/supervisor/conf.d/neoson.conf`

```ini
[program:neoson]
directory=/home/usuario/neoson/agente_ia_poc
command=/home/usuario/neoson/venv/bin/python start_fastapi.py
user=usuario
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/neoson/app.log
stderr_logfile=/var/log/neoson/error.log
environment=PATH="/home/usuario/neoson/venv/bin"
```

```bash
# Criar diretório de logs
sudo mkdir -p /var/log/neoson
sudo chown usuario:usuario /var/log/neoson

# Recarregar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start neoson
sudo supervisorctl status
```

### **Passo 8: Configurar Nginx (Reverse Proxy)**

Arquivo: `/etc/nginx/sites-available/neoson-api`

```nginx
server {
    listen 80;
    server_name api.seu-dominio.com.br;  # ou IP da VM
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.seu-dominio.com.br;
    
    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.seu-dominio.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.seu-dominio.com.br/privkey.pem;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Logs
    access_log /var/log/nginx/neoson-access.log;
    error_log /var/log/nginx/neoson-error.log;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (para /chat/stream)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

```bash
# Habilitar site
sudo ln -s /etc/nginx/sites-available/neoson-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### **Passo 9: Configurar SSL (Let's Encrypt)**

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot --nginx -d api.seu-dominio.com.br

# Renovação automática já está configurada
sudo certbot renew --dry-run
```

### **Passo 10: Configurar Windows Service (Windows)**

```powershell
# Usando NSSM
nssm install Neoson "C:\Apps\neoson\venv\Scripts\python.exe" "C:\Apps\neoson\agente_ia_poc\start_fastapi.py"
nssm set Neoson AppDirectory "C:\Apps\neoson\agente_ia_poc"
nssm set Neoson DisplayName "Neoson AI Backend"
nssm set Neoson Description "Sistema Multi-Agente de IA - Backend API"
nssm set Neoson Start SERVICE_AUTO_START

# Iniciar serviço
nssm start Neoson

# Verificar status
nssm status Neoson
```

---

## 🌍 Configuração de Domínio {#dominio}

### **DNS Records**

```
# Frontend
seu-dominio.com.br        A     IP-DA-HOSPEDAGEM
www.seu-dominio.com.br    CNAME seu-dominio.com.br

# Backend
api.seu-dominio.com.br    A     IP-DA-VM
```

### **Firewall na VM**

```bash
# Linux (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Windows Firewall
New-NetFirewallRule -DisplayName "HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
```

---

## 🔒 Segurança e SSL {#seguranca}

### **1. HTTPS Obrigatório**
- ✅ Frontend: Certificado SSL na hospedagem
- ✅ Backend: Let's Encrypt com Certbot

### **2. Environment Variables**
- ❌ NUNCA commitar `.env` no Git
- ✅ Usar variáveis de ambiente seguras

### **3. CORS Restritivo**
```python
# ❌ DESENVOLVIMENTO
allow_origins=["*"]

# ✅ PRODUÇÃO
allow_origins=[
    "https://seu-dominio.com.br",
    "https://www.seu-dominio.com.br"
]
```

### **4. Rate Limiting**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/factory/create-subagent")
@limiter.limit("10/minute")
async def create_subagent(...):
    ...
```

### **5. Autenticação JWT**
- ✅ Já implementado no sistema
- ⚠️ Configurar `JWT_SECRET_KEY` no `.env`

---

## 📊 Monitoramento {#monitoramento}

### **1. Logs**

**Backend (Linux):**
```bash
# Logs da aplicação
tail -f /var/log/neoson/app.log

# Logs do Nginx
tail -f /var/log/nginx/neoson-access.log
```

**Backend (Windows):**
```powershell
# Logs do serviço
Get-Content C:\Apps\neoson\logs\app.log -Tail 50 -Wait
```

### **2. Health Check Endpoint**

Adicionar em `app_fastapi.py`:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.3"
    }
```

### **3. Uptime Monitoring**

Usar serviços como:
- **UptimeRobot** (gratuito)
- **Pingdom**
- **StatusCake**

Configurar para monitorar:
- `https://api.seu-dominio.com.br/health`

---

## 📦 Checklist de Deploy

### **Frontend (Hospedagem)**
- [ ] Criar `/config.js` com URL da API
- [ ] Extrair CSS inline para `/static/styles.css`
- [ ] Modificar `index.html` para referenciar `config.js`
- [ ] Atualizar JavaScript para usar `getApiUrl()`
- [ ] Criar `.htaccess` (Apache) ou equivalente
- [ ] Upload via FTP/SFTP
- [ ] Testar acesso: `https://seu-dominio.com.br`
- [ ] Verificar console do navegador (sem erros CORS)

### **Backend (VM)**
- [ ] Instalar Python 3.11+
- [ ] Instalar PostgreSQL
- [ ] Criar banco de dados e usuário
- [ ] Clonar/transferir código fonte
- [ ] Criar ambiente virtual
- [ ] Instalar dependências (`pip install -r requirements.txt`)
- [ ] Configurar `.env` com credenciais
- [ ] Modificar `app_fastapi.py` (CORS com domínio específico)
- [ ] Configurar Supervisor (Linux) ou NSSM (Windows)
- [ ] Configurar Nginx como reverse proxy
- [ ] Obter certificado SSL (Let's Encrypt)
- [ ] Configurar firewall (portas 80, 443)
- [ ] Testar endpoint: `https://api.seu-dominio.com.br/health`
- [ ] Verificar logs sem erros

### **DNS e Domínio**
- [ ] Configurar A record para frontend
- [ ] Configurar A record para backend (`api.seu-dominio.com.br`)
- [ ] Aguardar propagação DNS (até 48h)
- [ ] Testar resolução DNS: `nslookup api.seu-dominio.com.br`

### **Testes de Integração**
- [ ] Criar agente via Factory
- [ ] Verificar registro em `agents_registry.json`
- [ ] Testar Árvore de Agentes (atualização dinâmica)
- [ ] Testar Base de Conhecimento (upload de documentos)
- [ ] Testar Chat (comunicação com agentes)
- [ ] Verificar logs de erro no backend
- [ ] Testar em diferentes navegadores

---

## 🔄 Processo de Atualização

### **Frontend**
1. Modificar arquivos localmente
2. Incrementar versão no `config.js` e parâmetros `?v=`
3. Upload via FTP
4. Limpar cache do navegador (Ctrl+F5)

### **Backend**
```bash
# Linux
cd /home/usuario/neoson/agente_ia_poc
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo supervisorctl restart neoson

# Windows
cd C:\Apps\neoson\agente_ia_poc
git pull origin main
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade
nssm restart Neoson
```

---

## 📞 Suporte e Troubleshooting

### **Erro CORS**
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

**Solução:**
- Verificar `allow_origins` em `app_fastapi.py`
- Adicionar domínio exato (sem barra final)
- Reiniciar backend

### **502 Bad Gateway**
```
nginx: 502 Bad Gateway
```

**Solução:**
- Verificar se FastAPI está rodando: `curl http://localhost:8000/health`
- Verificar logs: `sudo supervisorctl status neoson`
- Reiniciar: `sudo supervisorctl restart neoson`

### **Database Connection Error**
```
psycopg2.OperationalError: could not connect to server
```

**Solução:**
- Verificar credenciais no `.env`
- Verificar se PostgreSQL está rodando: `sudo systemctl status postgresql`
- Testar conexão: `psql -U neoson_user -d neoson_db -h localhost`

---

## 📚 Recursos Adicionais

- **FastAPI Deployment Guide:** https://fastapi.tiangolo.com/deployment/
- **Nginx Configuration:** https://nginx.org/en/docs/
- **Let's Encrypt:** https://letsencrypt.org/
- **Supervisor:** http://supervisord.org/
- **PostgreSQL:** https://www.postgresql.org/docs/

---

**Versão do Documento:** 1.0  
**Data:** 21 de Outubro de 2025  
**Autor:** GitHub Copilot
