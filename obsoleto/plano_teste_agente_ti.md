# Plano de Teste – Validação do Agente de TI com a base `knowledge_tech`

## Objetivo
Confirmar que o agente Alex (TI) está consultando corretamente a base PostgreSQL `knowledge_tech`, recuperando documentos relevantes, aplicando as regras de governança e exibindo as fontes utilizadas ao final de cada resposta.

## Pré-requisitos
- Ambiente virtual `neoson` ativado e dependências instaladas (`pip install -r requirements.txt`).
- Variáveis de ambiente configuradas:
  - `OPENAI_API_KEY`
  - `KNOWLEDGE_TECH_DATABASE_URL` (ou `DATABASE_URL`) apontando para o Postgres com extensão `pgvector` habilitada.
  - `KNOWLEDGE_TECH_TABLE` (opcional; padrão `knowledge_tech`).
- Tabela `knowledge_tech` existente com as colunas mínimas: `id`, `conteudo_original`, `embedding`, `fonte_documento`, `areas_liberadas`, `nivel_hierarquico_minimo`, `geografias_liberadas`, `projetos_liberados`, `data_validade`, `apenas_para_si`, `responsavel`, `dado_sensivel`.

## Preparação dos dados
1. Escolha um documento de referência que esteja claramente relacionado à TI e tenha um campo `fonte_documento` identificável.
2. Se não houver um documento conhecido, insira manualmente um registro de teste. Exemplo SQL (ajuste os valores conforme necessário):
   ```sql
   INSERT INTO knowledge_tech (
       conteudo_original,
       embedding,
       fonte_documento,
       areas_liberadas,
       nivel_hierarquico_minimo,
       geografias_liberadas,
       projetos_liberados,
       data_validade,
       apenas_para_si,
       responsavel,
       dado_sensivel
   ) VALUES (
       'O procedimento para resetar senhas corporativas é feito via portal ServiceNow em service-now.example.com/reset.',
       pgvector_generate_embedding('text-embedding-3-small', 'O procedimento para resetar senhas corporativas é feito via portal ServiceNow em service-now.example.com/reset.'),
       'Procedimento Reset de Senhas v1',
       ARRAY['TI'],
       1,
       ARRAY['ALL'],
       ARRAY['ALL'],
       CURRENT_DATE + INTERVAL '30 day',
       FALSE,
       NULL,
       FALSE
   );
   ```
   > Observação: ajuste a função de geração de embedding para corresponder à configuração disponível no seu banco. Em ambientes sem função nativa, utilize o pipeline de ingestão `ingest_data.py` para gerar embeddings via API OpenAI.

## Execução do teste
1. Garanta que o agente de TI inicia sem erros:
   ```powershell
   conda run --name neoson python agente_ti.py
   ```
   - Esperado: logs indicando carregamento de configurações, conexão com o banco e mensagens "Agente de TI (Alex) pronto para uso!".
2. No prompt interativo aberto pelo script, utilize o perfil de exemplo apresentado no arquivo (`João Silva`). Faça uma pergunta diretamente relacionada ao documento preparado, por exemplo:
   ```text
   Como faço para resetar minha senha corporativa?
   ```
3. Caso esteja usando a aplicação completa (`app.py`), execute-a e use a interface para enviar a mesma pergunta, certificando-se de selecionar uma persona com acesso à área TI.

## Critérios de aceite
- A resposta do agente deve mencionar o conteúdo correspondente ao documento (ex.: o portal ServiceNow).
- A seção “Fontes consultadas” deve aparecer ao final da resposta com a referência do documento (`Procedimento Reset de Senhas v1` ou equivalente).
- O log do backend não deve apresentar erros de acesso ao banco nem exceções relacionadas ao vetor.
- Se o documento estiver restrito (ex.: `areas_liberadas` diferente de `ALL`), usuários sem permissão devem receber uma mensagem de acesso negado.

## Checks automatizados opcionais
- Verifique via SQL que o campo `embedding` não é nulo para os registros utilizados.
- Execute uma consulta rápida à tabela para confirmar que o documento está acessível:
  ```sql
  SELECT id, fonte_documento, areas_liberadas, data_validade
  FROM knowledge_tech
  ORDER BY id DESC
  LIMIT 5;
  ```

## Troubleshooting
- **Erro de conexão**: confirme as variáveis de ambiente e se o host/porta estão abertos.
- **Fonte não exibida**: verifique se o campo `fonte_documento` está preenchido no banco; caso contrário, o agente tentará usar `fonte`, `titulo` ou `id` como fallback.
- **Documento não retornado**: revise as regras de governança (área, nível hierárquico, geografia, projetos, validade e `apenas_para_si`).
- **Embeddings inconsistentes**: se os embeddings foram gerados com outro modelo, reprocessar o conteúdo com `ingest_data.py` para alinhar com `text-embedding-3-small`.
