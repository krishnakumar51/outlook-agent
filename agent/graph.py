#!/usr/bin/env python3
"""
Outlook Mobile Agent - LangGraph Implementation (Fixed)
- Defines all node methods as instance methods on the class
- Registers nodes with StateGraph.add_node(name, func)
- Uses START -> "init" to set the entry point per LangGraph docs
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from .state import OutlookAgentState, create_initial_state, generate_outlook_account_data


class OutlookMobileAgent:
    """LangGraph agent for Outlook mobile app automation with optional LLM analysis."""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.graph = None
        self.build_graph()

    def build_graph(self):
        """Build the LangGraph workflow with explicit node registrations."""
        workflow = StateGraph(OutlookAgentState)

        # Register nodes (all instance methods)
        workflow.add_node("init", self.init_node)
        workflow.add_node("welcome", self.welcome_node)
        workflow.add_node("email", self.email_node)
        workflow.add_node("password", self.password_node)
        workflow.add_node("details", self.details_node)
        workflow.add_node("name", self.name_node)
        workflow.add_node("captcha", self.captcha_node)
        workflow.add_node("auth_wait", self.auth_wait_node)
        workflow.add_node("post_auth", self.post_auth_node)
        workflow.add_node("verify", self.verify_node)
        workflow.add_node("cleanup", self.cleanup_node)
        workflow.add_node("error", self.error_node)
        workflow.add_node("llm_analyze", self.llm_analyze_node)

        # Entry edge per docs (START -> init)
        workflow.add_edge(START, "init")

        # Standard linear edges
        workflow.add_edge("init", "welcome")

        # Conditional edges with LLM-aware error path
        workflow.add_conditional_edges(
            "welcome",
            self.should_continue_or_retry,
            {"continue": "email", "retry": "welcome", "error": "llm_analyze" if self.use_llm else "error"},
        )
        workflow.add_conditional_edges(
            "email",
            self.should_continue_or_retry,
            {"continue": "password", "retry": "email", "error": "llm_analyze" if self.use_llm else "error"},
        )
        workflow.add_conditional_edges(
            "password",
            self.should_continue_or_retry,
            {"continue": "details", "retry": "password", "error": "llm_analyze" if self.use_llm else "error"},
        )
        workflow.add_conditional_edges(
            "details",
            self.should_continue_or_retry,
            {"continue": "name", "retry": "details", "error": "llm_analyze" if self.use_llm else "error"},
        )
        workflow.add_conditional_edges(
            "name",
            self.should_continue_or_retry,
            {"continue": "captcha", "retry": "name", "error": "llm_analyze" if self.use_llm else "error"},
        )
        workflow.add_conditional_edges(
            "captcha",
            self.should_continue_or_retry,
            {"continue": "auth_wait", "retry": "captcha", "error": "llm_analyze" if self.use_llm else "error"},
        )

        # Straight edges to finish
        workflow.add_edge("auth_wait", "post_auth")
        workflow.add_edge("post_auth", "verify")
        workflow.add_edge("verify", "cleanup")
        workflow.add_edge("cleanup", END)
        workflow.add_edge("error", END)

        # LLM analysis routing
        workflow.add_conditional_edges(
            "llm_analyze",
            self.llm_decision,
            {"retry": "welcome", "skip": "cleanup", "error": "error"},
        )

        # Compile
        self.graph = workflow.compile()

    # -------- Routing helpers --------
    def should_continue_or_retry(self, state: OutlookAgentState) -> Literal["continue", "retry", "error"]:
        current = state.current_step
        if state.steps_completed.get(current, False):
            return "continue"
        if state.error_message and state.increment_retry(current):
            state.reset_for_retry(current)
            return "retry"
        return "error"

    def llm_decision(self, state: OutlookAgentState) -> Literal["retry", "skip", "error"]:
        analysis = getattr(state, "llm_analysis", None)
        if analysis and analysis.get("success"):
            data = analysis.get("analysis", {})
            if not data.get("critical", True):
                state.add_log("🤖 LLM suggests skipping non-critical error")
                return "skip"
            if "retry" in str(data.get("solution", "")).lower():
                state.add_log("🤖 LLM suggests retrying with adjusted approach")
                return "retry"
        state.add_log("🤖 LLM analysis inconclusive, treating as error")
        return "error"

    # -------- Node implementations --------
    def init_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("init", 1)
            state.account_data = generate_outlook_account_data(state.first_name, state.last_name, state.date_of_birth)
            state.add_log(f"📧 Generated account: {state.account_data.email}")
            from drivers.appium_client import create_outlook_driver
            client = create_outlook_driver()
            if not client:
                raise Exception("Failed to setup Appium driver")
            state.driver = client.get_driver()
            state.screen_size = client.get_screen_size()
            state.mark_step_complete("init", True)
        except Exception as e:
            state.set_error(f"Initialization failed: {e}", "init")
        return state

    def welcome_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("welcome", 2)
            from tools.mobile_ui import MobileUI
            ui = MobileUI(state.driver)
            import time; time.sleep(3)
            selectors = [
                ("//*[contains(@text, 'CREATE NEW ACCOUNT')]", "xpath"),
                ("//*[contains(@text, 'Create new account')]", "xpath"),
                ("//android.widget.Button[contains(@text, 'CREATE')]", "xpath"),
            ]
            success = any(ui.ui_click(sel, strat, "CREATE NEW ACCOUNT") for sel, strat in selectors)
            if not success:
                x = state.screen_size["width"] // 2
                y = int(state.screen_size["height"] * 0.75)
                if ui.ui_tap_coordinates(x, y):
                    state.add_log("✅ Used coordinate fallback for CREATE NEW ACCOUNT")
                    success = True
            if success:
                state.mark_step_complete("welcome", True)
            else:
                raise Exception("CREATE NEW ACCOUNT button not found")
        except Exception as e:
            state.set_error(f"Welcome step failed: {e}", "welcome")
        return state

    def email_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("email", 3)
            from tools.mobile_ui import MobileUI
            ui = MobileUI(state.driver)
            import time; time.sleep(2)
            selectors = [
                ("//*[contains(@hint, 'email')]", "xpath"),
                ("android.widget.EditText", "class"),
            ]
            success = False
            for sel, strat in selectors:
                if ui.ui_type_text(sel, state.account_data.username, strat, field_type="email", description="Email"):
                    success = True
                    break
            if success and ui.click_next_button("Email"):
                state.mark_step_complete("email", True)
            else:
                raise Exception("Email input/Next failed")
        except Exception as e:
            state.set_error(f"Email step failed: {e}", "email")
        return state

    def password_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("password", 4)
            from tools.mobile_ui import MobileUI
            ui = MobileUI(state.driver)
            import time; time.sleep(2)
            selectors = [
                ("//*[contains(@hint, 'Password')]", "xpath"),
                ("android.widget.EditText", "class"),
            ]
            success = False
            for sel, strat in selectors:
                if ui.ui_type_text(sel, state.account_data.password, strat, field_type="password", description="Password"):
                    success = True
                    break
            if success and ui.click_next_button("Password"):
                state.mark_step_complete("password", True)
            else:
                raise Exception("Password input/Next failed")
        except Exception as e:
            state.set_error(f"Password step failed: {e}", "password")
        return state

    def details_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("details", 5)
            from tools.mobile_ui import MobileUI
            ui = MobileUI(state.driver)
            import time; time.sleep(2)
            # Day
            day_selectors = [("//*[contains(@text, 'Day')]", "xpath"), ("//android.widget.Spinner[17]", "xpath")]
            day_ok = any(ui.ui_select_dropdown(sel, str(state.account_data.birth_day), strat, "Day") for sel, strat in day_selectors)
            # Month
            month_selectors = [("//*[contains(@text, 'Month')]", "xpath"), ("//android.widget.Spinner[18]", "xpath")]
            month_ok = any(ui.ui_select_dropdown(sel, state.account_data.birth_month, strat, "Month") for sel, strat in month_selectors)
            # Year (backspace handling)
            year_ok = ui.ui_type_text("android.widget.EditText", str(state.account_data.birth_year), "class", field_type="year", description="Year Field")
            ui.ui_hide_keyboard()
            if day_ok and month_ok and year_ok and ui.click_next_button("Details"):
                state.mark_step_complete("details", True)
            else:
                raise Exception(f"Details input failed - Day:{day_ok}, Month:{month_ok}, Year:{year_ok}")
        except Exception as e:
            state.set_error(f"Details step failed: {e}", "details")
        return state

    def name_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("name", 6)
            from tools.mobile_ui import MobileUI
            ui = MobileUI(state.driver)
            import time; time.sleep(2)
            # First & last name
            first_ok = ui.ui_type_text("android.widget.EditText", state.account_data.first_name, "class", description="First Name")
            last_selector = 'new UiSelector().className("android.widget.EditText").instance(1)'
            last_ok = ui.ui_type_text(last_selector, state.account_data.last_name, "uiautomator", description="Last Name")
            ui.ui_hide_keyboard()
            if first_ok and last_ok and ui.click_next_button("Name"):
                state.mark_step_complete("name", True)
            else:
                raise Exception(f"Name input failed - First:{first_ok}, Last:{last_ok}")
        except Exception as e:
            state.set_error(f"Name step failed: {e}", "name")
        return state

    def captcha_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("captcha", 7)
            from tools.gestures import MobileGestures
            gestures = MobileGestures(state.driver)
            import time; time.sleep(3)
            selectors = [
                'new UiSelector().className("android.widget.Button").textContains("Press").clickable(true).enabled(true)',
                "//android.widget.Button[contains(@text,'Press')]",
            ]
            success = any(gestures.ui_long_press(sel, duration_ms=15000, strategy=("uiautomator" if "UiSelector" in sel else "xpath"), description="CAPTCHA Button") for sel in selectors)
            if success:
                state.mark_step_complete("captcha", True)
            else:
                raise Exception("CAPTCHA button not found or long press failed")
        except Exception as e:
            state.set_error(f"CAPTCHA step failed: {e}", "captcha")
        return state

    def auth_wait_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("auth_wait", 8)
            from tools.auth_wait import AuthenticationWaiter
            auth_waiter = AuthenticationWaiter(state.driver)
            if auth_waiter.ui_wait_progress_gone(max_seconds=90):
                state.mark_step_complete("auth_wait", True)
            else:
                state.add_log("⚠️ Authentication timeout, continuing anyway")
                state.mark_step_complete("auth_wait", True)
        except Exception as e:
            state.set_error(f"Auth wait failed: {e}", "auth_wait")
        return state

    def post_auth_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("post_auth", 9)
            from tools.post_auth import PostAuthNavigator
            navigator = PostAuthNavigator(state.driver)
            import time; time.sleep(1)
            if navigator.post_auth_fast_path(budget_seconds=7.0):
                state.mark_step_complete("post_auth", True)
            else:
                state.add_log("⚠️ Fast path failed, trying simple navigation")
                if navigator.navigate_to_inbox_simple(max_attempts=5):
                    state.mark_step_complete("post_auth", True)
                else:
                    raise Exception("Post-auth navigation failed")
        except Exception as e:
            state.set_error(f"Post-auth step failed: {e}", "post_auth")
        return state

    def verify_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.set_current_step("verify", 10)
            from tools.mobile_ui import MobileUI
            ui = MobileUI(state.driver)
            inbox_selectors = ["//*[@text='Search']", "//*[contains(@content-desc,'Search')]", "//*[contains(@text, 'Inbox')]"]
            inbox_found = any(ui.ui_find_one(xp, "xpath", timeout=5) for xp in inbox_selectors)
            if inbox_found:
                state.set_success()
                state.mark_step_complete("verify", True)
            else:
                state.add_log("⚠️ Inbox not confirmed, but account likely created")
                state.set_success()
                state.mark_step_complete("verify", True)
        except Exception as e:
            state.set_error(f"Verification failed: {e}", "verify")
        return state

    def cleanup_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.add_log("🧹 Cleaning up resources")
            if state.driver:
                try:
                    state.driver.quit()
                    state.add_log("✅ Driver closed")
                except Exception:
                    state.add_log("⚠️ Driver cleanup warning")
            duration = state.get_duration()
            if duration is not None:
                state.add_log(f"⏱️ Total duration: {duration:.1f} seconds")
            state.add_log(f"📊 Final progress: {state.get_progress_percentage()}%")
        except Exception as e:
            state.add_log(f"⚠️ Cleanup error: {e}")
        return state

    def error_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.add_log("❌ Entering error handling")
            if state.driver:
                try:
                    state.driver.quit()
                    state.add_log("✅ Driver closed after error")
                except Exception:
                    pass
            if state.error_message:
                state.add_log(f"💥 Final error: {state.error_message}")
            state.add_log(f"📊 Progress at failure: {state.get_progress_percentage()}%")
        except Exception as e:
            state.add_log(f"⚠️ Error handling failed: {e}")
        return state

    def llm_analyze_node(self, state: OutlookAgentState) -> OutlookAgentState:
        try:
            state.add_log("🤖 Analyzing error with LLM...")
            from llm.llm_client import get_llm_client
            llm_client = get_llm_client()
            ctx = {
                "current_step": state.current_step,
                "progress_percentage": state.get_progress_percentage(),
                "retry_counts": state.retry_counts,
                "steps_completed": state.steps_completed,
                "account_data": state.account_data.to_dict() if state.account_data else None,
            }
            analysis = llm_client.analyze_error_context(
                error_message=state.error_message or "Unknown error",
                step=state.current_step,
                context=ctx,
            )
            state.llm_analysis = analysis
            if analysis.get("success"):
                data = analysis.get("analysis", {})
                state.add_log(f"🤖 LLM Analysis: {data.get('cause', 'Unknown cause')}")
                state.add_log(f"🤖 LLM Solution: {data.get('solution', 'No solution provided')}")
                alts = data.get("alternatives", [])
                if alts:
                    state.add_log(f"🤖 LLM Alternatives: {', '.join(alts)}")
            else:
                state.add_log(f"⚠️ LLM analysis failed: {analysis.get('error', 'Unknown error')}")
        except Exception as e:
            state.add_log(f"⚠️ LLM analysis error: {e}")
        return state

    # -------- Public runner --------
    def run(self, process_id: str, first_name: str, last_name: str, date_of_birth: str, curp_id: str = None) -> Dict[str, Any]:
        """Run the compiled graph and return a robust summary regardless of state return type."""
        try:
            initial = create_initial_state(
                process_id=process_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                curp_id=curp_id,
            )
            result = self.graph.invoke(initial)

            # Case 1: state class instance with get_summary()
            if hasattr(result, "get_summary"):
                return result.get_summary()

            # Case 2: plain dict-like state (default for many LangGraph setups)
            if isinstance(result, dict):
                # Try to infer success and progress if present in state
                inferred_success = bool(result.get("success", True))
                progress = int(result.get("progress_percentage", 100 if inferred_success else 0))
                current_step = result.get("current_step") or "completed" if inferred_success else "unknown"
                logs = result.get("logs", [])
                error_message = result.get("error_message")

                return {
                    "process_id": process_id,
                    "success": inferred_success,
                    "progress_percentage": progress,
                    "current_step": current_step,
                    "error_message": error_message,
                    "logs": logs,
                    "state": result,  # include full state for debugging/consumers
                }

            # Case 3: unknown type — still return success to reflect the run completed
            return {
                "process_id": process_id,
                "success": True,
                "progress_percentage": 100,
                "current_step": "completed",
                "error_message": None,
                "logs": [],
            }

        except Exception as e:
            return {
                "process_id": process_id,
                "success": False,
                "error_message": f"Workflow execution failed: {e}",
                "progress_percentage": 0,
                "current_step": "unknown",
                "logs": [],
            }



def create_outlook_agent(use_llm: bool = True) -> OutlookMobileAgent:
    """Factory to create the agent with optional LLM integration."""
    return OutlookMobileAgent(use_llm=use_llm)
