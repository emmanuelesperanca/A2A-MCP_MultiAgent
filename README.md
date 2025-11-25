# Neoson Reborn

Neoson is an advanced, asynchronous multi-agent AI system designed to provide specialized support across various domains (RH, TI, etc.) using a hierarchical agent architecture.

## 🚀 Features

- **Asynchronous Core**: Built with FastAPI and `asyncio` for high performance and scalability.
- **Multi-Agent Architecture**: Orchestrated by a master agent (Neoson) that delegates to specialized Coordinators and Subagents.
- **Agent Factory**: Dynamic creation and registration of agents based on configuration.
- **Hierarchical Support**: Complex domains like TI are managed by Coordinators with specific sub-specialists (Governance, Infra, Dev, Support).
- **Smart Classification**: LLM-based routing of questions to the most relevant agent.
- **Corporate Glossary**: Automatic detection and enrichment of internal terminology.
- **Knowledge Base**: Vector-based retrieval (RAG) using PostgreSQL/pgvector.

## 🛠️ Architecture Overview

The system follows a clear flow:
1.  **API Entry**: Requests enter via FastAPI (`app_fastapi.py`).
2.  **Orchestrator**: `NeosonAsync` analyzes the request.
3.  **Routing**: The request is classified and routed to a Coordinator (e.g., TI) or Subagent (e.g., RH).
4.  **Processing**: The target agent retrieves context from its knowledge base and generates a response.
5.  **Response**: The answer is returned to the user.

## 📦 Installation

1.  **Clone the repository**
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Setup**:
    - Copy `.env.example` to `.env`
    - Configure your OpenAI API Key and Database URL.

## 🚦 Usage

### Starting the Server
Run the FastAPI server:
```bash
python start_fastapi.py
```
The API will be available at `http://localhost:8000`.

### API Endpoints
-   `POST /ask_neoson_async`: Main endpoint for user questions.
-   `GET /health`: System health check.

## 📂 Project Structure

-   `agentes/`: Agent implementations (Neoson, Coordinators, Subagents).
-   `factory/`: Agent Factory and Registry.
-   `dal/`: Data Access Layer (PostgreSQL).
-   `core/`: Core utilities (Config, Classifier, Glossary).
-   `app_fastapi.py`: Main application entry point.

## 🤝 Contributing

1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.
