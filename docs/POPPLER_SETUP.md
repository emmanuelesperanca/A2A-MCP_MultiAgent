# 📄 Guia de Instalação - Poppler (PDF para Imagem)

## ⚠️ IMPORTANTE: Poppler é OBRIGATÓRIO para OCR de PDFs!

O **Poppler** converte PDFs em imagens. Sem ele, o Tesseract não consegue fazer OCR.

---

## 🎯 Solução: Incluir Poppler no Build

### Passo 1: Download do Poppler

**Link:** https://github.com/oschwartz10612/poppler-windows/releases/

1. Baixe a versão mais recente: `Release-XX.XX.X-0.zip`
2. Extraia o arquivo ZIP

### Passo 2: Copiar para hooks/

Copie a pasta extraída para dentro de `hooks/`:

```
agente_ia_poc/
├── hooks/
│   ├── Tesseract-OCR/          ← Você já tem
│   ├── poppler/                ← ADICIONE ESTA
│   │   ├── Library/
│   │   │   ├── bin/            ← DLLs do Poppler aqui
│   │   │   │   ├── pdfinfo.exe
│   │   │   │   ├── pdftoppm.exe
│   │   │   │   ├── pdftocairo.exe
│   │   │   │   └── várias .dll
│   │   │   └── ...
│   │   └── ...
│   └── pyi_rth_tesseract.py
```

### Passo 3: Rebuild

```powershell
pyinstaller neoson.spec --clean --noconfirm
```

Durante o build você verá:

```
🔍 Incluindo Poppler (para pdf2image)...
✅ Poppler incluído da pasta local: C:\...\hooks\poppler
   📦 Total de arquivos: XX
   📁 Library/bin/ com DLLs incluído
```

---

## 🧪 Testando

### 1. Verifique o console do executável

Ao processar um PDF escaneado, você deve ver:

```
🔍 === DIAGNÓSTICO OCR ===
📁 Base path: C:\...\dist\neoson\_internal
📄 Tesseract.exe: ...\tesseract\tesseract.exe
   Existe: True
✅ Tesseract configurado!

📄 Convertendo PDF para imagens (usando Poppler)...
✅ Poppler encontrado: C:\...\poppler\Library\bin
✅ 5 páginas convertidas
   🔍 Processando página 1/5...
      ✅ 1234 caracteres extraídos
...
✅ OCR concluído: 6789 caracteres totais
```

### 2. Erros Comuns

#### ❌ "Erro ao converter PDF - Poppler não disponível"

**Causa:** Poppler não está na pasta correta

**Solução:**
1. Verifique se `dist/neoson/_internal/poppler/Library/bin/` existe
2. Verifique se contém `pdftoppm.exe` e DLLs
3. Se não, baixe e coloque em `hooks/poppler/` e rebuilde

#### ❌ "Unable to get page count. Is poppler installed?"

**Causa:** DLLs do Poppler não encontradas

**Solução:**
1. Verifique se `poppler/Library/bin/` tem todas as DLLs:
   - `libcairo-2.dll`
   - `libfreetype-6.dll`
   - `libglib-2.0-0.dll`
   - `libpng16-16.dll`
   - `libpoppler-glib-8.dll`
   - E outras...
2. Baixe a versão completa do Poppler (não minimal)

---

## 📊 Estrutura Final

Após o build, a estrutura deve ser:

```
dist/neoson/
├── neoson.exe
├── _internal/
│   ├── tesseract/
│   │   ├── tesseract.exe
│   │   ├── tessdata/
│   │   └── DLLs do Tesseract
│   ├── poppler/
│   │   └── Library/
│   │       └── bin/
│   │           ├── pdftoppm.exe      ← Converte PDF → PNG
│   │           ├── pdfinfo.exe
│   │           └── várias .dll       ← Bibliotecas necessárias
│   ├── templates/
│   └── static/
└── .env
```

---

## 🔄 Fluxo Completo de OCR

```
1. PDF Escaneado
   ↓
2. Poppler (pdf2image)
   → Converte PDF em imagens PNG
   ↓
3. Tesseract (pytesseract)
   → Faz OCR nas imagens
   ↓
4. Texto extraído
```

**SEM Poppler:** Tudo falha no passo 2 ❌

---

## 📝 Checklist

- [ ] Download do Poppler
- [ ] Extrair ZIP
- [ ] Copiar para `hooks/poppler/`
- [ ] Verificar estrutura: `hooks/poppler/Library/bin/pdftoppm.exe`
- [ ] Rebuild: `pyinstaller neoson.spec --clean --noconfirm`
- [ ] Verificar logs: "✅ Poppler incluído"
- [ ] Testar com PDF escaneado
- [ ] Verificar OCR funcionando

---

## 🚀 Resumo

1. **Baixe:** https://github.com/oschwartz10612/poppler-windows/releases/
2. **Extraia para:** `hooks/poppler/`
3. **Rebuild:** `pyinstaller neoson.spec --clean --noconfirm`
4. **Teste:** Upload de PDF escaneado

**Tamanho adicional:** ~15-20 MB

---

**Última atualização:** 22/10/2025
