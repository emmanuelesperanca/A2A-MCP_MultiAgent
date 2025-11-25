# Guia de Publicação e Deploy - Neoson Reborn

Este guia descreve como publicar o sistema Neoson em um ambiente corporativo utilizando um servidor Apache existente como porta de entrada (Reverse Proxy) e um servidor de backend dedicado.

## 🏗️ Arquitetura Proposta

```mermaid
graph LR
    User[Usuários] -->|HTTPS/443| Apache[Servidor Apache\n(Reverse Proxy)]
    Apache -->|HTTP/8000| Backend[Servidor Backend\n(Docker ou Nativo)]
    Backend -->|TCP/5432| DB[(PostgreSQL)]
```

1.  **Servidor Apache:** Recebe as requisições dos usuários, gerencia o certificado SSL e repassa para o backend.
2.  **Servidor Backend:** Roda a aplicação FastAPI (Python). Recomendamos usar **Docker** para isolamento e facilidade de atualização.
3.  **Banco de Dados:** PostgreSQL acessível pelo servidor de backend.

---

## 🐳 Docker vs Kubernetes?

**Resposta Curta:** Use **Docker**. Kubernetes é exagero para este estágio.

*   **Docker:** Altamente recomendado. Ele empacota o Python, as bibliotecas e o código em uma "caixa" que funciona igual em qualquer máquina. Evita problemas de "na minha máquina funciona".
*   **Kubernetes:** Não é necessário a menos que você precise escalar para milhares de usuários simultâneos ou tenha uma infraestrutura de cluster já pronta. Para testes com múltiplos usuários (dezenas ou centenas), um único container Docker é suficiente.

---

## 🚀 Passo a Passo para Deploy

### 1. Preparar o Banco de Dados
Certifique-se de que o PostgreSQL está rodando e acessível pelo servidor onde ficará o backend.
*   Execute os scripts da pasta `migrations/` no banco de produção.
*   Crie um usuário e senha dedicados para a aplicação.

### 2. Preparar o Backend (Usando Docker - Recomendado)

No servidor que rodará o backend (pode ser o mesmo do Apache ou outro na mesma rede):

1.  **Instale o Docker:** [Guia de Instalação](https://docs.docker.com/engine/install/)
2.  **Copie o projeto** para o servidor.
3.  **Crie o arquivo `.env`** com as configurações de produção (baseado no código):
    ```env
    DATABASE_URL=postgresql://usuario:senha@host_do_banco:5432/nome_do_banco
    OPENAI_API_KEY=sk-...
    # Outras chaves necessárias
    ```
4.  **Construa a imagem:**
    ```bash
    docker build -t neoson-backend .
    ```
5.  **Rode o container:**
    ```bash
    docker run -d \
      --name neoson-app \
      --restart always \
      -p 8000:8000 \
      --env-file .env \
      neoson-backend
    ```

*Agora seu backend está rodando na porta 8000 deste servidor.*

### 3. Configurar o Apache (Reverse Proxy)

No servidor Apache da sua empresa, você precisará configurar um **VirtualHost** ou um **Location** para redirecionar o tráfego para o backend.

**Pré-requisitos no Apache:**
Certifique-se de que os módulos de proxy estão ativos:
```bash
a2enmod proxy
a2enmod proxy_http
systemctl restart apache2
```

**Exemplo de Configuração (VirtualHost):**
Se você tiver um domínio dedicado, ex: `neoson.suaempresa.com`.

```apache
<VirtualHost *:80>
    ServerName neoson.suaempresa.com
    # Redirecionar HTTP para HTTPS (Recomendado)
    Redirect permanent / https://neoson.suaempresa.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName neoson.suaempresa.com
    
    # Configuração SSL (Certificados da empresa)
    SSLEngine on
    SSLCertificateFile /caminho/para/certificado.crt
    SSLCertificateKeyFile /caminho/para/chave.key

    # Configuração do Proxy Reverso
    ProxyPreserveHost On
    ProxyRequests Off
    
    # Redireciona tudo para o backend (IP do servidor onde rodou o Docker)
    ProxyPass / http://192.168.X.X:8000/
    ProxyPassReverse / http://192.168.X.X:8000/
    
    # Ajustes para WebSocket (se necessário no futuro)
    # ProxyPass /ws ws://192.168.X.X:8000/ws
    # ProxyPassReverse /ws ws://192.168.X.X:8000/ws
</VirtualHost>
```

**Exemplo de Configuração (Subdiretório):**
Se for acessar via `suaempresa.com/neoson`.

```apache
<Location /neoson>
    ProxyPreserveHost On
    ProxyPass http://192.168.X.X:8000
    ProxyPassReverse http://192.168.X.X:8000
</Location>
```
*Nota: Para subdiretórios, o FastAPI precisa saber que está rodando em um prefixo. Pode ser necessário ajustar o `root_path` no FastAPI.*

### 4. Testes Finais

1.  Acesse a URL configurada no Apache (ex: `https://neoson.suaempresa.com`).
2.  Verifique se a página carrega.
3.  Tente fazer login e enviar uma mensagem.
4.  Verifique os logs do container se houver erro: `docker logs -f neoson-app`.

---

## 🛠️ Opção B: Deploy Nativo (Sem Docker)

Se não puder usar Docker, você terá que configurar o ambiente Python manualmente no servidor Windows/Linux.

1.  Instale Python 3.10+.
2.  Crie um ambiente virtual: `python -m venv venv`.
3.  Ative e instale dependências: `pip install -r requirements.txt`.
4.  Rode com um gerenciador de processos para garantir que não feche.
    *   **Linux:** Crie um serviço `systemd`.
    *   **Windows:** Use o **NSSM** (Non-Sucking Service Manager) ou o Agendador de Tarefas para rodar o script `start_fastapi.py` ou o comando do Uvicorn na inicialização.

**Desvantagem:** Mais difícil de manter e atualizar as dependências no futuro.
