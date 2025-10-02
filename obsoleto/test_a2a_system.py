"""Teste do sistema Agent-to-Agent (A2A) communication."""

import sys
import os
import logging

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import after path setup to avoid import errors
from a2a import AgentRegistry, DelegationRule  # noqa: E402
from subagents.base_subagent import BaseSubagent, SubagentConfig  # noqa: E402


def create_mock_rh_agent():
    """Cria um agente de RH mock para testes."""
    delegation_rules = [
        DelegationRule(
            name="financeiro_delegation",
            target_agent="finance",
            keywords=["custo", "orçamento", "valor", "preço", "financeiro", "gasto"],
            confidence_threshold=0.15,  # Reduzido para 1/6 das palavras
            description="Delega questões financeiras para o agente de finanças"
        ),
        DelegationRule(
            name="ti_delegation",
            target_agent="ti",
            keywords=["sistema", "erro", "login", "acesso", "senha", "VPN"],
            confidence_threshold=0.15,  # Reduzido para 1/6 das palavras
            description="Delega questões técnicas para o agente de TI"
        )
    ]
    
    config = SubagentConfig(
        identifier="rh",
        name="Sofia",
        specialty="Recursos Humanos",
        description="Especialista em RH com capacidades A2A",
        keywords=["férias", "benefícios", "salário", "contrato"],
        prompt_template="Você é Sofia, especialista em RH. {contexto}\n\nPergunta: {pergunta}\n\nResposta:",
        enable_a2a=True,
        delegation_rules=delegation_rules,
        debug=True
    )
    
    return BaseSubagent(config)


def create_mock_finance_agent():
    """Cria um agente financeiro mock para testes."""
    config = SubagentConfig(
        identifier="finance",
        name="Carlos",
        specialty="Finanças",
        description="Especialista financeiro",
        keywords=["orçamento", "custo", "ROI", "investimento"],
        prompt_template="Você é Carlos, especialista financeiro. {contexto}\n\nPergunta: {pergunta}\n\nResposta:",
        enable_a2a=False,  # Finance não delega por enquanto
        debug=True
    )
    
    return BaseSubagent(config)


def create_mock_ti_agent():
    """Cria um agente de TI mock para testes."""
    config = SubagentConfig(
        identifier="ti",
        name="Roberto",
        specialty="Tecnologia da Informação",
        description="Especialista em TI",
        keywords=["sistema", "erro", "rede", "servidor"],
        prompt_template="Você é Roberto, especialista em TI. {contexto}\n\nPergunta: {pergunta}\n\nResposta:",
        enable_a2a=False,  # TI não delega por enquanto
        debug=True
    )
    
    return BaseSubagent(config)


def test_delegation_rules():
    """Testa as regras de delegação."""
    print("🧪 Testando regras de delegação...")
    
    # Criar regra de teste
    rule = DelegationRule(
        name="test_rule",
        target_agent="finance",
        keywords=["custo", "preço", "orçamento"],
        confidence_threshold=0.33  # 1/3 das palavras deve ser suficiente
    )
    
    # Testar matches
    test_cases = [
        ("Qual o custo do novo benefício?", True),
        ("Preciso saber o preço do plano", True),
        ("Como solicitar férias?", False),
        ("Orçamento do projeto está aprovado?", True),
        ("O custo e orçamento do plano", True),
    ]
    
    for query, expected in test_cases:
        score = rule.matches(query)
        result = score > 0
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{query}' -> Score: {score:.2f}, Expected: {expected}, Got: {result}")
    
    print()


def test_a2a_basic_flow():
    """Testa o fluxo básico A2A."""
    print("🤝 Testando fluxo básico A2A...")
    
    try:
        # 1. Criar registry
        registry = AgentRegistry()
        print("✅ Registry A2A criado")
        
        # 2. Criar agentes mock (sem inicializar LLM para teste)
        rh_agent = create_mock_rh_agent()
        finance_agent = create_mock_finance_agent()
        ti_agent = create_mock_ti_agent()
        
        print("✅ Agentes mock criados")
        
        # 3. Registrar agentes
        registry.register_agent(rh_agent)
        registry.register_agent(finance_agent)
        registry.register_agent(ti_agent)
        
        print(f"✅ {len(registry.get_available_agents())} agentes registrados: {registry.get_available_agents()}")
        
        # 4. Testar identificação de delegação (sem LLM)
        print("\n📋 Testando identificação de delegação via regras...")
        
        test_queries = [
            "Qual o custo do novo plano de saúde?",
            "Problemas com login no sistema",
            "Como solicitar férias?",
            "Orçamento aprovado para contratação?"
        ]
        
        for query in test_queries:
            should_delegate, target, sub_query = rh_agent.can_delegate_query(query)
            print(f"  Query: '{query}'")
            print(f"    Delegar: {should_delegate}, Alvo: {target}, Sub-query: {sub_query}")
        
        # 5. Testar circuit breaker
        print("\n🔒 Testando circuit breaker...")
        cb = registry.circuit_breaker
        
        # Simular algumas falhas
        for i in range(4):
            cb.record_failure("rh", "finance", f"Erro teste {i}")
        
        is_blocked, reason = cb.is_route_blocked("rh", "finance")
        print(f"  Rota rh->finance bloqueada: {is_blocked} ({reason})")
        
        # Testar reset após sucesso
        cb.record_success("rh", "finance")
        is_blocked, reason = cb.is_route_blocked("rh", "finance")
        print(f"  Após sucesso - Bloqueada: {is_blocked}")
        
        # 6. Estatísticas
        stats = registry.get_stats()
        print(f"\n📊 Estatísticas do Registry:")
        print(f"  Agentes registrados: {stats['registered_agents']}")
        print(f"  Sessões ativas: {stats['active_sessions']}")
        print(f"  Mensagens totais: {stats['total_messages']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste A2A: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_session_tracking():
    """Testa o rastreamento de sessões A2A."""
    print("📝 Testando rastreamento de sessões...")
    
    try:
        from a2a import A2ASession, AgentMessage, MessageType
        
        # Criar sessão
        session = A2ASession(
            original_query="Teste de sessão A2A",
            user_profile={"nome": "João", "area": "TI"}
        )
        
        print(f"✅ Sessão criada: {session.session_id}")
        
        # Simular mensagens
        message1 = AgentMessage(
            sender="rh",
            recipient="finance",
            message_type=MessageType.DELEGATE,
            content="Qual o custo do benefício X?",
        )
        
        session.add_message(message1)
        
        message2 = AgentMessage(
            sender="finance", 
            recipient="rh",
            message_type=MessageType.RESPONSE,
            content="O custo é R$ 1000/mês"
        )
        
        session.add_message(message2)
        
        # Finalizar sessão
        session.finalize("Resposta final consolidada")
        
        print(f"✅ Sessão finalizada em {session.total_processing_time_ms}ms")
        print(f"✅ Agentes colaboradores: {session.contributing_agents}")
        
        # Testar summary de colaboração
        summary = session.get_collaboration_summary()
        print(f"📄 Summary: {summary[:100]}..." if len(summary) > 100 else f"📄 Summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de sessão: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🤝 TESTE DO SISTEMA A2A (Agent-to-Agent)")
    print("=" * 60)
    
    success = True
    
    # Teste 1: Regras de delegação
    test_delegation_rules()
    
    # Teste 2: Fluxo A2A básico
    if test_a2a_basic_flow():
        print("✅ Teste A2A básico passou!\n")
    else:
        print("❌ Teste A2A básico falhou!\n")
        success = False
    
    # Teste 3: Rastreamento de sessões
    if test_session_tracking():
        print("✅ Teste de sessões passou!\n")
    else:
        print("❌ Teste de sessões falhou!\n") 
        success = False
    
    print("=" * 60)
    if success:
        print("🎉 TODOS OS TESTES A2A PASSARAM!")
        print("Sistema A2A pronto para integração!")
    else:
        print("💥 ALGUNS TESTES A2A FALHARAM!")
        print("Verifique os erros acima.")
    print("=" * 60)