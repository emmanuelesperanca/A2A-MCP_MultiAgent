"""
Centralized configuration management for Neoson AI System.

This module handles all environment variables and configuration settings,
following the DRY principle to avoid code duplication across the application.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    # Main database URL
    main_url: str
    
    # Knowledge base URLs for different domains
    rh_url: str
    ti_url: str
    governance_url: str
    infra_url: str
    dev_url: str
    enduser_url: str
    
    # Table names
    rh_table: str
    ti_table: str
    governance_table: str
    infra_table: str
    dev_table: str
    enduser_table: str


@dataclass
class OpenAIConfig:
    """OpenAI API configuration settings."""
    api_key: str
    embedding_model: str
    chat_model: str
    temperature: float
    max_tokens: int


@dataclass 
class AppConfig:
    """Application-wide configuration settings."""
    debug: bool
    log_level: str
    flask_host: str
    flask_port: int
    environment: str


class ConfigManager:
    """
    Centralized configuration manager.
    
    Singleton pattern to ensure consistent configuration across the application.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_configuration()
            self._setup_logging()
            ConfigManager._initialized = True
    
    def _load_configuration(self):
        """Load all configuration from environment variables."""
        
        # Database Configuration
        self.database = DatabaseConfig(
            main_url=self._get_env_var("DATABASE_URL", required=True),
            
            # Knowledge base URLs (fallback to main if not specified)
            rh_url=self._get_env_var("KNOWLEDGE_RH_DATABASE_URL") or self._get_env_var("DATABASE_URL"),
            ti_url=self._get_env_var("KNOWLEDGE_TI_DATABASE_URL") or self._get_env_var("DATABASE_URL"),
            governance_url=self._get_env_var("KNOWLEDGE_GOVERNANCE_DATABASE_URL") or self._get_env_var("DATABASE_URL"),
            infra_url=self._get_env_var("KNOWLEDGE_INFRA_DATABASE_URL") or self._get_env_var("DATABASE_URL"),
            dev_url=self._get_env_var("KNOWLEDGE_DEV_DATABASE_URL") or self._get_env_var("DATABASE_URL"),
            enduser_url=self._get_env_var("KNOWLEDGE_ENDUSER_DATABASE_URL") or self._get_env_var("DATABASE_URL"),
            
            # Table names (usar os nomes reais das tabelas no banco)
            rh_table=self._get_env_var("KNOWLEDGE_RH_TABLE", "knowledge_hr"),
            ti_table=self._get_env_var("KNOWLEDGE_TI_TABLE", "knowledge_TECH"),
            governance_table=self._get_env_var("KNOWLEDGE_GOVERNANCE_TABLE", "knowledge_IT GOVERNANCE & DELIVERY METHODS"),
            infra_table=self._get_env_var("KNOWLEDGE_INFRA_TABLE", "knowledge_IT INFRASTRUCTURE & CLOUD"),
            dev_table=self._get_env_var("KNOWLEDGE_DEV_TABLE", "knowledge_ARCHITETURE & DEV"),
            enduser_table=self._get_env_var("KNOWLEDGE_ENDUSER_TABLE", "knowledge_END-USER")
        )
        
        # OpenAI Configuration
        self.openai = OpenAIConfig(
            api_key=self._get_env_var("OPENAI_API_KEY", required=True),
            embedding_model=self._get_env_var("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            chat_model=self._get_env_var("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            temperature=float(self._get_env_var("OPENAI_TEMPERATURE", "0.3")),
            max_tokens=int(self._get_env_var("OPENAI_MAX_TOKENS", "1500"))
        )
        
        # Application Configuration
        self.app = AppConfig(
            debug=self._get_env_var("DEBUG", "false").lower() == "true",
            log_level=self._get_env_var("LOG_LEVEL", "INFO").upper(),
            flask_host=self._get_env_var("FLASK_HOST", "127.0.0.1"),
            flask_port=int(self._get_env_var("FLASK_PORT", "5000")),
            environment=self._get_env_var("ENVIRONMENT", "development")
        )
    
    def _get_env_var(self, key: str, default: str = None, required: bool = False) -> str:
        """
        Get environment variable with proper error handling.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: If True, raises error when not found
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If required variable is not found
        """
        value = os.getenv(key, default)
        
        if required and not value:
            raise ValueError(f"Required environment variable '{key}' not found")
        
        return value
    
    def _setup_logging(self):
        """Configure logging for the application."""
        logging.basicConfig(
            level=getattr(logging, self.app.log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for the given name.
        
        Args:
            name: Name for the logger (typically module or class name)
            
        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)
    
    def get_database_config(self, domain: str = "main") -> Dict[str, str]:
        """
        Get database configuration for a specific domain.
        
        Args:
            domain: Database domain (main, rh, ti, governance, infra, dev, enduser)
            
        Returns:
            Dictionary with 'url' and 'table' keys
        """
        domain_mapping = {
            "main": {"url": self.database.main_url, "table": "main"},
            "rh": {"url": self.database.rh_url, "table": self.database.rh_table},
            "ti": {"url": self.database.ti_url, "table": self.database.ti_table},
            "governance": {"url": self.database.governance_url, "table": self.database.governance_table},
            "infra": {"url": self.database.infra_url, "table": self.database.infra_table},
            "dev": {"url": self.database.dev_url, "table": self.database.dev_table},
            "enduser": {"url": self.database.enduser_url, "table": self.database.enduser_table}
        }
        
        if domain not in domain_mapping:
            raise ValueError(f"Unknown database domain: {domain}")
        
        return domain_mapping[domain]
    
    def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate all configuration settings.
        
        Returns:
            Dictionary with validation results for each component
        """
        results = {}
        
        # Validate OpenAI configuration
        try:
            if not self.openai.api_key:
                results["openai"] = False
            else:
                results["openai"] = True
        except Exception:
            results["openai"] = False
        
        # Validate database configuration
        try:
            if not self.database.main_url:
                results["database"] = False
            else:
                results["database"] = True
        except Exception:
            results["database"] = False
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for debugging.
        
        Returns:
            Dictionary with sanitized configuration summary
        """
        return {
            "database": {
                "main_configured": bool(self.database.main_url),
                "rh_configured": bool(self.database.rh_url),
                "ti_configured": bool(self.database.ti_url),
                "governance_configured": bool(self.database.governance_url),
                "tables": {
                    "rh": self.database.rh_table,
                    "ti": self.database.ti_table,
                    "governance": self.database.governance_table,
                    "infra": self.database.infra_table,
                    "dev": self.database.dev_table,
                    "enduser": self.database.enduser_table
                }
            },
            "openai": {
                "api_key_configured": bool(self.openai.api_key),
                "embedding_model": self.openai.embedding_model,
                "chat_model": self.openai.chat_model,
                "temperature": self.openai.temperature,
                "max_tokens": self.openai.max_tokens
            },
            "app": {
                "debug": self.app.debug,
                "log_level": self.app.log_level,
                "flask_host": self.app.flask_host,
                "flask_port": self.app.flask_port,
                "environment": self.app.environment
            }
        }


# Global configuration instance (Singleton)
config = ConfigManager()


# Convenience functions for backward compatibility
def get_openai_config():
    """Get OpenAI configuration."""
    return config.openai


def get_database_url(domain: str = "main"):
    """Get database URL for specific domain."""
    db_config = config.get_database_config(domain)
    return db_config["url"]


def get_table_name(domain: str):
    """Get table name for specific domain."""
    db_config = config.get_database_config(domain)
    return db_config["table"]


def validate_config():
    """Validate all configuration settings."""
    return config.validate_configuration()


def print_config_summary():
    """Print configuration summary for debugging."""
    import json
    summary = config.get_summary()
    print("🔧 Configuration Summary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
