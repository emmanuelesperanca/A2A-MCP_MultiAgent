"""Registry central para comunicação Agent-to-Agent (A2A)."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from .messages import AgentMessage, AgentResponse, MessageStatus, A2ASession


logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker para prevenir loops infinitos entre agentes."""
    
    def __init__(self,
                 max_failures: int = 3,
                 max_messages_per_route: int = 5,
                 reset_timeout_minutes: int = 5):
        self.max_failures = max_failures
        self.max_messages_per_route = max_messages_per_route
        self.reset_timeout = timedelta(minutes=reset_timeout_minutes)
        
        # Estado do circuit breaker
        self.failure_counts: Dict[str, int] = defaultdict(int)
        self.last_failure_time: Dict[str, datetime] = {}
        self.route_message_counts: Dict[str, List[datetime]] = defaultdict(list)
        self.blocked_routes: Set[str] = set()
    
    def get_route_key(self, sender: str, recipient: str) -> str:
        """Gera chave única para uma rota entre agentes."""
        return f"{sender}->{recipient}"
    
    def is_route_blocked(self, sender: str, recipient: str) -> Tuple[bool, str]:
        """Verifica se uma rota está bloqueada pelo circuit breaker.
        
        Returns:
            Tuple (is_blocked, reason)
        """
        route_key = self.get_route_key(sender, recipient)
        
        # Verifica se está explicitamente bloqueado
        if route_key in self.blocked_routes:
            # Tenta resetar se passou do timeout
            if self._should_reset_route(route_key):
                self._reset_route(route_key)
                return False, ""
            return True, "Rota bloqueada por falhas excessivas"
        
        # Verifica contagem de mensagens recentes
        now = datetime.now()
        recent_window = now - timedelta(minutes=1)  # Janela de 1 minuto
        
        recent_messages = [
            msg_time for msg_time in self.route_message_counts[route_key]
            if msg_time > recent_window
        ]
        
        if len(recent_messages) >= self.max_messages_per_route:
            return True, f"Muitas mensagens na rota ({len(recent_messages)} em 1min)"
        
        return False, ""
    
    def record_message(self, sender: str, recipient: str):
        """Registra uma nova mensagem na rota."""
        route_key = self.get_route_key(sender, recipient)
        self.route_message_counts[route_key].append(datetime.now())
        
        # Limpa mensagens antigas (> 5 minutos)
        cutoff = datetime.now() - timedelta(minutes=5)
        self.route_message_counts[route_key] = [
            msg_time for msg_time in self.route_message_counts[route_key]
            if msg_time > cutoff
        ]
    
    def record_failure(self, sender: str, recipient: str, error_message: str = ""):
        """Registra uma falha na rota."""
        route_key = self.get_route_key(sender, recipient)
        self.failure_counts[route_key] += 1
        self.last_failure_time[route_key] = datetime.now()
        
        logger.warning(f"A2A Circuit Breaker: Failure recorded for route {route_key}", extra={
            "route": route_key,
            "failure_count": self.failure_counts[route_key],
            "error": error_message
        })
        
        # Bloqueia se excedeu limite
        if self.failure_counts[route_key] >= self.max_failures:
            self.blocked_routes.add(route_key)
            logger.error(f"A2A Circuit Breaker: Route {route_key} BLOCKED after {self.failure_counts[route_key]} failures")
    
    def record_success(self, sender: str, recipient: str):
        """Registra um sucesso na rota."""
        route_key = self.get_route_key(sender, recipient)
        
        # Reset do contador de falhas em caso de sucesso
        if route_key in self.failure_counts:
            self.failure_counts[route_key] = 0
        
        # Remove do bloqueio se estava bloqueado
        if route_key in self.blocked_routes:
            self.blocked_routes.remove(route_key)
            logger.info(f"A2A Circuit Breaker: Route {route_key} UNBLOCKED after success")
    
    def _should_reset_route(self, route_key: str) -> bool:
        """Verifica se uma rota deve ser resetada por timeout."""
        if route_key not in self.last_failure_time:
            return True
        
        return datetime.now() - self.last_failure_time[route_key] > self.reset_timeout
    
    def _reset_route(self, route_key: str):
        """Reseta uma rota bloqueada."""
        self.blocked_routes.discard(route_key)
        self.failure_counts[route_key] = 0
        logger.info(f"A2A Circuit Breaker: Route {route_key} RESET after timeout")
    
    def get_status(self) -> Dict:
        """Retorna status atual do circuit breaker."""
        return {
            "blocked_routes": list(self.blocked_routes),
            "active_routes": len(self.route_message_counts),
            "total_failures": sum(self.failure_counts.values()),
            "routes_with_failures": len([c for c in self.failure_counts.values() if c > 0])
        }


class AgentRegistry:
    """Registry central para comunicação A2A entre agentes."""
    
    def __init__(self):
        # Agentes registrados
        self.agents: Dict[str, 'BaseSubagent'] = {}
        
        # Sessões ativas
        self.active_sessions: Dict[str, A2ASession] = {}
        
        # Circuit breaker para prevenir loops
        self.circuit_breaker = CircuitBreaker()
        
        # Histórico para análise (últimas 100 mensagens)
        self.message_history: List[AgentMessage] = []
        self.response_history: List[AgentResponse] = []
        
        # Estatísticas
        self.stats = {
            "total_messages": 0,
            "successful_delegations": 0,
            "failed_delegations": 0,
            "circuit_breaker_blocks": 0,
            "avg_response_time_ms": 0
        }
    
    def register_agent(self, agent: 'BaseSubagent'):
        """Registra um agente no sistema A2A."""
        agent_id = agent.config.identifier
        self.agents[agent_id] = agent
        
        # Configura o registry no agente
        agent.set_agent_registry(self)
        
        logger.info(f"A2A Registry: Agent '{agent_id}' registered", extra={
            "agent_id": agent_id,
            "agent_name": agent.config.name,
            "specialty": agent.config.specialty,
            "a2a_enabled": getattr(agent.config, 'enable_a2a', False)
        })
    
    def unregister_agent(self, agent_id: str):
        """Remove um agente do registry."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"A2A Registry: Agent '{agent_id}' unregistered")
    
    def get_available_agents(self) -> List[str]:
        """Retorna lista de agentes disponíveis para delegação."""
        return list(self.agents.keys())
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        """Retorna informações sobre um agente."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        return {
            "id": agent_id,
            "name": agent.config.name,
            "specialty": agent.config.specialty,
            "description": agent.config.description,
            "keywords": getattr(agent.config, 'keywords', []),
            "a2a_enabled": getattr(agent.config, 'enable_a2a', False)
        }
    
    def create_session(self, original_query: str, user_profile: Dict) -> A2ASession:
        """Cria uma nova sessão A2A."""
        session = A2ASession(
            original_query=original_query,
            user_profile=user_profile
        )
        self.active_sessions[session.session_id] = session
        
        logger.info(f"A2A Registry: New session created", extra={
            "session_id": session.session_id,
            "query_length": len(original_query),
            "user": user_profile.get("nome", "Unknown")
        })
        
        return session
    
    def route_message(self, message: AgentMessage, session: Optional[A2ASession] = None) -> AgentResponse:
        """Roteia uma mensagem entre agentes com circuit breaker."""
        
        start_time = datetime.now()
        self.stats["total_messages"] += 1
        
        # 1. Verificar circuit breaker
        is_blocked, block_reason = self.circuit_breaker.is_route_blocked(
            message.sender, message.recipient
        )
        
        if is_blocked:
            self.stats["circuit_breaker_blocks"] += 1
            error_response = AgentResponse(
                message_id=message.id,
                task_id=message.task_id,
                responder="circuit_breaker",
                status=MessageStatus.ERROR,
                content=f"Rota bloqueada pelo circuit breaker: {block_reason}"
            )
            
            logger.warning(f"A2A Registry: Message blocked by circuit breaker", extra={
                "message": message.to_dict(),
                "reason": block_reason
            })
            
            return error_response
        
        # 2. Verificar se agente de destino existe
        target_agent = self.agents.get(message.recipient)
        if not target_agent:
            error_response = AgentResponse(
                message_id=message.id,
                task_id=message.task_id,
                responder="registry",
                status=MessageStatus.ERROR,
                content=f"Agente '{message.recipient}' não encontrado no registry"
            )
            
            self.circuit_breaker.record_failure(
                message.sender, message.recipient, "Agent not found"
            )
            self.stats["failed_delegations"] += 1
            
            return error_response
        
        # 3. Registrar mensagem
        self.circuit_breaker.record_message(message.sender, message.recipient)
        self.message_history.append(message)
        if len(self.message_history) > 100:
            self.message_history.pop(0)
        
        # Adicionar à sessão se fornecida
        if session:
            session.add_message(message)
        
        logger.info(f"A2A Registry: Routing message", extra={
            "message": message.to_dict(),
            "session_id": session.session_id if session else None
        })
        
        # 4. Processar mensagem no agente de destino
        try:
            if message.message_type.value == "delegate":
                # Processar delegação
                result = target_agent.processar_pergunta(
                    message.content,
                    message.context.get('user_profile', {})
                )
                
                # Criar resposta de sucesso
                response = AgentResponse(
                    message_id=message.id,
                    task_id=message.task_id,
                    responder=message.recipient,
                    status=MessageStatus.SUCCESS,
                    content=result,
                    processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    contribution_summary=f"Forneceu informações sobre {target_agent.config.specialty}"
                )
                
                # Adicionar metadados se disponíveis
                if hasattr(target_agent, 'last_sources_used'):
                    response.sources_used = getattr(target_agent, 'last_sources_used', [])
                
                if hasattr(target_agent, 'last_tools_used'):
                    response.tools_used = getattr(target_agent, 'last_tools_used', [])
                
                # Registrar sucesso
                self.circuit_breaker.record_success(message.sender, message.recipient)
                self.stats["successful_delegations"] += 1
                
                logger.info(f"A2A Registry: Message processed successfully", extra={
                    "response": response.to_dict(),
                    "session_id": session.session_id if session else None
                })
                
            else:
                # Outros tipos de mensagem (futuro)
                response = AgentResponse(
                    message_id=message.id,
                    task_id=message.task_id,
                    responder=message.recipient,
                    status=MessageStatus.ERROR,
                    content=f"Tipo de mensagem '{message.message_type.value}' não suportado"
                )
            
        except Exception as e:
            # Registrar falha
            self.circuit_breaker.record_failure(
                message.sender, message.recipient, str(e)
            )
            self.stats["failed_delegations"] += 1
            
            response = AgentResponse(
                message_id=message.id,
                task_id=message.task_id,
                responder=message.recipient,
                status=MessageStatus.ERROR,
                content=f"Erro no processamento: {str(e)}",
                processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            
            logger.error(f"A2A Registry: Error processing message", extra={
                "message": message.to_dict(),
                "error": str(e),
                "session_id": session.session_id if session else None
            })
        
        # 5. Registrar resposta no histórico e sessão
        self.response_history.append(response)
        if len(self.response_history) > 100:
            self.response_history.pop(0)
        
        if session:
            session.add_response(response)
        
        # Atualizar estatísticas de tempo
        total_responses = self.stats["successful_delegations"] + self.stats["failed_delegations"]
        if total_responses > 0:
            current_avg = self.stats["avg_response_time_ms"]
            new_time = response.processing_time_ms
            self.stats["avg_response_time_ms"] = int(
                (current_avg * (total_responses - 1) + new_time) / total_responses
            )
        
        return response
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do registry A2A."""
        return {
            **self.stats,
            "registered_agents": len(self.agents),
            "active_sessions": len(self.active_sessions),
            "circuit_breaker": self.circuit_breaker.get_status()
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessões antigas para liberar memória."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        old_sessions = [
            sid for sid, session in self.active_sessions.items()
            if session.start_time < cutoff
        ]
        
        for sid in old_sessions:
            del self.active_sessions[sid]
        
        if old_sessions:
            logger.info(f"A2A Registry: Cleaned up {len(old_sessions)} old sessions")