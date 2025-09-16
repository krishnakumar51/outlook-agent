#!/usr/bin/env python3
import sqlite3
import uuid
import threading
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Import our components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.constants import generate_demo_data, SAMPLE_USERS
from agent.graph import create_outlook_agent
from llm.llm_client import get_llm_client, test_llm_providers

# Import backend components
from .models import (
    OutlookAccountRequest, DemoAccountsRequest, LLMTestRequest, LLMErrorAnalysisRequest,
    OutlookAccountResponse, ProcessStatusResponse, LLMResponse, LLMProvidersResponse,
    OutlookAccountsResponse, SystemHealth, BaseResponse, OutlookAccountSummary
)
from .db import get_database
from .settings import get_settings
from .logging_middleware import setup_logging, get_process_logger

# Initialize settings and database
settings = get_settings()
db = get_database(settings.database.path)

# Create FastAPI app
app = FastAPI(
    title="Mobile Outlook Agent API",
    version="1.0.0",
    description="Automated Outlook account creation with LLM integration"
)

# Setup logging
logger = setup_logging(app)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for in-memory state
agent_results = {}
active_processes = {}

def outlook_automation_worker(request_data: Dict[str, Any], process_id: str):
    # Background worker for Outlook automation with enhanced logging
    process_logger = get_process_logger(process_id)

    try:
        process_logger.info(f"Starting Outlook automation", "init")

        # Update database status
        db.update_outlook_process(process_id, status="running")

        # Create and run agent with LLM support
        agent = create_outlook_agent(use_llm=request_data.get("use_llm", True))

        # Track process
        active_processes[process_id] = {
            "start_time": time.time(),
            "status": "running"
        }

        result = agent.run(
            process_id=process_id,
            first_name=request_data['first_name'],
            last_name=request_data['last_name'],
            date_of_birth=request_data['date_of_birth'],
            curp_id=request_data.get('curp_id')
        )

        # Calculate duration
        duration = time.time() - active_processes[process_id]["start_time"]

        # Store result
        agent_results[process_id] = result

        # Update database
        if result.get("success"):
            process_logger.info("Outlook automation completed successfully", "complete")
            db.update_outlook_process(
                process_id,
                email=result.get("account_email"),
                password=result.get("account_password", "wrfyh@6498$"),
                status="completed",
                completed_at=datetime.now(),
                duration=duration
            )
        else:
            process_logger.error(f"Outlook automation failed: {result.get('error_message')}", "error")
            db.update_outlook_process(
                process_id,
                status="failed",
                error_message=result.get("error_message"),
                completed_at=datetime.now(),
                duration=duration
            )

        # Remove from active processes
        active_processes.pop(process_id, None)

    except Exception as e:
        error_message = f"Automation worker failed: {e}"
        duration = time.time() - active_processes.get(process_id, {}).get("start_time", time.time())

        error_result = {
            "process_id": process_id,
            "success": False,
            "error_message": error_message,
            "progress_percentage": 0
        }

        agent_results[process_id] = error_result

        db.update_outlook_process(
            process_id,
            status="failed",
            error_message=error_message,
            completed_at=datetime.now(),
            duration=duration
        )

        process_logger.error(f"Worker error: {e}", "error")
        active_processes.pop(process_id, None)

# API Routes

@app.get("/", response_model=SystemHealth)
async def root():
    # API root endpoint with system status
    llm_client = get_llm_client()
    available_providers = llm_client.get_available_providers()

    return SystemHealth(
        status="running",
        features={
            "outlook_automation": True,
            "llm_integration": bool(available_providers),
            "database": True,
            "logging": True
        },
        llm_providers=available_providers
    )

@app.post("/outlook/create", response_model=OutlookAccountResponse)
async def create_outlook_account(request: OutlookAccountRequest, background_tasks: BackgroundTasks):
    # Create Outlook account with provided data

    # Generate process ID
    process_id = str(uuid.uuid4())

    # Create database record
    success = db.create_outlook_process(
        process_id=process_id,
        first_name=request.first_name,
        last_name=request.last_name,
        date_of_birth=request.date_of_birth,
        curp_id=request.curp_id,
        use_llm=request.use_llm
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to create process record")

    # Prepare request data
    request_data = {
        "first_name": request.first_name,
        "last_name": request.last_name,
        "date_of_birth": request.date_of_birth,
        "curp_id": request.curp_id,
        "use_llm": request.use_llm
    }

    logger.info(f"Queued Outlook creation: {request.first_name} {request.last_name}")

    # Start background task
    background_tasks.add_task(outlook_automation_worker, request_data, process_id)

    return OutlookAccountResponse(
        success=True,
        message=f"Started Outlook account creation for {request.first_name} {request.last_name}",
        process_id=process_id,
        account_data={"estimated_duration": 180}
    )

@app.post("/outlook/demo", response_model=BaseResponse)
async def create_demo_accounts(request: DemoAccountsRequest, background_tasks: BackgroundTasks):
    # Create demo Outlook accounts

    process_ids = []

    for i in range(request.count):
        # Generate demo data
        if i < len(SAMPLE_USERS):
            demo_data = SAMPLE_USERS[i].copy()
        else:
            demo_data = generate_demo_data()

        demo_data["use_llm"] = request.use_llm

        process_id = str(uuid.uuid4())
        process_ids.append(process_id)

        # Create database record
        db.create_outlook_process(
            process_id=process_id,
            first_name=demo_data['first_name'],
            last_name=demo_data['last_name'],
            date_of_birth=demo_data['date_of_birth'],
            curp_id=demo_data.get('curp_id'),
            use_llm=request.use_llm
        )

        logger.info(f"Queued demo {i+1}/{request.count}: {demo_data['first_name']} {demo_data['last_name']}")

        # Start background task
        background_tasks.add_task(outlook_automation_worker, demo_data, process_id)

    return BaseResponse(
        success=True,
        message=f"Started {request.count} demo Outlook creations"
    )

@app.get("/outlook/status/{process_id}", response_model=ProcessStatusResponse)
async def get_process_status(process_id: str):
    # Get status of specific process

    # Check if result is available in memory
    if process_id in agent_results:
        result = agent_results[process_id]
        logs = db.get_process_logs(process_id, limit=20)

        return ProcessStatusResponse(
            process_id=process_id,
            status="completed" if result.get("success") else "failed",
            progress_percentage=result.get("progress_percentage", 0),
            current_step=result.get("current_step"),
            error_message=result.get("error_message"),
            logs=[log["message"] for log in logs],
            duration=result.get("duration")
        )

    # Check if process is active
    if process_id in active_processes:
        logs = db.get_process_logs(process_id, limit=10)

        return ProcessStatusResponse(
            process_id=process_id,
            status="running",
            progress_percentage=50,
            current_step="processing",
            logs=[log["message"] for log in logs]
        )

    # Check database for stored results
    process_data = db.get_outlook_process(process_id)

    if process_data:
        logs = db.get_process_logs(process_id, limit=20)

        return ProcessStatusResponse(
            process_id=process_id,
            status=process_data["status"],
            progress_percentage=100 if process_data["status"] == "completed" else 0,
            current_step=process_data["status"],
            error_message=process_data["error_message"],
            logs=[log["message"] for log in logs],
            duration=process_data["duration"]
        )

    # Process not found
    raise HTTPException(status_code=404, detail="Process not found")

@app.get("/outlook/accounts", response_model=OutlookAccountsResponse)
async def get_all_accounts():
    # Get all created Outlook accounts
    try:
        accounts_data = db.get_all_outlook_accounts(limit=100)
        stats = db.get_account_stats()

        accounts = []
        for account in accounts_data:
            accounts.append(OutlookAccountSummary(
                process_id=account["process_id"],
                email=account["email"],
                password=account["password"],
                status=account["status"],
                created_at=account["created_at"],
                completed_at=account["completed_at"],
                error_message=account["error_message"],
                used_llm=bool(account.get("used_llm", False))
            ))

        return OutlookAccountsResponse(
            accounts=accounts,
            total_count=stats["total"],
            successful_count=stats["successful"],
            failed_count=stats["failed"]
        )

    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.post("/llm/test", response_model=LLMResponse)
async def test_llm_response(request: LLMTestRequest):
    # Test LLM response with different providers
    try:
        llm_client = get_llm_client()

        result = llm_client.generate_response(
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # Record usage
        db.record_llm_usage(
            provider=request.provider or "unknown",
            model=request.model,
            prompt=request.prompt,
            response=result.get("response"),
            success=result.get("success", False),
            error_message=result.get("error")
        )

        return LLMResponse(**result)

    except Exception as e:
        logger.error(f"LLM test error: {e}")
        return LLMResponse(
            success=False,
            response=None,
            provider=request.provider or "unknown",
            model=request.model,
            error=str(e),
            metadata={}
        )

@app.get("/llm/providers", response_model=LLMProvidersResponse)
async def get_available_providers():
    # Get list of available LLM providers
    try:
        llm_client = get_llm_client()
        available = llm_client.get_available_providers()

        return LLMProvidersResponse(
            available_providers=available,
            default_provider=settings.llm.default_provider if available else None,
            required_env_vars={
                "groq": "GROQ_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY", 
                "openai": "OPENAI_API_KEY",
                "gemini": "GOOGLE_API_KEY"
            }
        )
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        return LLMProvidersResponse(
            available_providers=[]
        )

@app.post("/llm/analyze-error")
async def analyze_automation_error(request: LLMErrorAnalysisRequest):
    # Use LLM to analyze automation errors and suggest solutions
    try:
        llm_client = get_llm_client()

        analysis = llm_client.analyze_error_context(
            error_message=request.error_message,
            step=request.step, 
            context=request.context
        )

        # Record usage
        db.record_llm_usage(
            provider=request.provider,
            prompt=f"Error analysis: {request.error_message}",
            response=str(analysis.get("analysis")),
            success=analysis.get("success", False),
            error_message=analysis.get("error")
        )

        return analysis

    except Exception as e:
        logger.error(f"LLM error analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "analysis": None
        }

@app.get("/health", response_model=SystemHealth)
async def health_check():
    # Health check endpoint
    try:
        # Check database
        stats = db.get_account_stats()

        # Check LLM providers
        llm_client = get_llm_client()
        available_providers = llm_client.get_available_providers()

        return SystemHealth(
            status="healthy",
            features={
                "outlook_automation": True,
                "llm_integration": bool(available_providers),
                "database": True,
                "logging": True
            },
            llm_providers=available_providers
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemHealth(
            status="unhealthy",
            features={
                "outlook_automation": False,
                "llm_integration": False,
                "database": False,
                "logging": True
            },
            llm_providers=[]
        )

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Mobile Outlook Agent API...")
    logger.info("Make sure Appium server is running on http://localhost:4723")

    uvicorn.run(app, host="0.0.0.0", port=8000)
