#!/usr/bin/env python3
"""
Agentic Outlook Mobile Agent - CORRECTED graph.py

CRITICAL FIXES:
- PASSWORD step now requires clicking Next after typing (like EMAIL step)
- Added password_typed flag to track state properly
- DETAILS step only handles actual details, not premature dropdown hunting
- Proper step gating: PASSWORD → type password → click Next → DETAILS
"""

from typing import Dict, Any, Literal, List, Optional
from datetime import datetime
import time

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from .state import (
    OutlookAgentState,
    WorkflowStep,
    create_initial_state,
    generate_outlook_account_data,
    add_tool_call_record,
    set_current_step,
    set_success,
    get_state_summary,
)
from .policy import create_outlook_policy
from tools.tool_registry import create_tool_list


class AgenticOutlookAgent:
    """Agentic mobile automation agent using LangGraph workflow orchestration."""

    def __init__(self, use_llm: bool = True, provider: str = "groq", max_tool_calls: int = 25):
        self.use_llm = use_llm
        self.provider = provider
        self.max_tool_calls = max_tool_calls
        self.policy = create_outlook_policy(use_llm=use_llm, provider=provider)
        self.graph = None
        self.tools = None
        self.tool_registry = None

        print(f"🤖 [AGENT] Initializing agentic agent (LLM: {'ON' if use_llm else 'OFF'}, Provider: {provider})")
        self.build_graph()

    def build_graph(self):
        """Build the complete agentic LangGraph workflow."""
        print("🏗️ [GRAPH] Building agentic workflow with Policy + ToolNode orchestration...")

        workflow = StateGraph(OutlookAgentState)

        # Nodes
        workflow.add_node("initialize", self.initialize_node)
        workflow.add_node("policy", self.policy_node)
        workflow.add_node("tools", self.create_tool_node_wrapper)
        workflow.add_node("evaluate", self.evaluate_node)
        workflow.add_node("llm_analyze", self.llm_analyze_node)
        workflow.add_node("cleanup", self.cleanup_node)
        workflow.add_node("error", self.error_node)

        # Edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "policy")
        workflow.add_edge("policy", "tools")
        workflow.add_edge("tools", "evaluate")

        workflow.add_conditional_edges(
            "evaluate",
            self.route_after_evaluation,
            {
                "continue": "policy",
                "success": "cleanup",
                "error": "error",
                "llm_analyze": "llm_analyze",
                "max_calls": "error",
            },
        )

        workflow.add_conditional_edges(
            "llm_analyze",
            self.route_after_llm_analysis,
            {"retry": "policy", "continue": "policy", "skip": "cleanup", "abort": "error"},
        )

        workflow.add_edge("cleanup", END)
        workflow.add_edge("error", END)

        self.graph = workflow.compile()
        print("✅ [GRAPH] Agentic workflow compiled successfully")

    # -------------------------
    # Tool node wrapper
    # -------------------------
    def create_tool_node_wrapper(self, state: OutlookAgentState) -> OutlookAgentState:
        if not self.tools and state.get("driver"):
            print("🛠️ [TOOLS] Creating ToolNode with available driver...")
            try:
                tool_list = create_tool_list(state["driver"])
                self.tools = ToolNode(tool_list)
                print(f"✅ [TOOLS] ToolNode created with {len(tool_list)} tools")
            except Exception as e:
                print(f"❌ [TOOLS] Failed to create ToolNode: {e}")
                state["error_message"] = f"Tool initialization failed: {e}"
                return state

        if self.tools:
            try:
                return self.tools.invoke(state)
            except Exception as e:
                print(f"❌ [TOOLS] ToolNode execution failed: {e}")
                state["error_message"] = f"Tool execution failed: {e}"
                return state
        else:
            state["error_message"] = "Tools not available - driver not initialized"
            return state

    # -------------------------
    # Core nodes
    # -------------------------
    def initialize_node(self, state: OutlookAgentState) -> OutlookAgentState:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"🚀 [{ts}] INITIALIZE: Starting agentic Outlook automation...")
        try:
            state = set_current_step(state, WorkflowStep.INIT, 5)

            # Generate data
            state["account_data"] = generate_outlook_account_data(
                state["first_name"], state["last_name"], state["date_of_birth"]
            )
            print(f"✅ [{ts}] Account generated: {state['account_data'].email}")

            # Driver
            from drivers.appium_client import create_outlook_driver

            driver_client = create_outlook_driver()
            if not driver_client:
                raise Exception("Failed to create Appium driver client")
            state["driver"] = driver_client.get_driver()
            state["screen_size"] = driver_client.get_screen_size()

            # Tools
            tool_list = create_tool_list(state["driver"])
            self.tools = ToolNode(tool_list)

            state["steps_completed"]["init"] = True
            state = set_current_step(state, WorkflowStep.WELCOME, 10)

            # Initial AI message
            initial_msg = AIMessage(content=self.policy.get_initial_message(state["account_data"].to_dict()))
            state["messages"].append(initial_msg)

            print(f"🎯 [{ts}] Initialization complete")
        except Exception as e:
            err = f"Initialization failed: {e}"
            print(f"❌ [{ts}] {err}")
            state["error_message"] = err
            state["current_step"] = WorkflowStep.ERROR
        return state

    def policy_node(self, state: OutlookAgentState) -> OutlookAgentState:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"🧠 [{ts}] POLICY: Analyzing state and planning next action...")

        tool_call_count = len(state.get("tool_call_history", []))
        if tool_call_count >= state.get("max_tool_calls", self.max_tool_calls):
            print(f"🛑 [{ts}] POLICY: Maximum tool calls reached ({tool_call_count})")
            state["error_message"] = "Maximum tool calls limit reached"
            return state

        try:
            context = self._get_policy_context(state)
            current_step = state["current_step"]
            print(f"📊 [{ts}] POLICY: Current step: {current_step.value}")
            print(f"📊 [{ts}] POLICY: Progress: {state.get('progress_percentage', 0)}% | Errors: {state.get('consecutive_errors', 0)}")

            # Force rule-based for core steps
            basic_steps = [
                WorkflowStep.WELCOME,
                WorkflowStep.EMAIL,
                WorkflowStep.PASSWORD,
                WorkflowStep.DETAILS,
                WorkflowStep.NAME,
            ]
            if current_step in basic_steps:
                print(f"🔄 [{ts}] POLICY: Using FORCED rule-based for {current_step.value} step")
                self._create_rule_based_tool_call(state, context)
            else:
                should_use_llm = self.policy.should_use_llm_decision(context)
                if should_use_llm and state.get("use_llm", False):
                    print(f"🤖 [{ts}] POLICY: Using LLM for decision making...")
                    action_plan = self.policy.plan_next_action(context)
                    if action_plan and action_plan.get("tool"):
                        state["messages"].append(self._create_tool_call_message(action_plan))
                        tool_name = action_plan["tool"]
                        action = action_plan.get("action", "unknown")
                        print(f"📋 [{ts}] POLICY: LLM decided → {tool_name}.{action}")
                    else:
                        self._create_fallback_tool_call(state)
                else:
                    print(f"🔄 [{ts}] POLICY: Using rule-based decision making...")
                    self._create_rule_based_tool_call(state, context)
        except Exception as e:
            print(f"❌ [{ts}] POLICY: Error: {e}")
            self._create_emergency_fallback(state)
        return state

    def evaluate_node(self, state: OutlookAgentState) -> OutlookAgentState:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"⚖️ [{ts}] EVALUATE: Analyzing tool execution results...")
        try:
            last_message = state["messages"][-1] if state["messages"] else None
            if isinstance(last_message, ToolMessage):
                tool_content = last_message.content
                tool_name = self._extract_tool_name_from_content(tool_content)

                print(f"🔍 [{ts}] EVALUATE: Tool: {tool_name}")
                print(f"🔍 [{ts}] EVALUATE: Content: {tool_content[:200]}...")

                success = self._analyze_tool_success(tool_content)
                duration_ms = self._extract_duration_from_content(tool_content)
                print(f"🔍 [{ts}] EVALUATE: Success: {success} | Duration: {duration_ms}ms")

                # Record tool call
                tool_record = self._create_tool_call_record(tool_name, tool_content, success, duration_ms)
                state = add_tool_call_record(
                    state,
                    tool_record["tool_name"],
                    tool_record["action"],
                    tool_record["parameters"],
                    tool_record["result"],
                    tool_record["duration_ms"],
                    tool_record["success"],
                )

                # Success handling and step gating
                current_step = state["current_step"]
                if self._check_automation_success(tool_content, state):
                    print(f"🎉 [{ts}] EVALUATE: SUCCESS CONDITIONS MET!")
                    state = set_success(state)
                elif success:
                    print(f"✅ [{ts}] EVALUATE: Tool executed successfully")
                    state["consecutive_errors"] = 0
                    self._update_progress_from_step(state)

                    content_l = tool_content.lower()

                    # WELCOME → EMAIL on click
                    if current_step == WorkflowStep.WELCOME and "clicked" in content_l:
                        state = set_current_step(state, WorkflowStep.EMAIL, 25)
                        print("📍 [STATE] Clicked CREATE → Advanced to EMAIL")

                    # EMAIL: type → set flag, Next click → advance to PASSWORD
                    elif current_step == WorkflowStep.EMAIL and "typed" in content_l:
                        state["email_typed"] = True
                        state["steps_completed"]["email_typed"] = True
                        print("📍 [STATE] Email typed - Next will be clicked")
                    elif current_step == WorkflowStep.EMAIL and state.get("email_typed") and "clicked" in content_l:
                        state = set_current_step(state, WorkflowStep.PASSWORD, 35)
                        print("📍 [STATE] Clicked Next after email → Advanced to PASSWORD")

                    # PASSWORD: type → set flag, Next click → advance to DETAILS
                    elif current_step == WorkflowStep.PASSWORD and "typed" in content_l:
                        state["password_typed"] = True
                        state["steps_completed"]["password_typed"] = True
                        print("📍 [STATE] Password typed - Next will be clicked")
                    elif current_step == WorkflowStep.PASSWORD and state.get("password_typed") and "clicked" in content_l:
                        state = set_current_step(state, WorkflowStep.DETAILS, 50)
                        print("📍 [STATE] Clicked Next after password → Advanced to DETAILS")

                    # DETAILS → NAME on Next click (skip dropdown if not needed)
                    elif current_step == WorkflowStep.DETAILS and "clicked" in content_l:
                        if "next" in content_l or "continue" in content_l:
                            state = set_current_step(state, WorkflowStep.NAME, 65)
                            print("📍 [STATE] Clicked Next after details → Advanced to NAME")
                        elif "dropdown" in content_l:
                            state["details_dropdown_clicked"] = True
                        elif "option" in content_l:
                            state["details_option_selected"] = True

                    # NAME: type first → flag, type last → flag, Next click → CAPTCHA
                    elif current_step == WorkflowStep.NAME and "typed" in content_l and ("first" in content_l):
                        state["first_name_typed"] = True
                        state["steps_completed"]["first_name_typed"] = True
                        print("📍 [STATE] First name typed")
                    elif current_step == WorkflowStep.NAME and "typed" in content_l and ("last" in content_l):
                        state["last_name_typed"] = True
                        state["steps_completed"]["last_name_typed"] = True
                        print("📍 [STATE] Last name typed")
                    elif current_step == WorkflowStep.NAME and "clicked" in content_l:
                        state = set_current_step(state, WorkflowStep.CAPTCHA, 75)
                        print("📍 [STATE] Clicked Next after name → Advanced to CAPTCHA")

                    # Default forward path for later steps
                    elif current_step == WorkflowStep.CAPTCHA:
                        state = set_current_step(state, WorkflowStep.AUTH_WAIT, 85)
                    elif current_step == WorkflowStep.AUTH_WAIT:
                        state = set_current_step(state, WorkflowStep.POST_AUTH, 90)
                    elif current_step == WorkflowStep.POST_AUTH:
                        state = set_current_step(state, WorkflowStep.VERIFY, 95)
                    elif current_step == WorkflowStep.VERIFY:
                        state = set_current_step(state, WorkflowStep.CLEANUP, 100)
                else:
                    print(f"⚠️ [{ts}] EVALUATE: Tool execution failed")
                    print(f"🔍 [{ts}] EVALUATE: Failure content: {tool_content}")
                    state["consecutive_errors"] = state.get("consecutive_errors", 0) + 1
            else:
                print(f"🔍 [{ts}] EVALUATE: No tool message found")
                state["consecutive_errors"] = state.get("consecutive_errors", 0) + 1

        except Exception as e:
            print(f"❌ [{ts}] EVALUATE: Error: {e}")
            state["error_message"] = f"Evaluation error: {e}"
        return state

    def llm_analyze_node(self, state: OutlookAgentState) -> OutlookAgentState:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"🔍 [{ts}] LLM_ANALYZE: Engaging LLM for error analysis...")
        if not state.get("use_llm", False):
            state["llm_analysis"] = {"success": False, "reason": "LLM disabled"}
            return state
        try:
            error_context = {
                "current_step": state["current_step"].value,
                "consecutive_errors": state.get("consecutive_errors", 0),
                "tool_call_history": [call.to_dict() for call in state.get("tool_call_history", [])[-3:]],
                "progress_percentage": state.get("progress_percentage", 0),
            }
            analysis_result = self.policy.analyze_error_and_suggest_action(error_context)
            state["llm_analysis"] = analysis_result
            if analysis_result.get("success"):
                print(f"🤖 [{ts}] LLM_ANALYZE: Suggested action → {analysis_result.get('action', 'retry')}")
            else:
                print(f"❌ [{ts}] LLM_ANALYZE: Analysis failed")
                state["llm_analysis"]["action"] = "retry"
        except Exception as e:
            print(f"❌ [{ts}] LLM_ANALYZE: Exception: {e}")
            state["llm_analysis"] = {"success": False, "error": str(e), "action": "retry"}
        return state

    def cleanup_node(self, state: OutlookAgentState) -> OutlookAgentState:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"🧹 [{ts}] CLEANUP: Finalizing automation...")
        try:
            if state.get("driver"):
                try:
                    state["driver"].quit()
                    print(f"✅ [{ts}] CLEANUP: Driver closed")
                except Exception as e:
                    print(f"⚠️ [{ts}] CLEANUP: Driver warning: {e}")

            if not state.get("end_time"):
                state["end_time"] = time.time()

            duration = state["end_time"] - state["start_time"] if state.get("start_time") else 0
            tool_calls_made = len(state.get("tool_call_history", []))

            print(f"⏱️ [{ts}] CLEANUP: Duration: {duration:.1f}s | Tool calls: {tool_calls_made}")

            if state.get("success"):
                final_content = "✅ Outlook account creation completed!"
                if state.get("account_data"):
                    final_content += f" Account: {state['account_data'].email}"
            else:
                final_content = f"❌ Automation failed: {state.get('error_message', 'Unknown error')}"

            state["messages"].append(AIMessage(content=final_content))
        except Exception as e:
            print(f"❌ [{ts}] CLEANUP: Error: {e}")
        return state

    def error_node(self, state: OutlookAgentState) -> OutlookAgentState:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"❌ [{ts}] ERROR: Terminal error handling...")
        try:
            if state.get("driver"):
                try:
                    state["driver"].quit()
                except Exception:
                    pass
            state["success"] = False
            if not state.get("end_time"):
                state["end_time"] = time.time()
            err = state.get("error_message", "Unknown error")
            print(f"💥 [{ts}] ERROR: {err}")
            state["messages"].append(AIMessage(content=f"❌ Automation failed: {err}"))
        except Exception as e:
            print(f"⚠️ [{ts}] ERROR: Exception in error handling: {e}")
        return state

    # -------------------------
    # Routing
    # -------------------------
    def route_after_evaluation(self, state: OutlookAgentState) -> Literal[
        "continue", "success", "error", "llm_analyze", "max_calls"
    ]:
        if state.get("success", False):
            return "success"
        tool_calls_made = len(state.get("tool_call_history", []))
        if tool_calls_made >= state.get("max_tool_calls", self.max_tool_calls):
            state["error_message"] = "Maximum tool calls limit reached"
            return "max_calls"
        consecutive_errors = state.get("consecutive_errors", 0)
        if consecutive_errors >= 5:
            state["error_message"] = "Too many consecutive errors"
            return "error"
        if consecutive_errors >= 2 and state.get("use_llm", False):
            return "llm_analyze"
        return "continue"

    def route_after_llm_analysis(self, state: OutlookAgentState) -> Literal[
        "retry", "continue", "skip", "abort"
    ]:
        analysis = state.get("llm_analysis", {})
        act = analysis.get("action", "retry")
        if act == "abort":
            return "abort"
        elif act == "skip":
            return "skip"
        elif act == "try_alternative":
            return "retry"
        else:
            return "continue"

    # -------------------------
    # Helpers
    # -------------------------
    def _get_policy_context(self, state: OutlookAgentState) -> Dict[str, Any]:
        recent_tools = []
        if state.get("tool_call_history"):
            recent_calls = state["tool_call_history"][-3:]
            recent_tools = [call.to_dict() for call in recent_calls]
        return {
            "current_step": state["current_step"].value,
            "progress_percentage": state.get("progress_percentage", 0),
            "account_data": state["account_data"].to_dict() if state.get("account_data") else None,
            "recent_tool_results": recent_tools,
            "consecutive_errors": state.get("consecutive_errors", 0),
            "retry_counts": state.get("retry_counts", {}),
            "steps_completed": state.get("steps_completed", {}),
            "automation_goal": state.get("automation_goal", "Create Outlook account"),
            "tool_calls_made": len(state.get("tool_call_history", [])),
            "force_llm": state.get("consecutive_errors", 0) > 1,
            "email_typed": state.get("email_typed", False),
            "password_typed": state.get("password_typed", False),
            "first_name_typed": state.get("first_name_typed", False),
            "last_name_typed": state.get("last_name_typed", False),
            "details_dropdown_clicked": state.get("details_dropdown_clicked", False),
            "details_option_selected": state.get("details_option_selected", False),
        }

    def _create_tool_call_message(self, action_plan: Dict[str, Any]) -> AIMessage:
        tool_name = action_plan["tool"]
        action = action_plan.get("action", "unknown")
        parameters = action_plan.get("parameters", {})
        parameters["action"] = action
        tool_call = {"name": tool_name, "args": parameters, "id": f"call_{int(time.time()*1000)}"}
        reasoning = action_plan.get("reasoning", f"Execute {tool_name}.{action}")
        return AIMessage(content=f"🤖 {reasoning}", tool_calls=[tool_call])

    def _create_fallback_tool_call(self, state: OutlookAgentState):
        tool_call = {"name": "ocr", "args": {"action": "capture_and_read"}, "id": f"call_fallback_{int(time.time()*1000)}"}
        state["messages"].append(AIMessage(content="🔍 Fallback: Using OCR to understand screen", tool_calls=[tool_call]))

    def _create_rule_based_tool_call(self, state: OutlookAgentState, context: Dict[str, Any]):
        current_step = state["current_step"]
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"🔧 [{ts}] RULE: Creating tool call for {current_step.value}")

        if current_step == WorkflowStep.WELCOME:
            tool_call = {
                "name": "mobile_ui",
                "args": {"action": "click", "locator": "//*[contains(@text, 'CREATE')]", "description": "Create new account button"},
                "id": f"call_rule_{int(time.time()*1000)}",
            }
            content = "🔄 Rule: Click CREATE NEW ACCOUNT"

        elif current_step == WorkflowStep.EMAIL:
            if not state.get("email_typed", False) and state.get("account_data"):
                print(f"🔧 [{ts}] RULE: Typing email: {state['account_data'].username}")
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type",
                        "locator": "android.widget.EditText",
                        "strategy": "class",
                        "text": state["account_data"].username,
                        "description": "Email input field",
                    },
                    "id": f"call_rule_{int(time.time()*1000)}",
                }
                content = f"🔄 Rule: Type email {state['account_data'].username}"
            else:
                print(f"🔧 [{ts}] RULE: Clicking Next after email")
                tool_call = {
                    "name": "mobile_ui",
                    "args": {"action": "next_button", "description": "Next button after email"},
                    "id": f"call_rule_{int(time.time()*1000)}",
                }
                content = "🔄 Rule: Click Next after typing email"

        elif current_step == WorkflowStep.PASSWORD:
            # FIXED: PASSWORD should behave like EMAIL - type then next
            if not state.get("password_typed", False) and state.get("account_data"):
                print(f"🔧 [{ts}] RULE: Typing password")
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type",
                        "locator": "android.widget.EditText",
                        "strategy": "class",
                        "text": state["account_data"].password,
                        "description": "Password input field",
                    },
                    "id": f"call_rule_{int(time.time()*1000)}",
                }
                content = "🔄 Rule: Type password"
            else:
                print(f"🔧 [{ts}] RULE: Clicking Next after password")
                tool_call = {
                    "name": "mobile_ui",
                    "args": {"action": "next_button", "description": "Next button after password"},
                    "id": f"call_rule_{int(time.time()*1000)}",
                }
                content = "🔄 Rule: Click Next after typing password"

        elif current_step == WorkflowStep.DETAILS:
            # SIMPLIFIED: Just click Next, skip dropdown hunting unless really needed
            print(f"🔧 [{ts}] RULE: Clicking Next after details (skip dropdown)")
            tool_call = {
                "name": "mobile_ui",
                "args": {"action": "next_button", "description": "Next button after details"},
                "id": f"call_rule_{int(time.time()*1000)}",
            }
            content = "🔄 Rule: Click Next after details"

        elif current_step == WorkflowStep.NAME:
            # 1) First name
            if not state.get("first_name_typed", False) and state.get("account_data"):
                print(f"🔧 [{ts}] RULE: Typing first name: {state['account_data'].first_name}")
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type",
                        "locator": "//*[contains(@text,'First') or contains(@content-desc,'First') or contains(@resource-id,'first') or contains(@hint,'First')]",
                        "strategy": "xpath",
                        "text": state["account_data"].first_name,
                        "description": "First name input",
                    },
                    "id": f"call_rule_{int(time.time()*1000)}",
                }
                content = "🔄 Rule: Type first name"
            # 2) Last name
            elif not state.get("last_name_typed", False) and state.get("account_data"):
                print(f"🔧 [{ts}] RULE: Typing last name: {state['account_data'].last_name}")
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type",
                        "locator": "//*[contains(@text,'Last') or contains(@content-desc,'Last') or contains(@resource-id,'last') or contains(@hint,'Last')]",
                        "strategy": "xpath",
                        "text": state["account_data"].last_name,
                        "description": "Last name input",
                    },
                    "id": f"call_rule_{int(time.time()*1000)}",
                }
                content = "🔄 Rule: Type last name"
            # 3) Next
            else:
                print(f"🔧 [{ts}] RULE: Clicking Next after name")
                tool_call = {
                    "name": "mobile_ui",
                    "args": {"action": "next_button", "description": "Next button after name"},
                    "id": f"call_rule_{int(time.time()*1000)}",
                }
                content = "🔄 Rule: Click Next after name"

        else:
            print(f"🔧 [{ts}] RULE: No rule for {current_step.value}, using fallback")
            self._create_fallback_tool_call(state)
            return

        print(f"🔧 [{ts}] RULE: Tool call created: {tool_call}")
        state["messages"].append(AIMessage(content=content, tool_calls=[tool_call]))

    def _create_emergency_fallback(self, state: OutlookAgentState):
        tool_call = {"name": "ocr", "args": {"action": "capture_and_read"}, "id": f"call_emergency_{int(time.time()*1000)}"}
        state["messages"].append(AIMessage(content="🆘 Emergency fallback: OCR screen assessment", tool_calls=[tool_call]))

    def _analyze_tool_success(self, tool_content: str) -> bool:
        up = tool_content.upper()
        success_keywords = ["SUCCESS", "COMPLETED", "FOUND", "CLICKED", "TYPED"]
        failure_keywords = ["FAILED", "ERROR", "TIMEOUT", "NOT FOUND"]
        return (sum(1 for k in success_keywords if k in up) > sum(1 for k in failure_keywords if k in up)) or (
            "Status: SUCCESS" in tool_content
        )

    def _check_automation_success(self, tool_content: str, state: OutlookAgentState) -> bool:
        low = tool_content.lower()
        return any(
            [
                "inbox" in low,
                ("search" in low and "outlook" in low),
                state["current_step"] == WorkflowStep.VERIFY and "success" in low,
            ]
        )

    def _extract_tool_name_from_content(self, content: str) -> str:
        for tool_name in ["mobile_ui", "gestures", "ocr", "navigator"]:
            if tool_name in content.lower():
                return tool_name
        return "unknown"

    def _extract_duration_from_content(self, content: str) -> int:
        import re

        patterns = [r"in (\d+)ms", r"Duration: (\d+)ms", r"(\d+)ms"]
        for p in patterns:
            m = re.search(p, content)
            if m:
                try:
                    return int(m.group(1))
                except (ValueError, IndexError):
                    continue
        return 0

    def _create_tool_call_record(self, tool_name: str, tool_content: str, success: bool, duration_ms: int) -> Dict[str, Any]:
        action = "unknown"
        if "Action:" in tool_content:
            try:
                part = tool_content.split("Action:")[1].split("|")[0].strip()
                action = part.split()[0] if part else "unknown"
            except Exception:
                pass
        return {
            "tool_name": tool_name,
            "action": action,
            "parameters": {},
            "result": {"content": tool_content[:200] + "..." if len(tool_content) > 200 else tool_content},
            "success": success,
            "duration_ms": max(duration_ms, 0),
            "timestamp": datetime.now(),
        }

    def _update_progress_from_step(self, state: OutlookAgentState):
        step_progress_map = {
            WorkflowStep.INIT: 5,
            WorkflowStep.WELCOME: 15,
            WorkflowStep.EMAIL: 25,
            WorkflowStep.PASSWORD: 35,
            WorkflowStep.DETAILS: 50,
            WorkflowStep.NAME: 65,
            WorkflowStep.CAPTCHA: 75,
            WorkflowStep.AUTH_WAIT: 85,
            WorkflowStep.POST_AUTH: 90,
            WorkflowStep.VERIFY: 95,
            WorkflowStep.CLEANUP: 100,
        }
        current = step_progress_map.get(state["current_step"], state.get("progress_percentage", 0))
        if current > state.get("progress_percentage", 0):
            state["progress_percentage"] = current

    # -------------------------
    # Public API
    # -------------------------
    def run(
        self,
        process_id: str,
        first_name: str,
        last_name: str,
        date_of_birth: str,
        curp_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_ts = datetime.now().strftime("%H:%M:%S")
        print(f"🚀 [{start_ts}] AGENT: Starting agentic workflow...")
        print(f"🆔 [{start_ts}] AGENT: Process: {process_id}")
        print(f"👤 [{start_ts}] AGENT: Target: {first_name} {last_name}")
        try:
            initial_state = create_initial_state(
                process_id=process_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                curp_id=curp_id,
                use_llm=self.use_llm,
            )
            initial_state["max_tool_calls"] = self.max_tool_calls

            print(f"🔄 [{start_ts}] AGENT: Executing agentic workflow...")
            final_state = self.graph.invoke(initial_state)

            end_ts = datetime.now().strftime("%H:%M:%S")
            summary = get_state_summary(final_state)
            success_icon = "🎉" if summary.get("success") else "💥"
            print(f"{success_icon} [{end_ts}] AGENT: {'SUCCESS' if summary.get('success') else 'FAILED'}")
            return summary
        except Exception as e:
            err = f"Workflow execution failed: {e}"
            print(f"❌ [{start_ts}] AGENT: {err}")
            return {
                "process_id": process_id,
                "success": False,
                "error_message": err,
                "progress_percentage": 0,
                "current_step": "error",
                "tool_calls_made": 0,
                "use_llm": self.use_llm,
                "duration_seconds": 0,
            }


def create_agentic_outlook_agent(use_llm: bool = True, provider: str = "groq", max_tool_calls: int = 25) -> AgenticOutlookAgent:
    """Factory function to create agentic Outlook automation agent."""
    return AgenticOutlookAgent(use_llm=use_llm, provider=provider, max_tool_calls=max_tool_calls)
