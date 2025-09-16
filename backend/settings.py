#!/usr/bin/env python3
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class DatabaseSettings:
    path: str = "outlook_automation.db"
    timeout: int = 30
    enable_wal_mode: bool = True
    backup_enabled: bool = False
    backup_interval_hours: int = 24

@dataclass 
class AppiumSettings:
    server_url: str = "http://localhost:4723"
    timeout: int = 300
    implicit_wait: int = 10
    app_package: str = "com.microsoft.office.outlook"
    app_activity: str = ".MainActivity"
    device_name: str = "Android"
    platform_name: str = "Android"
    automation_name: str = "UiAutomator2"
    no_reset: bool = False
    full_reset: bool = False
    auto_grant_permissions: bool = True
    unicode_keyboard: bool = True
    reset_keyboard: bool = True

class LLMSettings:
    default_provider: str = "gemini"
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 30
    max_retries: int = 2
    enable_usage_tracking: bool = True
    enable_error_analysis: bool = True

    # Provider-specific settings
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"  # current Groq production model

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"

    google_api_key: Optional[str] = None
    google_model: str = "gemini-2.0-flash" 

@dataclass
class AutomationSettings:
    max_retries: int = 3
    retry_delay: float = 0.5
    element_timeout: int = 10
    long_press_duration: int = 15000
    auth_wait_timeout: int = 90
    post_auth_budget: float = 7.0
    enable_coordinate_fallback: bool = True
    enable_adb_fallback: bool = True
    screenshot_on_error: bool = True

@dataclass
class APISettings:
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    workers: int = 1
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_enabled: bool = False
    rate_limit_calls: int = 100
    rate_limit_period: int = 3600  # 1 hour

@dataclass
class LoggingSettings:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_file: bool = True
    log_file_path: str = "logs/outlook_agent.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_requests: bool = True
    log_responses: bool = False
    sensitive_fields: List[str] = field(default_factory=lambda: ["password", "api_key", "token"])

@dataclass
class SecuritySettings:
    api_key_required: bool = False
    api_key: Optional[str] = None
    rate_limiting: bool = False
    max_processes_per_ip: int = 3
    process_timeout: int = 1800  # 30 minutes
    enable_request_validation: bool = True

class Settings:
    def __init__(self):
        self.database = DatabaseSettings()
        self.appium = AppiumSettings()
        self.llm = LLMSettings()
        self.automation = AutomationSettings()
        self.api = APISettings()
        self.logging = LoggingSettings()
        self.security = SecuritySettings()

        self.load_from_environment()

    def load_from_environment(self):
        # Database settings
        self.database.path = os.getenv("DATABASE_PATH", self.database.path)

        # Appium settings
        self.appium.server_url = os.getenv("APPIUM_SERVER_URL", self.appium.server_url)
        self.appium.app_package = os.getenv("OUTLOOK_APP_PACKAGE", self.appium.app_package)
        self.appium.app_activity = os.getenv("OUTLOOK_APP_ACTIVITY", self.appium.app_activity)

        # LLM settings
        self.llm.default_provider = os.getenv("DEFAULT_LLM_PROVIDER", self.llm.default_provider)
        self.llm.temperature = float(os.getenv("LLM_TEMPERATURE", self.llm.temperature))
        self.llm.max_tokens = int(os.getenv("LLM_MAX_TOKENS", self.llm.max_tokens))

        # LLM API Keys
        self.llm.groq_api_key = os.getenv("GROQ_API_KEY")
        self.llm.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.llm.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llm.google_api_key = os.getenv("GOOGLE_API_KEY")

        # API settings
        self.api.host = os.getenv("API_HOST", self.api.host)
        self.api.port = int(os.getenv("API_PORT", self.api.port))
        self.api.debug = os.getenv("API_DEBUG", "false").lower() == "true"

        # Logging settings
        self.logging.level = os.getenv("LOG_LEVEL", self.logging.level)
        self.logging.log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"

        # Security settings
        self.security.api_key = os.getenv("API_KEY")
        self.security.api_key_required = bool(self.security.api_key)

    def get_llm_providers_config(self) -> Dict[str, Dict[str, Any]]:
        providers = {}

        if self.llm.groq_api_key:
            providers["groq"] = {
                "api_key": self.llm.groq_api_key,
                "model": self.llm.groq_model,
                "available": True
            }

        if self.llm.anthropic_api_key:
            providers["anthropic"] = {
                "api_key": self.llm.anthropic_api_key,
                "model": self.llm.anthropic_model,
                "available": True
            }

        if self.llm.openai_api_key:
            providers["openai"] = {
                "api_key": self.llm.openai_api_key,
                "model": self.llm.openai_model,
                "available": True
            }

        if self.llm.google_api_key:
            providers["gemini"] = {
                "api_key": self.llm.google_api_key,
                "model": self.llm.google_model,
                "available": True
            }

        return providers

    def get_appium_capabilities(self) -> Dict[str, Any]:
        return {
            "platformName": self.appium.platform_name,
            "deviceName": self.appium.device_name,
            "appPackage": self.appium.app_package,
            "appActivity": self.appium.app_activity,
            "automationName": self.appium.automation_name,
            "noReset": self.appium.no_reset,
            "fullReset": self.appium.full_reset,
            "autoGrantPermissions": self.appium.auto_grant_permissions,
            "unicodeKeyboard": self.appium.unicode_keyboard,
            "resetKeyboard": self.appium.reset_keyboard,
            "newCommandTimeout": self.appium.timeout
        }

    def validate_settings(self) -> List[str]:
        errors = []

        # Validate database path
        db_dir = Path(self.database.path).parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                errors.append(f"Cannot create database directory: {db_dir}")

        # Validate log directory
        if self.logging.log_to_file:
            log_dir = Path(self.logging.log_file_path).parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception:
                    errors.append(f"Cannot create log directory: {log_dir}")

        # Validate LLM configuration
        if not self.get_llm_providers_config():
            errors.append("No LLM providers configured. Set at least one API key.")

        # Validate automation settings
        if self.automation.max_retries < 0:
            errors.append("max_retries must be >= 0")

        if self.automation.element_timeout < 1:
            errors.append("element_timeout must be >= 1")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "database": {
                "path": self.database.path,
                "timeout": self.database.timeout
            },
            "appium": {
                "server_url": self.appium.server_url,
                "app_package": self.appium.app_package,
                "timeout": self.appium.timeout
            },
            "llm": {
                "default_provider": self.llm.default_provider,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "available_providers": list(self.get_llm_providers_config().keys())
            },
            "automation": {
                "max_retries": self.automation.max_retries,
                "element_timeout": self.automation.element_timeout,
                "enable_coordinate_fallback": self.automation.enable_coordinate_fallback
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "debug": self.api.debug
            },
            "logging": {
                "level": self.logging.level,
                "log_to_file": self.logging.log_to_file
            },
            "security": {
                "api_key_required": self.security.api_key_required,
                "rate_limiting": self.security.rate_limiting
            }
        }

# Global settings instance
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings():
    global _settings
    _settings = Settings()
    return _settings

# Convenience functions for common settings
def get_database_path() -> str:
    return get_settings().database.path

def get_llm_default_provider() -> str:
    return get_settings().llm.default_provider

def get_appium_server_url() -> str:
    return get_settings().appium.server_url

def is_llm_enabled() -> bool:
    return bool(get_settings().get_llm_providers_config())

def get_api_config() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "host": settings.api.host,
        "port": settings.api.port,
        "debug": settings.api.debug,
        "reload": settings.api.reload
    }
