"""Estruturas de mensagens para comunicação Agent-to-Agent (A2A)."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Tipos de mensagem A2A."""
    DELEGATE = "delegate"
    RESPONSE = "response"
    ERROR = "error"
    INFO = "info"


class MessageStatus(Enum):
    """Status de processamento da mensagem."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class AgentMessage:
    """Mensagem entre agentes no sistema A2A."""
    
    # Identificação
    id: str = field(default_factory=lambda: f"msg_{uuid4().hex[:8]}")
    sender: str = ""
    recipient: str = ""
    
    # Conteúdo
    message_type: MessageType = MessageType.DELEGATE
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Controle
    task_id: str = field(default_factory=lambda: f"task_{uuid4().hex[:8]}")
    requires_response: bool = True
    timeout_seconds: int = 30
    priority: int = 1  # 1=baixa, 5=alta
    
    # Rastreabilidade
    timestamp: datetime = field(default_factory=datetime.now)
    parent_message_id: Optional[str] = None
    delegation_chain: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte mensagem para dicionário para logging."""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.message_type.value,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "chain": " -> ".join(self.delegation_chain) if self.delegation_chain else "direct"
        }


@dataclass
class AgentResponse:
    """Resposta de um agente para outro."""
    
    # Identificação
    id: str = field(default_factory=lambda: f"resp_{uuid4().hex[:8]}")
    message_id: str = ""  # ID da mensagem original
    task_id: str = ""
    responder: str = ""
    
    # Resultado
    status: MessageStatus = MessageStatus.SUCCESS
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Rastreabilidade
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: int = 0
    sources_used: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    
    # Para o usuário final
    contribution_summary: str = ""  # Resumo do que este agente contribuiu
    
    @property
    def is_success(self) -> bool:
        """Verifica se a resposta foi bem-sucedida."""
        return self.status == MessageStatus.SUCCESS
    
    @property
    def error_message(self) -> str:
        """Retorna mensagem de erro se aplicável."""
        if self.is_success:
            return ""
        return self.content or f"Erro no processamento pelo agente {self.responder}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte resposta para dicionário para logging."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "task_id": self.task_id,
            "responder": self.responder,
            "status": self.status.value,
            "content_length": len(self.content),
            "processing_time_ms": self.processing_time_ms,
            "sources_count": len(self.sources_used),
            "tools_count": len(self.tools_used),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DelegationRule:
    """Regra de quando delegar para outro agente."""
    
    name: str
    target_agent: str
    keywords: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.7
    description: str = ""
    enabled: bool = True
    
    # Estatísticas (para aprendizado futuro)
    times_triggered: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: int = 0
    
    def matches(self, query: str) -> float:
        """Calcula score de match para uma query.
        
        Returns:
            Score de 0.0 a 1.0 indicando o quanto a regra se aplica
        """
        if not self.enabled or not self.keywords:
            return 0.0
        
        query_lower = query.lower()
        matches = sum(1 for keyword in self.keywords if keyword.lower() in query_lower)
        score = matches / len(self.keywords)
        
        return score if score >= self.confidence_threshold else 0.0
    
    def record_usage(self, success: bool, response_time_ms: int):
        """Registra uso da regra para estatísticas."""
        self.times_triggered += 1
        
        # Atualiza success rate com média móvel simples
        if self.times_triggered == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            weight = 1 / self.times_triggered
            self.success_rate = (self.success_rate * (1 - weight)) + (1.0 if success else 0.0) * weight
        
        # Atualiza tempo médio de resposta
        if self.times_triggered == 1:
            self.avg_response_time_ms = response_time_ms
        else:
            weight = 1 / self.times_triggered
            self.avg_response_time_ms = int(
                (self.avg_response_time_ms * (1 - weight)) + (response_time_ms * weight)
            )


@dataclass
class A2ASession:
    """Sessão A2A para rastrear uma conversa completa."""
    
    session_id: str = field(default_factory=lambda: f"session_{uuid4().hex[:8]}")
    original_query: str = ""
    user_profile: Dict[str, Any] = field(default_factory=dict)
    
    # Histórico
    messages: List[AgentMessage] = field(default_factory=list)
    responses: List[AgentResponse] = field(default_factory=list)
    
    # Estado
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "active"  # active, completed, error, timeout
    
    # Resultado final
    final_response: str = ""
    contributing_agents: List[str] = field(default_factory=list)
    total_processing_time_ms: int = 0
    
    def add_message(self, message: AgentMessage):
        """Adiciona uma mensagem à sessão."""
        message.delegation_chain = self.get_current_chain() + [message.sender]
        self.messages.append(message)
        
        logger.info(f"A2A Session {self.session_id}: New message", extra={
            "session_id": self.session_id,
            "a2a_message": message.to_dict()
        })
    
    def add_response(self, response: AgentResponse):
        """Adiciona uma resposta à sessão."""
        self.responses.append(response)
        
        if response.responder not in self.contributing_agents:
            self.contributing_agents.append(response.responder)
        
        logger.info(f"A2A Session {self.session_id}: New response", extra={
            "session_id": self.session_id,
            "a2a_response": response.to_dict()
        })
    
    def get_current_chain(self) -> List[str]:
        """Retorna a cadeia de delegação atual."""
        if not self.messages:
            return []
        return self.messages[-1].delegation_chain.copy()
    
    def get_collaboration_summary(self) -> str:
        """Gera resumo da colaboração entre agentes para o usuário."""
        if not self.contributing_agents:
            return ""
        
        if len(self.contributing_agents) == 1:
            return f"Resposta elaborada pelo especialista em {self.contributing_agents[0].title()}"
        
        summary_parts = []
        
        for response in self.responses:
            if response.contribution_summary and response.is_success:
                agent_name = response.responder.title()
                summary_parts.append(f"**{agent_name}**: {response.contribution_summary}")
        
        if summary_parts:
            header = f"🤝 **Colaboração entre {len(self.contributing_agents)} especialistas:**\n\n"
            return header + "\n".join(summary_parts)
        
        return f"Resposta elaborada em colaboração entre: {', '.join(self.contributing_agents)}"
    
    def finalize(self, final_response: str):
        """Finaliza a sessão A2A."""
        self.end_time = datetime.now()
        self.final_response = final_response
        self.status = "completed"
        self.total_processing_time_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
        
        logger.info(f"A2A Session {self.session_id}: Completed", extra={
            "session_id": self.session_id,
            "contributing_agents": self.contributing_agents,
            "total_time_ms": self.total_processing_time_ms,
            "messages_count": len(self.messages),
            "responses_count": len(self.responses)
        })
