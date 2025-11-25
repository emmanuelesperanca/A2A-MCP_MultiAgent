# 🎯 QUICK START - Base de Conhecimento

## ⚡ Para Usar Agora (5 minutos)

### 1. Instale as dependências que faltam
```powershell
pip install pypdf==4.0.1 python-docx==1.1.0
```

### 2. Inicie o servidor
```powershell
uvicorn app_fastapi:app --reload
```

### 3. Acesse a interface
1. Abra: http://localhost:8000
2. Faça login (usuario: admin, senha: admin)
3. Clique em **"Base de Conhecimento"** no sidebar esquerdo

### 4. Faça seu primeiro upload
1. **Arraste um PDF** para a área de upload (ou clique para selecionar)
2. **Escolha o agente**: Ex: "Neoson - Conhecimento Geral"
3. **Preencha os campos obrigatórios**:
   ```
   Áreas Liberadas: ALL
   Geografias Liberadas: ALL
   Projetos Liberados: ALL
   Nível Hierárquico: 1
   Idioma: pt-br
   ```
4. Clique em **"Iniciar Ingestão"**
5. Aguarde o processamento (acompanhe o log)

### 5. Veja o resultado
```
✅ Arquivo: seu-arquivo.pdf
  → Enviando arquivo para o servidor...
  → Texto extraído: 2345 caracteres
  → Chunks gerados: 3
  → Embeddings criados: 3
  → Inseridos no banco: 3

✅ Ingestão concluída com sucesso!
```

---

## 📊 O Que Acontece nos Bastidores

```
PDF/DOCX → Extração de Texto → Limpeza → Chunking → Embeddings → PostgreSQL
   ↓              ↓                ↓          ↓           ↓            ↓
Arquivo      pypdf/docx      Normalização  1000chars  OpenAI API   Vetores 1536D
```

---

## 🎯 15 Agentes Disponíveis

### 🧑‍💼 RH (3 agentes)
- Benefícios
- Folha de Pagamento
- Recrutamento

### 💻 TI (7 agentes)
- Infraestrutura
- Redes
- Segurança
- Armazenamento
- Bancos de Dados
- Monitoramento
- Cloud

### 🏢 Enterprise (2 agentes)
- ERP
- Business Intelligence

### 🎯 Outros (3 agentes)
- CRM
- Service Desk
- Neoson (conhecimento geral)

---

## 📚 Metadados de Governança

### Obrigatórios ✅
- **Áreas Liberadas**: Quais áreas podem acessar (RH, TI, ALL, etc.)
- **Geografias Liberadas**: Regiões permitidas (BR, US, ALL, etc.)
- **Projetos Liberados**: Projetos específicos ou ALL
- **Nível Hierárquico Mínimo**: 1-5 (1=Estagiário, 5=Executivo)
- **Idioma**: pt-br, en-us ou es-es

### Opcionais ❌
- Data de Validade
- Responsável pelo conteúdo
- Aprovador
- Dado Sensível (checkbox)
- Apenas Para SI (checkbox)

---

## 🔍 Exemplo Prático

### Cenário: Adicionar Manual de Onboarding

```
1. Arquivo: manual_onboarding_2024.pdf
2. Agente: Agente RH - Recrutamento
3. Metadados:
   - Áreas: RH
   - Geografias: BR
   - Projetos: ALL
   - Nível: 1 (todos)
   - Idioma: pt-br
   - Responsável: Maria Silva
   - Aprovador: João Santos
```

**Resultado**: O manual será dividido em chunks, transformado em vetores e disponibilizado para o agente de Recrutamento responder perguntas sobre onboarding.

---

## 🛠️ Troubleshooting Rápido

### ❌ "Module not found: pypdf"
```powershell
pip install pypdf==4.0.1
```

### ❌ "Module not found: docx"
```powershell
pip install python-docx==1.1.0
```

### ❌ "Não foi possível extrair texto"
- PDF é escaneado? Instale Tesseract OCR:
  - Windows: https://github.com/UB-Mannheim/tesseract/wiki
  - Linux: `sudo apt-get install tesseract-ocr`

### ❌ "Erro ao gerar embeddings"
- Verifique se tem créditos na OpenAI: https://platform.openai.com/usage
- API key está correta? (já configurada no código)

### ❌ "Erro ao inserir no banco"
- Verifique se a tabela existe no PostgreSQL
- Verifique a conexão DATABASE_URL

---

## 📈 Performance Esperada

| Tamanho do Documento | Tempo de Processamento |
|----------------------|------------------------|
| 1-5 páginas          | ~5 segundos           |
| 10-30 páginas        | ~15 segundos          |
| 50-100 páginas       | ~45 segundos          |
| 200+ páginas         | ~2 minutos            |

---

## 🎓 Onde Encontrar Mais Informações

1. **Guia do Usuário Completo**
   - `docs/KNOWLEDGE_BASE_GUIDE.md`
   - Como usar, best practices, troubleshooting detalhado

2. **Documentação Técnica**
   - `docs/KNOWLEDGE_IMPLEMENTATION.md`
   - Arquitetura, código, database schema, deployment

3. **Resumo Executivo**
   - `docs/KNOWLEDGE_BASE_SUMMARY.md`
   - Status, checklist, próximos passos

---

## ✅ Checklist de Primeiro Uso

- [ ] Instalar pypdf e python-docx
- [ ] Iniciar servidor com uvicorn
- [ ] Fazer login na interface
- [ ] Acessar "Base de Conhecimento"
- [ ] Fazer upload de um PDF de teste
- [ ] Preencher metadados obrigatórios
- [ ] Iniciar ingestão
- [ ] Verificar log de sucesso
- [ ] Confirmar no banco de dados

---

## 🎉 Pronto!

Sua Base de Conhecimento está **100% operacional**. 

Qualquer dúvida, consulte a documentação completa em:
- `docs/KNOWLEDGE_BASE_GUIDE.md`
- `docs/KNOWLEDGE_IMPLEMENTATION.md`

**Happy Knowledge Injecting! 🚀**
