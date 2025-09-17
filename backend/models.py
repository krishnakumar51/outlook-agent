#!/usr/bin/env python3
"""
Backend Models - Data models for agentic mobile automation system
Enhanced models for tool calls, conversations, and automation tracking
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    GEMINI = "gemini" 
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class AutomationStatus(str, Enum):
    """Automation execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStep(str, Enum):
    """Workflow step identifiers."""
    INIT = "init"
    WELCOME = "welcome"
    EMAIL = "email"
    PASSWORD = "password"
    DETAILS = "details"
    NAME = "name"
    CAPTCHA = "captcha"
    AUTH_WAIT = "auth_wait"
    POST_AUTH = "post_auth"
    VERIFY = "verify"
    CLEANUP = "cleanup"
    ERROR = "error"

# ============================================================================
# REQUEST MODELS
# ============================================================================

class AutomationRequest(BaseModel):
    """Request model for starting automation."""

    first_name: str = Field(..., min_length=1, max_length=50, description="First name for account")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name for account")
    date_of_birth: str = Field(..., pattern=r"\d{4}-\d{2}-\d{2}", description="Date of birth (YYYY-MM-DD)")
    curp_id: Optional[str] = Field(None, max_length=18, description="CURP ID (optional)")

    # Agentic settings
    use_llm: bool = Field(True, description="Enable LLM-driven decision making")
    llm_provider: LLMProvider = Field(LLMProvider.GROQ, description="LLM provider to use")
    max_tool_calls: Optional[int] = Field(25, ge=1, le=50, description="Maximum tool calls limit")

    # Advanced settings
    enable_ocr: bool = Field(True, description="Enable OCR for screen understanding")
    ocr_engine: Optional[str] = Field("tesseract", description="OCR engine preference")
    debug_mode: bool = Field(False, description="Enable detailed debug logging")

class ToolCallRequest(BaseModel):
    """Request model for manual tool execution."""

    tool_name: str = Field(..., description="Name of tool to execute")
    action: str = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    description: Optional[str] = Field(None, description="Human-readable description")

# ============================================================================
# RESPONSE MODELS  
# ============================================================================

class AutomationResponse(BaseModel):
    """Response model for automation operations."""

    process_id: str = Field(..., description="Unique process identifier")
    status: AutomationStatus = Field(..., description="Current automation status")
    message: str = Field(..., description="Human-readable status message")

    # Progress tracking
    progress_percentage: int = Field(0, ge=0, le=100, description="Completion percentage")
    current_step: Optional[WorkflowStep] = Field(None, description="Current workflow step")

    # Results
    account_email: Optional[str] = Field(None, description="Created account email")
    account_password: Optional[str] = Field(None, description="Account password")

    # Performance metrics
    duration_seconds: Optional[float] = Field(None, description="Total execution time")
    tool_calls_made: Optional[int] = Field(None, description="Number of tool calls executed")
    successful_tool_calls: Optional[int] = Field(None, description="Number of successful tool calls")
    failed_tool_calls: Optional[int] = Field(None, description="Number of failed tool calls")

    # System info
    use_llm: Optional[bool] = Field(None, description="Whether LLM was used")
    llm_provider: Optional[LLMProvider] = Field(None, description="LLM provider used")

    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: Optional[int] = Field(None, description="Number of retries attempted")

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class ToolCallResponse(BaseModel):
    """Response model for tool call execution."""

    tool_name: str = Field(..., description="Name of executed tool")
    action: str = Field(..., description="Action performed")
    success: bool = Field(..., description="Whether tool call succeeded")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")

    result: Dict[str, Any] = Field(..., description="Tool execution result")
    parameters: Dict[str, Any] = Field(..., description="Parameters used")

    timestamp: datetime = Field(..., description="Execution timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")

# ============================================================================
# LOGGING MODELS
# ============================================================================

class ToolCallLog(BaseModel):
    """Model for tool call logging."""

    id: Optional[int] = Field(None, description="Database ID")
    process_id: str = Field(..., description="Associated automation process ID")

    # Tool information
    tool_name: str = Field(..., description="Name of the tool")
    action: str = Field(..., description="Action performed")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")

    # Execution details
    success: bool = Field(..., description="Whether execution succeeded")
    duration_ms: int = Field(..., description="Execution duration")
    result: Dict[str, Any] = Field(..., description="Tool result")
    error_message: Optional[str] = Field(None, description="Error if failed")

    # Context
    step: Optional[WorkflowStep] = Field(None, description="Workflow step during execution")
    retry_attempt: int = Field(0, description="Retry attempt number")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Execution timestamp")
    user_agent: Optional[str] = Field(None, description="User agent if applicable")

class ConversationLog(BaseModel):
    """Model for conversation/message logging."""

    id: Optional[int] = Field(None, description="Database ID")
    process_id: str = Field(..., description="Associated automation process ID")

    # Message details
    message_type: str = Field(..., description="Message type (human, ai, tool)")
    content: str = Field(..., description="Message content")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Associated tool calls")

    # Context
    step: Optional[WorkflowStep] = Field(None, description="Workflow step")
    sequence_number: int = Field(..., description="Message order in conversation")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class OCRResult(BaseModel):
    """Model for OCR result data."""

    text: str = Field(..., description="Extracted text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    engine: str = Field(..., description="OCR engine used")

    # Performance
    duration_ms: int = Field(..., description="Processing duration")
    word_count: int = Field(..., description="Number of words found")

    # Region information
    region: Optional[Dict[str, int]] = Field(None, description="Screen region processed")
    bounding_boxes: Optional[List[Dict[str, int]]] = Field(None, description="Text bounding boxes")

    # Cache info
    cached: bool = Field(False, description="Whether result was cached")
    screen_hash: Optional[str] = Field(None, description="Screen hash for caching")

# ============================================================================
# SYSTEM STATUS MODELS
# ============================================================================

class SystemStatus(BaseModel):
    """System health and status information."""

    status: str = Field(..., description="Overall system status")
    version: str = Field(..., description="System version")
    timestamp: datetime = Field(..., description="Status check timestamp")

    # Automation statistics
    active_automations: int = Field(..., description="Currently running automations")
    completed_automations: int = Field(..., description="Successfully completed automations")
    failed_automations: int = Field(..., description="Failed automations")
    total_automations: int = Field(..., description="Total automations processed")

    # Resource usage
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")
    disk_usage_mb: Optional[float] = Field(None, description="Disk usage in MB")

    # Component status
    database_connected: bool = Field(..., description="Database connection status")
    ocr_engines_available: List[str] = Field(..., description="Available OCR engines")
    llm_providers_available: List[str] = Field(..., description="Available LLM providers")

    # Configuration
    settings: Dict[str, Any] = Field(..., description="Current system settings")

class AutomationStatistics(BaseModel):
    """Automation execution statistics."""

    # Time period
    period_start: datetime = Field(..., description="Statistics period start")
    period_end: datetime = Field(..., description="Statistics period end")

    # Counts
    total_automations: int = Field(..., description="Total automations in period")
    successful_automations: int = Field(..., description="Successful automations")
    failed_automations: int = Field(..., description="Failed automations")

    # Performance
    average_duration_seconds: float = Field(..., description="Average execution time")
    average_tool_calls: float = Field(..., description="Average tool calls per automation")
    success_rate_percent: float = Field(..., description="Success rate percentage")

    # Tool usage
    most_used_tools: List[Dict[str, Any]] = Field(..., description="Most frequently used tools")
    tool_success_rates: Dict[str, float] = Field(..., description="Success rate per tool")

    # LLM usage
    llm_usage_percent: float = Field(..., description="Percentage of automations using LLM")
    llm_provider_distribution: Dict[str, int] = Field(..., description="LLM provider usage")

# ============================================================================
# EXPORT/IMPORT MODELS
# ============================================================================

class AutomationExport(BaseModel):
    """Complete automation data for export."""

    # Metadata
    export_version: str = Field("2.0", description="Export format version")
    exported_at: datetime = Field(..., description="Export timestamp")
    process_id: str = Field(..., description="Process ID")

    # Automation details
    request: AutomationRequest = Field(..., description="Original request")
    response: AutomationResponse = Field(..., description="Final response")

    # Execution trace
    tool_calls: List[ToolCallLog] = Field(..., description="All tool calls")
    conversation: List[ConversationLog] = Field(..., description="Conversation log")

    # Performance data
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")

    # System context
    system_info: Dict[str, Any] = Field(..., description="System information during execution")

class TraceData(BaseModel):
    """Detailed trace data for debugging."""

    process_id: str = Field(..., description="Process ID")
    timeline: List[Dict[str, Any]] = Field(..., description="Chronological event timeline")

    # Execution flow
    decision_points: List[Dict[str, Any]] = Field(..., description="LLM decision points")
    tool_executions: List[Dict[str, Any]] = Field(..., description="Tool execution details")
    error_events: List[Dict[str, Any]] = Field(..., description="Error and retry events")

    # State transitions
    state_changes: List[Dict[str, Any]] = Field(..., description="State transition log")
    screen_captures: Optional[List[str]] = Field(None, description="Screen capture hashes")

    # Analysis
    bottlenecks: List[Dict[str, Any]] = Field(..., description="Performance bottlenecks")
    suggestions: List[str] = Field(..., description="Improvement suggestions")

# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class AgentConfiguration(BaseModel):
    """Configuration for agentic automation."""

    # LLM settings
    use_llm: bool = Field(True, description="Enable LLM decision making")
    llm_provider: LLMProvider = Field(LLMProvider.GROQ, description="Default LLM provider")
    llm_temperature: float = Field(0.2, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(1024, ge=100, le=4000, description="Max LLM tokens")

    # Tool execution
    max_tool_calls: int = Field(25, ge=1, le=100, description="Max tool calls per automation")
    tool_timeout_seconds: int = Field(30, ge=5, le=300, description="Tool execution timeout")
    enable_tool_logging: bool = Field(True, description="Enable detailed tool logging")

    # OCR settings
    enable_ocr: bool = Field(True, description="Enable OCR capabilities")
    ocr_engine: str = Field("tesseract", description="Primary OCR engine")
    ocr_preprocessing: bool = Field(True, description="Enable OCR preprocessing")
    ocr_caching: bool = Field(True, description="Enable OCR result caching")

    # Error handling
    max_retries_per_step: int = Field(3, ge=0, le=10, description="Max retries per step")
    retry_delay_seconds: float = Field(1.0, ge=0.1, le=10.0, description="Delay between retries")

    # Performance
    enable_parallel_tools: bool = Field(False, description="Enable parallel tool execution")
    cache_screen_captures: bool = Field(True, description="Cache screen captures")

    # Debug options
    debug_mode: bool = Field(False, description="Enable debug mode")
    save_screenshots: bool = Field(False, description="Save all screenshots")
    verbose_logging: bool = Field(False, description="Enable verbose logging")

# Model exports for easy importing
__all__ = [
    "LLMProvider", "AutomationStatus", "WorkflowStep",
    "AutomationRequest", "ToolCallRequest",
    "AutomationResponse", "ToolCallResponse",
    "ToolCallLog", "ConversationLog", "OCRResult",
    "SystemStatus", "AutomationStatistics",
    "AutomationExport", "TraceData",
    "AgentConfiguration"
]
