# Build do Executável Ingest_Data com OCR

## Como usar

### 1. Preparação
```powershell
# Ativar ambiente conda
conda activate neoson

# Navegar para o diretório do projeto
cd "c:/Users/u137147/OneDrive - Straumann Group/Documents/Automacoes/Neoson Reborn/agente_ia_poc"
```

### 2. Executar o build automatizado
```powershell
python build_ingest_executable.py
```

Este script automaticamente:
- ✅ Detecta o Tesseract instalado em `C:\Users\u137147\AppData\Local\Programs\Tesseract-OCR`
- ✅ Instala dependências necessárias (pyinstaller, pytesseract, pdf2image, pillow)
- ✅ Cria arquivo `.spec` personalizado incluindo binários do Tesseract
- ✅ Inclui dados de idioma (português e inglês)
- ✅ Gera executável único `ingest_data.exe` em `dist/`

### 3. Comando manual alternativo (se preferir)
```powershell
# Instalar PyInstaller se necessário
pip install pyinstaller pytesseract pdf2image pillow

# Comando completo com todas as dependências OCR
pyinstaller --onefile --windowed ^
    --add-data ".env;." ^
    --add-binary "C:\Users\u137147\AppData\Local\Programs\Tesseract-OCR\tesseract.exe;tesseract" ^
    --add-binary "C:\Users\u137147\AppData\Local\Programs\Tesseract-OCR\*.dll;tesseract" ^
    --add-data "C:\Users\u137147\AppData\Local\Programs\Tesseract-OCR\tessdata\*.traineddata;tesseract\tessdata" ^
    --hidden-import pytesseract ^
    --hidden-import pdf2image ^
    --hidden-import PIL ^
    --hidden-import psycopg2 ^
    --hidden-import pgvector ^
    ingest_data.py
```

### 4. Estrutura do executável final
```
ingest_data.exe (contém internamente:)
├── ingest_data.py (código principal)
├── tesseract/
│   ├── tesseract.exe
│   ├── *.dll (bibliotecas)
│   └── tessdata/
│       ├── por.traineddata (português)
│       └── eng.traineddata (inglês)
├── .env (se existir)
└── todas as dependências Python
```

## Vantagens do script automatizado

1. **Detecção automática**: Encontra Tesseract automaticamente
2. **Inclusão completa**: Todos os arquivos OCR necessários
3. **Configuração runtime**: Hook configura pytesseract automaticamente
4. **Portabilidade**: Executável funciona em máquinas sem Tesseract instalado
5. **Logs detalhados**: Mostra progresso e erros claramente

## Troubleshooting

### Erro "tesseract not found" no executável
- Verifique se o build incluiu a pasta `tesseract/` corretamente
- O script automatizado resolve isso automaticamente

### Executável muito grande (>100MB)
- Normal devido à inclusão do Tesseract completo
- Para reduzir: remover idiomas não utilizados do tessdata

### Erro de DLL faltando
- O script inclui automaticamente todas as DLLs necessárias
- Se ainda ocorrer, copie manualmente DLLs adicionais

### Performance lenta do OCR
- OCR é naturalmente mais lento que extração direta
- Use apenas para PDFs que realmente precisam (automático no código)