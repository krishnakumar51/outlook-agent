#!/usr/bin/env python3
"""
Backend Settings - Configuration for agentic mobile automation system
Updated for enhanced OCR, tool orchestration, and LLM integration
"""

from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class LLMSettings:
    """LLM provider settings with updated model defaults."""
    default_provider: str = "gemini"
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 30
    max_retries: int = 2
    enable_usage_tracking: bool = True
    enable_error_analysis: bool = True

    # Provider-specific settings with updated models
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"  # Current Groq production model

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"

    google_api_key: Optional[str] = None
    google_model: str = "gemini-2.0-flash"  # Updated to Gemini 2.0 Flash

    def __post_init__(self):
        """Load API keys from environment variables."""
        self.groq_api_key = self.groq_api_key or os.getenv("GROQ_API_KEY")
        self.anthropic_api_key = self.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = self.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.google_api_key = self.google_api_key or os.getenv("GOOGLE_API_KEY")

@dataclass
class OCRSettings:
    """OCR and image processing settings."""
    default_engine: str = "tesseract"  # tesseract, paddleocr, easyocr
    enable_preprocessing: bool = True
    enable_caching: bool = True
    cache_max_size: int = 50

    # Preprocessing settings
    target_height: int = 800
    threshold_method: str = "adaptive"  # adaptive, otsu, simple
    enable_deskew: bool = True
    enable_denoise: bool = True

    # Confidence thresholds
    min_confidence: float = 0.3
    fallback_confidence: float = 0.1

    # Region processing
    enable_region_ocr: bool = True
    max_region_cache: int = 20

@dataclass
class AgentSettings:
    """Agentic automation settings."""
    use_llm: bool = True
    max_tool_calls: int = 25
    max_retries_per_step: int = 3
    enable_tool_logging: bool = True
    enable_structured_logs: bool = True

    # Policy settings
    llm_decision_threshold: int = 1  # errors before using LLM
    enable_fallback_rules: bool = True
    policy_temperature: float = 0.2

    # Success detection
    success_keywords: list = None
    error_keywords: list = None

    def __post_init__(self):
        if self.success_keywords is None:
            self.success_keywords = ["inbox", "search", "outlook"]
        if self.error_keywords is None:
            self.error_keywords = ["error", "failed", "timeout", "not found"]

@dataclass  
class AppiumSettings:
    """Appium driver settings."""
    platform_name: str = "Android"
    automation_name: str = "UiAutomator2" 
    device_name: str = "Android Emulator"
    app_activity: str = "com.microsoft.office.outlook.MainActivity"
    app_package: str = "com.microsoft.office.outlook"

    # Connection settings
    appium_server_url: str = "http://127.0.0.1:4723"
    implicit_wait: int = 10
    command_timeout: int = 60
    new_command_timeout: int = 300

    # Capabilities
    no_reset: bool = True
    full_reset: bool = False
    auto_grant_permissions: bool = True
    disable_window_animation: bool = True

@dataclass
class DatabaseSettings:
    """Database configuration."""
    database_url: str = "sqlite:///./outlook_automation.db"
    echo: bool = False
    pool_pre_ping: bool = True

    # Agentic-specific tables
    enable_tool_call_logging: bool = True
    enable_conversation_logging: bool = True
    retention_days: int = 30

@dataclass
class APISettings:
    """API server settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # CORS
    allow_origins: list = None
    allow_credentials: bool = True
    allow_methods: list = None
    allow_headers: list = None

    # Rate limiting
    enable_rate_limiting: bool = True
    requests_per_minute: int = 60

    # Tracing and monitoring
    enable_tool_tracing: bool = True
    enable_conversation_export: bool = True

    def __post_init__(self):
        if self.allow_origins is None:
            self.allow_origins = ["*"]
        if self.allow_methods is None:
            self.allow_methods = ["*"] 
        if self.allow_headers is None:
            self.allow_headers = ["*"]

@dataclass
class LoggingSettings:
    """Logging configuration for agentic system."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # File logging
    enable_file_logging: bool = True
    log_file: str = "logs/automation.log"
    max_file_size: str = "10MB"
    backup_count: int = 5

    # Structured logging for tools
    enable_structured_logging: bool = True
    structured_log_file: str = "logs/tool_calls.jsonl"

    # Console output control
    console_level: str = "INFO"
    disable_llm_logs: bool = True  # Don't clutter console with LLM debug logs
    tool_call_format: str = "banner"  # banner, json, minimal

# Global settings instances
llm_settings = LLMSettings()
ocr_settings = OCRSettings()
agent_settings = AgentSettings()
appium_settings = AppiumSettings()
database_settings = DatabaseSettings()
api_settings = APISettings()
logging_settings = LoggingSettings()

def get_settings():
    """Get all settings as a dictionary."""
    return {
        "llm": llm_settings,
        "ocr": ocr_settings,
        "agent": agent_settings,
        "appium": appium_settings,
        "database": database_settings,
        "api": api_settings,
        "logging": logging_settings
    }

def print_settings_summary():
    """Print a summary of current settings."""
    print("⚙️ [SETTINGS] Configuration Summary:")
    print(f"  🤖 LLM: {llm_settings.default_provider} ({llm_settings.groq_model})")
    print(f"  👁️ OCR: {ocr_settings.default_engine} (preprocessing: {ocr_settings.enable_preprocessing})")
    print(f"  🧠 Agent: LLM {'enabled' if agent_settings.use_llm else 'disabled'} (max tools: {agent_settings.max_tool_calls})")
    print(f"  📱 Appium: {appium_settings.device_name}")
    print(f"  🌐 API: {api_settings.host}:{api_settings.port}")
    print(f"  📊 Database: {database_settings.database_url}")
