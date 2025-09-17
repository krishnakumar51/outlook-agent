#!/usr/bin/env python3
"""
Backend API - Enhanced for agentic mobile automation system
Provides REST API for automation management, tool call tracing, and conversation logs
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
import asyncio
from datetime import datetime, timedelta
import logging
import json
import os

from .settings import get_settings, print_settings_summary
from .models import AutomationRequest, AutomationResponse, ToolCallLog, ConversationLog
from .db import get_database, log_tool_call, log_conversation, get_automation_logs

# Initialize FastAPI app
app = FastAPI(
    title="Mobile Outlook Agent - Agentic API",
    description="REST API for agentic mobile automation with OCR and LLM orchestration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global settings
settings = get_settings()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["api"].allow_origins,
    allow_credentials=settings["api"].allow_credentials,
    allow_methods=settings["api"].allow_methods,
    allow_headers=settings["api"].allow_headers,
)

# Global state for active automations
active_automations: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("🚀 [API] Starting Agentic Mobile Automation API...")
    print_settings_summary()

    # Initialize database
    try:
        db = get_database()
        print("✅ [API] Database connection established")
    except Exception as e:
        print(f"❌ [API] Database initialization failed: {e}")

    print("✅ [API] Agentic API server started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🔄 [API] Shutting down agentic API server...")

    # Cancel any active automations
    for process_id in list(active_automations.keys()):
        active_automations[process_id]["cancelled"] = True

    print("✅ [API] API server shutdown complete")

# ============================================================================
# CORE AUTOMATION ENDPOINTS
# ============================================================================

@app.post("/api/v2/automation/start", response_model=AutomationResponse)
async def start_automation(
    request: AutomationRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """Start agentic automation workflow."""

    process_id = f"outlook_{uuid.uuid4().hex[:8]}"

    print(f"🚀 [API] Starting automation {process_id}")
    print(f"👤 [API] User: {request.first_name} {request.last_name}")
    print(f"🤖 [API] LLM: {'Enabled' if request.use_llm else 'Disabled'}")

    try:
        # Initialize automation state
        automation_state = {
            "process_id": process_id,
            "status": "running",
            "created_at": datetime.now(),
            "progress": 0,
            "current_step": "initializing",
            "use_llm": request.use_llm,
            "llm_provider": request.llm_provider,
            "cancelled": False,
            "tool_calls": [],
            "messages": [],
            "error_message": None
        }

        active_automations[process_id] = automation_state

        # Start automation in background
        background_tasks.add_task(
            run_automation_workflow,
            process_id,
            request,
            db
        )

        response = AutomationResponse(
            process_id=process_id,
            status="started",
            message="Agentic automation workflow initiated",
            progress_percentage=0,
            current_step="initializing"
        )

        print(f"✅ [API] Automation {process_id} started successfully")
        return response

    except Exception as e:
        error_msg = f"Failed to start automation: {e}"
        print(f"❌ [API] {error_msg}")

        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/v2/automation/{process_id}/status", response_model=AutomationResponse)
async def get_automation_status(process_id: str):
    """Get current automation status with tool call summary."""

    if process_id not in active_automations:
        raise HTTPException(status_code=404, detail=f"Automation {process_id} not found")

    automation = active_automations[process_id]

    # Count successful/failed tool calls
    tool_calls = automation.get("tool_calls", [])
    successful_tools = sum(1 for call in tool_calls if call.get("success", False))
    failed_tools = len(tool_calls) - successful_tools

    response = AutomationResponse(
        process_id=process_id,
        status=automation["status"],
        message=automation.get("error_message") or f"Automation {automation['status']}",
        progress_percentage=automation.get("progress", 0),
        current_step=automation.get("current_step", "unknown"),
        account_email=automation.get("account_email"),
        duration_seconds=automation.get("duration_seconds"),
        tool_calls_made=len(tool_calls),
        successful_tool_calls=successful_tools,
        failed_tool_calls=failed_tools,
        use_llm=automation["use_llm"]
    )

    return response

@app.post("/api/v2/automation/{process_id}/cancel")
async def cancel_automation(process_id: str):
    """Cancel running automation."""

    if process_id not in active_automations:
        raise HTTPException(status_code=404, detail=f"Automation {process_id} not found")

    automation = active_automations[process_id]

    if automation["status"] in ["completed", "failed", "cancelled"]:
        return JSONResponse(content={"message": f"Automation already {automation['status']}"})

    automation["cancelled"] = True
    automation["status"] = "cancelled"

    print(f"⚠️ [API] Automation {process_id} cancelled by request")

    return JSONResponse(content={"message": "Automation cancellation requested"})

# ============================================================================
# TOOL CALL TRACING ENDPOINTS
# ============================================================================

@app.get("/api/v2/automation/{process_id}/tools")
async def get_tool_calls(process_id: str, limit: int = 50):
    """Get tool call history for automation."""

    if process_id not in active_automations:
        raise HTTPException(status_code=404, detail=f"Automation {process_id} not found")

    automation = active_automations[process_id]
    tool_calls = automation.get("tool_calls", [])

    # Return most recent tool calls
    recent_calls = tool_calls[-limit:] if len(tool_calls) > limit else tool_calls

    return {
        "process_id": process_id,
        "total_tool_calls": len(tool_calls),
        "returned_calls": len(recent_calls),
        "tool_calls": recent_calls
    }

@app.get("/api/v2/automation/{process_id}/trace")
async def get_automation_trace(process_id: str):
    """Get complete automation trace including messages and tool calls."""

    if process_id not in active_automations:
        raise HTTPException(status_code=404, detail=f"Automation {process_id} not found")

    automation = active_automations[process_id]

    # Generate trace summary
    tool_calls = automation.get("tool_calls", [])
    messages = automation.get("messages", [])

    trace_data = {
        "process_id": process_id,
        "status": automation["status"],
        "created_at": automation["created_at"].isoformat(),
        "progress": automation.get("progress", 0),
        "current_step": automation.get("current_step"),
        "use_llm": automation["use_llm"],
        "llm_provider": automation.get("llm_provider"),

        # Conversation trace
        "messages": [
            {
                "timestamp": msg.get("timestamp", "unknown"),
                "type": msg.get("type", "unknown"),
                "content": msg.get("content", "")[:200] + "..." if len(msg.get("content", "")) > 200 else msg.get("content", ""),
                "tool_calls": msg.get("tool_calls", [])
            }
            for msg in messages
        ],

        # Tool execution trace
        "tool_calls": [
            {
                "timestamp": call.get("timestamp"),
                "tool_name": call.get("tool_name"),
                "action": call.get("action"),
                "parameters": call.get("parameters", {}),
                "success": call.get("success", False),
                "duration_ms": call.get("duration_ms", 0),
                "result_summary": str(call.get("result", {}))[:100] + "..." if len(str(call.get("result", {}))) > 100 else str(call.get("result", {}))
            }
            for call in tool_calls
        ],

        # Summary statistics
        "summary": {
            "total_messages": len(messages),
            "total_tool_calls": len(tool_calls),
            "successful_tool_calls": sum(1 for call in tool_calls if call.get("success", False)),
            "unique_tools_used": len(set(call.get("tool_name") for call in tool_calls)),
            "duration_seconds": automation.get("duration_seconds")
        }
    }

    return trace_data

@app.get("/api/v2/automation/{process_id}/export")
async def export_automation_data(process_id: str, format: str = "json"):
    """Export complete automation data for analysis."""

    if process_id not in active_automations:
        raise HTTPException(status_code=404, detail=f"Automation {process_id} not found")

    automation = active_automations[process_id]

    export_data = {
        "metadata": {
            "process_id": process_id,
            "exported_at": datetime.now().isoformat(),
            "status": automation["status"],
            "created_at": automation["created_at"].isoformat(),
            "use_llm": automation["use_llm"],
            "llm_provider": automation.get("llm_provider")
        },
        "conversation": automation.get("messages", []),
        "tool_calls": automation.get("tool_calls", []),
        "final_state": {
            "progress": automation.get("progress", 0),
            "current_step": automation.get("current_step"),
            "account_email": automation.get("account_email"),
            "error_message": automation.get("error_message"),
            "duration_seconds": automation.get("duration_seconds")
        }
    }

    if format == "json":
        # Save to temporary file
        filename = f"automation_export_{process_id}.json"
        filepath = f"/tmp/{filename}"

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        return FileResponse(
            filepath,
            media_type="application/json",
            filename=filename
        )

    else:
        return export_data

# ============================================================================
# SYSTEM STATUS ENDPOINTS
# ============================================================================

@app.get("/api/v2/system/status")
async def get_system_status():
    """Get system status and health."""

    active_count = len([a for a in active_automations.values() if a["status"] == "running"])
    completed_count = len([a for a in active_automations.values() if a["status"] == "completed"])
    failed_count = len([a for a in active_automations.values() if a["status"] == "failed"])

    return {
        "status": "healthy",
        "version": "2.0.0",
        "system_type": "agentic_mobile_automation",
        "timestamp": datetime.now().isoformat(),
        "automation_stats": {
            "active_automations": active_count,
            "completed_automations": completed_count,
            "failed_automations": failed_count,
            "total_automations": len(active_automations)
        },
        "capabilities": {
            "llm_integration": True,
            "ocr_support": True,
            "tool_orchestration": True,
            "conversation_logging": True,
            "trace_export": True
        },
        "settings": {
            "max_tool_calls": settings["agent"].max_tool_calls,
            "default_llm_provider": settings["llm"].default_provider,
            "ocr_engine": settings["ocr"].default_engine,
            "tool_logging_enabled": settings["agent"].enable_tool_logging
        }
    }

@app.get("/api/v2/system/logs")
async def get_system_logs(lines: int = 100):
    """Get recent system logs."""

    log_file = settings["logging"].log_file

    if not os.path.exists(log_file):
        return {"logs": [], "message": "Log file not found"}

    try:
        with open(log_file, "r") as f:
            all_lines = f.readlines()

        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines),
            "logs": [line.strip() for line in recent_lines]
        }

    except Exception as e:
        return {"error": f"Failed to read logs: {e}"}

# ============================================================================
# BACKGROUND AUTOMATION WORKFLOW
# ============================================================================

async def run_automation_workflow(process_id: str, request: AutomationRequest, db):
    """Run the complete automation workflow in background."""

    automation = active_automations[process_id]

    try:
        print(f"🔄 [WORKFLOW] Starting background automation for {process_id}")

        # Import and create agentic agent
        from agent.graph import create_agentic_outlook_agent

        agent = create_agentic_outlook_agent(
            use_llm=request.use_llm,
            provider=request.llm_provider
        )

        automation["status"] = "running"
        automation["current_step"] = "agent_initialized"

        # Run the automation
        result = agent.run(
            process_id=process_id,
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=request.date_of_birth,
            curp_id=request.curp_id
        )

        # Update automation state with results
        automation["status"] = "completed" if result.get("success", False) else "failed"
        automation["progress"] = result.get("progress_percentage", 0)
        automation["current_step"] = result.get("current_step", "unknown")
        automation["account_email"] = result.get("account_email")
        automation["duration_seconds"] = result.get("duration_seconds")
        automation["tool_calls"] = result.get("recent_tool_calls", [])
        automation["error_message"] = result.get("error_message")

        # Log to database if enabled
        if settings["database"].enable_tool_call_logging:
            try:
                await log_automation_result(db, process_id, result)
            except Exception as e:
                print(f"⚠️ [WORKFLOW] Database logging failed: {e}")

        status = "✅ Completed" if result.get("success") else "❌ Failed"
        print(f"{status} [WORKFLOW] Automation {process_id} finished")

    except Exception as e:
        error_msg = f"Workflow execution failed: {e}"
        print(f"❌ [WORKFLOW] {error_msg}")

        automation["status"] = "failed"
        automation["error_message"] = error_msg

        import traceback
        traceback.print_exc()

async def log_automation_result(db, process_id: str, result: Dict[str, Any]):
    """Log automation result to database."""

    try:
        # Log main automation record
        automation_log = {
            "process_id": process_id,
            "success": result.get("success", False),
            "progress_percentage": result.get("progress_percentage", 0),
            "current_step": result.get("current_step"),
            "duration_seconds": result.get("duration_seconds"),
            "account_email": result.get("account_email"),
            "error_message": result.get("error_message"),
            "tool_calls_made": result.get("tool_calls_made", 0),
            "created_at": datetime.now()
        }

        # Log individual tool calls if available
        tool_calls = result.get("recent_tool_calls", [])
        for call in tool_calls:
            await log_tool_call(db, process_id, call)

        print(f"📊 [LOG] Logged automation result for {process_id}")

    except Exception as e:
        print(f"⚠️ [LOG] Database logging error: {e}")

if __name__ == "__main__":
    import uvicorn

    config = settings["api"]

    print("🚀 Starting Agentic Mobile Automation API Server...")
    print(f"🌐 Server: http://{config.host}:{config.port}")
    print(f"📖 Docs: http://{config.host}:{config.port}/docs")

    uvicorn.run(
        "backend.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )
