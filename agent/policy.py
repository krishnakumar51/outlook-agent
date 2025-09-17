#!/usr/bin/env python3
"""
Agent Policy - LLM-based decision making for mobile automation
Provides prompts and logic for agentic tool orchestration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from llm.llm_client import get_llm_client
from tools.tool_registry import get_tool_descriptions_for_prompt

class OutlookAgentPolicy:
    """LLM-based policy for Outlook account creation automation."""

    def __init__(self, use_llm: bool = True, provider: str = "groq"):
        self.use_llm = use_llm
        self.llm_client = get_llm_client(provider) if use_llm else None
        self.conversation_history = []
        self.goal = "Create a Microsoft Outlook account successfully"

    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM policy."""
        tool_descriptions = get_tool_descriptions_for_prompt()

        return f"""You are an expert mobile automation agent specialized in creating Microsoft Outlook accounts.

GOAL: {self.goal}

TOOLS AVAILABLE:
{tool_descriptions}

OUTLOOK ACCOUNT CREATION WORKFLOW:
1. Welcome Screen: Find and click "CREATE NEW ACCOUNT" button
2. Email Input: Type the generated username/email
3. Password Input: Type the secure password  
4. Details Input: Select birth day, month, and type year
5. Name Input: Type first name and last name
6. CAPTCHA: Long press the CAPTCHA button for 15 seconds
7. Authentication: Wait for progress bars to complete
8. Post-Auth Navigation: Navigate through setup screens to inbox
9. Verification: Confirm inbox is visible

STRATEGY:
- Always use OCR first to understand what's on screen before taking actions
- Use exists/wait_for tools to verify elements before clicking/typing
- Be patient - mobile UIs can be slow to respond
- If an action fails, try OCR to understand the current state
- Use coordinate fallback only as last resort
- For CAPTCHA, always use long_press with 15000ms duration

DECISION RULES:
1. If unsure about screen content → use OCR to capture and analyze
2. If looking for specific element → use exists to check first
3. If element not found → try wait_for before giving up
4. If repeated failures → use OCR to reassess and adjust strategy
5. If stuck → use navigator tools for common flows

SAFETY:
- Maximum 20 tool calls per session to avoid infinite loops
- Stop immediately when inbox is detected (success)
- If same error occurs 3+ times, try different approach or abort

Be concise and focused. Make one tool call at a time. Explain your reasoning briefly.
"""

    def get_initial_message(self, account_data: Dict[str, Any]) -> str:
        """Get initial message to start the automation."""
        return f"""Starting Outlook account creation automation.

Account Details:
- Email: {account_data.get('email', 'unknown')}
- Name: {account_data.get('first_name', '')} {account_data.get('last_name', '')}
- Birth Date: {account_data.get('birth_day', '')}/{account_data.get('birth_month', '')}/{account_data.get('birth_year', '')}

Current status: Ready to begin automation. Let me first check what's currently on screen.
"""

    def should_use_llm_decision(self, context: Dict[str, Any]) -> bool:
        """Determine if LLM should make the next decision."""
        if not self.use_llm:
            return False

        # Use LLM for decision making in these cases:
        # 1. Error occurred and need to analyze
        # 2. Uncertain about screen state  
        # 3. Multiple retry attempts
        # 4. Starting new step

        error_count = context.get('consecutive_errors', 0)
        retry_count = sum(context.get('retry_counts', {}).values())
        last_action_failed = context.get('last_action_failed', False)

        return error_count > 0 or retry_count > 2 or last_action_failed or context.get('force_llm', False)

    def analyze_error_and_suggest_action(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze error and suggest next action."""
        if not self.use_llm or not self.llm_client:
            return {
                "success": False,
                "suggestion": "LLM not available for error analysis",
                "action": "continue"
            }

        prompt = f"""AUTOMATION ERROR ANALYSIS

Current Step: {error_context.get('current_step', 'unknown')}
Error Message: {error_context.get('error_message', 'No error message')}
Retry Count: {error_context.get('retry_count', 0)}
Last Tool Results: {error_context.get('recent_tool_results', [])}

Context:
- Progress: {error_context.get('progress_percentage', 0)}%
- Steps Completed: {error_context.get('steps_completed', {})}
- Account Data: {error_context.get('account_data', {})}

Based on this error, what should be the next action? Consider:
1. Is this a temporary UI issue (retry same action)?
2. Is the screen different than expected (use OCR to reassess)?
3. Is this a critical failure (abort)?
4. Should we try an alternative approach?

Provide your analysis and recommended action.
"""

        try:
            response = self.llm_client.generate_response(prompt, temperature=0.1)
            if response.get('success'):
                analysis_text = response.get('response', '')

                # Parse response for action recommendation
                action = "retry"  # default
                if any(word in analysis_text.lower() for word in ['abort', 'stop', 'critical', 'fatal']):
                    action = "abort"
                elif any(word in analysis_text.lower() for word in ['ocr', 'screen', 'assess', 'understand']):
                    action = "ocr_reassess"
                elif any(word in analysis_text.lower() for word in ['alternative', 'different', 'fallback']):
                    action = "try_alternative"

                return {
                    "success": True,
                    "analysis": analysis_text,
                    "action": action,
                    "provider": response.get('provider')
                }
            else:
                return {
                    "success": False,
                    "error": response.get('error'),
                    "action": "retry"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": "retry"
            }

    def plan_next_action(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to plan the next action based on current state."""
        if not self.use_llm or not self.llm_client:
            return self._fallback_planning(current_state)

        # Build context for LLM
        context_prompt = self._build_context_prompt(current_state)

        try:
            response = self.llm_client.generate_response(context_prompt, temperature=0.2, max_tokens=1024)

            if response.get('success'):
                plan_text = response.get('response', '')

                # Parse the response for action plan
                action_plan = self._parse_action_plan(plan_text)
                action_plan['llm_reasoning'] = plan_text
                action_plan['provider'] = response.get('provider')

                return action_plan
            else:
                print(f"🤖 [POLICY] LLM planning failed: {response.get('error')}")
                return self._fallback_planning(current_state)

        except Exception as e:
            print(f"🤖 [POLICY] LLM planning error: {e}")
            return self._fallback_planning(current_state)

    def _build_context_prompt(self, state: Dict[str, Any]) -> str:
        """Build context prompt for LLM planning."""
        current_step = state.get('current_step', 'unknown')
        progress = state.get('progress_percentage', 0)
        last_tool_results = state.get('recent_tool_results', [])
        account_data = state.get('account_data', {})

        prompt = f"""MOBILE AUTOMATION PLANNING

Current Situation:
- Step: {current_step}
- Progress: {progress}%
- Account: {account_data.get('email', 'unknown')}

Recent Tool Results:
{self._format_tool_results(last_tool_results)}

Your task: Plan the next action to progress toward creating the Outlook account.

Consider the current step in the workflow:
- welcome: Look for CREATE NEW ACCOUNT button
- email: Type username/email into input field  
- password: Type password into input field
- details: Select birth day, month, type year
- name: Type first and last name
- captcha: Long press CAPTCHA button for 15 seconds
- auth_wait: Wait for authentication to complete
- post_auth: Navigate through setup screens
- verify: Check if inbox is visible

What should be the next tool call? Be specific about the action and parameters.
Respond with your reasoning and the exact tool call to make.
"""

        return prompt

    def _format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """Format recent tool results for prompt."""
        if not results:
            return "No recent tool results"

        formatted = []
        for result in results[-3:]:  # Last 3 results
            tool_name = result.get('tool', 'unknown')
            status = result.get('status', 'unknown')
            message = result.get('message', '')[:100] + "..." if len(result.get('message', '')) > 100 else result.get('message', '')
            formatted.append(f"- {tool_name}: {status} - {message}")

        return "\n".join(formatted)

    def _parse_action_plan(self, plan_text: str) -> Dict[str, Any]:
        """Parse LLM response into actionable plan."""
        # Default plan
        plan = {
            "tool": "ocr",
            "action": "capture_and_read", 
            "parameters": {},
            "reasoning": "Default OCR to understand screen"
        }

        text_lower = plan_text.lower()

        # Look for tool mentions
        if "mobile_ui" in text_lower:
            plan["tool"] = "mobile_ui"
            if "click" in text_lower:
                plan["action"] = "click"
            elif "type" in text_lower:
                plan["action"] = "type"
            elif "exists" in text_lower:
                plan["action"] = "exists"
            elif "wait" in text_lower:
                plan["action"] = "wait_for"

        elif "gestures" in text_lower:
            plan["tool"] = "gestures"
            if "long_press" in text_lower or "captcha" in text_lower:
                plan["action"] = "long_press"
                plan["parameters"]["duration_ms"] = 15000
            elif "swipe" in text_lower:
                plan["action"] = "swipe"
            elif "tap" in text_lower:
                plan["action"] = "tap_coordinates"

        elif "navigator" in text_lower:
            plan["tool"] = "navigator"
            if "fast_path" in text_lower:
                plan["action"] = "fast_path"
            elif "wait_auth" in text_lower:
                plan["action"] = "wait_auth"
            elif "accept" in text_lower:
                plan["action"] = "accept_dialogs"

        # Extract reasoning
        if "reasoning:" in text_lower or "because" in text_lower:
            plan["reasoning"] = plan_text[:200] + "..." if len(plan_text) > 200 else plan_text

        return plan

    def _fallback_planning(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback planning when LLM is not available."""
        current_step = state.get('current_step', 'unknown')

        # Simple rule-based fallback
        if current_step == "welcome":
            return {
                "tool": "mobile_ui", 
                "action": "click",
                "parameters": {"locator": "//*[contains(@text, 'CREATE')]", "description": "Create account button"},
                "reasoning": "Fallback: Click create account button"
            }
        elif current_step == "email":
            return {
                "tool": "mobile_ui",
                "action": "type", 
                "parameters": {"locator": "android.widget.EditText", "strategy": "class", "text": state.get('account_data', {}).get('username', 'test')},
                "reasoning": "Fallback: Type email"
            }
        else:
            return {
                "tool": "ocr",
                "action": "capture_and_read",
                "parameters": {},
                "reasoning": "Fallback: Use OCR to understand screen"
            }

def create_outlook_policy(use_llm: bool = True, provider: str = "gemini") -> OutlookAgentPolicy:
    """Factory function to create Outlook agent policy."""
    return OutlookAgentPolicy(use_llm=use_llm, provider=provider)
