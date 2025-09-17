#!/usr/bin/env python3
"""
LLM Client - Unified interface for multiple LLM providers
Supports Anthropic Claude, OpenAI GPT, Google Gemini, and Groq (ChatGroq)

Key behaviors:
- Groq (ChatGroq): Instantiate per-call with model=<id>; do NOT mutate a .model attribute
- Groq deprecation fallback: auto-retry once with recommended replacement when model is decommissioned
- Gemini: default to gemini-2.0-flash; on 429/quota, return structured error and optionally fallback to Groq
"""

import os
import json
from typing import Dict, Any, Optional, List
from enum import Enum

# Groq deprecation replacement map (extend with future deprecations)
GROQ_MODEL_REPLACEMENTS = {
    # Groq-deprecated family replacements
    "llama-3.1-70b-versatile": "llama-3.3-70b-versatile",
    "llama3-70b-8192": "llama-3.3-70b-versatile",
    "llama3-8b-8192": "llama-3.1-8b-instant",
    # Add other mappings as necessary based on Groq’s deprecations page
}

class LLMProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROQ = "groq"

class LLMClient:
    """
    Unified LLM client supporting multiple providers.
    - Default provider is Groq with llama-3.3-70b-versatile.
    - Gemini default is gemini-2.0-flash.
    """

    def __init__(self, default_provider: str = "groq"):
        self.default_provider = LLMProvider(default_provider)
        self.defaults = {
            "groq_model": os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile"),
            "gemini_model": os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.0-flash"),
            "anthropic_model": os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-sonnet-20240229"),
            "openai_model": os.getenv("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo"),
        }
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize provider availability and configure SDKs."""
        self.groq_ready = bool(os.getenv("GROQ_API_KEY"))
        self.anthropic_ready = bool(os.getenv("ANTHROPIC_API_KEY"))
        self.openai_ready = bool(os.getenv("OPENAI_API_KEY"))
        self.gemini_ready = bool(os.getenv("GOOGLE_API_KEY"))

        # Configure Google Gemini SDK on demand
        self._genai = None
        if self.gemini_ready:
            try:
                import google.generativeai as genai  # type: ignore
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self._genai = genai
            except Exception:
                self.gemini_ready = False  # disable if import/config fails

    def get_available_providers(self) -> List[str]:
        """Return the list of providers that have API keys set."""
        providers = []
        if self.groq_ready:
            providers.append(LLMProvider.GROQ.value)
        if self.anthropic_ready:
            providers.append(LLMProvider.ANTHROPIC.value)
        if self.openai_ready:
            providers.append(LLMProvider.OPENAI.value)
        if self.gemini_ready:
            providers.append(LLMProvider.GEMINI.value)
        return providers

    # --------------------
    # Provider Implementations
    # --------------------

    def _groq_invoke(self, prompt: str, model: Optional[str], temperature: float, max_tokens: int) -> Dict[str, Any]:
        """
        Groq via LangChain ChatGroq: instantiate per call with model=<id>.
        If the model is decommissioned, retry once with a mapped replacement.
        """
        if not self.groq_ready:
            return {"success": False, "error": "GROQ_API_KEY not set", "provider": "groq", "model": model}

        try:
            from langchain_groq import ChatGroq  # type: ignore
        except Exception as e:
            return {"success": False, "error": f"ChatGroq import error: {e}", "provider": "groq", "model": model}

        model_id = model or self.defaults["groq_model"]
        llm = ChatGroq(model=model_id, temperature=temperature, max_tokens=max_tokens, timeout=30, max_retries=2)
        try:
            resp = llm.invoke([("human", prompt)])
            return {
                "success": True,
                "response": resp.content,
                "provider": "groq",
                "model": model_id,
                "metadata": {
                    "usage": getattr(resp, "usage_metadata", None),
                    "reasoning": getattr(resp, "additional_kwargs", {}).get("reasoning_content"),
                },
            }
        except Exception as e:
            msg = str(e)
            # Handle Groq decommissioned models by retrying once with recommended replacement
            if "decommissioned" in msg or "model_decommissioned" in msg:
                replacement = GROQ_MODEL_REPLACEMENTS.get(model_id)
                if replacement:
                    try:
                        llm2 = ChatGroq(model=replacement, temperature=temperature, max_tokens=max_tokens, timeout=30, max_retries=2)
                        resp2 = llm2.invoke([("human", prompt)])
                        return {
                            "success": True,
                            "response": resp2.content,
                            "provider": "groq",
                            "model": replacement,
                            "metadata": {
                                "usage": getattr(resp2, "usage_metadata", None),
                                "reasoning": getattr(resp2, "additional_kwargs", {}).get("reasoning_content"),
                                "fallback_from": model_id,
                            },
                        }
                    except Exception as e2:
                        return {"success": False, "error": f"Groq fallback failed: {e2}", "provider": "groq", "model": replacement}
            return {"success": False, "error": f"{e}", "provider": "groq", "model": model_id}

    def _generate_gemini(self, prompt: str, model: Optional[str], temperature: float, max_tokens: int) -> Dict[str, Any]:
        """
        Google Gemini via google-generativeai.
        Default model: gemini-2.0-flash; on 429 quota exceeded, return structured error and let caller decide fallback/backoff.
        """
        if not self.gemini_ready or self._genai is None:
            return {"success": False, "error": "GOOGLE_API_KEY not set or SDK not available", "provider": "gemini", "model": model}

        mdl = model or self.defaults["gemini_model"]
        generation_config = {"temperature": temperature, "max_output_tokens": max_tokens}
        try:
            gm = self._genai.GenerativeModel(mdl)
            resp = gm.generate_content(prompt, generation_config=generation_config)
            return {"success": True, "response": resp.text, "provider": "gemini", "model": mdl, "metadata": {}}
        except Exception as e:
            msg = str(e)
            if "429" in msg or "quota" in msg.lower():
                return {
                    "success": False,
                    "error": f"quota_exceeded:{e}",
                    "provider": "gemini",
                    "model": mdl,
                    "metadata": {"hint": "Retry with server-provided delay or fallback to another provider"},
                }
            return {"success": False, "error": f"{e}", "provider": "gemini", "model": mdl}

    def _generate_anthropic(self, prompt: str, model: Optional[str], temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Anthropic Claude messages API."""
        if not self.anthropic_ready:
            return {"success": False, "error": "ANTHROPIC_API_KEY not set", "provider": "anthropic", "model": model}
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            mdl = model or self.defaults["anthropic_model"]
            resp = client.messages.create(
                model=mdl,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content.text if getattr(resp, "content", None) else ""
            usage = {"input_tokens": getattr(resp, "usage", {}).get("input_tokens", None),
                     "output_tokens": getattr(resp, "usage", {}).get("output_tokens", None)}
            return {"success": True, "response": text, "provider": "anthropic", "model": mdl, "metadata": {"usage": usage}}
        except Exception as e:
            return {"success": False, "error": f"{e}", "provider": "anthropic", "model": model}

    def _generate_openai(self, prompt: str, model: Optional[str], temperature: float, max_tokens: int) -> Dict[str, Any]:
        """OpenAI Chat Completions API."""
        if not self.openai_ready:
            return {"success": False, "error": "OPENAI_API_KEY not set", "provider": "openai", "model": model}
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            mdl = model or self.defaults["openai_model"]
            resp = client.chat.completions.create(
                model=mdl,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            usage = {"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens, "total_tokens": resp.usage.total_tokens}
            return {"success": True, "response": resp.choices.message.content, "provider": "openai", "model": mdl, "metadata": {"usage": usage}}
        except Exception as e:
            return {"success": False, "error": f"{e}", "provider": "openai", "model": model}

    # --------------------
    # Public API
    # --------------------

    def generate_response(self, prompt: str, provider: Optional[str] = None,
                          model: Optional[str] = None, temperature: float = 0.1,
                          max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate a response using the selected provider.
        Optional behavior: if Gemini returns quota_exceeded, try Groq as a fallback when available.
        """
        prov = LLMProvider(provider or self.default_provider.value)

        if prov == LLMProvider.GROQ:
            return self._groq_invoke(prompt, model, temperature, max_tokens)

        if prov == LLMProvider.GEMINI:
            res = self._generate_gemini(prompt, model, temperature, max_tokens)
            # Optional fallback: if Gemini quota is exceeded and Groq is ready, retry on Groq
            if not res.get("success") and str(res.get("error", "")).startswith("quota_exceeded:") and self.groq_ready:
                return self._groq_invoke(prompt, None, temperature, max_tokens)
            return res

        if prov == LLMProvider.ANTHROPIC:
            return self._generate_anthropic(prompt, model, temperature, max_tokens)

        if prov == LLMProvider.OPENAI:
            return self._generate_openai(prompt, model, temperature, max_tokens)

        return {"success": False, "error": f"Provider {prov.value} not supported", "provider": prov.value, "model": model}

    def analyze_error_context(self, error_message: str, step: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use the default provider to analyze an automation error and suggest solutions.
        Returns parsed JSON when possible; otherwise includes the raw response.
        """
        prompt = f"""
You are an expert mobile automation assistant. Analyze this automation error and provide suggestions.

Error Context:
- Step: {step}
- Error: {error_message}
- Context: {json.dumps(context, indent=2)}

Please provide:
1. Likely cause of the error
2. Suggested solution/retry strategy
3. Alternative approaches
4. Whether this is a critical failure or can be skipped

Respond in JSON with keys: cause, solution, alternatives, critical
""".strip()
        res = self.generate_response(prompt)
        if res.get("success"):
            try:
                analysis = json.loads(res["response"])
                return {"success": True, "analysis": analysis, "raw_response": res["response"], "provider": res.get("provider"), "model": res.get("model")}
            except Exception:
                return {
                    "success": True,
                    "analysis": {"cause": "Unknown", "solution": res["response"], "alternatives": [], "critical": True},
                    "raw_response": res["response"],
                    "provider": res.get("provider"),
                    "model": res.get("model"),
                }
        return {"success": False, "error": res.get("error", "Unknown error"), "provider": res.get("provider"), "model": res.get("model")}

    def generate_automation_instructions(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate step-by-step automation instructions for the given task and context.
        """
        prompt = f"""
You are a mobile automation expert. Generate step-by-step instructions for this task:

Task: {task}
Context: {json.dumps(context, indent=2)}

Provide detailed steps that can be executed by an automation framework.
Consider element selectors, timing, backoff, and robust error handling.

Respond with a structured plan.
""".strip()
        return self.generate_response(prompt)

# Singleton helpers
_llm_client_singleton = None

def get_llm_client(provider: str = "gemini") -> LLMClient:
    global _llm_client_singleton
    if _llm_client_singleton is None:
        _llm_client_singleton = LLMClient(default_provider=provider)
    return _llm_client_singleton

def test_llm_providers() -> Dict[str, Any]:
    client = get_llm_client()
    prompt = "Explain mobile app automation in one sentence."
    results = {}
    for prov in client.get_available_providers():
        res = client.generate_response(prompt, provider=prov, temperature=0.1, max_tokens=128)
        results[prov] = res
    return results
