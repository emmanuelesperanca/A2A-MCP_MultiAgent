# 🚀 GUIA RÁPIDO DE DEPLOY - NEOSON

## ⚡ TL;DR - Passos Essenciais

### 1️⃣ Preparar Arquivos (no seu PC)

```powershell
# Frontend
.\build_frontend.ps1

# Backend
.\build_backend.ps1
```

### 2️⃣ Configurar Backend (na VM)

```bash
# Copiar para VM
scp -r build/backend/* usuario@IP-VM:/home/usuario/neoson/

# Conectar na VM
ssh usuario@IP-VM

# Instalar
cd /home/usuario/neoson
cp .env.example .env
nano .env  # Configurar credenciais
./install_linux.sh
```

### 3️⃣ Configurar Frontend (na Hospedagem)

```javascript
// Editar build/frontend/config.js
BASE_URL: 'https://api.seu-dominio.com.br'

// Upload via FTP para /public_html/
```

---

## 📋 Checklist Rápido

### Backend (VM)
- [ ] Executar `build_backend.ps1`
- [ ] Copiar `.env.example` → `.env`
- [ ] Configurar credenciais no `.env`
- [ ] Transferir para VM via SCP
- [ ] Executar `install_linux.sh` ou `install_windows.ps1`
- [ ] Testar: `curl http://localhost:8000/health`
- [ ] Configurar DNS: `api.seu-dominio.com.br → IP-VM`

### Frontend (Hospedagem)
- [ ] Executar `build_frontend.ps1`
- [ ] Editar `config.js` com URL da API
- [ ] Upload via FTP para `/public_html/`
- [ ] Testar: `https://seu-dominio.com.br`
- [ ] Verificar console (F12) sem erros CORS

---

## 🎯 Arquitetura Final

```
┌────────────────────────────────────────────────────────────┐
│  🌐 HOSPEDAGEM WEB                                         │
│  https://seu-dominio.com.br                                │
│                                                            │
│  📁 /public_html/                                          │
│  ├── index.html                                            │
│  ├── config.js  ← BASE_URL da API                         │
│  └── static/                                               │
│      ├── styles.css                                        │
│      ├── factory.css                                       │
│      ├── factory.js                                        │
│      ├── knowledge.js                                      │
│      └── preferences.js                                    │
└────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌────────────────────────────────────────────────────────────┐
│  🖥️ MÁQUINA VIRTUAL                                        │
│  https://api.seu-dominio.com.br                            │
│                                                            │
│  📁 /home/usuario/neoson/app/                              │
│  ├── app_fastapi.py  ← CORS configurado                   │
│  ├── .env  ← Credenciais                                  │
│  ├── factory/                                              │
│  ├── agentes/                                              │
│  ├── dal/                                                  │
│  ├── core/                                                 │
│  └── tools/                                                │
│                                                            │
│  🗄️ PostgreSQL (localhost:5432)                           │
│  🌐 Nginx (reverse proxy)                                  │
│  ⚙️ Supervisor (manter app rodando)                        │
└────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configurações Essenciais

### 1. `.env` (Backend)

```bash
POSTGRES_PASSWORD=senha_super_segura
OPENAI_API_KEY=sk-sua-chave-aqui
JWT_SECRET_KEY=chave_aleatoria_32_chars
ALLOWED_ORIGINS=https://seu-dominio.com.br
```

### 2. `config.js` (Frontend)

```javascript
BASE_URL: 'https://api.seu-dominio.com.br'
```

### 3. DNS Records

```
seu-dominio.com.br       A      IP-DA-HOSPEDAGEM
api.seu-dominio.com.br   A      IP-DA-VM
```

---

## 📊 Comandos Úteis

### Backend (Linux)

```bash
# Ver logs
sudo tail -f /var/log/neoson/app.log

# Reiniciar
sudo supervisorctl restart neoson

# Status
sudo supervisorctl status neoson

# Testar API
curl https://api.seu-dominio.com.br/health
```

### Backend (Windows)

```powershell
# Ver logs
Get-Content C:\Apps\neoson\logs\app.log -Tail 50 -Wait

# Reiniciar
nssm restart Neoson

# Status
nssm status Neoson
```

---

## 🔍 Testes de Validação

### 1. Backend Online

```bash
curl https://api.seu-dominio.com.br/health

# Resposta esperada:
{
  "status": "healthy",
  "timestamp": "2025-10-21T...",
  "version": "1.1.3"
}
```

### 2. Frontend Conectado

1. Abrir `https://seu-dominio.com.br`
2. Abrir DevTools (F12) → Console
3. Verificar logs:
   ```
   ✅ config.js carregado - versão 1.0.0
   ✅ Backend online: {...}
   🏭 Factory.js carregado - versão 1.1.3
   ```

### 3. Criar Agente (Teste End-to-End)

1. Ir para aba "Criar Agente"
2. Preencher formulário:
   - Nome: "Teste Deploy"
   - Identifier: "teste_deploy"
   - Especialidade: "Teste"
   - Coordenador: "Coordenador de TI"
3. Clicar "Criar Subagente"
4. Verificar sucesso:
   - ✅ Notificação de sucesso
   - ✅ Agente aparece na tabela
   - ✅ Agente aparece na Árvore
   - ✅ Agente no dropdown da Base de Conhecimento

---

## ❌ Problemas Comuns

### 1. Erro CORS

**Sintoma:**
```
Access to fetch at '...' has been blocked by CORS policy
```

**Solução:**
1. Verificar `ALLOWED_ORIGINS` no `.env` do backend
2. Deve incluir domínio exato: `https://seu-dominio.com.br`
3. Reiniciar backend: `sudo supervisorctl restart neoson`

### 2. Backend Offline

**Sintoma:**
```
❌ Backend offline: TypeError: Failed to fetch
```

**Solução:**
1. Verificar se backend está rodando: `sudo supervisorctl status neoson`
2. Verificar logs: `sudo tail -f /var/log/neoson/error.log`
3. Testar localmente: `curl http://localhost:8000/health`
4. Verificar firewall: `sudo ufw status`

### 3. Database Error

**Sintoma:**
```
psycopg2.OperationalError: could not connect to server
```

**Solução:**
1. Verificar PostgreSQL rodando: `sudo systemctl status postgresql`
2. Verificar credenciais no `.env`
3. Testar conexão: `psql -U neoson_user -d neoson_db -h localhost`

---

## 📞 Suporte

**Documentação Completa:**
- `docs/DEPLOY_PRODUCAO.md` - Guia detalhado
- `build/frontend/README_DEPLOY.txt` - Instruções do frontend
- `build/backend/README_INSTALL.txt` - Instruções do backend

**Scripts Automatizados:**
- `build_frontend.ps1` - Preparar frontend
- `build_backend.ps1` - Preparar backend
- `build/backend/install_linux.sh` - Instalar no Linux
- `build/backend/install_windows.ps1` - Instalar no Windows

---

**Versão:** 1.0  
**Data:** 21 de Outubro de 2025
