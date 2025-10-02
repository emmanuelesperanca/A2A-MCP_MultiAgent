"""
Aplicação Flask para servir como API backend para o Sistema Neoson
Agente Master que coordena múltiplos agentes especializados
Integrado com PyWebView para interface desktop
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import webview
import threading
import time

import asyncio

# Importa o sistema Neoson
from neoson import criar_neoson

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
CORS(app)

# Variável global para armazenar o sistema Neoson
neoson_sistema = None

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


@app.route('/')
def index():
    """Página principal da aplicação"""
    return render_template('index.html')


@app.route('/api/perfis', methods=['GET'])
def get_perfis():
    """Retorna a lista de perfis disponíveis"""
    return jsonify({
        'success': True,
        'perfis': list(PERFIS_TESTE.keys())
    })


@app.route('/api/historico/<perfil_nome>', methods=['GET'])
def get_historico(perfil_nome):
    """Retorna o histórico de conversas de um usuário"""
    try:
        global agente_rh
        if agente_rh is None:
            return jsonify({
                'success': False,
                'error': 'Agente não inicializado'
            }), 500

        if perfil_nome not in PERFIS_TESTE:
            return jsonify({
                'success': False,
                'error': 'Perfil inválido'
            }), 400

        perfil = PERFIS_TESTE[perfil_nome]
        usuario_id = f"{perfil['Nome']}_{perfil['Departamento']}"

        # Acessar memória do agente (assumindo que temos acesso à função interna)
        # Por enquanto, retornar vazio - seria necessário expor a memória
        return jsonify({
            'success': True,
            'historico': [],  # TODO: Implementar acesso à memória
            'usuario_id': usuario_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter histórico: {str(e)}'
        }), 500


@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint principal para conversas com o sistema Neoson"""
    try:
        data = request.get_json()

        if not data or 'mensagem' not in data:
            return jsonify({
                'erro': 'Mensagem é obrigatória'
            }), 400

        mensagem = data['mensagem'].strip()
        persona_selecionada = data.get('persona_selecionada', 'Gerente')
        custom_persona = data.get('custom_persona', None)

        # Validações
        if not mensagem:
            return jsonify({
                'erro': 'Mensagem não pode estar vazia'
            }), 400

        if len(mensagem) > 1000:
            return jsonify({
                'erro': 'Mensagem deve ter no máximo 1000 caracteres'
            }), 400

        # Usa o sistema Neoson global
        global neoson_sistema
        if neoson_sistema is None:
            return jsonify({
                'erro': 'Sistema Neoson não inicializado'
            }), 500

        # Seleciona perfil baseado na persona
        if custom_persona:
            # Usa persona personalizada
            perfil = custom_persona
            print(f"🎭 Usando persona personalizada: {perfil['Nome']} - {perfil['Cargo']}")
        elif persona_selecionada in PERFIS_TESTE:
            perfil = PERFIS_TESTE[persona_selecionada]
        else:
            # Usa o primeiro perfil disponível como fallback
            perfil = list(PERFIS_TESTE.values())[0]

        # Processa a pergunta através do Neoson
        print(f"🎯 App processando pergunta: '{mensagem[:50]}...'")
        resultado = neoson_sistema.processar_pergunta(mensagem, perfil)
        
        print(f"📊 Resultado do Neoson - Sucesso: {resultado['sucesso']}")
        if resultado['sucesso']:
            resposta_texto = resultado['resposta']
            print(f"📝 Resposta gerada: {len(resposta_texto)} caracteres")
            print(f"🔍 Primeiros 100 chars: {resposta_texto[:100]}...")
            
            try:
                response_data = {
                    'resposta': resultado['resposta'],
                    'agent_usado': resultado['agente_usado'],
                    'especialidade': resultado.get('especialidade', ''),
                    'classificacao': resultado.get('classificacao', ''),
                    'sucesso': True
                }
                print("✅ JSON response criado com sucesso")
                return jsonify(response_data)
            except Exception as json_error:
                print(f"❌ Erro ao criar JSON response: {json_error}")
                return jsonify({
                    'erro': f'Erro na serialização da resposta: {str(json_error)}'
                }), 500
        else:
            print(f"❌ Neoson retornou erro: {resultado['resposta']}")
            return jsonify({
                'erro': resultado['resposta']
            }), 500

    except Exception as e:
        print(f"❌ ERRO CRÍTICO no endpoint /chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'erro': f'Erro interno: {str(e)}'
        }), 500


@app.route('/api/pergunta', methods=['POST'])
def fazer_pergunta():
    """Processa a pergunta do usuário através do sistema Neoson (API legada)"""
    try:
        data = request.get_json()

        if not data or 'pergunta' not in data or 'perfil' not in data:
            return jsonify({
                'success': False,
                'error': 'Pergunta e perfil são obrigatórios'
            }), 400
        
        pergunta = data['pergunta'].strip()
        perfil_nome = data['perfil']
        
        # Validações
        if not pergunta:
            return jsonify({
                'success': False,
                'error': 'Pergunta não pode estar vazia'
            }), 400
        
        if len(pergunta) > 200:
            return jsonify({
                'success': False,
                'error': 'Pergunta deve ter no máximo 200 caracteres'
            }), 400
        
        if perfil_nome not in PERFIS_TESTE:
            return jsonify({
                'success': False,
                'error': 'Perfil inválido'
            }), 400
        
        # Usa o sistema Neoson global
        global neoson_sistema
        if neoson_sistema is None:
            return jsonify({
                'success': False,
                'error': 'Sistema Neoson não inicializado'
            }), 500
        
        # Processa a pergunta através do Neoson
        perfil = PERFIS_TESTE[perfil_nome]
        resultado = neoson_sistema.processar_pergunta(pergunta, perfil)
        
        if resultado['sucesso']:
            return jsonify({
                'success': True,
                'resposta': resultado['resposta'],
                'agente_usado': resultado['agente_usado'],
                'especialidade': resultado['especialidade'],
                'classificacao': resultado['classificacao'],
                'perfil_usado': perfil_nome,
                'caracteres': len(pergunta)
            })
        else:
            return jsonify({
                'success': False,
                'error': resultado['resposta']
            }), 500
        
    except Exception as e:
        print(f"Erro ao processar pergunta: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Retorna o status do sistema Neoson e agentes"""
    global neoson_sistema
    if neoson_sistema:
        status_sistema = neoson_sistema.obter_status_sistema()
        
        # Adicionar informações detalhadas dos sub-agentes TI
        if 'ti' in neoson_sistema.agentes:
            ti_coordinator = neoson_sistema.agentes['ti']['instancia']
            if hasattr(ti_coordinator, 'get_info'):
                ti_info = ti_coordinator.get_info()
                status_sistema['agentes']['ti']['sub_agents_info'] = ti_info.get('hierarchy_stats', {})
        
        return jsonify({
            'success': True,
            'sistema_pronto': True,
            'neoson': status_sistema
        })
    else:
        return jsonify({
            'success': True,
            'sistema_pronto': False,
            'neoson': None
        })


@app.route('/api/ti-hierarchy', methods=['GET'])
def get_ti_hierarchy():
    """Retorna informações detalhadas da hierarquia TI"""
    global neoson_sistema
    if not neoson_sistema:
        return jsonify({
            'success': False,
            'error': 'Sistema Neoson não inicializado'
        }), 500
    
    if 'ti' not in neoson_sistema.agentes:
        return jsonify({
            'success': False,
            'error': 'Sistema TI não disponível'
        }), 404
    
    try:
        ti_coordinator = neoson_sistema.agentes['ti']['instancia']
        if hasattr(ti_coordinator, 'get_info'):
            info = ti_coordinator.get_info()
            return jsonify({
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
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Informações da hierarquia não disponíveis'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter informações da hierarquia: {str(e)}'
        }), 500


@app.route('/api/test-chat', methods=['POST'])
def test_chat():
    """Endpoint de teste para depuração de problemas de chat"""
    try:
        data = request.get_json()
        print(f"🧪 Test endpoint recebeu: {data}")
        
        # Simular resposta do sistema hierárquico
        test_response = {
            'resposta': 'Esta é uma resposta de teste do sistema hierárquico TI. O sistema está funcionando corretamente e pode processar perguntas através dos sub-especialistas.',
            'agent_usado': 'Test Agent',
            'especialidade': 'Teste',
            'classificacao': 'test',
            'sucesso': True
        }
        
        print(f"✅ Test endpoint retornando: {test_response}")
        return jsonify(test_response)
        
    except Exception as e:
        print(f"❌ Erro no test endpoint: {e}")
        return jsonify({'erro': str(e)}), 500


@app.route('/limpar_memoria', methods=['POST'])
def limpar_memoria_chat():
    """Limpa a memória de conversas para a interface de chat"""
    try:
        global neoson_sistema
        if neoson_sistema is None:
            return jsonify({
                'erro': 'Sistema Neoson não inicializado'
            }), 500
        
        # Limpa memória de todos os perfis
        sucesso_total = True
        for perfil in PERFIS_TESTE.values():
            sucesso = neoson_sistema.limpar_memoria_usuario(perfil)
            if not sucesso:
                sucesso_total = False
        
        if sucesso_total:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Memória limpa com sucesso'
            })
        else:
            return jsonify({
                'erro': 'Erro parcial ao limpar memória'
            }), 500
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro ao limpar memória: {str(e)}'
        }), 500


@app.route('/api/limpar-memoria/<perfil_nome>', methods=['POST'])
def limpar_memoria(perfil_nome):
    """Limpa a memória de conversas de um usuário em todos os agentes"""
    try:
        if perfil_nome not in PERFIS_TESTE:
            return jsonify({
                'success': False,
                'error': 'Perfil inválido'
            }), 400
        
        global neoson_sistema
        if neoson_sistema is None:
            return jsonify({
                'success': False,
                'error': 'Sistema Neoson não inicializado'
            }), 500
        
        perfil = PERFIS_TESTE[perfil_nome]
        sucesso = neoson_sistema.limpar_memoria_usuario(perfil)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': f'Memória do usuário {perfil_nome} limpa em todos os agentes'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao limpar memória'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao limpar memória: {str(e)}'
        }), 500


def inicializar_neoson_background():
    """Inicializa o sistema Neoson em background"""
    global neoson_sistema
    try:
        print("🚀 Inicializando sistema Neoson...")
        # Como asyncio.run não funciona bem em threads, vamos criar um loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        neoson_sistema = loop.run_until_complete(criar_neoson())
        if neoson_sistema:
            print("✅ Sistema Neoson inicializado com sucesso!")
        else:
            print("❌ Falha na inicialização do sistema Neoson")
            neoson_sistema = None
        loop.close()
    except Exception as e:
        print(f"❌ Erro ao inicializar sistema Neoson: {e}")
        neoson_sistema = None


def start_flask():
    """Inicia o servidor Flask"""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def main():
    """Função principal que inicia a aplicação"""
    print("🔄 Iniciando Sistema Neoson Multi-Agente...")
    
    # Inicia a inicialização do sistema em background
    neoson_thread = threading.Thread(target=inicializar_neoson_background)
    neoson_thread.daemon = True
    neoson_thread.start()
    
    # Inicia o Flask em uma thread separada
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Aguarda um pouco para o Flask iniciar
    time.sleep(3)
    
    # Cria a janela do PyWebView
    webview.create_window(
        'Neoson - Sistema Multi-Agente de IA',
        'http://127.0.0.1:5000',
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # Inicia o PyWebView (bloqueia até a janela ser fechada)
    webview.start(debug=False)


if __name__ == '__main__':
    main()