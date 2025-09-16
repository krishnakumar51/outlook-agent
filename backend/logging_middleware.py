#!/usr/bin/env python3
import time
import uuid
import logging
import json
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware 
from starlette.responses import Response as StarletteResponse

from .settings import get_settings
from .db import get_database

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger: Optional[logging.Logger] = None):
        super().__init__(app)
        self.logger = logger or logging.getLogger("outlook_agent.middleware")
        self.settings = get_settings()
        self.db = get_database()

        # Configure logger if needed
        if not self.logger.handlers:
            self.setup_logger()

    def setup_logger(self):
        formatter = logging.Formatter(self.settings.logging.format)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler if enabled
        if self.settings.logging.log_to_file:
            try:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    self.settings.logging.log_file_path,
                    maxBytes=self.settings.logging.max_file_size,
                    backupCount=self.settings.logging.backup_count
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Could not setup file logging: {e}")

        self.logger.setLevel(getattr(logging, self.settings.logging.level.upper()))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()
        timestamp = datetime.now()

        # Log request
        if self.settings.logging.log_requests:
            await self.log_request(request, request_id, timestamp)

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            if self.settings.logging.log_responses:
                await self.log_response(request, response, request_id, duration)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log error
            await self.log_error(request, e, request_id, duration)

            # Re-raise the exception
            raise e

    async def log_request(self, request: Request, request_id: str, timestamp: datetime):
        try:
            # Get client IP
            client_ip = self.get_client_ip(request)

            # Get request details
            method = request.method
            url = str(request.url)
            path = request.url.path
            query_params = dict(request.query_params)
            headers = dict(request.headers)

            # Remove sensitive headers
            headers = self.sanitize_headers(headers)

            # Get request body for POST/PUT requests
            body = None
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        body = body_bytes.decode("utf-8")
                        # Sanitize sensitive data in body
                        body = self.sanitize_body(body)
                except Exception:
                    body = "<could not read body>"

            # Create log entry
            log_data = {
                "type": "request",
                "request_id": request_id,
                "timestamp": timestamp.isoformat(),
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "url": url,
                "query_params": query_params,
                "headers": headers,
                "body": body
            }

            self.logger.info(f"Request {request_id}: {method} {path}", extra=log_data)

        except Exception as e:
            self.logger.error(f"Error logging request: {e}")

    async def log_response(self, request: Request, response: Response, 
                          request_id: str, duration: float):
        try:
            # Get response details
            status_code = response.status_code
            headers = dict(response.headers)

            # Remove sensitive headers
            headers = self.sanitize_headers(headers)

            # Create log entry
            log_data = {
                "type": "response",
                "request_id": request_id,
                "status_code": status_code,
                "duration": round(duration, 3),
                "headers": headers,
                "path": request.url.path,
                "method": request.method
            }

            # Determine log level based on status code
            if status_code >= 500:
                log_level = "error"
            elif status_code >= 400:
                log_level = "warning"
            else:
                log_level = "info"

            getattr(self.logger, log_level)(
                f"Response {request_id}: {status_code} in {duration:.3f}s",
                extra=log_data
            )

        except Exception as e:
            self.logger.error(f"Error logging response: {e}")

    async def log_error(self, request: Request, error: Exception, 
                       request_id: str, duration: float):
        try:
            # Create error log entry
            log_data = {
                "type": "error",
                "request_id": request_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "duration": round(duration, 3),
                "path": request.url.path,
                "method": request.method,
                "client_ip": self.get_client_ip(request)
            }

            self.logger.error(
                f"Request {request_id} failed: {type(error).__name__}: {str(error)}",
                extra=log_data,
                exc_info=True
            )

        except Exception as e:
            self.logger.error(f"Error logging error: {e}")

    def get_client_ip(self, request: Request) -> str:
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"

    def sanitize_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        sensitive_keys = {"authorization", "cookie", "x-api-key", "x-auth-token"}

        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value

        return sanitized

    def sanitize_body(self, body: str) -> str:
        try:
            # Try to parse as JSON and sanitize
            data = json.loads(body)

            if isinstance(data, dict):
                for field in self.settings.logging.sensitive_fields:
                    if field in data:
                        data[field] = "***REDACTED***"

                return json.dumps(data)

        except json.JSONDecodeError:
            # Not JSON, return as is (could add more sanitization)
            pass

        return body

class ProcessLogger:
    def __init__(self, process_id: str, logger: Optional[logging.Logger] = None):
        self.process_id = process_id
        self.logger = logger or logging.getLogger("outlook_agent.process")
        self.db = get_database()
        self.start_time = time.time()

    def log(self, message: str, level: str = "INFO", step: Optional[str] = None, 
           extra: Optional[Dict[str, Any]] = None):
        # Add to database
        self.db.add_process_log(
            process_id=self.process_id,
            message=message,
            step=step,
            log_level=level.upper()
        )

        # Add to application logger
        log_data = {
            "process_id": self.process_id,
            "step": step,
            "duration": round(time.time() - self.start_time, 3)
        }

        if extra:
            log_data.update(extra)

        getattr(self.logger, level.lower())(
            f"[{self.process_id}] {message}",
            extra=log_data
        )

    def info(self, message: str, step: Optional[str] = None, **kwargs):
        self.log(message, "INFO", step, kwargs)

    def warning(self, message: str, step: Optional[str] = None, **kwargs):
        self.log(message, "WARNING", step, kwargs)

    def error(self, message: str, step: Optional[str] = None, **kwargs):
        self.log(message, "ERROR", step, kwargs)

    def debug(self, message: str, step: Optional[str] = None, **kwargs):
        self.log(message, "DEBUG", step, kwargs)

def setup_logging(app):
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Setup root logger
    logger = logging.getLogger("outlook_agent")
    settings = get_settings()

    if not logger.handlers:
        formatter = logging.Formatter(settings.logging.format)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler if enabled
        if settings.logging.log_to_file:
            try:
                from logging.handlers import RotatingFileHandler
                import os

                # Create log directory if needed
                log_dir = os.path.dirname(settings.logging.log_file_path)
                os.makedirs(log_dir, exist_ok=True)

                file_handler = RotatingFileHandler(
                    settings.logging.log_file_path,
                    maxBytes=settings.logging.max_file_size,
                    backupCount=settings.logging.backup_count
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Could not setup file logging: {e}")

        logger.setLevel(getattr(logging, settings.logging.level.upper()))

    return logger

def get_process_logger(process_id: str) -> ProcessLogger:
    return ProcessLogger(process_id)
