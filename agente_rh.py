"""Agente especializado em Recursos Humanos padronizado com a infraestrutura compartilhada."""

from __future__ import annotations

from textwrap import dedent
from typing import Optional

from subagents.base_subagent import BaseSubagent, SubagentConfig

PROMPT_TEMPLATE = dedent(
    """
    Você é Ana, uma especialista em Recursos Humanos. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas à área de RH.

    IMPORTANTE: Baseie suas respostas SOMENTE nas informações do contexto fornecido abaixo.

    DIRETRIZES DE RESPOSTA:
    - Adote tom profissional, cordial e acessível
    - Explique políticas e procedimentos de forma clara e compreensível
    - Mencione histórico prévio quando aplicável
    - Varie saudações e evite repetição excessiva
    - Utilize emojis moderadamente para humanizar a conversa (opcional)
    - Alerte quando o conteúdo parecer desatualizado ou incompleto

    CASOS ESPECIAIS:
    - Sem informação relevante: "Não localizei essa informação na base atual. Recomendo acionar o time de RH diretamente ou registrar um ticket conforme o procedimento padrão."
    - Informação restrita: "Essa informação é confidencial. Solicite autorização formal à liderança de RH ou registre um ticket justificando a necessidade."
    - Conteúdo possivelmente obsoleto: "⚠️ Atenção: essa informação pode estar desatualizada. Valide com o time de RH antes de seguir."

    {historico_conversa}CONTEXTO DISPONÍVEL:
    {contexto}

    PERGUNTA DO COLABORADOR:
    {pergunta}

    RESPOSTA (considere políticas de RH e histórico ao responder):
    """
).strip()

KEYWORDS = [
    'rh', 'recursos humanos', 'férias', 'benefícios', 'salário', 'contrato',
    'home office', 'folga', 'falta', 'atestado', 'demissão', 'contratação',
    'política', 'procedimento', 'vale refeição', 'vale transporte', 'plr',
    'décimo terceiro', 'licença', 'maternidade', 'paternidade', 'treinamento',
    'desenvolvimento', 'carreira', 'avaliação', 'desempenho', 'ponto',
    'horário', 'escala', 'banco de horas', 'overtime', 'extra'
]


class AgenteRH(BaseSubagent):
    """Agente especializado em Recursos Humanos configurado via infraestrutura compartilhada."""

    def __init__(self, *, debug: bool = False) -> None:
        config = SubagentConfig(
            identifier="rh",
            name="Ana",
            specialty="Recursos Humanos",
            description="Especialista em recursos humanos, políticas de pessoal, benefícios e procedimentos internos",
            keywords=KEYWORDS,
            table_name="knowledge_hr",
            prompt_template=PROMPT_TEMPLATE,
            debug=debug
        )
        super().__init__(config)


def criar_agente_rh(*, debug: bool = False) -> Optional[AgenteRH]:
    """Factory function para criar o agente de RH."""
    try:
        if debug:
            print("🏭 Criando agente RH padronizado...")

        agente = AgenteRH(debug=debug)

        if debug:
            print(f"✅ Agente RH criado: {agente.config.name}")
            print(f"📊 Keywords: {len(agente.config.keywords)} termos")
            print(f"🗄️ Tabela: {agente.config.table_name}")

        return agente

    except Exception as e:
        if debug:
            print(f"❌ Erro ao criar agente RH: {e}")
        return None


# Manter compatibilidade com o código existente
def inicializar_agente(*args, **kwargs):
    """Função de compatibilidade para manter o código existente funcionando."""
    return criar_agente_rh(**kwargs)


if __name__ == "__main__":
    # Teste do agente RH
    print("🧪 Testando Agente RH...")

    agente = criar_agente_rh(debug=True)

    if agente:
        print("✅ Agente RH inicializado com sucesso!")

        # Perfil de teste
        perfil_teste = {
            "nome": "João Silva",
            "cargo": "Analista",
            "area": "RH",
            "nivel_hierarquico": 3,
            "geografia": "BR",
            "projetos": ["Projeto X"]
        }

        # Teste de pergunta
        pergunta_teste = "Qual é a política de férias da empresa?"

        print(f"\n🎯 Pergunta de teste: {pergunta_teste}")
        resposta = agente.processar_pergunta(pergunta_teste, perfil_teste)
        print(f"🤖 Resposta: {resposta[:200]}...")

        print("\n📊 Informações do agente:")
        info = agente.obter_info_agente()
        for chave, valor in info.items():
            print(f"  {chave}: {valor}")
    else:
        print("❌ Falha na inicialização do agente RH")
