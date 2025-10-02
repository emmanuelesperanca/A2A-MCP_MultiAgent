#!/usr/bin/env python3
"""Script de teste para validar a classificação híbrida do Neoson."""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neoson import Neoson


async def testar_classificacao():
    """Testa a nova lógica de classificação híbrida."""
    print("🚀 === TESTE DA CLASSIFICAÇÃO HÍBRIDA NEOSON ===\n")
    
    # Inicializar Neoson
    neoson = Neoson()
    sucesso = await neoson.inicializar()
    
    if not sucesso:
        print("❌ Falha ao inicializar Neoson")
        return False
    
    print("✅ Neoson inicializado com sucesso!\n")
    
    # Casos de teste
    casos_teste = [
        # Casos óbvios que devem ser resolvidos por keywords
        ("Como solicitar férias?", "rh"),
        ("Preciso resetar minha senha", "ti"),
        ("Qual o benefício médico?", "rh"),
        ("Problema com VPN", "ti"),
        
        # Casos semânticos que precisam de embeddings
        ("Quero trabalhar remotamente", "rh"),  # home office
        ("Meu computador está lento", "ti"),    # performance
        ("Processo de avaliação de performance", "rh"),  # RH
        ("Como fazer backup dos meus dados", "ti"),      # TI
        
        # Casos ambíguos
        ("Como funciona o sistema de ponto?", "rh"),  # Pode ser RH ou TI
        ("Política de uso de equipamentos", "ti"),    # Pode ser RH ou TI
        
        # Casos que devem ir para geral
        ("Qual o horário da cantina?", "geral"),
        ("Como está o tempo hoje?", "geral"),
    ]
    
    print("📋 Executando casos de teste:\n")
    
    acertos = 0
    total = len(casos_teste)
    
    for i, (pergunta, esperado) in enumerate(casos_teste, 1):
        print(f"🔍 Teste {i}/{total}: {pergunta}")
        resultado = neoson.classificar_pergunta(pergunta)
        
        status = "✅" if resultado == esperado else "❌"
        print(f"{status} Resultado: {resultado.upper()} (esperado: {esperado.upper()})")
        
        if resultado == esperado:
            acertos += 1
        
        print("-" * 60)
    
    # Relatório final
    taxa_acerto = (acertos / total) * 100
    print("\n📊 RELATÓRIO FINAL:")
    print(f"   Acertos: {acertos}/{total} ({taxa_acerto:.1f}%)")
    
    if taxa_acerto >= 80:
        print("🎉 Classificação híbrida funcionando bem!")
    elif taxa_acerto >= 60:
        print("⚠️ Classificação precisa de ajustes nos thresholds")
    else:
        print("❌ Classificação precisa de revisão significativa")
    
    return taxa_acerto >= 80


if __name__ == "__main__":
    try:
        sucesso = asyncio.run(testar_classificacao())
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        sys.exit(1)