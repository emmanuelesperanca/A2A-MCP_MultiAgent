"""Script utilitário para validar a conexão com a base `knowledge_tech`.

Executa duas checagens:
1. Consulta direta à tabela para verificar contagem de registros e últimas fontes
2. Busca vetorial usando o mesmo fluxo do Agente de TI (Alex)

Uso básico:
    conda run --name neoson python test_connection_knowledge_tech.py \
        --question "Como redefinir minha senha do domínio?"
"""
from __future__ import annotations

import argparse
import os
import sys
from textwrap import shorten
from typing import Dict, List

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from postgres_vector_store import PostgresVectorStore


def carregar_configuracoes() -> Dict[str, str]:
    """Carrega variáveis de ambiente necessárias para o teste."""
    load_dotenv()

    dsn = os.getenv("KNOWLEDGE_TECH_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("Configure KNOWLEDGE_TECH_DATABASE_URL ou DATABASE_URL nas variáveis de ambiente.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("A variável de ambiente OPENAI_API_KEY é obrigatória para gerar embeddings.")

    table_name = os.getenv("KNOWLEDGE_TECH_TABLE", "knowledge_tech")

    return {"dsn": dsn, "api_key": api_key, "table_name": table_name}


def coletar_overview_base(store: PostgresVectorStore) -> Dict[str, List[Dict[str, str]]]:
    """Retorna métricas simples da tabela, como contagem total e últimas fontes."""
    with store._connection() as conn:  # noqa: SLF001 - uso interno aceitável para script de teste
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                sql.SQL("SELECT COUNT(*) AS total FROM {table};").format(
                    table=sql.Identifier(store.table_name)
                )
            )
            total = cur.fetchone()["total"]

            cur.execute(
                sql.SQL(
                    """
                    SELECT id, fonte_documento, data_ingestao
                    FROM {table}
                    ORDER BY data_ingestao DESC NULLS LAST, id DESC
                    LIMIT 5;
                    """
                ).format(table=sql.Identifier(store.table_name))
            )
            recentes = cur.fetchall()

    return {"total": total, "recentes": recentes}


def executar_busca_vetorial(
    store: PostgresVectorStore,
    embeddings: OpenAIEmbeddings,
    pergunta: str,
    *,
    top_k: int,
) -> List[Dict[str, str]]:
    consulta_embedding = embeddings.embed_query(pergunta)
    candidatos = store.similarity_search(consulta_embedding, limit=top_k)
    return candidatos


def imprimir_relatorio(overview: Dict[str, List[Dict[str, str]]], resultados: List[Dict[str, str]]) -> None:
    print("\n=== Visão Geral da Tabela ===")
    print(f"Total de registros: {overview['total']}")
    if overview["recentes"]:
        print("Últimas fontes ingeridas:")
        for registro in overview["recentes"]:
            fonte = registro.get("fonte_documento") or "(sem fonte)"
            data_ingestao = registro.get("data_ingestao")
            print(f"  - ID {registro['id']}: {fonte} | data_ingestao={data_ingestao}")
    else:
        print("Nenhum registro encontrado na tabela.")

    print("\n=== Resultado da Busca Vetorial ===")
    if not resultados:
        print("Nenhum documento retornado para a pergunta informada.")
        return

    for idx, registro in enumerate(resultados, start=1):
        fonte = registro.get("fonte_documento") or registro.get("fonte") or registro.get("id")
        distancia = registro.get("distancia")
        conteudo = shorten((registro.get("conteudo_original") or "").replace("\n", " "), width=160, placeholder="...")
        print(f"[{idx}] Fonte: {fonte} | Distância: {distancia:.4f}")
        print(f"     Conteúdo: {conteudo}")

    fontes = [registro.get("fonte_documento") or registro.get("fonte") or str(registro.get("id")) for registro in resultados]
    fontes_unicas = [fonte for i, fonte in enumerate(fontes) if fonte and fonte not in fontes[:i]]
    if fontes_unicas:
        print("\nFontes consultadas:")
        for fonte in fontes_unicas:
            print(f"  - {fonte}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida a conexão e a busca vetorial da base knowledge_tech.")
    parser.add_argument(
        "--question",
        default="Como faço para resetar minha senha corporativa?",
        help="Pergunta usada para gerar o embedding de teste.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Quantidade de documentos a retornar na busca vetorial.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        cfg = carregar_configuracoes()
    except RuntimeError as exc:
        print(f"[ERRO] {exc}")
        return 1

    print("🔌 Testando conexão com a base knowledge_tech...")
    try:
        store = PostgresVectorStore(cfg["table_name"], dsn=cfg["dsn"], min_connections=1, max_connections=2)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERRO] Não foi possível criar o pool de conexões: {exc}")
        return 1

    try:
        overview = coletar_overview_base(store)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERRO] Falha ao coletar visão geral da tabela: {exc}")
        store.close()
        return 1

    try:
        embeddings = OpenAIEmbeddings(api_key=cfg["api_key"], model="text-embedding-3-small")
        resultados = executar_busca_vetorial(store, embeddings, args.question, top_k=args.top_k)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERRO] Falha na etapa de busca vetorial: {exc}")
        store.close()
        return 1
    finally:
        store.close()

    imprimir_relatorio(overview, resultados)
    print("\n✅ Teste concluído.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
