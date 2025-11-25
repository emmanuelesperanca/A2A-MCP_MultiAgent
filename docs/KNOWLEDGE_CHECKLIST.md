# ✅ CHECKLIST DE INSTALAÇÃO - Base de Conhecimento

Use este checklist para garantir que tudo está configurado corretamente.

---

## 📦 STEP 1: Dependências Python

### Verificar instalação atual
```powershell
pip list | findstr -i "pypdf docx langchain openai psycopg2"
```

### Instalar dependências faltantes
```powershell
# Instalar novos pacotes
pip install pypdf==4.0.1 python-docx==1.1.0

# Ou instalar tudo de uma vez
pip install -r requirements_fastapi.txt
```

### Checklist de Dependências
- [ ] pypdf (4.0.1) - Extração de texto PDF
- [ ] python-docx (1.1.0) - Extração de texto DOCX
- [ ] langchain - Chunking de texto (já deve estar instalado)
- [ ] openai - Geração de embeddings (já deve estar instalado)
- [ ] psycopg2 - Conexão PostgreSQL (já deve estar instalado)
- [ ] fastapi - Framework web (já deve estar instalado)

---

## 🖼️ STEP 2: OCR (Opcional mas Recomendado)

### Windows
1. Baixe o instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Execute o instalador (.exe)
3. Adicione ao PATH: `C:\Program Files\Tesseract-OCR`
4. Teste no terminal:
   ```powershell
   tesseract --version
   ```
5. Instale pacotes Python:
   ```powershell
   pip install pytesseract pdf2image
   ```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-por tesseract-ocr-eng
pip install pytesseract pdf2image
```

### Checklist OCR
- [ ] Tesseract instalado no sistema
- [ ] Tesseract no PATH
- [ ] pytesseract (Python package)
- [ ] pdf2image (Python package)
- [ ] Linguagens instaladas (por + eng)

**Nota**: OCR é opcional. Funciona sem ele para PDFs com texto selecionável.

---

## 🗄️ STEP 3: Banco de Dados PostgreSQL

### Verificar conexão
```python
import psycopg2

DATABASE_URL = "postgresql://user:pass@host:5432/db"

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Conexão OK")
    conn.close()
except Exception as e:
    print(f"❌ Erro: {e}")
```

### Verificar tabelas existem
```sql
-- Execute no psql ou pgAdmin
SELECT tablename 
FROM pg_tables 
WHERE tablename LIKE '%knowledge%'
ORDER BY tablename;
```

**Esperado**: 15 tabelas
- rh_benefits_knowledge
- rh_payroll_knowledge
- rh_recruitment_knowledge
- it_infrastructure_knowledge
- it_network_knowledge
- it_security_knowledge
- it_storage_knowledge
- it_database_knowledge
- it_monitoring_knowledge
- it_cloud_knowledge
- enterprise_erp_knowledge
- enterprise_bi_knowledge
- crm_knowledge
- service_desk_knowledge
- neoson_knowledge

### Checklist Banco
- [ ] PostgreSQL rodando
- [ ] Conexão DATABASE_URL funciona
- [ ] Extensão pgvector instalada
- [ ] 15 tabelas de conhecimento existem
- [ ] Permissões de INSERT/SELECT OK

---

## 🔑 STEP 4: OpenAI API

### Verificar API Key
```python
from openai import OpenAI

OPENAI_API_KEY = "sk-proj-..."  # Sua key

client = OpenAI(api_key=OPENAI_API_KEY)

try:
    response = client.embeddings.create(
        input="teste",
        model="text-embedding-3-small"
    )
    print("✅ API Key válida")
    print(f"Dimensões: {len(response.data[0].embedding)}")
except Exception as e:
    print(f"❌ Erro: {e}")
```

### Verificar créditos
1. Acesse: https://platform.openai.com/usage
2. Verifique se tem créditos disponíveis
3. Recomendado: $5+ para testes

### Checklist OpenAI
- [ ] API Key válida
- [ ] Acesso ao modelo text-embedding-3-small
- [ ] Créditos disponíveis ($5+ recomendado)
- [ ] Rate limits conhecidos (3,000 RPM)

---

## 📁 STEP 5: Arquivos do Projeto

### Verificar arquivos criados
```powershell
dir api_knowledge.py
dir static\knowledge.js
dir templates\index.html
dir docs\KNOWLEDGE_*.md
```

### Checklist de Arquivos
- [ ] `api_knowledge.py` (252 linhas) - Backend API
- [ ] `static/knowledge.js` (318 linhas) - Frontend JS
- [ ] `templates/index.html` - Contém HTML + CSS da Base de Conhecimento
- [ ] `app_fastapi.py` - Contém import do knowledge_router
- [ ] `requirements_fastapi.txt` - Contém pypdf e python-docx
- [ ] `docs/KNOWLEDGE_QUICK_START.md` - Quick start guide
- [ ] `docs/KNOWLEDGE_BASE_GUIDE.md` - Guia completo
- [ ] `docs/KNOWLEDGE_IMPLEMENTATION.md` - Docs técnicas
- [ ] `docs/KNOWLEDGE_BASE_SUMMARY.md` - Resumo executivo

---

## 🚀 STEP 6: Iniciar Servidor

### Comando de inicialização
```powershell
uvicorn app_fastapi:app --reload
```

### Verificar startup
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process...
INFO:     Started server process...
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Checklist de Startup
- [ ] Servidor inicia sem erros
- [ ] Porta 8000 disponível
- [ ] Mensagem "Application startup complete"
- [ ] Sem erros de import
- [ ] Acesso a http://localhost:8000 funciona

---

## 🌐 STEP 7: Testar Interface

### 1. Abrir browser
```
http://localhost:8000
```

### 2. Fazer login
```
Usuário: admin
Senha: admin
```

### 3. Acessar Base de Conhecimento
- Clique em "Base de Conhecimento" no sidebar
- Deve abrir a página com área de upload

### Checklist de Interface
- [ ] Página principal carrega
- [ ] Login funciona
- [ ] Sidebar aparece
- [ ] "Base de Conhecimento" está visível
- [ ] Clique abre a página correta
- [ ] Área de upload aparece
- [ ] Dropdown de agentes tem 15 opções
- [ ] Formulário de metadados completo
- [ ] Log container presente

---

## 📄 STEP 8: Teste de Upload

### Preparar arquivo de teste
- Use um PDF pequeno (1-5 páginas)
- Ou um DOCX simples
- Tamanho recomendado: <1MB para primeiro teste

### Fazer upload
1. Arraste arquivo para área de upload
2. Verifique se aparece na lista de arquivos
3. Selecione agente: "Neoson - Conhecimento Geral"
4. Preencha metadados:
   ```
   Áreas: ALL
   Geografias: ALL
   Projetos: ALL
   Nível: 1
   Idioma: pt-br
   ```
5. Clique em "Iniciar Ingestão"

### Checklist de Upload
- [ ] Drag-and-drop funciona
- [ ] Arquivo aparece na lista
- [ ] Botão "Remover" funciona
- [ ] Seleção de agente funciona
- [ ] Formulário aceita inputs
- [ ] Botão "Iniciar Ingestão" ativo
- [ ] Log começa a aparecer
- [ ] Status popup aparece
- [ ] Mensagem de sucesso ao final

---

## ✅ STEP 9: Verificar Resultado

### No log da interface
Esperado:
```
✅ Arquivo: teste.pdf
  → Enviando arquivo para o servidor...
  → Texto extraído: 1234 caracteres
  → Chunks gerados: 2
  → Embeddings criados: 2
  → Inseridos no banco: 2

✅ Ingestão concluída com sucesso!
```

### No banco de dados
```sql
SELECT 
    fonte_documento,
    LEFT(conteudo_original, 50) as preview,
    LENGTH(conteudo_original) as tamanho,
    created_at
FROM neoson_knowledge
ORDER BY created_at DESC
LIMIT 5;
```

### Checklist de Resultado
- [ ] Log mostra todas as etapas
- [ ] Sem mensagens de erro
- [ ] Contagem de chunks > 0
- [ ] Contagem de embeddings = chunks
- [ ] Mensagem final de sucesso
- [ ] Dados aparecem no banco
- [ ] Vetor tem 1536 dimensões
- [ ] Metadados salvos corretamente

---

## 📊 STEP 10: Validação Final

### Teste de busca semântica (opcional)
```python
from openai import OpenAI
import psycopg2

# 1. Gerar embedding da query
client = OpenAI(api_key="sk-...")
response = client.embeddings.create(
    input="como fazer onboarding",
    model="text-embedding-3-small"
)
query_vector = response.data[0].embedding

# 2. Buscar no banco
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("""
    SELECT conteudo_original, fonte_documento,
           1 - (vetor <=> %s::vector) as similarity
    FROM neoson_knowledge
    ORDER BY vetor <=> %s::vector
    LIMIT 3
""", (query_vector, query_vector))

results = cur.fetchall()
for content, source, similarity in results:
    print(f"\nSimilaridade: {similarity:.3f}")
    print(f"Fonte: {source}")
    print(f"Conteúdo: {content[:200]}...")
```

### Checklist Final
- [ ] Upload de PDF funciona
- [ ] Upload de DOCX funciona
- [ ] OCR funciona (se instalado)
- [ ] Múltiplos arquivos funcionam
- [ ] Todos os 15 agentes disponíveis
- [ ] Metadados salvos corretamente
- [ ] Busca vetorial funciona
- [ ] Performance aceitável (<30s para doc pequeno)

---

## 🎉 INSTALAÇÃO COMPLETA!

Se todos os checkboxes estão marcados, sua Base de Conhecimento está **100% operacional**.

### Próximos Passos
1. ✅ Adicione documentos reais
2. ✅ Configure metadados adequados
3. ✅ Teste busca com agentes
4. ✅ Monitore uso da API OpenAI
5. ✅ Consulte docs para features avançadas

---

## 📞 Suporte

### Se algo falhou:

**Dependências**:
- Reveja STEP 1 e 2
- Execute: `pip install -r requirements_fastapi.txt`

**Banco de Dados**:
- Reveja STEP 3
- Verifique conexão e tabelas

**API OpenAI**:
- Reveja STEP 4
- Verifique key e créditos

**Servidor**:
- Reveja STEP 6
- Verifique console do uvicorn para erros

**Interface**:
- Reveja STEP 7
- Abra console do browser (F12) para ver erros JS

**Upload**:
- Reveja STEP 8
- Verifique console do browser E do servidor

### Documentação Completa
- `docs/KNOWLEDGE_BASE_GUIDE.md` - Troubleshooting detalhado
- `docs/KNOWLEDGE_IMPLEMENTATION.md` - Detalhes técnicos

---

**Versão**: 1.0.0  
**Data**: Dezembro 2024  
**Status**: ✅ Ready for Production
