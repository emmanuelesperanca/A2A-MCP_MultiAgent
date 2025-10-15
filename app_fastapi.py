"""
Aplicação FastAPI assíncrona para o Sistema Neoson
Backend completamente assíncrono para escalabilidade máxima
Substitui o app.py Flask por uma solução moderna e performática
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime
import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager

# Core configuration
from core.config import config, print_config_summary

# Importa o sistema Neoson assíncrono
from neoson_async import criar_neoson_async

# Importa o sistema de feedback
from core.feedback_system import FeedbackSystem, get_feedback_system

# Importa o sistema de enriquecimento de respostas
from core.enrichment_system import ResponseEnricher, create_faqs_table, save_faq

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
                
                logger.info(f"✅ Resposta enriquecida com {len(enriched_data.get('documentos_relacionados', []))} docs, "
                           f"{len(enriched_data.get('faqs_similares', []))} FAQs, "
                           f"{len(enriched_data.get('proximas_sugestoes', []))} sugestões, "
                           f"{len(enriched_data.get('glossario', {}))} termos no glossário")
            
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
