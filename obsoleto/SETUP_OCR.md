# Configuração OCR para PDFs baseados em imagem

## Pré-requisitos

### 1. Instalar Tesseract OCR
**Windows:**
```powershell
# Opção 1: Via Chocolatey (recomendado)
choco install tesseract

# Opção 2: Download direto
# Baixe de: https://github.com/UB-Mannheim/tesseract/wiki
# Instale e adicione ao PATH: C:\Program Files\Tesseract-OCR
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-por
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

### 2. Instalar dependências Python
```powershell
conda activate neoson
pip install pytesseract pdf2image pillow
```

### 3. Configuração automática
O `ingest_data.py` agora detecta automaticamente o Tesseract nos seguintes locais:
- `C:\Users\u137147\AppData\Local\Programs\Tesseract-OCR\tesseract.exe` ✅
- `C:\Program Files\Tesseract-OCR\tesseract.exe`
- `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`

### 4. Testar instalação
```python
import pytesseract
print(pytesseract.get_tesseract_version())
```

## Como funciona no ingest_data.py

1. **Tentativa padrão**: Extrai texto com `pypdf` normalmente
2. **Detecção de PDF baseado em imagem**: Se texto extraído < 50 caracteres
3. **Fallback OCR**: Converte PDF para imagens e aplica OCR
4. **Logs detalhados**: Mostra progresso de conversão e OCR por página

## Idiomas suportados
- Português: `por` (padrão)
- Inglês: `eng` (padrão) 
- Espanhol: `spa`

Para adicionar outros idiomas:
```bash
# Linux
sudo apt install tesseract-ocr-spa

# Windows - baixar pacotes de idioma do GitHub do Tesseract
```

## Limitações
- OCR é mais lento que extração direta de texto
- Qualidade depende da resolução e clareza do PDF original
- Requer mais RAM para PDFs grandes (muitas páginas)

## Troubleshooting
- **Erro "tesseract not found"**: Verificar PATH do sistema
- **Erro de memória**: Reduzir DPI ou processar páginas individualmente
- **Texto mal reconhecido**: Melhorar qualidade do PDF original