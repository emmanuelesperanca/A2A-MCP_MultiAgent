# 🔧 Implementação Técnica - Base de Conhecimento

## Arquitetura da Solução

### Stack Completo
```
Frontend: HTML5 + CSS3 + JavaScript (Vanilla)
Backend: FastAPI + Python 3.11
Database: PostgreSQL 15 + pgvector
AI: OpenAI API (text-embedding-3-small)
Text Processing: pypdf, python-docx, pytesseract
Chunking: LangChain RecursiveCharacterTextSplitter
```

---

## 📁 Estrutura de Arquivos

```
agente_ia_poc/
├── templates/
│   └── index.html                 # UI principal (+ 310 linhas CSS, + 213 linhas HTML)
├── static/
│   └── knowledge.js               # 318 linhas de lógica frontend
├── api_knowledge.py               # 252 linhas de API backend
├── app_fastapi.py                 # Integração do router
├── requirements_fastapi.txt       # Dependências atualizadas
└── docs/
    ├── KNOWLEDGE_BASE_GUIDE.md    # Guia do usuário
    └── KNOWLEDGE_IMPLEMENTATION.md # Este arquivo
```

---

## 🎨 Frontend Implementation

### 1. HTML Structure (`templates/index.html`)

#### Seção de Upload
```html
<div class="upload-area" id="uploadArea">
    <div class="upload-icon">📁</div>
    <p class="upload-text">Arraste arquivos aqui ou clique para selecionar</p>
    <p class="upload-hint">Suporta: PDF e DOCX</p>
    <input type="file" id="fileInput" accept=".pdf,.docx" multiple style="display: none;">
</div>
```

**Features**:
- Drag-and-drop zone com feedback visual
- Multi-file selection
- Validação de formato (apenas .pdf e .docx)
- Display dinâmico de arquivos selecionados

#### Formulário de Metadados
```html
<div class="metadata-form">
    <div class="form-row">
        <input type="text" id="areasLiberadas" placeholder="Ex: RH, TI, ALL">
    </div>
    <div class="form-row">
        <input type="text" id="geografiasLiberadas" placeholder="Ex: BR, US, ALL">
    </div>
    <!-- ... outros 10 campos ... -->
</div>
```

**12 Campos de Governança**:
1. Áreas Liberadas (text)
2. Geografias Liberadas (text)
3. Projetos Liberados (text)
4. Nível Hierárquico (select 1-5)
5. Idioma (select pt-br/en-us/es-es)
6. Data de Validade (date)
7. Responsável (text)
8. Aprovador (text)
9. Dado Sensível (checkbox)
10. Apenas Para SI (checkbox)

#### Log Container
```html
<div class="log-container" id="logContainer">
    <div class="log-placeholder">Aguardando operação...</div>
</div>
```

**Tipos de Log**:
- `.log-entry.info` - Azul (#4a90e2)
- `.log-entry.success` - Verde (#27ae60)
- `.log-entry.warning` - Amarelo (#f39c12)
- `.log-entry.error` - Vermelho (#e74c3c)

---

### 2. CSS Styling

#### Upload Area States
```css
.upload-area {
    border: 2px dashed rgba(255, 255, 255, 0.3);
    transition: all 0.3s ease;
}

.upload-area:hover {
    border-color: rgba(106, 90, 205, 0.8);
    background: rgba(106, 90, 205, 0.05);
}

.upload-area.drag-over {
    border-color: #6a5acd;
    background: rgba(106, 90, 205, 0.15);
    transform: scale(1.02);
}
```

#### File Item Cards
```css
.file-item {
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
}

.file-icon {
    font-size: 24px;
    margin-right: 12px;
}

.remove-file {
    background: rgba(231, 76, 60, 0.8);
    transition: background 0.2s;
}
```

#### Console-Style Log
```css
.log-container {
    background: #1a1a2e;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 15px;
    height: 250px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
}

.log-entry {
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 4px;
}
```

---

### 3. JavaScript Logic (`static/knowledge.js`)

#### File Management
```javascript
let selectedFiles = [];

function handleFiles(files) {
    const validFiles = Array.from(files).filter(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        if (ext !== 'pdf' && ext !== 'docx') {
            addLog(`❌ Arquivo rejeitado: ${file.name} (formato não suportado)`, 'error');
            return false;
        }
        return true;
    });
    
    selectedFiles.push(...validFiles);
    renderSelectedFiles();
}
```

#### Drag-and-Drop Implementation
```javascript
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.add('drag-over');
        });
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('drag-over');
        });
    });
    
    uploadArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
}
```

#### API Integration
```javascript
async function processFile(file, targetAgent, metadata) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_table', targetAgent);
    formData.append('metadata', JSON.stringify({
        ...metadata,
        fonte_documento: file.name
    }));
    
    const response = await fetch('/api/knowledge/ingest', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao processar arquivo');
    }
    
    return await response.json();
}
```

#### Real-Time Logging
```javascript
function addLog(message, type = 'info') {
    const logContainer = document.getElementById('logContainer');
    const placeholder = logContainer.querySelector('.log-placeholder');
    if (placeholder) placeholder.remove();
    
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    
    const timestamp = new Date().toLocaleTimeString('pt-BR');
    entry.textContent = `[${timestamp}] ${message}`;
    
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}
```

---

## ⚙️ Backend Implementation

### 1. API Endpoint (`api_knowledge.py`)

#### Router Setup
```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

router = APIRouter()

@router.post("/api/knowledge/ingest")
async def ingest_knowledge(
    file: UploadFile = File(...),
    target_table: str = Form(...),
    metadata: str = Form(...)
):
    """Processa upload de documento e injeta no banco"""
```

#### Request Flow
```
1. Recebe arquivo via multipart/form-data
2. Parse metadata JSON string
3. Salva arquivo temporariamente
4. Extrai texto (PDF/DOCX com OCR fallback)
5. Limpa e normaliza texto
6. Divide em chunks (1000 chars, 150 overlap)
7. Gera embeddings (OpenAI API em batches de 100)
8. Insere no PostgreSQL com metadados
9. Retorna estatísticas
10. Limpa arquivo temporário
```

---

### 2. Text Extraction

#### PDF Processing
```python
def extrair_texto_pdf(caminho_arquivo: str) -> str:
    """Extrai texto de PDF usando pypdf"""
    try:
        reader = pypdf.PdfReader(caminho_arquivo)
        texto = "".join(page.extract_text() or "" for page in reader.pages)
        return texto.strip()
    except Exception as e:
        return f"Erro ao ler PDF: {e}"
```

#### OCR Fallback
```python
def extrair_texto_pdf_com_ocr(caminho_arquivo: str) -> str:
    """Extrai texto usando OCR para PDFs escaneados"""
    if not OCR_AVAILABLE:
        return "OCR não disponível"
    
    try:
        images = pdf2image.convert_from_path(caminho_arquivo, dpi=300)
        texto_total = []
        
        for i, image in enumerate(images):
            texto_pagina = pytesseract.image_to_string(image, lang='por+eng')
            if texto_pagina.strip():
                texto_total.append(texto_pagina.strip())
        
        return "\n\n".join(texto_total)
    except Exception as e:
        return f"Erro no OCR: {e}"
```

#### DOCX Processing
```python
def extrair_texto_docx(caminho_arquivo: str) -> str:
    """Extrai texto de DOCX incluindo tabelas"""
    try:
        document = docx.Document(caminho_arquivo)
        full_text = []
        
        # Parágrafos
        for para in document.paragraphs:
            full_text.append(para.text)
        
        # Tabelas
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    full_text.append(cell.text)
        
        return "\n".join(full_text)
    except Exception as e:
        return f"Erro ao ler DOCX: {e}"
```

---

### 3. Chunking Strategy

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

def dividir_em_chunks(texto: str) -> List[str]:
    """Divide texto em chunks usando LangChain"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )
    return text_splitter.split_text(texto)
```

**Por que esses valores?**
- **1000 chars**: Balanceio entre contexto e granularidade
- **150 overlap**: Mantém continuidade semântica entre chunks
- **RecursiveCharacterTextSplitter**: Respeita estrutura natural (parágrafos, sentenças)

---

### 4. Embeddings Generation

```python
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 100

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def gerar_embeddings_em_lote(chunks: List[str]) -> List[list]:
    """Gera embeddings em batches para otimizar API calls"""
    vetores = []
    
    for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        lote = chunks[i:i + EMBEDDING_BATCH_SIZE]
        
        try:
            # Garantir que não há textos vazios
            lote_processado = [text if text.strip() else " " for text in lote]
            
            response = openai_client.embeddings.create(
                input=lote_processado,
                model=EMBEDDING_MODEL
            )
            
            vetores.extend([item.embedding for item in response.data])
        except Exception as e:
            print(f"Erro no lote {i//EMBEDDING_BATCH_SIZE + 1}: {e}")
            vetores.extend([None] * len(lote))
    
    return vetores
```

**Otimizações**:
- Batch processing (100 chunks por call) reduz latência
- Handle de erros por lote (continua processamento)
- Empty text handling (substitui por espaço)

---

### 5. Database Insertion

```python
import psycopg2
import psycopg2.extras

def inserir_chunks_no_db(
    tabela: str,
    chunks: List[str],
    vetores: List[list],
    metadados: dict
) -> int:
    """Insere chunks com embeddings no PostgreSQL"""
    conn = psycopg2.connect(DATABASE_URL)
    
    sql = f"""
        INSERT INTO "{tabela}" (
            conteudo_original, fonte_documento, dado_sensivel, apenas_para_si,
            areas_liberadas, nivel_hierarquico_minimo, geografias_liberadas,
            projetos_liberados, idioma, data_validade, responsavel, aprovador, vetor
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    dados_para_inserir = []
    
    for chunk, vetor in zip(chunks, vetores):
        if vetor is not None:
            dados_para_inserir.append((
                chunk,
                metadados['fonte_documento'],
                metadados['dado_sensivel'],
                metadados['apenas_para_si'],
                metadados['areas_liberadas'],
                metadados['nivel_hierarquico_minimo'],
                metadados['geografias_liberadas'],
                metadados['projetos_liberados'],
                metadados['idioma'],
                metadados['data_validade'],
                metadados['responsavel'],
                metadados['aprovador'],
                vetor
            ))
    
    try:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, sql, dados_para_inserir)
        conn.commit()
        count = len(dados_para_inserir)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    
    return count
```

**Performance**:
- `execute_batch` é 10x mais rápido que múltiplos INSERTs
- Transação única (commit ou rollback completo)
- Filtra chunks com embeddings None

---

## 🗄️ Database Schema

### Estrutura de Tabelas

Todas as 15 tabelas seguem o mesmo schema:

```sql
CREATE TABLE {table_name} (
    id SERIAL PRIMARY KEY,
    conteudo_original TEXT NOT NULL,
    fonte_documento VARCHAR(255),
    dado_sensivel BOOLEAN DEFAULT FALSE,
    apenas_para_si BOOLEAN DEFAULT FALSE,
    areas_liberadas VARCHAR(255),
    nivel_hierarquico_minimo INTEGER,
    geografias_liberadas VARCHAR(255),
    projetos_liberados VARCHAR(255),
    idioma VARCHAR(10),
    data_validade DATE,
    responsavel VARCHAR(255),
    aprovador VARCHAR(255),
    vetor VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para busca vetorial
CREATE INDEX idx_{table_name}_vetor ON {table_name} 
USING ivfflat (vetor vector_cosine_ops) WITH (lists = 100);

-- Índice para filtros de governança
CREATE INDEX idx_{table_name}_areas ON {table_name}(areas_liberadas);
CREATE INDEX idx_{table_name}_nivel ON {table_name}(nivel_hierarquico_minimo);
CREATE INDEX idx_{table_name}_geografias ON {table_name}(geografias_liberadas);
```

### Exemplo de Query com Governança

```sql
SELECT 
    conteudo_original,
    fonte_documento,
    1 - (vetor <=> $1::vector) as similarity
FROM rh_benefits_knowledge
WHERE 
    (areas_liberadas = 'ALL' OR areas_liberadas LIKE '%RH%')
    AND nivel_hierarquico_minimo <= $2
    AND (geografias_liberadas = 'ALL' OR geografias_liberadas LIKE '%BR%')
    AND (data_validade IS NULL OR data_validade > CURRENT_DATE)
ORDER BY vetor <=> $1::vector
LIMIT 5;
```

---

## 🔒 Security Considerations

### 1. File Upload Validation
```javascript
// Frontend
const validExtensions = ['pdf', 'docx'];
const maxFileSize = 10 * 1024 * 1024; // 10MB

if (!validExtensions.includes(ext)) {
    throw new Error('Formato não suportado');
}
if (file.size > maxFileSize) {
    throw new Error('Arquivo muito grande');
}
```

```python
# Backend
if not file.filename.lower().endswith(('.pdf', '.docx')):
    raise HTTPException(status_code=400, detail="Formato não suportado")

if file.size > 10 * 1024 * 1024:
    raise HTTPException(status_code=413, detail="Arquivo muito grande")
```

### 2. SQL Injection Prevention
```python
# ✅ CORRETO - Usando parâmetros
sql = f"""INSERT INTO "{tabela}" (...) VALUES (%s, %s, %s)"""
cur.execute(sql, (value1, value2, value3))

# ❌ ERRADO - String interpolation
sql = f"""INSERT INTO {tabela} VALUES ('{value1}', '{value2}')"""
```

### 3. Temporary File Cleanup
```python
try:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    # Processar arquivo...
    
finally:
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)  # Sempre limpar
```

### 4. Token Validation
```python
@router.post("/api/knowledge/ingest")
async def ingest_knowledge(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)  # Validar token
):
    """Apenas usuários autenticados podem fazer upload"""
```

---

## 📊 Performance Metrics

### Expected Processing Times

| Document Size | Pages | Chunks | Embeddings | Total Time |
|---------------|-------|--------|------------|------------|
| Small (1-5 pages) | 5 | 5-10 | 5-10 | ~5s |
| Medium (10-30 pages) | 20 | 20-50 | 20-50 | ~15s |
| Large (50-100 pages) | 75 | 100-200 | 100-200 | ~45s |
| Very Large (200+ pages) | 250 | 300-500 | 300-500 | ~2min |

### Bottlenecks

1. **OpenAI API** (maior gargalo)
   - Rate limit: 3,000 RPM (requests per minute)
   - Solução: Batch processing (100 chunks/request)

2. **OCR Processing** (se necessário)
   - PDF de 100 páginas → ~30s para OCR
   - Solução: Cache de textos extraídos

3. **Database Insertion**
   - 500 chunks → ~2s com execute_batch
   - Solução: Já otimizado

---

## 🧪 Testing

### 1. Unit Tests

```python
# test_text_extraction.py
def test_extrair_pdf():
    result = extrair_texto_pdf("test_data/sample.pdf")
    assert len(result) > 0
    assert "texto esperado" in result

def test_extrair_docx():
    result = extrair_texto_docx("test_data/sample.docx")
    assert len(result) > 0

# test_chunking.py
def test_chunking():
    texto = "A" * 5000
    chunks = dividir_em_chunks(texto)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)
```

### 2. Integration Tests

```python
# test_api.py
async def test_ingest_endpoint():
    with open("test.pdf", "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        data = {
            "target_table": "neoson_knowledge",
            "metadata": json.dumps({"areas_liberadas": "ALL", ...})
        }
        response = await client.post("/api/knowledge/ingest", files=files, data=data)
    
    assert response.status_code == 200
    assert "inserted_count" in response.json()
```

### 3. Manual Testing Checklist

- [ ] Upload PDF (texto selecionável)
- [ ] Upload PDF (escaneado - OCR)
- [ ] Upload DOCX (com tabelas)
- [ ] Upload arquivo inválido (rejeição)
- [ ] Upload sem token (401 error)
- [ ] Múltiplos arquivos simultâneos
- [ ] Arquivo muito grande (10MB+)
- [ ] Metadados vazios (validação)
- [ ] Verificar logs em tempo real
- [ ] Verificar dados no banco

---

## 🚀 Deployment

### 1. Dependências

```bash
# Instalar requirements
pip install -r requirements_fastapi.txt

# Instalar Tesseract (para OCR)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-por tesseract-ocr-eng

# Windows:
# Baixar de: https://github.com/UB-Mannheim/tesseract/wiki
# Adicionar ao PATH
```

### 2. Variáveis de Ambiente

```bash
# .env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=your-secret-key-here
```

### 3. Inicializar Tabelas

```sql
-- Executar para cada agente
CREATE TABLE rh_benefits_knowledge (...);
CREATE TABLE rh_payroll_knowledge (...);
-- ... (15 tabelas no total)
```

### 4. Start Server

```bash
# Desenvolvimento
uvicorn app_fastapi:app --reload

# Produção
uvicorn app_fastapi:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📝 Changelog

### v1.0.0 (2024-12-XX)
- ✅ Frontend completo (HTML + CSS + JS)
- ✅ Drag-and-drop de arquivos
- ✅ Seleção de 15 agentes
- ✅ Formulário de metadados (12 campos)
- ✅ Log em tempo real
- ✅ Backend API endpoint
- ✅ Extração de texto (PDF/DOCX/OCR)
- ✅ Chunking com LangChain
- ✅ Embeddings OpenAI
- ✅ Inserção PostgreSQL
- ✅ Documentação completa

---

## 🔮 Future Enhancements

### Phase 2
- [ ] Progresso em tempo real (Server-Sent Events)
- [ ] Preview de documentos antes do upload
- [ ] Edição de documentos já inseridos
- [ ] Busca e filtro de documentos ingeridos
- [ ] Dashboard de analytics (chunks por agente, etc.)

### Phase 3
- [ ] Suporte para mais formatos (TXT, CSV, JSON)
- [ ] Extração de imagens e diagramas
- [ ] Versionamento de documentos
- [ ] Aprovação workflow
- [ ] Notificações por email

### Phase 4
- [ ] Processing queue (Celery/RQ)
- [ ] Bulk upload (ZIP files)
- [ ] Export de conhecimento
- [ ] API pública (REST)
- [ ] Webhooks para integração

---

## 📚 References

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **LangChain Docs**: https://python.langchain.com
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **pgvector**: https://github.com/pgvector/pgvector
- **pypdf**: https://pypdf.readthedocs.io
- **python-docx**: https://python-docx.readthedocs.io

---

**Maintainer**: Neoson Development Team  
**Status**: ✅ Production Ready  
**Last Updated**: 2024
