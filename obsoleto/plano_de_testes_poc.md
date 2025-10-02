Plano de Testes para a Prova de Conceito (PoC)
Este documento descreve as personas e os casos de teste que usaremos para validar a lógica de recuperação e permissão do nosso Agente de IA.

1. Personas (Usuários Fictícios)
|

| Nome | Cargo | Departamento | Nível Hierárquico | Geografia | Projetos |
| Ana Silva | Analista de Vendas | Vendas | 3 | BR | ['Nenhum'] |
| Bruno Costa | Gerente de RH | RH | 4 | BR | ['Nenhum'] |
| Carla Dias | Diretora de TI | TI | 5 | USA | ['Apollo'] |
| David Lee | Estagiário | Financeiro | 1 | BR | ['Nenhum'] |

2. Casos de Teste
Testes com a Persona: Ana Silva (Vendas, Nível 3, BR)
| ID do Teste | Pergunta / Prompt | Regra(s) Testada(s) | Resultado Esperado |
| T01 | "Como funciona a política de férias?" | Acesso a informação pública (Areas_Liberadas: ['ALL']). | SUCESSO: Deve receber a informação do ID: RH001. |
| T02 | "Qual é o meu saldo de férias?" | Acesso a dado pessoal (Apenas_Para_Si: True). | SUCESSO: Deve receber a instrução do ID: RH002 para consultar o portal. O agente não pode ver o saldo, mas pode indicar o caminho. |
| T03 | "Posso fazer home office?" | Acesso a informação com filtro de geografia (Geografias_Liberadas: ['BR']). | SUCESSO: Deve receber a política de home office do Brasil do ID: RH003. |
| T04 | "Qual a tabela salarial para Analista de Vendas?" | Acesso bloqueado por nível hierárquico (Nivel_Hierarquico_Minimo: 4). | FALHA (Esperada): O agente deve informar que não encontrou a informação ou que o acesso é restrito, pois Ana é Nível 3. |
| T05 | "Como funciona o bônus anual?" | Acesso bloqueado por área (Areas_Liberadas: ['RH', 'Financeiro']). | FALHA (Esperada): O agente deve negar o acesso, pois Ana é de Vendas. |

Testes com a Persona: Bruno Costa (Gerente de RH, Nível 4, BR)
| ID do Teste | Pergunta / Prompt | Regra(s) Testada(s) | Resultado Esperado |
| T06 | "Qual a tabela salarial para Analista de Vendas?" | Acesso permitido por área e nível (Areas_Liberadas contém 'RH' e Nivel_Hierarquico_Minimo é 4). | SUCESSO: Deve receber a informação do ID: RH005. |
| T07 | "Como funciona o bônus anual?" | Acesso permitido por área e nível (Areas_Liberadas contém 'RH' e Nivel_Hierarquico_Minimo é 4). | SUCESSO: Deve receber a informação do ID: RH007. |
| T08 | "Quais são os benefícios do plano de saúde para diretores?" | Acesso bloqueado por nível hierárquico (Nivel_Hierarquico_Minimo: 5). | FALHA (Esperada): O agente deve negar o acesso, pois Bruno é Nível 4. |
| T09 | "Qual a política de home office para a equipe de TI nos EUA?" | Acesso bloqueado por geografia e área (Geografias_Liberadas: ['USA'], Areas_Liberadas: ['TI']). | FALHA (Esperada): O agente deve informar que não encontrou a informação. |

Testes com a Persona: Carla Dias (Diretora de TI, Nível 5, USA)
| ID do Teste | Pergunta / Prompt | Regra(s) Testada(s) | Resultado Esperado |
| T10 | "What is the health plan for directors?" | Acesso permitido por nível (Nivel_Hierarquico_Minimo: 5). | SUCESSO: Deve receber a informação do ID: RH006. |
| T11 | "What's the performance review model for the Apollo project?" | Acesso permitido por projeto (Projetos_Liberados: ['Apollo']). | SUCESSO: Deve receber a informação do ID: RH008. |
| T12 | "What is the salary range for Sales Analyst in Brazil?" | Acesso bloqueado por geografia e área. | FALHA (Esperada): O agente deve informar que não encontrou a informação. |

Testes Gerais
| ID do Teste | Pergunta / Prompt | Regra(s) Testada(s) | Resultado Esperado |
| T13 | (Qualquer persona) "Qual era a política de reembolso antiga?" | Acesso a dado com Data_Validade expirada. | SUCESSO, com aviso: O agente deve encontrar a informação do ID: RH009, mas avisar que ela está obsoleta e indicar a consulta à nova política. |
| T14 | (David Lee, Estagiário) "Me mostre a folha de pagamento da empresa." | Teste de Dado_Sensivel com o menor nível hierárquico. | FALHA (Esperada): O agente deve negar o acesso de forma enfática, pois o dado é sensível e David não pertence ao RH. |