# 🎁 Guia de Criação de Executável - Neoson

## 📋 Visão Geral

Este guia explica como criar um executável standalone do Neoson usando PyInstaller, permitindo distribuir o sistema sem necessidade de instalar Python ou dependências.

---

## 🎯 Benefícios do Executável

✅ **Distribuição Simples**
- Um único arquivo/pasta para distribuir
- Não requer Python instalado no sistema de destino
- Todas as dependências embutidas

✅ **Fácil Implantação**
- Copiar pasta e executar
- Ideal para ambientes corporativos
- Funcionamento offline (exceto APIs externas)

✅ **Segurança**
- Código Python compilado (não facilmente legível)
- Proteção de propriedade intelectual

---

## 📦 Requisitos

### **No Sistema de Build:**

```powershell
# Python 3.11+ instalado
python --version

# PyInstaller
pip install pyinstaller

# Todas as dependências do projeto
pip install -r requirements.txt
```

### **Espaço em Disco:**
- **Fonte**: ~500 MB (projeto + dependências)
- **Build**: ~1 GB (temporário)
- **Executável final**: ~200-300 MB

---

## 🚀 Como Criar o Executável

### **Método 1: Script Automatizado (Recomendado)**

```powershell
# Executar script de build
.\build_executable.ps1
```

O script irá:
1. ✅ Verificar PyInstaller
2. ✅ Verificar dependências
3. ✅ Limpar builds anteriores
4. ✅ Criar .env.example
5. ✅ Executar PyInstaller
6. ✅ Criar README e scripts auxiliares
7. ✅ Exibir estatísticas

### **Método 2: Manual**

```powershell
# 1. Instalar PyInstaller (se não tiver)
pip install pyinstaller

# 2. Limpar builds anteriores
Remove-Item -Path build, dist -Recurse -Force -ErrorAction SilentlyContinue

# 3. Executar PyInstaller
pyinstaller neoson.spec --clean --noconfirm

# 4. O executável estará em: dist\neoson\neoson.exe
```

---

## 📊 Processo de Build

### **Tempo de Build:**
- **Primeira vez**: 5-10 minutos
- **Rebuilds**: 3-5 minutos

### **Etapas do PyInstaller:**

```
1. 📋 Análise (Analysis)
   └─ Escaneia imports e dependências
   
2. 🗜️ Compilação (PYZ)
   └─ Compila bytecode Python
   
3. 🔨 Criação do EXE
   └─ Gera executável Windows
   
4. 📦 Coleta (COLLECT)
   └─ Agrupa binários e dados
   
5. ✅ Finalização
   └─ Executável pronto em dist/
```

---

## 📁 Estrutura do Executável Gerado

```
dist/
└── neoson/
    ├── neoson.exe              ← Executável principal
    ├── START.bat               ← Script de inicialização rápida
    ├── README.txt              ← Instruções de uso
    ├── .env.example            ← Template de configuração
    │
    ├── _internal/              ← Bibliotecas e dependências
    │   ├── python311.dll
    │   ├── fastapi/
    │   ├── langchain/
    │   ├── openai/
    │   └── ...
    │
    ├── templates/              ← Templates HTML
    │   └── index.html
    │
    ├── static/                 ← Arquivos estáticos
    │   ├── factory.css
    │   ├── factory.js
    │   └── ...
    │
    ├── factory/                ← Módulo Factory
    ├── agentes/                ← Agentes IA
    ├── dal/                    ← Camada de dados
    ├── core/                   ← Core do sistema
    ├── tools/                  ← Ferramentas
    └── docs/                   ← Documentação
```

---

## 🎁 Distribuição do Executável

### **Preparar para Distribuição:**

```powershell
# 1. Navegar para dist/
cd dist

# 2. Criar ZIP
Compress-Archive -Path neoson -DestinationPath neoson-v2.0.0-windows.zip

# 3. Tamanho do ZIP: ~100-150 MB (comprimido)
```

### **Instruções para o Usuário Final:**

```
1. Extrair neoson-v2.0.0-windows.zip
2. Copiar .env.example para .env
3. Editar .env com credenciais
4. Duplo clique em START.bat
```

---

## ⚙️ Configuração do Executável

### **Arquivo: neoson.spec**

O arquivo `.spec` controla o comportamento do PyInstaller:

```python
# Nome do executável
APP_NAME = 'neoson'

# Módulos ocultos a incluir
hiddenimports = [
    'fastapi',
    'uvicorn',
    'langchain',
    # ...
]

# Dados a incluir
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    # ...
]

# Exclusões (reduz tamanho)
excludes = [
    'matplotlib',
    'jupyter',
    'pytest',
    # ...
]
```

### **Personalizações Possíveis:**

#### **1. Adicionar Ícone**
```python
exe = EXE(
    # ...
    icon='icon.ico',  # Adicionar ícone customizado
)
```

#### **2. Modo Sem Console (Windowed)**
```python
exe = EXE(
    # ...
    console=False,  # Ocultar console
)
```

#### **3. Um Único Arquivo (OnFile)**
```python
exe = EXE(
    # ...
    onefile=True,  # Tudo em um único .exe
)
```

**⚠️ Atenção:** OneFile é mais lento para iniciar (extrai arquivos temporários a cada execução)

---

## 🐛 Troubleshooting

### **Problema 1: Módulo não encontrado em runtime**

**Sintoma:**
```
ModuleNotFoundError: No module named 'xxx'
```

**Solução:**
Adicionar ao `hiddenimports` em `neoson.spec`:
```python
hiddenimports = [
    # ...
    'xxx',
]
```

### **Problema 2: Arquivo de dados não encontrado**

**Sintoma:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'templates/index.html'
```

**Solução:**
Adicionar ao `datas` em `neoson.spec`:
```python
datas = [
    # ...
    ('templates', 'templates'),
]
```

### **Problema 3: Executável muito grande**

**Solução 1 - Excluir pacotes desnecessários:**
```python
excludes = [
    'matplotlib',
    'scipy',
    'jupyter',
    'pytest',
    'tkinter',
]
```

**Solução 2 - Usar UPX (compressão):**
```python
exe = EXE(
    # ...
    upx=True,
)
```

⚠️ **Atenção:** UPX pode causar falsos positivos em antivírus

### **Problema 4: Antivírus bloqueia executável**

**Causa:** Falso positivo (comum com PyInstaller)

**Soluções:**
1. Adicionar exceção no antivírus
2. Assinar digitalmente o executável
3. Reportar como falso positivo ao fornecedor do antivírus
4. Usar certificado de code signing

### **Problema 5: Executável não inicia**

**Debug:**
```powershell
# Executar via CMD para ver erros
cd dist\neoson
.\neoson.exe

# Ou com mais verbosidade
.\neoson.exe --log-level debug
```

---

## 📊 Comparação: OneFile vs OneFolder

| Característica | OneFolder (Padrão) | OneFile |
|----------------|-------------------|---------|
| **Tamanho total** | ~250 MB | ~200 MB |
| **Tempo de inicialização** | Rápido (~1s) | Lento (~5-10s) |
| **Extração de arquivos** | Não | Sim (a cada execução) |
| **Facilidade distribuição** | Pasta inteira | Um único .exe |
| **Atualização** | Trocar arquivos específicos | Trocar tudo |
| **Recomendado para** | Produção | Demos/Testes |

**Recomendação:** Use **OneFolder** (padrão) para produção.

---

## 🔒 Segurança

### **Código Compilado**

O código Python é compilado em bytecode (`.pyc`), tornando mais difícil reverter para código fonte original.

**⚠️ Importante:** Não é criptografia! Com ferramentas adequadas, ainda é possível extrair o bytecode.

### **Proteção de Credenciais**

✅ **Faça:**
- Usar arquivo `.env` separado (não incluir no executável)
- Instruir usuários a nunca commitar `.env`
- Usar variáveis de ambiente do sistema

❌ **Não Faça:**
- Incluir `.env` com credenciais reais no executável
- Hardcode de senhas no código
- Distribuir executável com credenciais de teste

### **Code Signing (Opcional)**

Para ambientes corporativos, considere assinar o executável:

```powershell
# Usando signtool (Windows SDK)
signtool sign /f certificado.pfx /p senha /t http://timestamp.digicert.com neoson.exe
```

---

## 📈 Otimizações

### **1. Reduzir Tamanho**

```python
# Em neoson.spec
excludes = [
    'matplotlib',  # -50 MB
    'scipy',       # -30 MB
    'jupyter',     # -20 MB
    'pytest',      # -10 MB
    'sphinx',      # -10 MB
]
```

### **2. Melhorar Performance**

```python
# Compilar para bytecode antes
import compileall
compileall.compile_dir('.', force=True)

# Usar UPX (cuidado com antivírus)
upx=True
```

### **3. Builds Incrementais**

```powershell
# Não usar --clean para builds rápidos
pyinstaller neoson.spec --noconfirm
```

---

## 🔄 Atualizações

### **Atualizar Executável:**

```powershell
# 1. Modificar código fonte
# 2. Rebuild
.\build_executable.ps1

# 3. Distribuir nova versão
```

### **Atualizar Apenas Dados (sem rebuild):**

Se só mudou templates/static:
```powershell
# Copiar manualmente para dist/neoson/
Copy-Item templates\* dist\neoson\templates\ -Recurse -Force
Copy-Item static\* dist\neoson\static\ -Recurse -Force
```

---

## 📞 Suporte e Recursos

**Documentação Oficial:**
- PyInstaller: https://pyinstaller.org/
- PyInstaller Manual: https://pyinstaller.org/en/stable/usage.html

**Arquivos do Projeto:**
- `neoson.spec` - Configuração do build
- `build_executable.ps1` - Script automatizado
- `docs/PYINSTALLER_GUIDE.md` - Este guia

---

## ✅ Checklist Final

Antes de distribuir:

- [ ] Executável inicia sem erros
- [ ] Interface web acessível
- [ ] Todas as funcionalidades testadas
- [ ] README.txt incluído
- [ ] .env.example incluído
- [ ] Instruções claras de instalação
- [ ] PostgreSQL testado
- [ ] OpenAI API testada
- [ ] Antivírus não bloqueia
- [ ] Tamanho otimizado
- [ ] Documentação completa

---

**Versão do Guia:** 1.0  
**Data:** 22 de Outubro de 2025  
**Autor:** GitHub Copilot
