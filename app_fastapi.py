"""
Aplicação FastAPI assíncrona para o Sistema Neoson
Backend completamente assíncrono para escalabilidade máxima
Substitui o app.py Flask por uma solução moderna e performática
"""

from dataclasses import dataclass
import importlib
import inspect
import threading
import time

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
import time
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
import secrets
from contextlib import asynccontextmanager

# Core configuration
from core.config import config

# Importa o sistema Neoson assíncrono
from agentes.neoson.neoson_async import criar_neoson_async

# Importa o sistema de feedback
from core.feedback_system import get_feedback_system

# Importa o sistema de enriquecimento de respostas
from core.enrichment_system import ResponseEnricher, create_faqs_table, save_faq

# Importa Agent Factory
from factory.agent_factory import create_subagent_from_config, create_coordinator_from_config
from factory.agent_registry import get_registry

# Importa API de Knowledge
from api_knowledge import router as knowledge_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variáveis globais
neoson_sistema = None
feedback_system = None
response_enricher = None


@dataclass
class AgentDescriptor:
    """Metadados mínimos para execução direta de um agente."""

    identifier: str
    module_path: str
    factory_name: str
    display_name: str
    specialty: str
    agent_type: str = "subagent"
    source: str = "registry"


# Caches para instâncias e metadados dos agentes diretos
agent_instance_cache: Dict[str, Any] = {}
agent_descriptor_cache: Dict[str, AgentDescriptor] = {}
agent_cache_lock: Optional[asyncio.Lock] = None

# Cache do registro de agentes criado pela Agent Factory
registry_cache_lock = threading.Lock()
registry_cache_data: Dict[str, Dict[str, Any]] = {}
registry_cache_timestamp: float = 0.0
REGISTRY_CACHE_TTL = 60  # segundos

# ============================================================================
# CONFIGURAÇÕES DE AUTENTICAÇÃO
# ============================================================================

# Secret key para JWT (em produção, use variável de ambiente!)
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Credenciais de teste (em produção, use banco de dados!)
USUARIOS_DB = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # Em produção, use hash bcrypt!
        "user_type": "admin",
        "full_name": "Administrador do Sistema"
    },
    "user": {
        "username": "user",
        "password": "user123",
        "user_type": "user",
        "full_name": "Usuário Padrão"
    },
    "joao": {
        "username": "joao",
        "password": "joao123",
        "user_type": "user",
        "full_name": "João Silva"
    },
    "maria": {
        "username": "maria",
        "password": "maria123",
        "user_type": "admin",
        "full_name": "Maria Santos"
    }
}

# Security
security = HTTPBearer()

# Perfis de teste para a aplicação
PERFIS_TESTE = {
    "João Silva - Analista TI": {
        "Nome": "João Silva",
        "Cargo": "Analista de TI",
        "Departamento": "TI",
        "Nivel_Hierarquico": 2,
        "Geografia": "Brasil",
        "Projetos": ["Projeto A", "Projeto C"]
    },
    "Maria Santos - Gerente RH": {
        "Nome": "Maria Santos",
        "Cargo": "Gerente de RH",
        "Departamento": "RH",
        "Nivel_Hierarquico": 4,
        "Geografia": "Brasil",
        "Projetos": ["Projeto B", "Projeto D"]
    },
    "Carlos Oliveira - Diretor TI": {
        "Nome": "Carlos Oliveira",
        "Cargo": "Diretor de TI",
        "Departamento": "TI",
        "Nivel_Hierarquico": 5,
        "Geografia": "Brasil",
        "Projetos": ["ALL"]
    },
    "Ana Costa - Coordenadora Marketing": {
        "Nome": "Ana Costa",
        "Cargo": "Coordenadora de Marketing",
        "Departamento": "Marketing",
        "Nivel_Hierarquico": 3,
        "Geografia": "Brasil",
        "Projetos": ["Projeto A"]
    }
}


# Models Pydantic para validação

# Modelos de Autenticação
class LoginRequest(BaseModel):
    """Modelo para requisição de login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=3, max_length=100)
    user_type: str = Field("user", description="Tipo de usuário (admin ou user)")


class LoginResponse(BaseModel):
    """Modelo para resposta de login"""
    success: bool
    token: str
    username: str
    user_type: str
    message: str


class TokenData(BaseModel):
    """Dados contidos no token JWT"""
    username: str
    user_type: str
    exp: int

# Modelos de Chat


class ChatRequest(BaseModel):
    """Modelo para requisição de chat"""
    mensagem: str = Field(..., min_length=1, max_length=1000)
    persona_selecionada: Optional[str] = "Gerente"
    custom_persona: Optional[Dict] = None

    @validator('mensagem')
    def validate_mensagem(cls, v):
        if not v.strip():
            raise ValueError('Mensagem não pode estar vazia')
        return v.strip()


class PerguntaRequest(BaseModel):
    """Modelo para requisição de pergunta (API legada)"""
    pergunta: str = Field(..., min_length=1, max_length=200)
    perfil: str

    @validator('pergunta')
    def validate_pergunta(cls, v):
        if not v.strip():
            raise ValueError('Pergunta não pode estar vazia')
        return v.strip()


class ChatResponse(BaseModel):
    """Modelo para resposta de chat"""
    resposta: str
    cadeia_raciocinio: Optional[str] = None
    agent_usado: str
    especialidade: str
    classificacao: str
    sucesso: bool = True
    
    # Campos de enriquecimento (opcionais)
    enriched: Optional[Dict] = None  # Dados enriquecidos completos
    documentos_relacionados: Optional[List[Dict]] = None
    faqs_similares: Optional[List[Dict]] = None
    especialistas_contato: Optional[List[Dict]] = None
    proximas_sugestoes: Optional[List[str]] = None
    glossario: Optional[Dict[str, str]] = None


class PerguntaResponse(BaseModel):
    """Modelo para resposta de pergunta"""
    success: bool
    resposta: Optional[str] = None
    agente_usado: Optional[str] = None
    especialidade: Optional[str] = None
    classificacao: Optional[str] = None
    perfil_usado: Optional[str] = None
    caracteres: Optional[int] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Modelo para resposta de status"""
    success: bool
    sistema_pronto: bool
    neoson: Optional[Dict] = None


class AgentCatalogEntry(BaseModel):
    """Representa um agente disponível para invocação direta."""

    identifier: str
    name: str
    specialty: Optional[str] = None
    type: Optional[str] = None
    endpoint: str
    ask_endpoint: Optional[str] = None
    path: Optional[str] = None
    module_path: Optional[str] = None


class AgentCatalogResponse(BaseModel):
    """Payload retornado pelo catálogo de agentes."""

    success: bool
    agents: List[AgentCatalogEntry]


# ============================================================================
# MODELOS PARA FEEDBACK SYSTEM
# ============================================================================

class FeedbackSubmitRequest(BaseModel):
    """Modelo para submissão de feedback"""
    usuario_id: str = Field(..., min_length=1, max_length=100)
    feedback_id: str = Field(..., min_length=1)  # ID da resposta original
    rating: int = Field(..., ge=1, le=5)  # 1 ou 5
    comentario: Optional[str] = Field(None, max_length=2000)
    
    # Campos adicionais para contexto completo
    pergunta: str = Field(..., min_length=1, max_length=5000)
    resposta: str = Field(..., min_length=1, max_length=10000)
    agente: str = Field(..., min_length=1, max_length=200)
    classificacao: str = Field(..., min_length=1, max_length=100)
    
    @validator('rating')
    def validate_rating(cls, v):
        if v not in [1, 5]:
            raise ValueError('Rating deve ser 1 (não útil) ou 5 (útil)')
        return v


class FeedbackSubmitResponse(BaseModel):
    """Modelo para resposta de submissão de feedback"""
    status: str
    feedback_id: str
    mensagem: str


class TesterFeedbackRequest(BaseModel):
    """Modelo para submissão de feedback do programa de testers"""
    usuario_id: str = Field(..., min_length=1, max_length=150)
    nota: int = Field(..., ge=0, le=10)
    comentario: Optional[str] = Field(None, max_length=2000)
    origem: Optional[str] = Field(None, max_length=100)
    contexto: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TesterFeedbackResponse(BaseModel):
    """Modelo para resposta da submissão de testers"""
    status: str
    tester_feedback_id: str
    mensagem: str


class AgentStatsResponse(BaseModel):
    """Modelo para resposta de estatísticas de agente"""
    agent_name: str
    period: str
    stats: Dict


class DashboardStatsResponse(BaseModel):
    """Modelo para resposta de dashboard"""
    period: str
    global_stats: Dict
    by_agent: List[Dict]
    by_classification: Dict
    top_agents: List[str]


# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    logger.info("🚀 Inicializando Sistema Neoson Multi-Agente...")
    global neoson_sistema, feedback_system, response_enricher
    
    try:
        neoson_sistema = await criar_neoson_async()
        if neoson_sistema:
            logger.info("✅ Sistema Neoson inicializado com sucesso!")
        else:
            logger.error("❌ Falha na inicialização do sistema Neoson")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar sistema Neoson: {e}")
        neoson_sistema = None
    
    # Inicializar sistema de feedback
    try:
        from core.config import config as app_config
        feedback_system = get_feedback_system(
            db_url=app_config.database.main_url,
            use_redis=False  # Redis opcional, desabilitado por padrão
        )
        logger.info("✅ Sistema de Feedback inicializado com sucesso!")
    except Exception as e:
        logger.warning(f"⚠️ Sistema de Feedback não disponível: {e}")
        feedback_system = None
    
    # Inicializar sistema de enriquecimento
    try:
        from core.config import config as app_config
        from dal.postgres_dal_async import PostgresDALAsync
        
        # Obter pool de conexões do DAL
        dal = PostgresDALAsync(app_config.database.main_url)
        await dal.initialize()
        
        # Criar tabela de FAQs se não existir
        await create_faqs_table(dal.pool)
        
        # Inicializar enricher
        response_enricher = ResponseEnricher(config=app_config, db_pool=dal.pool)
        logger.info("✅ Sistema de Enriquecimento de Respostas inicializado com sucesso!")
    except Exception as e:
        logger.warning(f"⚠️ Sistema de Enriquecimento não disponível: {e}")
        response_enricher = None
    
    yield
    
    # Shutdown
    logger.info("🔄 Encerrando Sistema Neoson...")
    if neoson_sistema:
        # Cleanup se necessário
        pass
    logger.info("👋 Sistema Neoson encerrado")


# Criar aplicação FastAPI
app = FastAPI(
    title="Neoson API",
    description="Sistema Multi-Agente de IA com backend assíncrono",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Incluir routers
app.include_router(knowledge_router)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler customizado para HTTPException"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"erro": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler customizado para exceções gerais"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"erro": f"Erro interno: {str(exc)}"}
    )


# ============================================================================
# AUTENTICAÇÃO - FUNÇÕES AUXILIARES
# ============================================================================

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Cria um token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verifica e decodifica um token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("Token expirado")
        return None
    except DecodeError as e:
        logger.warning(f"Erro ao decodificar token: {e}")
        return None
    except InvalidTokenError as e:
        logger.warning(f"Token inválido: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao verificar token: {e}")
        return None


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Autentica um usuário"""
    user = USUARIOS_DB.get(username)
    if not user:
        return None
    if user['password'] != password:  # Em produção, use bcrypt!
        return None
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency para obter usuário atual do token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado"
        )
    
    username = payload.get("username")
    user = USUARIOS_DB.get(username)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário não encontrado"
        )
    
    return user


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency que requer usuário admin"""
    if current_user.get("user_type") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas administradores podem acessar este recurso."
        )
    return current_user


# ============================================================================
# UTILITÁRIOS PARA ROTEAR AGENTES DIRETOS
# ============================================================================

def _normalize_agent_key(agent_key: str) -> str:
    """Normaliza identificadores e caminhos de agentes para facilitar caching."""

    return agent_key.strip().replace("\\", "/").strip("/").replace("-", "_").lower()


def _strip_agent_identifier(identifier: str) -> str:
    """Remove prefixos/sufixos padrão (agente_, _async)."""

    value = identifier
    if value.startswith("agente_"):
        value = value[len("agente_"):]
    if value.endswith("_async"):
        value = value[: -len("_async")]
    return value


def _module_path_from_file_path(file_path: str) -> str:
    """Converte caminho de arquivo em caminho de módulo Python."""

    normalized = file_path.replace("\\", "/").replace(".py", "")
    return normalized.replace("/", ".")


def _title_from_identifier(identifier: str) -> str:
    """Gera um nome amigável a partir do identificador."""

    if not identifier:
        return "Agente"
    return " ".join(part.capitalize() for part in identifier.split("_"))


def _cache_descriptor(descriptor: AgentDescriptor, *keys: str) -> None:
    """Armazena descritores em cache para múltiplas chaves equivalentes."""

    for key in keys:
        if key:
            agent_descriptor_cache[_normalize_agent_key(key)] = descriptor


def _descriptor_from_registry(identifier: str, data: Dict[str, Any]) -> AgentDescriptor:
    """Cria um descriptor completo a partir do registro persistido."""

    file_path = data.get("file_path")
    if not file_path:
        raise ValueError(f"Registro do agente {identifier} sem file_path")

    module_path = _module_path_from_file_path(file_path)
    module_name = module_path.split(".")[-1]
    factory_name = f"criar_{module_name}"

    return AgentDescriptor(
        identifier=identifier,
        module_path=module_path,
        factory_name=factory_name,
        display_name=data.get("name", _title_from_identifier(identifier)),
        specialty=data.get("specialty", _title_from_identifier(identifier)),
        agent_type=data.get("type", "subagent"),
        source="registry"
    )


def _get_registry_snapshot(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """Obtém snapshot em cache do registro de agentes."""

    global registry_cache_data, registry_cache_timestamp

    now = time.time()
    needs_refresh = (
        force_refresh
        or not registry_cache_data
        or (now - registry_cache_timestamp) > REGISTRY_CACHE_TTL
    )

    if needs_refresh:
        with registry_cache_lock:
            now = time.time()
            if (
                force_refresh
                or not registry_cache_data
                or (now - registry_cache_timestamp) > REGISTRY_CACHE_TTL
            ):
                registry = get_registry()
                registry.reload()
                registry_cache_data = dict(registry.agents)
                registry_cache_timestamp = now

    return registry_cache_data


def _resolve_descriptor_from_registry(agent_key: str, *, force_refresh: bool = False) -> Optional[AgentDescriptor]:
    """Tenta resolver um agente pelo registro persistido."""

    snapshot = _get_registry_snapshot(force_refresh=force_refresh)
    normalized = _normalize_agent_key(agent_key)

    candidates = {normalized, _strip_agent_identifier(normalized)}
    if "/" in normalized:
        candidates.add(_strip_agent_identifier(normalized.split("/")[-1]))

    for candidate in candidates:
        if not candidate:
            continue
        data = snapshot.get(candidate)
        if data:
            descriptor = _descriptor_from_registry(candidate, data)
            _cache_descriptor(
                descriptor,
                candidate,
                descriptor.identifier,
                descriptor.module_path,
                data.get("file_path", "")
            )
            return descriptor

    # Verificar por caminho de arquivo equivalente
    for identifier, data in snapshot.items():
        file_path = data.get("file_path", "")
        if not file_path:
            continue
        normalized_path = _normalize_agent_key(file_path)
        normalized_path_no_prefix = normalized_path.replace("agentes/", "", 1)
        if normalized in {normalized_path, normalized_path_no_prefix}:
            descriptor = _descriptor_from_registry(identifier, data)
            _cache_descriptor(
                descriptor,
                identifier,
                normalized_path,
                normalized_path_no_prefix
            )
            return descriptor

    return None


def _resolve_descriptor_via_path(agent_key: str) -> Optional[AgentDescriptor]:
    """Constroi descriptor a partir de um caminho literal informado na rota."""

    normalized = _normalize_agent_key(agent_key).replace(".py", "")
    if not normalized:
        return None

    if not normalized.startswith("agentes/"):
        normalized = f"agentes/{normalized}"

    module_path = normalized.replace("/", ".")
    module_name = module_path.split(".")[-1]
    identifier = _strip_agent_identifier(module_name)

    descriptor = AgentDescriptor(
        identifier=identifier or module_name,
        module_path=module_path,
        factory_name=f"criar_{module_name}",
        display_name=_title_from_identifier(identifier or module_name),
        specialty=_title_from_identifier(identifier or module_name),
        agent_type="custom",
        source="path"
    )

    _cache_descriptor(descriptor, normalized, module_path, identifier)
    return descriptor


def _resolve_agent_descriptor(agent_key: str) -> AgentDescriptor:
    """Resolve metadados mínimos de um agente por id ou caminho."""

    normalized = _normalize_agent_key(agent_key)
    if not normalized:
        raise HTTPException(status_code=400, detail="Identificador de agente inválido")

    cached = agent_descriptor_cache.get(normalized)
    if cached:
        return cached

    descriptor = _resolve_descriptor_from_registry(normalized)
    if not descriptor:
        descriptor = _resolve_descriptor_from_registry(normalized, force_refresh=True)
    if not descriptor:
        descriptor = _resolve_descriptor_via_path(normalized)

    if not descriptor:
        raise HTTPException(status_code=404, detail=f"Agente '{agent_key}' não encontrado")

    _cache_descriptor(descriptor, normalized, descriptor.identifier, descriptor.module_path)
    return descriptor


async def _get_or_create_agent_instance(descriptor: AgentDescriptor) -> Any:
    """Obtém instância única para o agente alvo."""

    global agent_cache_lock

    cache_key = descriptor.module_path
    instance = agent_instance_cache.get(cache_key)
    if instance:
        return instance

    if agent_cache_lock is None:
        agent_cache_lock = asyncio.Lock()

    async with agent_cache_lock:
        instance = agent_instance_cache.get(cache_key)
        if instance:
            return instance

        instance = await _instantiate_agent(descriptor)
        agent_instance_cache[cache_key] = instance
        return instance


async def _instantiate_agent(descriptor: AgentDescriptor) -> Any:
    """Carrega módulo e cria instância do agente."""

    try:
        module = importlib.import_module(descriptor.module_path)
    except ModuleNotFoundError as exc:
        logger.error("❌ Módulo do agente não encontrado: %s", descriptor.module_path)
        raise HTTPException(status_code=404, detail=f"Módulo do agente indisponível: {descriptor.module_path}") from exc

    factory = getattr(module, descriptor.factory_name, None)
    instance = None

    try:
        if factory:
            instance = factory(debug=False)
            if inspect.isawaitable(instance):
                instance = await instance
        else:
            class_name = "".join(part.capitalize() for part in descriptor.module_path.split(".")[-1].split("_"))
            cls = getattr(module, class_name, None)
            if cls:
                try:
                    instance = cls(debug=False)
                except TypeError:
                    instance = cls()
    except Exception as exc:  # noqa: BLE001
        logger.exception("❌ Erro ao instanciar agente %s", descriptor.identifier)
        raise HTTPException(status_code=500, detail=f"Falha ao instanciar agente {descriptor.identifier}") from exc

    if instance is None:
        raise HTTPException(status_code=500, detail=f"Agente {descriptor.identifier} não possui factory compatível")

    logger.info("🤖 Instância inicializada para agente direto: %s (%s)", descriptor.identifier, descriptor.module_path)
    return instance


async def _call_with_variations(method, mensagem: str, perfil: dict) -> Any:
    """Invoca método tratando variações de assinatura comuns."""

    attempts = [
        lambda: method(mensagem, perfil),
        lambda: method(mensagem, perfil_usuario=perfil),
        lambda: method(pergunta=mensagem, user_profile=perfil),
        lambda: method(mensagem=mensagem, perfil=perfil),
        lambda: method(mensagem=mensagem, user_profile=perfil),
        lambda: method(message=mensagem, profile=perfil),
        lambda: method(pergunta=mensagem),
        lambda: method(mensagem=mensagem),
    ]

    last_type_error: Optional[TypeError] = None
    for attempt in attempts:
        try:
            result = attempt()
        except TypeError as exc:
            last_type_error = exc
            continue

        if inspect.isawaitable(result):
            result = await result
        return result

    if last_type_error:
        raise last_type_error
    raise HTTPException(status_code=500, detail="Método do agente não pôde ser invocado")


async def _dispatch_to_agent(agent_instance: Any, mensagem: str, perfil: dict) -> str:
    """Tenta executar mensagem diretamente no agente disponível."""

    candidate_methods = [
        getattr(agent_instance, "handle_message", None),
        getattr(agent_instance, "processar_async", None),
        getattr(agent_instance, "processar_pergunta_async", None),
        getattr(agent_instance, "processar_pergunta", None),
    ]

    for method in candidate_methods:
        if method is None:
            continue
        try:
            resposta = await _call_with_variations(method, mensagem, perfil)
            if resposta is not None:
                return str(resposta)
        except TypeError:
            continue

    raise HTTPException(status_code=500, detail="Nenhum manipulador compatível encontrado para este agente")


def _build_default_profile(current_user: dict) -> dict:
    """Gera perfil mínimo usando dados do usuário autenticado."""

    return {
        "Nome": current_user.get("full_name", current_user.get("username", "Usuário")),
        "Cargo": "Gerente" if current_user.get("user_type") == "admin" else "Colaborador",
        "Departamento": "Geral",
        "Nivel_Acesso": current_user.get("user_type", "user"),
    }


def _build_agents_catalog() -> List[Dict[str, Any]]:
    """Monta catálogo utilizado pelo frontend para seleção de destino."""

    snapshot = _get_registry_snapshot()
    catalog = []

    for identifier, data in snapshot.items():
        entry = {
            "identifier": identifier,
            "name": data.get("name", _title_from_identifier(identifier)),
            "specialty": data.get("specialty"),
            "type": data.get("type"),
            "endpoint": f"/api/agents/{identifier}",
            "path": data.get("file_path"),
            "ask_endpoint": f"/ask_agentes/{data.get('file_path')}" if data.get("file_path") else None,
            "module_path": _module_path_from_file_path(data.get("file_path")) if data.get("file_path") else None,
        }
        catalog.append(entry)

    # Ordenar por nome para UX consistente
    catalog.sort(key=lambda item: item["name"] or item["identifier"])
    return catalog


def _split_resposta(resposta_texto: str) -> Tuple[str, Optional[str]]:
    """Separa resposta principal da cadeia de raciocínio quando aplicável."""

    cadeia_separador = "=" * 60
    if cadeia_separador in resposta_texto:
        partes = resposta_texto.split(cadeia_separador, 1)
        resposta_principal = partes[0].strip()
        cadeia_raciocinio = cadeia_separador + partes[1]
        return resposta_principal, cadeia_raciocinio
    return resposta_texto, None


async def _process_direct_agent_request(agent_reference: str, request: ChatRequest, current_user: dict) -> ChatResponse:
    """Fluxo compartilhado para rotas diretas de agentes."""

    descriptor = _resolve_agent_descriptor(agent_reference)
    agent_instance = await _get_or_create_agent_instance(descriptor)
    perfil = _build_default_profile(current_user)

    logger.info("🎯 Rota direta acionada: %s (%s)", descriptor.identifier, descriptor.module_path)
    resposta_texto = await _dispatch_to_agent(agent_instance, request.mensagem, perfil)
    resposta_principal, cadeia = _split_resposta(resposta_texto)

    return ChatResponse(
        resposta=resposta_principal,
        cadeia_raciocinio=cadeia,
        agent_usado=descriptor.display_name,
        especialidade=descriptor.specialty,
        classificacao=descriptor.identifier,
        sucesso=True
    )

# ============================================================================
# AUTENTICAÇÃO - ENDPOINTS
# ============================================================================


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Endpoint de login
    
    Credenciais de teste:
    - admin/admin123 (administrador)
    - user/user123 (usuário comum)
    - joao/joao123 (usuário comum)
    - maria/maria123 (administrador)
    """
    user = authenticate_user(request.username, request.password)
    
    if not user:
        return LoginResponse(
            success=False,
            token="",
            username="",
            user_type="",
            message="Usuário ou senha incorretos"
        )
    
    # Criar token
    access_token = create_access_token(
        data={"username": user["username"], "user_type": user["user_type"]}
    )
    
    logger.info(f"✅ Login bem-sucedido: {user['username']} ({user['user_type']})")
    
    return LoginResponse(
        success=True,
        token=access_token,
        username=user["username"],
        user_type=user["user_type"],
        message=f"Bem-vindo, {user['full_name']}!"
    )


@app.post("/api/auth/verify")
async def verify_auth(current_user: dict = Depends(get_current_user)):
    """Verifica se o token ainda é válido"""
    return {
        "success": True,
        "username": current_user["username"],
        "user_type": current_user["user_type"],
        "full_name": current_user["full_name"]
    }


@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Endpoint de logout (apenas para consistência, JWT é stateless)"""
    logger.info(f"👋 Logout: {current_user['username']}")
    return {
        "success": True,
        "message": "Logout realizado com sucesso"
    }


@app.get("/api/user")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """Retorna informações do usuário autenticado"""
    return {
        "success": True,
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "role": current_user["user_type"],
        "user_type": current_user["user_type"]
    }


@app.get("/api/agents", response_model=AgentCatalogResponse)
async def list_direct_agents(current_user: dict = Depends(get_current_user)):
    """Lista agentes disponíveis para invocação direta via API."""

    try:
        catalog = [
            AgentCatalogEntry(
                identifier="neoson",
                name="Neoson (Orquestrador)",
                specialty="Roteamento Inteligente",
                type="orchestrator",
                endpoint="/api/chat",
                ask_endpoint=None,
                path=None,
                module_path=None,
            )
        ]

        for agent in _build_agents_catalog():
            catalog.append(AgentCatalogEntry(**agent))

        return AgentCatalogResponse(success=True, agents=catalog)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("❌ Erro ao listar agentes diretos")
        raise HTTPException(status_code=500, detail=f"Erro ao listar agentes: {exc}") from exc


@app.post("/api/agents/{agent_name}", response_model=ChatResponse)
async def chat_with_specific_agent(
    agent_name: str,
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Envia mensagem diretamente a um agente identificado no registro."""

    return await _process_direct_agent_request(agent_name, request, current_user)


@app.post("/ask_agentes/{agent_path:path}", response_model=ChatResponse)
async def chat_with_agent_by_path(
    agent_path: str,
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Versão compatível com caminhos completos do arquivo do agente."""

    return await _process_direct_agent_request(agent_path, request, current_user)


@app.post("/api/chat")
async def api_chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Endpoint de chat para a nova interface
    Processa mensagem do usuário e retorna resposta do Neoson
    """
    if neoson_sistema is None:
        raise HTTPException(status_code=500, detail='Sistema Neoson não inicializado')
    
    try:
        # Usar perfil padrão baseado no tipo de usuário
        perfil = {
            "Nome": current_user.get("full_name", current_user["username"]),
            "Cargo": "Gerente" if current_user["user_type"] == "admin" else "Colaborador",
            "Departamento": "Geral",
            "Nivel_Acesso": current_user["user_type"]
        }
        
        logger.info(f"💬 Chat - Usuário: {current_user['username']}, Mensagem: '{request.mensagem[:50]}...'")
        
        # Processar pergunta de forma assíncrona
        resultado = await neoson_sistema.processar_pergunta_async(request.mensagem, perfil)
        
        if resultado['sucesso']:
            resposta_texto = resultado['resposta']
            
            # Separar resposta da cadeia de raciocínio se houver
            cadeia_separador = "="*60
            if cadeia_separador in resposta_texto:
                partes = resposta_texto.split(cadeia_separador, 1)
                resposta_principal = partes[0].strip()
                cadeia_raciocinio = cadeia_separador + partes[1]
            else:
                resposta_principal = resposta_texto
                cadeia_raciocinio = None
            
            logger.info(f"✅ Resposta gerada: {len(resposta_principal)} caracteres")
            
            return {
                "success": True,
                "response": resposta_principal,
                "cadeia_raciocinio": cadeia_raciocinio,
                "agent_usado": resultado.get('agente_usado', 'Neoson'),
                "classificacao": resultado.get('classificacao', 'Geral'),
                "especialidade": resultado.get('especialidade', 'Geral')
            }
        else:
            logger.error(f"❌ Erro ao processar: {resultado.get('erro', 'Erro desconhecido')}")
            raise HTTPException(
                status_code=500,
                detail=resultado.get('erro', 'Erro ao processar mensagem')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Erro inesperado no chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )


# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})


# Rotas
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Página principal da aplicação"""
    # Adicionar url_for ao contexto para compatibilidade com templates Flask
    context = {
        "request": request,
        # Não precisamos adicionar url_for manualmente, Starlette já fornece
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/showcase", response_class=HTMLResponse)
async def showcase(request: Request):
    """Página de apresentação/marketing do Neoson"""
    context = {
        "request": request,
    }
    return templates.TemplateResponse("showcase.html", context)


@app.get("/api/perfis")
async def get_perfis():
    """Retorna a lista de perfis disponíveis"""
    return {
        'success': True,
        'perfis': list(PERFIS_TESTE.keys())
    }


@app.get("/api/historico/{perfil_nome}")
async def get_historico(perfil_nome: str):
    """Retorna o histórico de conversas de um usuário"""
    if neoson_sistema is None:
        raise HTTPException(status_code=500, detail='Agente não inicializado')

    if perfil_nome not in PERFIS_TESTE:
        raise HTTPException(status_code=400, detail='Perfil inválido')

    perfil = PERFIS_TESTE[perfil_nome]
    usuario_id = f"{perfil['Nome']}_{perfil['Departamento']}"

    # TODO: Implementar acesso à memória
    return {
        'success': True,
        'historico': [],
        'usuario_id': usuario_id
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal para conversas com o sistema Neoson (ASSÍNCRONO)"""
    if neoson_sistema is None:
        raise HTTPException(status_code=500, detail='Sistema Neoson não inicializado')

    # Seleciona perfil baseado na persona
    if request.custom_persona:
        perfil = request.custom_persona
        nome = perfil.get('Nome', perfil.get('nome', 'Persona Customizada'))
        cargo = perfil.get('Cargo', perfil.get('cargo', 'N/A'))
        logger.info(f"🎭 Usando persona personalizada: {nome} - {cargo}")
    elif request.persona_selecionada in PERFIS_TESTE:
        perfil = PERFIS_TESTE[request.persona_selecionada]
    else:
        perfil = list(PERFIS_TESTE.values())[0]

    # Processa a pergunta através do Neoson (ASSÍNCRONO)
    logger.info(f"🎯 App processando pergunta: '{request.mensagem[:50]}...'")
    
    # Usar await aqui é a chave da performance assíncrona
    resultado = await neoson_sistema.processar_pergunta_async(request.mensagem, perfil)
    
    logger.info(f"📊 Resultado do Neoson - Sucesso: {resultado['sucesso']}")
    
    if resultado['sucesso']:
        resposta_texto = resultado['resposta']
        logger.info(f"📝 Resposta gerada: {len(resposta_texto)} caracteres")
        
        # Separar resposta da cadeia de raciocínio se houver
        resposta_completa = resultado['resposta']
        cadeia_separador = "="*60
        
        if cadeia_separador in resposta_completa:
            partes = resposta_completa.split(cadeia_separador, 1)
            resposta_principal = partes[0].strip()
            cadeia_raciocinio = cadeia_separador + partes[1] if len(partes) > 1 else None
        else:
            resposta_principal = resposta_completa
            cadeia_raciocinio = None
        
        # NOVO: Enriquecer resposta com informações adicionais
        enriched_data = None
        if response_enricher:
            try:
                logger.info("✨ Enriquecendo resposta com informações adicionais...")
                
                # Determinar base de conhecimento usada
                base_conhecimento = None
                if 'ti' in resultado.get('classificacao', '').lower():
                    if 'governance' in resultado.get('agente_usado', '').lower():
                        base_conhecimento = 'knowledge_IT_GOVERNANCE'
                    elif 'infra' in resultado.get('agente_usado', '').lower():
                        base_conhecimento = 'knowledge_IT_INFRA'
                elif 'rh' in resultado.get('classificacao', '').lower():
                    base_conhecimento = 'knowledge_HR'
                
                # Enriquecer resposta
                enriched_data = await response_enricher.enrich(
                    resposta_principal=resposta_principal,
                    pergunta=request.mensagem,
                    agente_usado=resultado['agente_usado'],
                    perfil_usuario=perfil,
                    base_conhecimento=base_conhecimento
                )
                
                # Salvar FAQ para histórico (fire and forget)
                try:
                    asyncio.create_task(
                        save_faq(
                            db_pool=response_enricher.db_pool,
                            embeddings=response_enricher.embeddings,
                            pergunta=request.mensagem,
                            resposta=resposta_principal,
                            agente_usado=resultado['agente_usado']
                        )
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao salvar FAQ: {e}")
                
                logger.info(
                    f"✅ Resposta enriquecida com {len(enriched_data.get('documentos_relacionados', []))} docs, "
                    f"{len(enriched_data.get('faqs_similares', []))} FAQs, "
                    f"{len(enriched_data.get('proximas_sugestoes', []))} sugestões, "
                    f"{len(enriched_data.get('glossario', {}))} termos no glossário"
                )
            
            except Exception as e:
                logger.warning(f"⚠️ Erro ao enriquecer resposta: {e}")
                enriched_data = None
        
        # Montar resposta final
        response = ChatResponse(
            resposta=resposta_principal,
            cadeia_raciocinio=cadeia_raciocinio,
            agent_usado=resultado['agente_usado'],
            especialidade=resultado.get('especialidade', ''),
            classificacao=resultado.get('classificacao', ''),
            sucesso=True
        )
        
        # Adicionar dados enriquecidos se disponíveis
        if enriched_data:
            response.enriched = enriched_data
            response.documentos_relacionados = enriched_data.get('documentos_relacionados', [])
            response.faqs_similares = enriched_data.get('faqs_similares', [])
            response.especialistas_contato = enriched_data.get('especialistas_contato', [])
            response.proximas_sugestoes = enriched_data.get('proximas_sugestoes', [])
            response.glossario = enriched_data.get('glossario', {})
        
        return response
    else:
        raise HTTPException(status_code=500, detail=resultado['resposta'])


@app.post("/api/pergunta", response_model=PerguntaResponse)
async def fazer_pergunta(request: PerguntaRequest):
    """Processa a pergunta do usuário através do sistema Neoson (API legada - ASSÍNCRONO)"""
    if neoson_sistema is None:
        raise HTTPException(status_code=500, detail='Sistema Neoson não inicializado')
    
    if request.perfil not in PERFIS_TESTE:
        raise HTTPException(status_code=400, detail='Perfil inválido')
    
    # Processa a pergunta através do Neoson (ASSÍNCRONO)
    perfil = PERFIS_TESTE[request.perfil]
    resultado = await neoson_sistema.processar_pergunta_async(request.pergunta, perfil)
    
    if resultado['sucesso']:
        return PerguntaResponse(
            success=True,
            resposta=resultado['resposta'],
            agente_usado=resultado['agente_usado'],
            especialidade=resultado['especialidade'],
            classificacao=resultado['classificacao'],
            perfil_usado=request.perfil,
            caracteres=len(request.pergunta)
        )
    else:
        raise HTTPException(status_code=500, detail=resultado['resposta'])


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Retorna o status do sistema Neoson e agentes"""
    if neoson_sistema:
        status_sistema = neoson_sistema.obter_status_sistema()
        
        # Adicionar informações detalhadas dos sub-agentes TI
        if 'ti' in neoson_sistema.agentes:
            ti_coordinator = neoson_sistema.agentes['ti']['instancia']
            if hasattr(ti_coordinator, 'get_info'):
                ti_info = ti_coordinator.get_info()
                status_sistema['agentes']['ti']['sub_agents_info'] = ti_info.get('hierarchy_stats', {})
        
        return StatusResponse(
            success=True,
            sistema_pronto=True,
            neoson=status_sistema
        )
    else:
        return StatusResponse(
            success=True,
            sistema_pronto=False,
            neoson=None
        )


@app.get("/api/ti-hierarchy")
async def get_ti_hierarchy():
    """Retorna informações detalhadas da hierarquia TI"""
    if not neoson_sistema:
        raise HTTPException(status_code=500, detail='Sistema Neoson não inicializado')
    
    if 'ti' not in neoson_sistema.agentes:
        raise HTTPException(status_code=404, detail='Sistema TI não disponível')
    
    ti_coordinator = neoson_sistema.agentes['ti']['instancia']
    if hasattr(ti_coordinator, 'get_info'):
        info = ti_coordinator.get_info()
        return {
            'success': True,
            'ti_system': {
                'status': info.get('status'),
                'base_agent': info.get('base_agent'),
                'hierarchy_stats': info.get('hierarchy_stats', {}),
                'sub_agents': [
                    {'name': 'Ariel', 'specialty': 'Governança', 'expertise': 'LGPD, Compliance, Delivery Methods'},
                    {'name': 'Alice', 'specialty': 'Infraestrutura', 'expertise': 'Servidores, Redes, Monitoramento'},
                    {'name': 'Carlos', 'specialty': 'Desenvolvimento', 'expertise': 'APIs, Deploy, Arquitetura'},
                    {'name': 'Marina', 'specialty': 'Usuário Final', 'expertise': 'Senhas, Acessos, Suporte'}
                ]
            }
        }
    else:
        raise HTTPException(status_code=500, detail='Informações da hierarquia não disponíveis')


@app.post("/api/test-chat")
async def test_chat(request: Request):
    """Endpoint de teste para depuração de problemas de chat"""
    data = await request.json()
    logger.info(f"🧪 Test endpoint recebeu: {data}")
    
    # Simular resposta do sistema hierárquico
    test_response = {
        'resposta': 'Esta é uma resposta de teste do sistema hierárquico TI assíncrono. O sistema está funcionando corretamente e pode processar perguntas através dos sub-especialistas de forma não-bloqueante.',
        'agent_usado': 'Test Agent (Async)',
        'especialidade': 'Teste Assíncrono',
        'classificacao': 'test',
        'sucesso': True
    }
    
    logger.info(f"✅ Test endpoint retornando: {test_response}")
    return test_response


@app.post("/limpar_memoria")
async def limpar_memoria_chat():
    """Limpa a memória de conversas para a interface de chat"""
    if neoson_sistema is None:
        raise HTTPException(status_code=500, detail='Sistema Neoson não inicializado')
    
    # Limpa memória de todos os perfis
    sucesso_total = True
    for perfil in PERFIS_TESTE.values():
        sucesso = neoson_sistema.limpar_memoria_usuario(perfil)
        if not sucesso:
            sucesso_total = False
    
    if sucesso_total:
        return {
            'sucesso': True,
            'mensagem': 'Memória limpa com sucesso'
        }
    else:
        raise HTTPException(status_code=500, detail='Erro parcial ao limpar memória')


@app.post("/api/limpar-memoria/{perfil_nome}")
async def limpar_memoria(perfil_nome: str):
    """Limpa a memória de conversas de um usuário em todos os agentes"""
    if perfil_nome not in PERFIS_TESTE:
        raise HTTPException(status_code=400, detail='Perfil inválido')
    
    if neoson_sistema is None:
        raise HTTPException(status_code=500, detail='Sistema Neoson não inicializado')
    
    perfil = PERFIS_TESTE[perfil_nome]
    sucesso = neoson_sistema.limpar_memoria_usuario(perfil)
    
    if sucesso:
        return {
            'success': True,
            'message': f'Memória do usuário {perfil_nome} limpa em todos os agentes'
        }
    else:
        raise HTTPException(status_code=500, detail='Erro ao limpar memória')


# Health check
@app.get("/health")
async def health_check():
    """Endpoint para verificar saúde da aplicação"""
    return {
        "status": "healthy",
        "neoson_initialized": neoson_sistema is not None
    }


# Endpoint de métricas (para monitoramento)
@app.get("/metrics")
async def metrics():
    """Endpoint para métricas da aplicação"""
    if neoson_sistema:
        status = neoson_sistema.obter_status_sistema()
        return {
            "agentes_ativos": len([a for a in status['agentes'].values() if a['status'] == 'ativo']),
            "total_agentes": len(status['agentes']),
            "sistema_status": "operational"
        }
    return {
        "sistema_status": "initializing"
    }


# ============================================================================
# ENDPOINTS DO SISTEMA DE FEEDBACK
# ============================================================================

@app.post("/api/feedback", response_model=FeedbackSubmitResponse)
async def submit_feedback(request: FeedbackSubmitRequest):
    """
    Submete feedback do usuário para uma resposta.
    
    Args:
        request: Dados do feedback (usuario_id, feedback_id, rating, comentario)
    
    Returns:
        Confirmação com feedback_id
    
    Raises:
        HTTPException: Se feedback_system não estiver disponível
    """
    if not feedback_system:
        raise HTTPException(
            status_code=503,
            detail="Sistema de feedback não está disponível. Verifique a conexão com o banco de dados."
        )
    
    try:
        # Salvar feedback no banco de dados
        logger.info(
            f"📝 Feedback recebido: {request.rating}/5 de {request.usuario_id} "
            f"para resposta {request.feedback_id[:8]}..."
        )
        
        # Salvar no PostgreSQL (a função save_feedback gera o feedback_id internamente)
        saved_feedback_id = await feedback_system.save_feedback(
            usuario_id=request.usuario_id,
            pergunta=request.pergunta,
            resposta=request.resposta,
            agente_usado=request.agente,
            classificacao=request.classificacao,
            rating=request.rating,
            comentario=request.comentario
        )
        
        if not saved_feedback_id:
            raise Exception("Falha ao salvar feedback no banco de dados")
        
        logger.info(f"✅ Feedback {saved_feedback_id[:8]} salvo com sucesso!")
        
        return FeedbackSubmitResponse(
            status="success",
            feedback_id=saved_feedback_id,
            mensagem=f"Obrigado pelo seu feedback {'positivo' if request.rating == 5 else 'negativo'}!"
        )
    
    except Exception as e:
        logger.error(f"❌ Erro ao salvar feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar feedback: {str(e)}")


@app.post("/api/feedback/testers", response_model=TesterFeedbackResponse)
async def submit_tester_feedback(request: TesterFeedbackRequest):
    """Mantém feedbacks dos testers armazenados diretamente em PostgreSQL."""
    if not feedback_system:
        raise HTTPException(
            status_code=503,
            detail="Sistema de feedback não está disponível. Verifique a conexão com o banco de dados."
        )

    try:
        logger.info(
            "🧪 Feedback de tester recebido: nota %s por %s", request.nota, request.usuario_id
        )
        tester_feedback_id = await feedback_system.save_tester_feedback(
            usuario_id=request.usuario_id,
            comentario=request.comentario,
            nota=request.nota,
            origem=request.origem,
            contexto=request.contexto,
            metadata=request.metadata
        )
        return TesterFeedbackResponse(
            status="success",
            tester_feedback_id=tester_feedback_id,
            mensagem="Obrigado por compartilhar seu feedback como tester interno!"
        )
    except Exception as exc:
        logger.error("❌ Erro ao salvar feedback de tester: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro ao salvar feedback de tester: {exc}")


@app.get("/api/stats/agent/{agent_name}", response_model=AgentStatsResponse)
async def get_agent_stats(agent_name: str, days: int = 7):
    """
    Retorna estatísticas de um agente específico.
    
    Args:
        agent_name: Nome do agente (ex: "Alice - Infrastructure")
        days: Número de dias para considerar (default: 7)
    
    Returns:
        Estatísticas do agente
    
    Raises:
        HTTPException: Se feedback_system não estiver disponível
    """
    if not feedback_system:
        raise HTTPException(
            status_code=503,
            detail="Sistema de feedback não está disponível"
        )
    
    try:
        stats = await feedback_system.get_agent_stats(agent_name, days=days)
        
        return AgentStatsResponse(
            agent_name=agent_name,
            period=f"{days} days",
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"❌ Erro ao obter stats do agente {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@app.get("/api/stats/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(days: int = 7):
    """
    Retorna estatísticas globais para dashboard.
    
    Args:
        days: Número de dias para considerar (default: 7)
    
    Returns:
        Estatísticas globais agregadas
    
    Raises:
        HTTPException: Se feedback_system não estiver disponível
    """
    if not feedback_system:
        raise HTTPException(
            status_code=503,
            detail="Sistema de feedback não está disponível"
        )
    
    try:
        dashboard = await feedback_system.get_dashboard_stats(days=days)
        
        return DashboardStatsResponse(
            period=dashboard['period'],
            global_stats=dashboard['global'],
            by_agent=dashboard['by_agent'],
            by_classification=dashboard['by_classification'],
            top_agents=dashboard['top_agents']
        )
    
    except Exception as e:
        logger.error(f"❌ Erro ao obter dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter dashboard: {str(e)}")


@app.get("/api/feedback/metrics", response_class=PlainTextResponse)
async def get_feedback_metrics():
    """
    Exporta métricas do sistema de feedback no formato Prometheus.
    
    Returns:
        Métricas em formato Prometheus text exposition
    
    Raises:
        HTTPException: Se feedback_system não estiver disponível
    """
    if not feedback_system:
        raise HTTPException(
            status_code=503,
            detail="Sistema de feedback não está disponível"
        )
    
    try:
        metrics_text = feedback_system.export_prometheus_metrics()
        return PlainTextResponse(content=metrics_text, media_type="text/plain; version=0.0.4")
    
    except Exception as e:
        logger.error(f"❌ Erro ao exportar métricas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao exportar métricas: {str(e)}")


# ============================================================================
# FIM DOS ENDPOINTS DE FEEDBACK
# ============================================================================


# ============================================================================
# DASHBOARD ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/dashboard")
async def dashboard_page(request: Request):
    """Página do dashboard analytics"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/dashboard/analytics")
async def get_dashboard_analytics(
    period: int = 7,
    agent: str = "all",
    classification: str = "all"
):
    """
    Retorna dados agregados para o dashboard analytics.
    
    Args:
        period: Número de dias para análise (default: 7)
        agent: Filtro por agente (default: "all")
        classification: Filtro por classificação (default: "all")
    
    Returns:
        Dados completos para renderizar o dashboard
    """
    if not feedback_system:
        raise HTTPException(
            status_code=503,
            detail="Sistema de feedback não está disponível"
        )
    
    try:
        from datetime import datetime, timedelta
        
        # Calcular período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period)
        
        # Query base
        query = """
            SELECT 
                feedback_id,
                timestamp,
                usuario_id,
                agente_usado,
                classificacao,
                rating,
                comentario,
                tempo_resposta_ms
            FROM feedback
            WHERE timestamp >= $1
        """
        params = [start_date]
        
        # Filtros adicionais
        if agent != "all":
            query += " AND agente_usado = $2"
            params.append(agent)
        
        if classification != "all":
            query += f" AND classificacao = ${len(params) + 1}"
            params.append(classification)
        
        query += " ORDER BY timestamp DESC"
        
        # Executar query
        import asyncpg
        conn = await asyncpg.connect(config.database.main_url)
        try:
            feedbacks = await conn.fetch(query, *params)
            
            # Processar dados
            total_feedbacks = len(feedbacks)
            
            if total_feedbacks == 0:
                return {
                    "kpis": {
                        "total_feedbacks": 0,
                        "avg_rating": 0,
                        "positive_rate": 0,
                        "avg_response_time": 0,
                        "feedback_trend": 0,
                        "rating_trend": 0,
                        "positive_trend": 0,
                        "time_trend": 0
                    },
                    "agents": [],
                    "agentStats": [],
                    "trends": [],
                    "heatmap": [],
                    "insights": [{
                        "title": "Sem dados disponíveis",
                        "description": "Ainda não há feedbacks registrados no período selecionado.",
                        "severity": "warning",
                        "icon": "exclamation-triangle"
                    }]
                }
            
            # KPIs
            ratings = [f['rating'] for f in feedbacks]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            positive_count = sum(1 for r in ratings if r == 5)
            positive_rate = (positive_count / total_feedbacks) * 100 if total_feedbacks > 0 else 0
            
            response_times = [f['tempo_resposta_ms'] for f in feedbacks if f['tempo_resposta_ms']]
            avg_response_time = (sum(response_times) / len(response_times) / 1000) if response_times else 0
            
            # Obter dados do período anterior para cálculo de tendências
            prev_start = start_date - timedelta(days=period)
            prev_feedbacks = await conn.fetch("""
                SELECT rating, tempo_resposta_ms
                FROM feedback
                WHERE timestamp >= $1 AND timestamp < $2
            """, prev_start, start_date)
            
            # Calcular tendências
            if prev_feedbacks:
                prev_avg_rating = sum(f['rating'] for f in prev_feedbacks) / len(prev_feedbacks)
                prev_positive_rate = (sum(1 for f in prev_feedbacks if f['rating'] == 5) / len(prev_feedbacks)) * 100
                
                rating_trend = ((avg_rating - prev_avg_rating) / prev_avg_rating) * 100 if prev_avg_rating > 0 else 0
                positive_trend = positive_rate - prev_positive_rate
                feedback_trend = ((total_feedbacks - len(prev_feedbacks)) / len(prev_feedbacks)) * 100 if len(prev_feedbacks) > 0 else 0
                
                prev_times = [f['tempo_resposta_ms'] for f in prev_feedbacks if f['tempo_resposta_ms']]
                if prev_times:
                    prev_avg_time = sum(prev_times) / len(prev_times) / 1000
                    time_trend = ((avg_response_time - prev_avg_time) / prev_avg_time) * 100 if prev_avg_time > 0 else 0
                else:
                    time_trend = 0
            else:
                rating_trend = 0
                positive_trend = 0
                feedback_trend = 0
                time_trend = 0
            
            # Stats por agente
            agents_dict = {}
            for f in feedbacks:
                agent_name = f['agente_usado']
                if agent_name not in agents_dict:
                    agents_dict[agent_name] = []
                agents_dict[agent_name].append(f['rating'])
            
            agent_stats = [
                {
                    "agent": agent,
                    "avg_rating": sum(ratings) / len(ratings),
                    "count": len(ratings)
                }
                for agent, ratings in agents_dict.items()
            ]
            agent_stats.sort(key=lambda x: x['avg_rating'], reverse=True)
            
            # Tendências temporais (por dia)
            from collections import defaultdict
            daily_data = defaultdict(lambda: {"positive": 0, "negative": 0})
            
            for f in feedbacks:
                date_key = f['timestamp'].strftime('%Y-%m-%d')
                if f['rating'] == 5:
                    daily_data[date_key]["positive"] += 1
                else:
                    daily_data[date_key]["negative"] += 1
            
            trends = [
                {
                    "date": date,
                    "positive": data["positive"],
                    "negative": data["negative"]
                }
                for date, data in sorted(daily_data.items())
            ]
            
            # Heatmap de tópicos problemáticos (feedbacks negativos com comentários)
            negative_feedbacks = [f for f in feedbacks if f['rating'] == 1 and f['comentario']]
            
            # Analisar comentários para identificar tópicos
            topic_counts = defaultdict(int)
            for f in negative_feedbacks:
                comment = f['comentario'].lower()
                # Palavras-chave para categorização
                if any(word in comment for word in ['lento', 'demora', 'tempo', 'demorado']):
                    topic_counts['Latência/Performance'] += 1
                if any(word in comment for word in ['errado', 'incorreto', 'erro', 'não encontrou']):
                    topic_counts['Precisão/Relevância'] += 1
                if any(word in comment for word in ['confuso', 'difícil', 'complicado', 'entender']):
                    topic_counts['Clareza/Explicação'] += 1
                if any(word in comment for word in ['incompleto', 'faltou', 'mais detalhes']):
                    topic_counts['Completude'] += 1
                if any(word in comment for word in ['acesso', 'permissão', 'bloqueado']):
                    topic_counts['Acesso/Permissões'] += 1
                if len(topic_counts) == 0 or all(k not in comment for k in topic_counts.keys()):
                    topic_counts['Outros'] += 1
            
            # Criar heatmap (2 linhas x 3 colunas)
            heatmap_topics = list(topic_counts.items())
            heatmap = []
            for i in range(0, len(heatmap_topics), 3):
                row = {
                    "cells": [
                        {"topic": topic, "count": count, "value": count}
                        for topic, count in heatmap_topics[i:i+3]
                    ]
                }
                heatmap.append(row)
            
            # Gerar insights automáticos
            insights = []
            
            # Insight 1: Rating geral
            if avg_rating >= 4.5:
                insights.append({
                    "title": "Excelente desempenho!",
                    "description": f"O sistema está com rating médio de {avg_rating:.1f}/5.0, indicando alta satisfação dos usuários.",
                    "severity": "",
                    "icon": "check-circle"
                })
            elif avg_rating < 3.0:
                insights.append({
                    "title": "Atenção: Rating abaixo do esperado",
                    "description": f"O rating médio de {avg_rating:.1f}/5.0 indica problemas de qualidade. Revise os feedbacks negativos.",
                    "severity": "critical",
                    "icon": "exclamation-circle"
                })
            
            # Insight 2: Agente com problema
            if agent_stats:
                worst_agent = min(agent_stats, key=lambda x: x['avg_rating'])
                if worst_agent['avg_rating'] < 3.0:
                    insights.append({
                        "title": f"Agente '{worst_agent['agent']}' precisa de atenção",
                        "description": f"Rating médio de apenas {worst_agent['avg_rating']:.1f}/5.0. Considere revisar a base de conhecimento ou prompts.",
                        "severity": "warning",
                        "icon": "user-times"
                    })
            
            # Insight 3: Tópico mais problemático
            if topic_counts:
                worst_topic = max(topic_counts.items(), key=lambda x: x[1])
                if worst_topic[1] >= 3:
                    insights.append({
                        "title": f"Tópico recorrente: {worst_topic[0]}",
                        "description": f"{worst_topic[1]} feedbacks negativos mencionam problemas com {worst_topic[0].lower()}. Priorize melhorias nesta área.",
                        "severity": "warning",
                        "icon": "exclamation-triangle"
                    })
            
            # Insight 4: Tendência positiva/negativa
            if feedback_trend > 20:
                insights.append({
                    "title": "Crescimento de uso",
                    "description": f"Aumento de {feedback_trend:.1f}% no número de feedbacks comparado ao período anterior. Sistema ganhando tração!",
                    "severity": "",
                    "icon": "chart-line"
                })
            
            return {
                "kpis": {
                    "total_feedbacks": total_feedbacks,
                    "avg_rating": round(avg_rating, 2),
                    "positive_rate": round(positive_rate, 1),
                    "avg_response_time": round(avg_response_time, 1),
                    "feedback_trend": round(feedback_trend, 1),
                    "rating_trend": round(rating_trend, 1),
                    "positive_trend": round(positive_trend, 1),
                    "time_trend": round(time_trend, 1)
                },
                "agents": list(agents_dict.keys()),
                "agentStats": agent_stats,
                "trends": trends,
                "heatmap": heatmap,
                "insights": insights
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter analytics: {str(e)}")


# ============================================================================
# FIM DOS ENDPOINTS DE DASHBOARD
# ============================================================================


# ============================================================================
# ENDPOINTS DA AGENT FACTORY
# ============================================================================

class CreateSubagentRequest(BaseModel):
    """Request para criar subagente"""
    name: str = Field(..., description="Nome do agente (ex: 'Carlos', 'Marina')")
    identifier: str = Field(..., description="ID único (ex: 'dev', 'enduser')")
    specialty: str = Field(..., description="Especialidade (ex: 'Desenvolvimento', 'Suporte')")
    description: str = Field(..., description="Descrição detalhada do agente")
    keywords: List[str] = Field(..., description="Palavras-chave relacionadas")
    parent_coordinator: Optional[str] = Field(None, description="ID do coordenador pai (ex: 'ti_coordinator', 'rh')")
    table_name: Optional[str] = Field(None, description="Nome da tabela (default: knowledge_{identifier})")
    prompt_template: Optional[str] = Field(None, description="Template customizado do prompt")
    enable_mcp_tools: bool = Field(False, description="Habilitar ferramentas MCP")
    mcp_tools_category: Optional[str] = Field(None, description="Categoria das ferramentas MCP")
    allowed_tools: List[str] = Field(default_factory=list, description="Lista de ferramentas permitidas")
    llm_model: str = Field("gpt-4o-mini", description="Modelo LLM a usar")
    llm_temperature: float = Field(0.3, description="Temperatura do LLM")
    llm_max_tokens: int = Field(10000, description="Máximo de tokens")


class CreateCoordinatorRequest(BaseModel):
    """Request para criar coordenador"""
    name: str = Field(..., description="Nome do coordenador (ex: 'Coordenador TI')")
    identifier: str = Field(..., description="ID único (ex: 'ti', 'rh')")
    specialty: str = Field(..., description="Especialidade (ex: 'TI', 'Recursos Humanos')")
    description: str = Field(..., description="Descrição detalhada do coordenador")
    children_agents: List[str] = Field(..., description="Lista de IDs dos agentes filhos")


class AgentFactoryResponse(BaseModel):
    """Response da criação de agente"""
    success: bool
    identifier: str
    file_path: Optional[str] = None
    table_name: Optional[str] = None
    children: Optional[List[str]] = None
    message: str = ""
    error: Optional[str] = None


class AgentListResponse(BaseModel):
    """Response da listagem de agentes"""
    total: int
    subagents: int
    coordinators: int
    with_mcp_tools: int
    agents: List[Dict[str, Any]]


class RegistryStatsResponse(BaseModel):
    """Response das estatísticas do registry"""
    total: int
    subagents: int
    coordinators: int
    with_mcp_tools: int
    agents: List[str]


@app.post("/api/factory/create-subagent", response_model=AgentFactoryResponse)
async def create_subagent(request: CreateSubagentRequest):
    """
    Cria um novo subagent via Agent Factory
    
    Args:
        request: Dados do subagente a criar
    
    Returns:
        Resultado da criação do subagente
    
    Example:
        ```json
        {
            "name": "Roberto",
            "identifier": "servicedesk",
            "specialty": "Service Desk",
            "description": "Especialista em atendimento e suporte técnico",
            "keywords": ["suporte", "ticket", "chamado", "help desk"],
            "parent_coordinator": "ti_coordinator",
            "enable_mcp_tools": true,
            "mcp_tools_category": "servicedesk",
            "allowed_tools": ["create_ticket", "get_ticket_status"]
        }
        ```
    """
    try:
        logger.info(f"🏭 [API] Criando subagente: {request.identifier}")
        logger.info(f"   Nome: {request.name}")
        logger.info(f"   Coordenador pai: {request.parent_coordinator}")
        
        result = await create_subagent_from_config(
            name=request.name,
            identifier=request.identifier,
            specialty=request.specialty,
            description=request.description,
            keywords=request.keywords,
            table_name=request.table_name,
            prompt_template=request.prompt_template,
            enable_mcp_tools=request.enable_mcp_tools,
            mcp_tools_category=request.mcp_tools_category,
            allowed_tools=request.allowed_tools,
            llm_model=request.llm_model,
            llm_temperature=request.llm_temperature,
            llm_max_tokens=request.llm_max_tokens
        )
        
        logger.info(f"📊 [API] Resultado da criação: success={result.get('success')}, error={result.get('error')}")
        
        # ⚠️ CRÍTICO: Só vincular ao coordenador se criação foi bem-sucedida
        if not result.get('success'):
            logger.error(f"❌ [API] Subagente NÃO foi criado com sucesso, abortando vinculação ao coordenador")
            return AgentFactoryResponse(**result)
        
        # Se especificou um coordenador pai, adicionar o subagente como filho
        if request.parent_coordinator:
            try:
                logger.info(f"🔗 [API] Vinculando subagente ao coordenador {request.parent_coordinator}...")
                registry = get_registry()
                coordinator = registry.get_agent(request.parent_coordinator)
                
                if coordinator:
                    if coordinator.get('type') == 'coordinator':
                        children = coordinator.get('children', [])
                        if request.identifier not in children:
                            children.append(request.identifier)
                            registry.update_agent(request.parent_coordinator, {'children': children})
                            logger.info(f"✅ Subagente {request.identifier} adicionado ao coordenador {request.parent_coordinator}")
                        else:
                            logger.info(f"ℹ️ Subagente {request.identifier} já estava no coordenador")
                    else:
                        logger.warning(f"⚠️ {request.parent_coordinator} não é um coordenador")
                else:
                    logger.warning(f"⚠️ Coordenador {request.parent_coordinator} não encontrado")
            except Exception as e:
                logger.error(f"❌ Erro ao vincular subagente ao coordenador: {e}")
                import traceback
                traceback.print_exc()
        
        return AgentFactoryResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar subagente: {e}")
        import traceback
        traceback.print_exc()
        return AgentFactoryResponse(
            success=False,
            identifier=request.identifier,
            message="Erro ao criar subagente",
            error=str(e)
        )


@app.post("/api/factory/create-coordinator", response_model=AgentFactoryResponse)
async def create_coordinator(request: CreateCoordinatorRequest):
    """
    Cria um novo coordenador via Agent Factory
    
    Args:
        request: Dados do coordenador a criar
    
    Returns:
        Resultado da criação do coordenador
    
    Example:
        ```json
        {
            "name": "Coordenador de Vendas",
            "identifier": "vendas",
            "specialty": "Vendas e Comercial",
            "description": "Coordena agentes de vendas, propostas e CRM",
            "children_agents": ["crm", "propostas", "clientes"]
        }
        ```
    """
    try:
        logger.info(f"🏭 [API] Criando coordenador: {request.identifier}")
        
        result = await create_coordinator_from_config(
            name=request.name,
            identifier=request.identifier,
            specialty=request.specialty,
            description=request.description,
            children_agents=request.children_agents
        )
        
        return AgentFactoryResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar coordenador: {e}")
        return AgentFactoryResponse(
            success=False,
            identifier=request.identifier,
            message="Erro ao criar coordenador",
            error=str(e)
        )


@app.get("/api/factory/agents", response_model=AgentListResponse)
async def list_agents(agent_type: Optional[str] = None):
    """
    Lista todos os agentes criados via factory
    
    Args:
        agent_type: Filtrar por tipo ('coordinator' ou 'subagent')
    
    Returns:
        Lista de agentes registrados
    """
    try:
        registry = get_registry()
        
        # 🔥 CRÍTICO: Recarregar dados do arquivo antes de listar
        registry.reload()
        
        agents = registry.list_agents(agent_type=agent_type)
        stats = registry.get_statistics()
        
        logger.info(f"📊 [API] Listando agentes: total={stats['total']}, subagents={stats['subagents']}, coordinators={stats['coordinators']}")
        
        return AgentListResponse(
            total=stats['total'],
            subagents=stats['subagents'],
            coordinators=stats['coordinators'],
            with_mcp_tools=stats['with_mcp_tools'],
            agents=agents
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar agentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar agentes: {str(e)}")


@app.get("/api/factory/agents/{identifier}")
async def get_agent(identifier: str):
    """
    Retorna dados de um agente específico
    
    Args:
        identifier: ID do agente
    
    Returns:
        Dados do agente
    """
    try:
        registry = get_registry()
        agent = registry.get_agent(identifier)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agente '{identifier}' não encontrado")
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar agente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar agente: {str(e)}")


@app.delete("/api/factory/agents/{identifier}")
async def delete_agent(identifier: str):
    """
    Remove um agente do registry
    
    Args:
        identifier: ID do agente
    
    Returns:
        Status da remoção
    """
    try:
        registry = get_registry()
        success = registry.delete_agent(identifier)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Agente '{identifier}' não encontrado")
        
        return {
            "success": True,
            "message": f"Agente '{identifier}' removido com sucesso",
            "identifier": identifier
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar agente: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar agente: {str(e)}")


@app.get("/api/factory/stats", response_model=RegistryStatsResponse)
async def get_factory_stats():
    """
    Retorna estatísticas sobre os agentes criados
    
    Returns:
        Estatísticas do registry
    """
    try:
        registry = get_registry()
        stats = registry.get_statistics()
        
        return RegistryStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@app.get("/api/factory/frontend-config")
async def get_frontend_config():
    """
    Exporta configuração de agentes para o frontend
    
    Returns:
        Configuração formatada para o index.html
    """
    try:
        registry = get_registry()
        config = registry.export_to_frontend_config()
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar config para frontend: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao exportar configuração: {str(e)}")


# ============================================================================
# ENDPOINT PARA SERVIR HTMLs DOS AGENTES
# ============================================================================

@app.get("/agents/{identifier}")
async def serve_agent_page(identifier: str):
    """
    Serve a página HTML de um agente específico
    
    Args:
        identifier: Identificador único do agente
        
    Returns:
        HTML da página do agente
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    try:
        registry = get_registry()
        agent = registry.get_agent(identifier)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agente '{identifier}' não encontrado")
        
        # Verificar se tem html_path no registro
        html_path = agent.get("html_path")
        
        if not html_path:
            raise HTTPException(
                status_code=404, 
                detail=f"Página HTML não encontrada para agente '{identifier}'"
            )
        
        # Verificar se arquivo existe
        html_file = Path(html_path)
        
        if not html_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Arquivo HTML não existe: {html_path}"
            )
        
        return FileResponse(
            path=html_file,
            media_type="text/html",
            headers={"Cache-Control": "no-cache"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao servir página do agente {identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar página: {str(e)}")


# ============================================================================
# FIM DOS ENDPOINTS DA AGENT FACTORY
# ============================================================================


# Montar arquivos estáticos (DEVE ser após todas as rotas)
logger.info("📁 Montando diretório /static...")
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("✅ Diretório /static montado com sucesso!")


if __name__ == '__main__':
    import uvicorn
    
    logger.info("🚀 Iniciando servidor FastAPI...")
    logger.info("📍 Servidor disponível em: http://127.0.0.1:8000")
    logger.info("📚 Documentação interativa em: http://127.0.0.1:8000/docs")
    logger.info("📊 Documentação alternativa em: http://127.0.0.1:8000/redoc")
    
    # Configuração para desenvolvimento
    uvicorn.run(
        "app_fastapi:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload em desenvolvimento
        log_level="info"
    )
