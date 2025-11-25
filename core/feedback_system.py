"""
Sistema de Feedback e Métricas para Neoson.

Coleta feedback explícito dos usuários (thumbs up/down) e métricas implícitas
(tempo de resposta, qualidade, fallbacks) para análise e melhoria contínua.

Autor: GitHub Copilot + Desenvolvedor
Data: 09/01/2025
Versão: 1.0.0
"""

import uuid
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging

# Para PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor

# Para Redis (cache de métricas)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # Para permitir mock em testes

logger = logging.getLogger(__name__)


@dataclass
class FeedbackEntry:
    """
    Representa uma entrada de feedback do usuário.
    
    Attributes:
        feedback_id: UUID único do feedback
        timestamp: Data/hora em formato ISO
        usuario_id: ID do usuário
        pergunta: Pergunta original
        resposta: Resposta fornecida (truncada)
        agente_usado: Nome do agente que respondeu
        classificacao: Tipo de pergunta (ti, rh, geral)
        rating: 1 (👎) ou 5 (👍)
        comentario: Feedback textual opcional
        tempo_resposta_ms: Latência em milissegundos
        score_qualidade: Score de validação (0-1)
        num_fallbacks: Número de tentativas até sucesso
        contexto_usado: Se usou histórico de conversa
    """
    feedback_id: str
    timestamp: str
    usuario_id: str
    pergunta: str
    resposta: str
    agente_usado: str
    classificacao: str
    rating: int  # 1 ou 5
    comentario: Optional[str] = None
    tempo_resposta_ms: Optional[int] = None
    score_qualidade: Optional[float] = None
    num_fallbacks: int = 0
    contexto_usado: bool = False
    
    def __post_init__(self):
        """Validações e truncamentos."""
        # Validar rating
        if self.rating not in [1, 5]:
            raise ValueError(f"Rating deve ser 1 ou 5, recebido: {self.rating}")
        
        # Validar score_qualidade
        if self.score_qualidade is not None:
            if not 0 <= self.score_qualidade <= 1:
                raise ValueError(f"score_qualidade deve estar entre 0 e 1, recebido: {self.score_qualidade}")
        
        # Truncar resposta para 1000 caracteres (banco de dados)
        if len(self.resposta) > 1000:
            self.resposta = self.resposta[:997] + "..."
        
        # Truncar comentário para 2000 caracteres
        if self.comentario and len(self.comentario) > 2000:
            self.comentario = self.comentario[:1997] + "..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackEntry':
        """Cria FeedbackEntry a partir de dicionário."""
        return cls(**data)
    
    def get_emoji(self) -> str:
        """Retorna emoji do rating."""
        return "👍" if self.rating == 5 else "👎"
    
    def get_summary(self) -> str:
        """Retorna resumo legível do feedback."""
        qualidade_str = f"{self.score_qualidade:.2f}" if self.score_qualidade is not None else "N/A"
        tempo_str = f"{self.tempo_resposta_ms}ms" if self.tempo_resposta_ms is not None else "N/A"
        
        return (
            f"{self.get_emoji()} Feedback de {self.usuario_id}\n"
            f"Agente: {self.agente_usado}\n"
            f"Rating: {self.rating}/5\n"
            f"Qualidade: {qualidade_str}\n"
            f"Tempo: {tempo_str}\n"
            f"Fallbacks: {self.num_fallbacks}\n"
            f"Comentário: {self.comentario or 'Nenhum'}"
        )


class FeedbackSystem:
    """
    Sistema centralizado de feedback e métricas.
    
    Funcionalidades:
    - Salvar feedback em PostgreSQL
    - Calcular métricas agregadas por agente
    - Cache em Redis para performance
    - Exportar métricas para Prometheus
    """
    
    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_name: str = "postgres",
        db_user: str = "postgres",
        db_password: str = "postgres",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        use_redis: bool = True
    ):
        """
        Inicializa o sistema de feedback.
        
        Args:
            db_host: Host do PostgreSQL
            db_port: Porta do PostgreSQL
            db_name: Nome do banco de dados
            db_user: Usuário do PostgreSQL
            db_password: Senha do PostgreSQL
            redis_host: Host do Redis (opcional)
            redis_port: Porta do Redis (opcional)
            use_redis: Se deve usar Redis para cache
        """
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        
        # Redis para cache (opcional)
        self.redis_client = None
        if use_redis and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("✅ Redis conectado para cache de métricas")
            except Exception as e:
                logger.warning(f"⚠️ Redis não disponível, usando apenas PostgreSQL: {e}")
                self.redis_client = None
        
        # Stats internas
        self.stats = {
            'feedbacks_saved': 0,
            'tester_feedbacks_saved': 0,
            'redis_hits': 0,
            'redis_misses': 0,
            'db_queries': 0
        }
    
    def _get_db_connection(self):
        """Cria conexão com PostgreSQL."""
        return psycopg2.connect(**self.db_config)
    
    async def save_feedback(
        self,
        usuario_id: str,
        pergunta: str,
        resposta: str,
        agente_usado: str,
        classificacao: str,
        rating: int,
        comentario: Optional[str] = None,
        tempo_resposta_ms: Optional[int] = None,
        score_qualidade: Optional[float] = None,
        num_fallbacks: int = 0,
        contexto_usado: bool = False
    ) -> str:
        """
        Salva feedback no banco de dados.
        
        Args:
            usuario_id: ID do usuário
            pergunta: Pergunta original
            resposta: Resposta fornecida
            agente_usado: Nome do agente
            classificacao: ti, rh, geral
            rating: 1 (👎) ou 5 (👍)
            comentario: Feedback textual opcional
            tempo_resposta_ms: Latência
            score_qualidade: Score de validação (0-1)
            num_fallbacks: Número de tentativas
            contexto_usado: Se usou histórico
        
        Returns:
            feedback_id: UUID do feedback criado
        
        Raises:
            ValueError: Se rating inválido
            psycopg2.Error: Se erro no banco
        """
        # Criar FeedbackEntry
        feedback = FeedbackEntry(
            feedback_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            usuario_id=usuario_id,
            pergunta=pergunta,
            resposta=resposta,
            agente_usado=agente_usado,
            classificacao=classificacao,
            rating=rating,
            comentario=comentario,
            tempo_resposta_ms=tempo_resposta_ms,
            score_qualidade=score_qualidade,
            num_fallbacks=num_fallbacks,
            contexto_usado=contexto_usado
        )
        
        # Salvar no PostgreSQL
        conn = self._get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO feedback (
                        feedback_id, timestamp, usuario_id, pergunta, resposta,
                        agente_usado, classificacao, rating, comentario,
                        tempo_resposta_ms, score_qualidade, num_fallbacks, contexto_usado
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    feedback.feedback_id,
                    feedback.timestamp,
                    feedback.usuario_id,
                    feedback.pergunta,
                    feedback.resposta,
                    feedback.agente_usado,
                    feedback.classificacao,
                    feedback.rating,
                    feedback.comentario,
                    feedback.tempo_resposta_ms,
                    feedback.score_qualidade,
                    feedback.num_fallbacks,
                    feedback.contexto_usado
                ))
                conn.commit()
                
                self.stats['feedbacks_saved'] += 1
                self.stats['db_queries'] += 1
                
                logger.info(
                    f"✅ Feedback salvo: {feedback.get_emoji()} | "
                    f"Agente: {agente_usado} | "
                    f"Rating: {rating}/5 | "
                    f"ID: {feedback.feedback_id[:8]}"
                )
                
                # Invalidar cache do agente (se Redis disponível)
                if self.redis_client:
                    try:
                        cache_key = f"agent_stats:{agente_usado}"
                        self.redis_client.delete(cache_key)
                        logger.debug(f"Cache invalidado para {agente_usado}")
                    except Exception as e:
                        logger.warning(f"Erro ao invalidar cache: {e}")
                
                return feedback.feedback_id
        
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro ao salvar feedback: {e}")
            raise
        finally:
            conn.close()

    async def save_tester_feedback(
        self,
        usuario_id: str,
        comentario: Optional[str],
        nota: int,
        origem: Optional[str] = None,
        contexto: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Armazena feedbacks do programa de testers em tabela dedicada."""
        tester_feedback_id = str(uuid.uuid4())
        conn = self._get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO feedback_testers (
                        tester_feedback_id,
                        timestamp,
                        usuario_id,
                        comentario,
                        nota,
                        origem,
                        contexto,
                        metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb
                    )
                """, (
                    tester_feedback_id,
                    datetime.now(timezone.utc).isoformat(),
                    usuario_id,
                    comentario,
                    nota,
                    origem,
                    json.dumps(contexto) if contexto else None,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                self.stats['tester_feedbacks_saved'] += 1
                self.stats['db_queries'] += 1
                logger.info(f"🧪 Feedback de tester salvo: {tester_feedback_id[:8]}")
                return tester_feedback_id
        except Exception as exc:
            conn.rollback()
            logger.error(f"❌ Erro ao salvar feedback de tester: {exc}")
            raise
        finally:
            conn.close()
    
    async def get_agent_stats(
        self,
        agent_name: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calcula estatísticas de um agente específico.
        
        Args:
            agent_name: Nome do agente
            days: Número de dias para considerar
        
        Returns:
            Dicionário com estatísticas:
            {
                'total_respostas': int,
                'rating_medio': float,
                'taxa_positiva': float,
                'tempo_medio_ms': int,
                'score_qualidade_medio': float,
                'taxa_fallback': float,
                'distribuicao_ratings': {'1': int, '5': int}
            }
        """
        # Verificar cache Redis primeiro
        cache_key = f"agent_stats:{agent_name}:{days}d"
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    self.stats['redis_hits'] += 1
                    logger.debug(f"✅ Cache hit para {agent_name}")
                    return json.loads(cached)
                else:
                    self.stats['redis_misses'] += 1
            except Exception as e:
                logger.warning(f"Erro ao acessar Redis: {e}")
        
        # Calcular do banco de dados
        conn = self._get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Data de corte
                cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
                
                # Query agregada
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_respostas,
                        AVG(rating) as rating_medio,
                        SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_positiva,
                        AVG(tempo_resposta_ms) as tempo_medio_ms,
                        AVG(score_qualidade) as score_qualidade_medio,
                        SUM(CASE WHEN num_fallbacks > 0 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_fallback,
                        SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as rating_1_count,
                        SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as rating_5_count
                    FROM feedback
                    WHERE agente_usado = %s
                      AND timestamp >= %s
                """, (agent_name, cutoff_date))
                
                row = cursor.fetchone()
                self.stats['db_queries'] += 1
                
                # Construir resultado
                if row and row['total_respostas'] > 0:
                    stats = {
                        'total_respostas': int(row['total_respostas']),
                        'rating_medio': float(row['rating_medio']) if row['rating_medio'] else 0.0,
                        'taxa_positiva': float(row['taxa_positiva']) if row['taxa_positiva'] else 0.0,
                        'tempo_medio_ms': int(row['tempo_medio_ms']) if row['tempo_medio_ms'] else 0,
                        'score_qualidade_medio': float(row['score_qualidade_medio']) if row['score_qualidade_medio'] else 0.0,
                        'taxa_fallback': float(row['taxa_fallback']) if row['taxa_fallback'] else 0.0,
                        'distribuicao_ratings': {
                            '1': int(row['rating_1_count']),
                            '5': int(row['rating_5_count'])
                        }
                    }
                else:
                    # Agente sem dados
                    stats = {
                        'total_respostas': 0,
                        'rating_medio': 0.0,
                        'taxa_positiva': 0.0,
                        'tempo_medio_ms': 0,
                        'score_qualidade_medio': 0.0,
                        'taxa_fallback': 0.0,
                        'distribuicao_ratings': {'1': 0, '5': 0}
                    }
                
                # Cachear resultado (TTL 5 minutos)
                if self.redis_client:
                    try:
                        self.redis_client.setex(
                            cache_key,
                            300,  # 5 minutos
                            json.dumps(stats)
                        )
                        logger.debug(f"Stats cacheadas para {agent_name}")
                    except Exception as e:
                        logger.warning(f"Erro ao cachear stats: {e}")
                
                return stats
        
        finally:
            conn.close()
    
    async def get_dashboard_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Retorna estatísticas globais para dashboard.
        
        Args:
            days: Número de dias para considerar
        
        Returns:
            Dicionário com:
            {
                'period': str,
                'global': {...},
                'by_agent': [...],
                'by_classification': {...},
                'top_agents': [...]
            }
        """
        conn = self._get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
                
                # Estatísticas globais
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_respostas,
                        AVG(rating) as rating_medio,
                        SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)::float / COUNT(*) as taxa_positiva,
                        AVG(tempo_resposta_ms) as tempo_medio_ms,
                        AVG(score_qualidade) as score_qualidade_medio
                    FROM feedback
                    WHERE timestamp >= %s
                """, (cutoff_date,))
                
                global_row = cursor.fetchone()
                self.stats['db_queries'] += 1
                
                # Estatísticas por agente (top 10)
                cursor.execute("""
                    SELECT
                        agente_usado,
                        COUNT(*) as total_respostas,
                        AVG(rating) as rating_medio,
                        AVG(tempo_resposta_ms) as tempo_medio_ms
                    FROM feedback
                    WHERE timestamp >= %s
                    GROUP BY agente_usado
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """, (cutoff_date,))
                
                by_agent = [dict(row) for row in cursor.fetchall()]
                self.stats['db_queries'] += 1
                
                # Estatísticas por classificação
                cursor.execute("""
                    SELECT
                        classificacao,
                        COUNT(*) as total_respostas,
                        AVG(rating) as rating_medio
                    FROM feedback
                    WHERE timestamp >= %s
                    GROUP BY classificacao
                """, (cutoff_date,))
                
                by_classification = {
                    row['classificacao']: {
                        'total_respostas': int(row['total_respostas']),
                        'rating_medio': float(row['rating_medio'])
                    }
                    for row in cursor.fetchall()
                }
                self.stats['db_queries'] += 1
                
                return {
                    'period': f'{days} days',
                    'global': {
                        'total_respostas': int(global_row['total_respostas']),
                        'rating_medio': float(global_row['rating_medio']) if global_row['rating_medio'] else 0.0,
                        'taxa_positiva': float(global_row['taxa_positiva']) if global_row['taxa_positiva'] else 0.0,
                        'tempo_medio_ms': int(global_row['tempo_medio_ms']) if global_row['tempo_medio_ms'] else 0,
                        'score_qualidade_medio': float(global_row['score_qualidade_medio']) if global_row['score_qualidade_medio'] else 0.0
                    },
                    'by_agent': by_agent,
                    'by_classification': by_classification,
                    'top_agents': [agent['agente_usado'] for agent in by_agent[:5]]
                }
        
        finally:
            conn.close()
    
    def export_prometheus_metrics(self) -> str:
        """
        Exporta métricas no formato Prometheus.
        
        Returns:
            String no formato Prometheus text exposition
        """
        # Nota: Este método será melhorado no Sprint 4
        # Por ora, retorna métricas básicas
        
        metrics = []
        
        # Métricas internas do sistema
        metrics.append("# HELP neoson_feedback_system_feedbacks_saved_total Total de feedbacks salvos")
        metrics.append("# TYPE neoson_feedback_system_feedbacks_saved_total counter")
        metrics.append(f"neoson_feedback_system_feedbacks_saved_total {self.stats['feedbacks_saved']}")

        metrics.append("# HELP neoson_feedback_system_tester_feedbacks_saved_total Total de feedbacks de testers salvos")
        metrics.append("# TYPE neoson_feedback_system_tester_feedbacks_saved_total counter")
        metrics.append(f"neoson_feedback_system_tester_feedbacks_saved_total {self.stats['tester_feedbacks_saved']}")
        
        metrics.append("# HELP neoson_feedback_system_redis_hits_total Cache hits do Redis")
        metrics.append("# TYPE neoson_feedback_system_redis_hits_total counter")
        metrics.append(f"neoson_feedback_system_redis_hits_total {self.stats['redis_hits']}")
        
        metrics.append("# HELP neoson_feedback_system_db_queries_total Queries ao PostgreSQL")
        metrics.append("# TYPE neoson_feedback_system_db_queries_total counter")
        metrics.append(f"neoson_feedback_system_db_queries_total {self.stats['db_queries']}")
        
        return "\n".join(metrics)
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas internas do sistema."""
        return self.stats.copy()


# Singleton global (opcional)
_feedback_system_instance: Optional[FeedbackSystem] = None


def get_feedback_system(
    db_url: Optional[str] = None,
    redis_host: str = "localhost",
    redis_port: int = 6379,
    use_redis: bool = True
) -> FeedbackSystem:
    """
    Retorna instância singleton do FeedbackSystem.
    
    Útil para garantir uma única conexão ao banco.
    
    Args:
        db_url: URL de conexão PostgreSQL (formato: postgresql://user:pass@host:port/db)
               Se None, usa valores padrão do localhost
        redis_host: Host do Redis
        redis_port: Porta do Redis
        use_redis: Se deve usar Redis para cache
    """
    global _feedback_system_instance
    
    if _feedback_system_instance is None:
        # Parsear DATABASE_URL se fornecido
        if db_url:
            # Formato: postgresql://user:password@host:port/dbname
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            
            db_host = parsed.hostname or "localhost"
            db_port = parsed.port or 5432
            db_name = parsed.path.lstrip('/') or "postgres"
            db_user = parsed.username or "postgres"
            db_password = parsed.password or "postgres"
        else:
            # Valores padrão
            db_host = "localhost"
            db_port = 5432
            db_name = "postgres"
            db_user = "postgres"
            db_password = "postgres"
        
        _feedback_system_instance = FeedbackSystem(
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            redis_host=redis_host,
            redis_port=redis_port,
            use_redis=use_redis
        )
    
    return _feedback_system_instance
