# 🚀 GUIA RÁPIDO - MELHORIAS v3.0

## 📋 O QUE MUDOU?

### ✅ 3 Melhorias Implementadas

1. **🔒 SEM LINKS** - Neoson nunca mais enviará links (segurança)
2. **📚 GLOSSÁRIO** - Reconhece 102 jargões da empresa automaticamente
3. **🤖 CLASSIFICAÇÃO INTELIGENTE** - LLM escolhe os melhores agentes

---

## 🎯 COMO USAR

### Nada Muda Para Você! 

As melhorias são **automáticas e invisíveis** para o usuário:

```python
# Continua usando normalmente:
resposta = await neoson.processar_pergunta_async(pergunta, perfil)

# Mas agora com:
# ✅ Links removidos automaticamente
# ✅ Jargões reconhecidos
# ✅ Classificação mais precisa
```

---

## 🧪 COMO TESTAR

### Opção 1: Script de Testes Completo

```powershell
# No terminal:
python test_melhorias_v3.py
```

Testa:
- ✅ Glossário (102 termos)
- ✅ Classificador LLM
- ✅ Remoção de links
- ✅ Integração completa

### Opção 2: Testar Individual

#### Teste 1: Glossário

```python
from core.glossario_corporativo import detectar_termos_corporativos

pergunta = "Como acesso o GBS para solicitar meu PPR?"
termos = detectar_termos_corporativos(pergunta)
print(termos)  # ['GBS', 'PPR']
```

#### Teste 2: Classificador

```python
from core.agent_classifier import AgentClassifier

classifier = AgentClassifier()
resultado = await classifier.classify_question("Como resetar senha do SAP?")

print(resultado['area_principal'])  # 'ti'
print(resultado['agentes_selecionados'])  # [enduser, governance, dev]
```

#### Teste 3: Links

```python
from neoson_async import NeosonAsync

neoson = NeosonAsync()
texto = "Acesse https://sap.com para mais info"
limpo = neoson.validar_resposta_sem_links(texto)

print(limpo)  # "Acesse [LINK REMOVIDO POR SEGURANÇA] para mais info"
```

---

## 📊 O QUE OBSERVAR

### Logs Importantes:

#### 1. Glossário Detectado
```
📚 Termos corporativos detectados: GBS, PPR, VDI
```

#### 2. Classificação LLM
```
🤖 Iniciando classificação inteligente (LLM)...
📊 Análise: Questão de acesso a sistema corporativo
🎯 Área: TI
🤖 Agentes selecionados:
  1. enduser (alta) - Suporte N1 para senha e acesso
  2. governance (media) - Políticas de senha aplicáveis
  3. infra (baixa) - Infraestrutura de sistemas
```

#### 3. Links Removidos
```
⚠️ 2 link(s) removido(s) da resposta por segurança
🔒 Links removidos: ['https://sap.com', 'www.totvs.com']
```

---

## 🆕 NOVOS METADADOS NA RESPOSTA

Agora a resposta inclui `metadata`:

```python
resultado = {
    'sucesso': True,
    'resposta': "...",
    'agente_usado': "Marina",
    'especialidade': "TI",
    'classificacao': "ti",
    'metadata': {  # 🆕 NOVO!
        'termos_corporativos': ['SAP', 'PPR'],
        'agentes_consultados': ['enduser', 'governance'],
        'analise': "Questão de acesso a sistema",
        'links_removidos': True
    }
}
```

### Como Usar os Metadados:

```python
# Dashboard: Mostrar termos detectados
termos = resultado['metadata']['termos_corporativos']
print(f"Jargões usados: {', '.join(termos)}")

# Analytics: Rastrear agentes mais usados
agentes = resultado['metadata']['agentes_consultados']
# Salvar para análise

# Segurança: Auditar remoções de links
if resultado['metadata']['links_removidos']:
    logging.warning(f"Links removidos na pergunta: {id_conversa}")
```

---

## 📚 ADICIONAR NOVOS TERMOS AO GLOSSÁRIO

### Passo 1: Abrir o arquivo
```
core/glossario_corporativo.py
```

### Passo 2: Adicionar termo
```python
GLOSSARIO_CORPORATIVO = {
    # ... termos existentes ...
    
    # 🆕 Adicionar aqui:
    "NOVO_TERMO": "Descrição clara do termo interno da empresa",
}
```

### Passo 3: Pronto!
✅ Termo será detectado automaticamente
✅ Contexto adicionado nas perguntas
✅ Zero configuração adicional

---

## 🔧 CONFIGURAÇÕES

### Desabilitar Glossário (se necessário)

```python
# Em neoson_async.py
neoson = NeosonAsync()
neoson.glossario_ativo = False  # Desabilita glossário
```

### Desabilitar Remoção de Links (NÃO RECOMENDADO)

```python
# Em neoson_async.py
neoson = NeosonAsync()
neoson.proibir_links = False  # ⚠️ RISCO DE SEGURANÇA
```

### Ajustar Temperatura do Classificador

```python
# Em core/agent_classifier.py, linha ~200
temperature=0.3  # Padrão: 0.3 (mais consistente)
# Aumentar para 0.5-0.7 = mais criativo
# Diminuir para 0.1 = mais determinístico
```

---

## 🐛 TROUBLESHOOTING

### Problema 1: Classificação Errada

**Sintoma:** Pergunta direcionada para agente errado

**Solução:**
1. Verificar logs de classificação LLM
2. Verificar se pergunta tem informações suficientes
3. Ajustar descrição do agente em `core/agent_classifier.py`

### Problema 2: Termo Não Detectado

**Sintoma:** Jargão não é reconhecido

**Solução:**
1. Adicionar termo ao glossário
2. Verificar grafia (case-insensitive)
3. Reiniciar sistema

### Problema 3: Link Não Removido

**Sintoma:** Link passou pela validação

**Solução:**
1. Verificar se `proibir_links = True`
2. Adicionar novo padrão regex em `validar_resposta_sem_links()`
3. Reportar padrão não coberto

---

## 📈 MÉTRICAS RECOMENDADAS

### Dashboard de Classificação
```python
# Rastrear por período:
- Total de classificações
- Área mais usada (TI vs RH)
- Agente mais consultado
- Taxa de sucesso (metadata)
```

### Dashboard de Glossário
```python
# Rastrear:
- Termos mais detectados (top 10)
- Perguntas com múltiplos termos
- Novos termos sugeridos
```

### Dashboard de Segurança
```python
# Rastrear:
- Total de links removidos
- Padrões de links tentados
- Usuários que tentaram enviar links (se foi resposta do sistema)
```

---

## 📞 SUPORTE

### Dúvidas?

1. Ler `docs/MELHORIAS_FEEDBACK_EQUIPE.md` (documentação completa)
2. Rodar `python test_melhorias_v3.py` (testes)
3. Verificar logs do sistema

### Bugs/Sugestões?

1. Adicionar ao backlog
2. Testar com `test_melhorias_v3.py`
3. Documentar comportamento esperado vs atual

---

## ✅ CHECKLIST DE VALIDAÇÃO

Antes de colocar em produção, validar:

- [ ] Glossário reconhece termos comuns (SAP, PPR, GBS, VDI)
- [ ] Classificador direciona corretamente (testar 10 perguntas)
- [ ] Links são removidos (testar http://, www., markdown)
- [ ] Logs aparecem corretamente no console
- [ ] Metadata está populada nas respostas
- [ ] Performance aceitável (< 5s por pergunta)

---

**Versão:** 3.0.0  
**Data:** 09/10/2025  
**Status:** ✅ Pronto para uso
