"""
Sistema de Memória de Conversas com Redis.

Mantém histórico das últimas 3-5 perguntas/respostas por usuário
para melhor tratamento de follow-up questions.

Características:
- Armazenamento em Redis com TTL de 1 hora
- Máximo de 5 mensagens por usuário
- Formato compacto para economizar memória
- Async-first para performance
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Representa uma mensagem na conversa."""
    timestamp: str
    pergunta: str
    resposta: str
    agente_usado: str
    classificacao: str
    score_qualidade: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Cria instância a partir de dicionário."""
        return cls(**data)
    
    def get_summary(self, max_length: int = 150) -> str:
        """Retorna resumo compacto da mensagem."""
        resposta_resumida = self.resposta[:max_length]
        if len(self.resposta) > max_length:
            resposta_resumida += "..."
        
        return f"P: {self.pergunta}\nR: {resposta_resumida}"


class ConversationMemory:
    """
    Gerencia memória de conversas usando Redis.
    
    Estrutura no Redis:
    - Key: conv:{usuario_id}
    - Value: Lista JSON de mensagens
    - TTL: 3600 segundos (1 hora)
    """
    
    def __init__(
        self,
        redis_client=None,
        max_messages: int = 5,
        ttl_seconds: int = 3600,
        use_fallback: bool = True
    ):
        """
        Inicializa sistema de memória.
        
        Args:
            redis_client: Cliente Redis (opcional, usa fallback se None)
            max_messages: Número máximo de mensagens por usuário
            ttl_seconds: Tempo de vida dos dados (padrão 1 hora)
            use_fallback: Usar memória local se Redis falhar
        """
        self.redis_client = redis_client
        self.max_messages = max_messages
        self.ttl_seconds = ttl_seconds
        self.use_fallback = use_fallback
        
        # Fallback: memória local (apenas para desenvolvimento)
        self._local_memory: Dict[str, List[Dict]] = {}
        
        # Estatísticas
        self.stats = {
            'total_saves': 0,
            'total_retrievals': 0,
            'redis_errors': 0,
            'fallback_uses': 0
        }
    
    async def save_message(
        self,
        usuario_id: str,
        pergunta: str,
        resposta: str,
        agente_usado: str,
        classificacao: str,
        score_qualidade: Optional[float] = None
    ) -> bool:
        """
        Salva uma mensagem no histórico do usuário.
        
        Args:
            usuario_id: ID único do usuário
            pergunta: Pergunta feita pelo usuário
            resposta: Resposta fornecida (resumida se muito longa)
            agente_usado: Nome do agente que respondeu
            classificacao: Classificação da pergunta (ti, rh, etc)
            score_qualidade: Score de qualidade da resposta (0-1)
        
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Criar mensagem
            message = ConversationMessage(
                timestamp=datetime.now().isoformat(),
                pergunta=pergunta,
                resposta=resposta[:500],  # Limitar tamanho da resposta
                agente_usado=agente_usado,
                classificacao=classificacao,
                score_qualidade=score_qualidade
            )
            
            # Tentar salvar no Redis primeiro
            if self.redis_client:
                try:
                    key = f"conv:{usuario_id}"
                    
                    # Buscar histórico existente
                    existing = await self._redis_get_list(key)
                    
                    # Adicionar nova mensagem no início
                    existing.insert(0, message.to_dict())
                    
                    # Manter apenas as últimas N mensagens
                    existing = existing[:self.max_messages]
                    
                    # Salvar de volta no Redis
                    await self._redis_set_list(key, existing)
                    
                    logger.debug(f"💾 Mensagem salva no Redis para usuário {usuario_id}")
                    self.stats['total_saves'] += 1
                    return True
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao salvar no Redis: {e}")
                    self.stats['redis_errors'] += 1
                    
                    if not self.use_fallback:
                        return False
            
            # Fallback: memória local
            if self.use_fallback:
                if usuario_id not in self._local_memory:
                    self._local_memory[usuario_id] = []
                
                self._local_memory[usuario_id].insert(0, message.to_dict())
                self._local_memory[usuario_id] = self._local_memory[usuario_id][:self.max_messages]
                
                logger.debug(f"💾 Mensagem salva em memória local (fallback) para {usuario_id}")
                self.stats['fallback_uses'] += 1
                self.stats['total_saves'] += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem: {e}")
            return False
    
    async def get_history(
        self,
        usuario_id: str,
        max_messages: Optional[int] = None
    ) -> List[ConversationMessage]:
        """
        Recupera histórico de conversas do usuário.
        
        Args:
            usuario_id: ID único do usuário
            max_messages: Número máximo de mensagens (None = usar padrão)
        
        Returns:
            Lista de mensagens ordenadas da mais recente para mais antiga
        """
        try:
            limit = max_messages if max_messages is not None else self.max_messages
            
            # Tentar buscar no Redis primeiro
            if self.redis_client:
                try:
                    key = f"conv:{usuario_id}"
                    messages_data = await self._redis_get_list(key)
                    
                    if messages_data:
                        messages = [
                            ConversationMessage.from_dict(msg)
                            for msg in messages_data[:limit]
                        ]
                        
                        logger.debug(f"📖 Recuperadas {len(messages)} mensagens do Redis para {usuario_id}")
                        self.stats['total_retrievals'] += 1
                        return messages
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao buscar no Redis: {e}")
                    self.stats['redis_errors'] += 1
                    
                    if not self.use_fallback:
                        return []
            
            # Fallback: memória local
            if self.use_fallback and usuario_id in self._local_memory:
                messages_data = self._local_memory[usuario_id][:limit]
                messages = [
                    ConversationMessage.from_dict(msg)
                    for msg in messages_data
                ]
                
                logger.debug(f"📖 Recuperadas {len(messages)} mensagens da memória local (fallback)")
                self.stats['fallback_uses'] += 1
                self.stats['total_retrievals'] += 1
                return messages
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar histórico: {e}")
            return []
    
    async def get_context_summary(
        self,
        usuario_id: str,
        num_messages: int = 3
    ) -> str:
        """
        Retorna resumo formatado do histórico para incluir no prompt.
        
        Args:
            usuario_id: ID único do usuário
            num_messages: Número de mensagens recentes a incluir
        
        Returns:
            String formatada com histórico resumido
        """
        messages = await self.get_history(usuario_id, max_messages=num_messages)
        
        if not messages:
            return ""
        
        context = "📚 **HISTÓRICO RECENTE DA CONVERSA**:\n\n"
        
        for i, msg in enumerate(messages, 1):
            # Calcular quanto tempo atrás
            try:
                msg_time = datetime.fromisoformat(msg.timestamp)
                time_ago = datetime.now() - msg_time
                minutes_ago = int(time_ago.total_seconds() / 60)
                
                if minutes_ago < 1:
                    time_str = "agora mesmo"
                elif minutes_ago < 60:
                    time_str = f"{minutes_ago} min atrás"
                else:
                    hours_ago = minutes_ago // 60
                    time_str = f"{hours_ago}h atrás"
            except:
                time_str = "recentemente"
            
            context += f"**Mensagem {i}** ({time_str}):\n"
            context += f"{msg.get_summary(max_length=100)}\n"
            context += f"*Respondido por: {msg.agente_usado}*\n\n"
        
        return context
    
    async def clear_history(self, usuario_id: str) -> bool:
        """
        Limpa histórico de um usuário.
        
        Args:
            usuario_id: ID único do usuário
        
        Returns:
            True se limpou com sucesso
        """
        try:
            # Limpar do Redis
            if self.redis_client:
                try:
                    key = f"conv:{usuario_id}"
                    await self._redis_delete(key)
                    logger.info(f"🗑️ Histórico limpo do Redis para {usuario_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao limpar Redis: {e}")
            
            # Limpar memória local
            if usuario_id in self._local_memory:
                del self._local_memory[usuario_id]
                logger.info(f"🗑️ Histórico limpo da memória local para {usuario_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar histórico: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso."""
        stats = self.stats.copy()
        stats['redis_available'] = self.redis_client is not None
        stats['fallback_enabled'] = self.use_fallback
        stats['local_memory_users'] = len(self._local_memory)
        
        return stats
    
    # Métodos auxiliares para Redis
    
    async def _redis_get_list(self, key: str) -> List[Dict]:
        """Busca lista do Redis."""
        if not self.redis_client:
            return []
        
        try:
            # Para redis síncrono
            if hasattr(self.redis_client, 'get'):
                data = self.redis_client.get(key)
            # Para redis assíncrono
            else:
                data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return []
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar do Redis: {e}")
            return []
    
    async def _redis_set_list(self, key: str, data: List[Dict]) -> bool:
        """Salva lista no Redis."""
        if not self.redis_client:
            return False
        
        # Não capturar exceções aqui - deixar propagar para o chamador
        json_data = json.dumps(data, ensure_ascii=False)
        
        # Para redis síncrono
        if hasattr(self.redis_client, 'setex'):
            self.redis_client.setex(key, self.ttl_seconds, json_data)
        # Para redis assíncrono
        else:
            await self.redis_client.setex(key, self.ttl_seconds, json_data)
        
        return True
    
    async def _redis_delete(self, key: str) -> bool:
        """Remove chave do Redis."""
        if not self.redis_client:
            return False
        
        try:
            # Para redis síncrono
            if hasattr(self.redis_client, 'delete'):
                self.redis_client.delete(key)
            # Para redis assíncrono
            else:
                await self.redis_client.delete(key)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao deletar do Redis: {e}")
            return False
