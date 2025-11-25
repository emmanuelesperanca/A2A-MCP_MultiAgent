# 🔍 Guia de Instalação - Tesseract OCR

## 📋 Visão Geral

O Tesseract é necessário para processar PDFs baseados em imagens (documentos escaneados). Sem ele, apenas PDFs com texto selecionável funcionarão.

---

## 🎯 Opção 1: Inclusão Automática no Build (Recomendado)

### Passo 1: Instalar o Tesseract no seu computador

**Windows:**
1. Baixe o instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Execute o instalador
3. **IMPORTANTE:** Durante a instalação, marque "Add to PATH" (adicionar ao PATH)
4. Instale em uma das localizações padrão:
   - `C:\Program Files\Tesseract-OCR\` (recomendado)
   - `C:\Program Files (x86)\Tesseract-OCR\`

**Via Chocolatey:**
```powershell
choco install tesseract
```

### Passo 2: Verificar instalação
```powershell
tesseract --version
```

Deve mostrar:
```
tesseract v5.x.x
 leptonica-1.x.x
  libgif 5.x.x : libjpeg 9e : libpng 1.6.x : libtiff 4.x.x : zlib 1.x.x
```

### Passo 3: Rebuild do executável

O `neoson.spec` foi atualizado para detectar automaticamente o Tesseract:

```powershell
pyinstaller neoson.spec --clean --noconfirm
```

Durante o build, você verá:
```
🔍 Procurando Tesseract OCR...
✅ Tesseract encontrado e incluído: C:\Program Files\Tesseract-OCR
   📄 Executável: tesseract.exe
   📁 Dados: tessdata/
```

**Pronto!** O Tesseract estará incluído no executável automaticamente.

---

## 🎯 Opção 2: Cópia Manual (Para distribuição)

Se você já buildou o executável **SEM** o Tesseract instalado, pode adicionar depois:

### Estrutura necessária:

```
dist/neoson/
├── neoson.exe
├── _internal/
├── tesseract/              ← Criar essa pasta
│   ├── tesseract.exe       ← Copiar daqui
│   └── tessdata/           ← Copiar daqui
│       ├── eng.traineddata
│       ├── por.traineddata
│       └── osd.traineddata
├── templates/
├── static/
└── .env
```

### Passos:

1. **Baixe o Tesseract** (mesmo link acima)

2. **Extraia os arquivos necessários:**
   ```
   De: C:\Program Files\Tesseract-OCR\
   
   Copiar:
   ├── tesseract.exe          → dist/neoson/tesseract/tesseract.exe
   └── tessdata/              → dist/neoson/tesseract/tessdata/
       ├── eng.traineddata    (inglês)
       ├── por.traineddata    (português)
       └── osd.traineddata    (detecção de orientação)
   ```

3. **Estrutura final:**
   ```
   dist/neoson/tesseract/tesseract.exe
   dist/neoson/tesseract/tessdata/eng.traineddata
   dist/neoson/tesseract/tessdata/por.traineddata
   dist/neoson/tesseract/tessdata/osd.traineddata
   ```

4. **Execute o neoson.exe** - O hook irá detectar automaticamente!

---

## 🎯 Opção 3: Instalação Separada (Não recomendado)

O usuário final instala o Tesseract no computador dele.

**Desvantagens:**
- Requer instalação adicional
- Pode causar problemas de PATH
- Mais suporte necessário

**Como funciona:**
1. Usuário instala Tesseract de: https://github.com/UB-Mannheim/tesseract/wiki
2. Adiciona ao PATH do sistema
3. Reinicia o computador
4. Executa o neoson.exe

---

## 🧪 Testando

### 1. Verifique se o Tesseract foi detectado

Ao iniciar o `neoson.exe`, verifique o console:

✅ **Funcionando:**
```
✅ Tesseract configurado: C:\...\dist\neoson\tesseract\tesseract.exe
```

❌ **Não encontrado:**
```
⚠️ Tesseract não encontrado em: C:\...\dist\neoson\tesseract\tesseract.exe
```

### 2. Teste com PDF escaneado

1. Acesse: http://localhost:8000
2. Vá em "Base de Conhecimento"
3. Faça upload de um PDF escaneado (imagem)
4. Aguarde o processamento

✅ **Sucesso:**
```
[13:00:15] 📄 Processando: documento_escaneado.pdf
[13:00:18] → Extraindo texto via OCR...
[13:00:45] ✅ documento_escaneado.pdf processado com sucesso!
```

❌ **Erro:**
```
[13:00:15] 📄 Processando: documento_escaneado.pdf
[13:00:16] ❌ Erro: OCR não disponível
```

---

## 📊 Tamanho do Executável

- **Sem Tesseract:** ~200-250 MB
- **Com Tesseract:** ~280-320 MB (+80 MB)

O Tesseract adiciona:
- `tesseract.exe`: ~3 MB
- `tessdata/eng.traineddata`: ~15 MB
- `tessdata/por.traineddata`: ~15 MB
- Bibliotecas de suporte: ~50 MB

---

## 🔧 Troubleshooting

### Erro: "OCR não disponível"

**Causa:** Tesseract não encontrado

**Solução:**
1. Verifique se a pasta `tesseract/` existe em `dist/neoson/`
2. Verifique se `tesseract.exe` está dentro dela
3. Verifique se `tessdata/` tem os arquivos `.traineddata`

### Erro: "Error opening data file"

**Causa:** Arquivos de idioma faltando

**Solução:**
Copie os arquivos de idioma necessários para `dist/neoson/tesseract/tessdata/`:
- `eng.traineddata` (inglês)
- `por.traineddata` (português)
- `osd.traineddata` (detecção de orientação)

Baixe de: https://github.com/tesseract-ocr/tessdata

### Erro: "Failed loading language"

**Causa:** Arquivo de idioma corrompido

**Solução:**
Re-baixe o arquivo `.traineddata` correspondente

---

## 📝 Notas Importantes

### Idiomas Suportados

Por padrão, o código usa: `lang='por+eng'` (português + inglês)

Para adicionar outros idiomas:
1. Baixe o `.traineddata` de: https://github.com/tesseract-ocr/tessdata
2. Copie para `dist/neoson/tesseract/tessdata/`
3. Modifique `api_knowledge.py` linha 72:
   ```python
   # Adicionar espanhol
   texto_pagina = pytesseract.image_to_string(image, lang='por+eng+spa')
   ```

### Performance

- DPI padrão: 300 (boa qualidade)
- Tempo médio: 2-5 segundos por página
- PDFs grandes (>50 páginas) podem demorar vários minutos

### Quando o OCR NÃO é necessário

O sistema funciona **sem OCR** para:
- PDFs com texto selecionável (nativos)
- Arquivos DOCX
- Arquivos TXT

O OCR só é usado quando:
- PDF não tem texto extraível
- Documento é escaneado/fotografado
- PDF é baseado em imagens

---

## 🚀 Resumo Rápido

### Para desenvolvimento:
```powershell
# Instalar Tesseract
choco install tesseract

# Rebuild
pyinstaller neoson.spec --clean --noconfirm
```

### Para distribuição:
```
Opção 1: Build com Tesseract (recomendado)
→ Instale Tesseract antes de buildar

Opção 2: Adicione manualmente
→ Copie tesseract/ para dist/neoson/
```

### Verificação:
```
✅ Tesseract detectado no console ao iniciar
✅ PDFs escaneados processam com sucesso
✅ Tempo de OCR razoável (2-5s por página)
```

---

## 📚 Links Úteis

- **Download Tesseract:** https://github.com/UB-Mannheim/tesseract/wiki
- **Idiomas (tessdata):** https://github.com/tesseract-ocr/tessdata
- **Documentação oficial:** https://github.com/tesseract-ocr/tesseract
- **pytesseract (Python wrapper):** https://pypi.org/project/pytesseract/

---

**Última atualização:** 22/10/2025
