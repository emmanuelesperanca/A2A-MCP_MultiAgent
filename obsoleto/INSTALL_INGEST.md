# Instalação do Ingest Data

## Instalação rápida
```powershell
# Criar ambiente conda (recomendado)
conda create -n ingest_env python=3.11
conda activate ingest_env

# Instalar dependências
pip install -r requirements_ingest.txt
```

## Instalação manual por categoria

### 1. Dependências principais
```powershell
pip install pypdf python-docx psycopg2-binary pgvector openai langchain python-dotenv
```

### 2. OCR (opcional - apenas para PDFs baseados em imagem)
```powershell
# Instalar Tesseract primeiro:
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Depois instalar wrappers Python:
pip install pytesseract pdf2image pillow
```

### 3. Build (para criar executável)
```powershell
pip install pyinstaller
```

## Verificar instalação
```powershell
python -c "
import pypdf, docx, psycopg2, openai, dotenv, langchain
print('✅ Dependências principais OK')

try:
    import pytesseract, pdf2image, PIL
    print('✅ OCR disponível')
except ImportError:
    print('⚠️  OCR não disponível (opcional)')
"
```

## Uso

### Executar aplicativo
```powershell
python ingest_data.py
```

### Criar executável
```powershell
python build_ingest_executable.py
```

## Dependências mínimas vs completas

### Mínima (sem OCR):
- pypdf, python-docx
- psycopg2-binary, pgvector  
- openai, langchain, python-dotenv

### Completa (com OCR):
- Tudo acima +
- pytesseract, pdf2image, pillow
- Tesseract instalado no sistema