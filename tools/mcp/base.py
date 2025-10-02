"""Base classes and interfaces for Model Context Protocol (MCP) tools."""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import requests
from requests.exceptions import RequestException


logger = logging.getLogger(__name__)


class MCPToolStatus(Enum):
    """Status de execução de uma tool MCP."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"


@dataclass
class MCPToolResult:
    """Resultado da execução de uma tool MCP."""
    status: MCPToolStatus
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    execution_time_ms: int = 0
    tool_name: str = ""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_success(self) -> bool:
        """Verifica se a execução foi bem-sucedida."""
        return self.status == MCPToolStatus.SUCCESS
    
    @property
    def error_message(self) -> str:
        """Retorna mensagem de erro amigável."""
        if self.is_success:
            return ""
        return self.message or f"Erro na execução da tool {self.tool_name}"


@dataclass
class MCPTool:
    """Definição de uma tool MCP."""
    name: str
    description: str
    parameters: Dict[str, Any]
    endpoint: Optional[str] = None
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    requires_auth: bool = False
    auth_header: Optional[str] = None
    category: Optional[str] = None
    
    def __post_init__(self):
        """Validações após inicialização."""
        if not self.name.strip():
            raise ValueError("Tool name cannot be empty")
        
        if not self.description.strip():
            raise ValueError("Tool description cannot be empty")
        
        # Headers padrão
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        
        # Validação de parâmetros
        if not isinstance(self.parameters, dict):
            raise ValueError("Parameters must be a dictionary")


class MCPClient:
    """Cliente para execução de tools MCP."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Inicializa o cliente MCP.
        
        Args:
            base_url: URL base para tools que usam endpoints relativos
        """
        self.base_url = base_url
        self.tools: Dict[str, MCPTool] = {}
        self.session = requests.Session()
        
    def register_tool(self, tool: MCPTool) -> None:
        """Registra uma tool no cliente.
        
        Args:
            tool: Tool a ser registrada
        """
        logger.info(f"Registrando tool: {tool.name}")
        self.tools[tool.name] = tool
        
    def unregister_tool(self, tool_name: str) -> bool:
        """Remove uma tool do registro.
        
        Args:
            tool_name: Nome da tool a ser removida
            
        Returns:
            True se removida com sucesso, False se não encontrada
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Tool removida: {tool_name}")
            return True
        return False
    
    def list_tools(self) -> List[str]:
        """Lista todas as tools registradas.
        
        Returns:
            Lista com nomes das tools
        """
        return list(self.tools.keys())
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Recupera uma tool pelo nome.
        
        Args:
            tool_name: Nome da tool
            
        Returns:
            Tool encontrada ou None
        """
        return self.tools.get(tool_name)
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Executa uma tool MCP.
        
        Args:
            tool_name: Nome da tool a executar
            parameters: Parâmetros para a tool
            
        Returns:
            Resultado da execução
        """
        start_time = datetime.now()
        
        # Verifica se tool existe
        tool = self.tools.get(tool_name)
        if not tool:
            return MCPToolResult(
                status=MCPToolStatus.NOT_FOUND,
                message=f"Tool '{tool_name}' não encontrada",
                tool_name=tool_name
            )
        
        # Valida parâmetros
        validation_error = self._validate_parameters(tool, parameters)
        if validation_error:
            return MCPToolResult(
                status=MCPToolStatus.ERROR,
                message=validation_error,
                tool_name=tool_name
            )
        
        # Executa a tool
        try:
            result = self._execute_tool(tool, parameters)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            result.execution_time_ms = execution_time
            result.tool_name = tool_name
            
            logger.info(f"Tool {tool_name} executada com sucesso em {execution_time}ms")
            return result
            
        except RequestException as e:
            logger.error(f"Erro de rede ao executar tool {tool_name}: {e}")
            return MCPToolResult(
                status=MCPToolStatus.ERROR,
                message=f"Erro de conexão: {str(e)}",
                tool_name=tool_name
            )
        except Exception as e:
            logger.error(f"Erro inesperado ao executar tool {tool_name}: {e}")
            return MCPToolResult(
                status=MCPToolStatus.ERROR,
                message=f"Erro interno: {str(e)}",
                tool_name=tool_name
            )
    
    def _validate_parameters(self, tool: MCPTool, parameters: Dict[str, Any]) -> Optional[str]:
        """Valida os parâmetros de uma tool.
        
        Args:
            tool: Tool a validar
            parameters: Parâmetros fornecidos
            
        Returns:
            Mensagem de erro ou None se válido
        """
        required_params = []
        
        # Busca parâmetros obrigatórios
        for param_name, param_def in tool.parameters.items():
            if isinstance(param_def, dict):
                if param_def.get("required", False) and param_def.get("optional") is not True:
                    required_params.append(param_name)
            
        # Verifica se todos os obrigatórios estão presentes
        missing_params = [p for p in required_params if p not in parameters]
        if missing_params:
            return f"Parâmetros obrigatórios não fornecidos: {', '.join(missing_params)}"
        
        return None
    
    def _execute_tool(self, tool: MCPTool, parameters: Dict[str, Any]) -> MCPToolResult:
        """Executa uma tool específica.
        
        Args:
            tool: Tool a executar
            parameters: Parâmetros validados
            
        Returns:
            Resultado da execução
        """
        # Se não há endpoint, é uma tool local/mock
        if not tool.endpoint:
            return self._execute_local_tool(tool, parameters)
        
        # Constrói URL completa
        url = tool.endpoint
        if self.base_url and not tool.endpoint.startswith(('http://', 'https://')):
            url = f"{self.base_url.rstrip('/')}/{tool.endpoint.lstrip('/')}"
        
        # Prepara headers
        headers = dict(tool.headers)
        if tool.requires_auth and tool.auth_header:
            headers["Authorization"] = tool.auth_header
        
        # Executa requisição
        try:
            if tool.method.upper() == "GET":
                response = self.session.get(
                    url, 
                    params=parameters, 
                    headers=headers, 
                    timeout=tool.timeout_seconds
                )
            else:
                response = self.session.request(
                    tool.method.upper(),
                    url,
                    json=parameters,
                    headers=headers,
                    timeout=tool.timeout_seconds
                )
            
            # Verifica status code
            if response.status_code == 401:
                return MCPToolResult(
                    status=MCPToolStatus.UNAUTHORIZED,
                    message="Não autorizado para executar esta tool"
                )
            
            if response.status_code == 404:
                return MCPToolResult(
                    status=MCPToolStatus.NOT_FOUND,
                    message="Endpoint da tool não encontrado"
                )
            
            if not (200 <= response.status_code < 300):
                return MCPToolResult(
                    status=MCPToolStatus.ERROR,
                    message=f"HTTP {response.status_code}: {response.text[:200]}"
                )
            
            # Parse da resposta
            try:
                data = response.json() if response.content else {}
            except json.JSONDecodeError:
                data = {"raw_response": response.text}
            
            return MCPToolResult(
                status=MCPToolStatus.SUCCESS,
                data=data,
                message="Executado com sucesso"
            )
            
        except requests.Timeout:
            return MCPToolResult(
                status=MCPToolStatus.TIMEOUT,
                message=f"Timeout após {tool.timeout_seconds} segundos"
            )
    
    def _execute_local_tool(self, tool: MCPTool, parameters: Dict[str, Any]) -> MCPToolResult:
        """Executa uma tool local (mock/simulada).
        
        Args:
            tool: Tool a executar
            parameters: Parâmetros
            
        Returns:
            Resultado simulado
        """
        # Por enquanto, retorna um resultado mock
        return MCPToolResult(
            status=MCPToolStatus.SUCCESS,
            data={
                "message": f"Tool local '{tool.name}' executada com sucesso",
                "parameters_received": parameters,
                "mock": True
            },
            message="Executado localmente (modo simulação)"
        )