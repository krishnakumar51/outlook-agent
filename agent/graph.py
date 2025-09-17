#!/usr/bin/env python3
"""
WORKING NAME INPUT FIX - Uses EXACT comp.py name typing method
CRITICAL: Implements the EXACT same name field logic as comp.py
Two methods: Direct element access + UiSelector fallback
"""

from typing import Dict, Any, Literal, Optional
from datetime import datetime
import time

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage

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


class WorkingNameInputAgent:
    """WORKING name input - uses EXACT comp.py methods"""
    
    def __init__(
        self,
        use_llm: bool = True,
        provider: str = "groq",
        max_tool_calls: int = 100,
        recursion_limit: int = 150,
    ):
        self.use_llm = use_llm
        self.provider = provider
        self.max_tool_calls = max_tool_calls
        self.recursion_limit = recursion_limit
        self.policy = create_outlook_policy(use_llm=use_llm, provider=provider)
        self.graph = None
        self.tools = None

        print(f"💯 [AGENT] WORKING NAME INPUT agent initialized")
        self.build_graph()

    def build_graph(self):
        """Build workflow graph"""
        workflow = StateGraph(OutlookAgentState)
        
        workflow.add_node("initialize", self.initialize_node)
        workflow.add_node("policy", self.policy_node)
        workflow.add_node("tools", self.tools_node)
        workflow.add_node("evaluate", self.evaluate_node)
        workflow.add_node("cleanup", self.cleanup_node)
        workflow.add_node("error", self.error_node)
        
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
                "max_calls": "error",
            },
        )
        
        workflow.add_edge("cleanup", END)
        workflow.add_edge("error", END)
        
        self.graph = workflow.compile()
        print("✅ [GRAPH] WORKING NAME INPUT workflow compiled")

    def initialize_node(self, state: OutlookAgentState) -> OutlookAgentState:
        """Initialize with driver setup"""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"🚀 [{ts}] INITIALIZE: Starting...")
        
        try:
            state = set_current_step(state, WorkflowStep.INIT, 5)
            
            state["account_data"] = generate_outlook_account_data(
                state["first_name"], state["last_name"], state["date_of_birth"]
            )
            print(f"✅ [{ts}] Account: {state['account_data'].email}")
            
            from drivers.appium_client import create_outlook_driver
            driver_client = create_outlook_driver()
            if not driver_client:
                raise Exception("Failed to create driver")
                
            state["driver"] = driver_client.get_driver()
            state["screen_size"] = driver_client.get_screen_size()
            
            self.tools = ToolNode(create_tool_list(state["driver"]))
            
            state["steps_completed"]["init"] = True
            state = set_current_step(state, WorkflowStep.WELCOME, 10)
            
            initial_msg = AIMessage(content=self.policy.get_initial_message(state["account_data"].to_dict()))
            state["messages"].append(initial_msg)
            
        except Exception as e:
            err = f"Initialization failed: {e}"
            print(f"❌ [{ts}] {err}")
            state["error_message"] = err
            state["current_step"] = WorkflowStep.ERROR
            
        return state

    def policy_node(self, state: OutlookAgentState) -> OutlookAgentState:
        """Policy node"""
        ts = datetime.now().strftime("%H:%M:%S")
        
        if state["current_step"] == WorkflowStep.ERROR:
            return state
        
        tool_call_count = len(state.get("tool_call_history", []))
        if tool_call_count >= self.max_tool_calls:
            state["error_message"] = "Max tool calls reached"
            state["current_step"] = WorkflowStep.ERROR
            return state
            
        try:
            current_step = state["current_step"]
            print(f"💯 [{ts}] WORKING: Planning for step {current_step.value}")
            self._create_working_tool_call(state)
        except Exception as e:
            print(f"❌ [{ts}] POLICY: {e}")
            self._create_fallback_tool_call(state)
            
        return state

    def tools_node(self, state: OutlookAgentState) -> OutlookAgentState:
        """Tools execution"""
        if not self.tools and state.get("driver"):
            try:
                self.tools = ToolNode(create_tool_list(state["driver"]))
            except Exception as e:
                state["error_message"] = f"Tool init failed: {e}"
                return state
                
        if self.tools:
            try:
                return self.tools.invoke(state)
            except Exception as e:
                state["error_message"] = f"Tool exec failed: {e}"
                return state
        else:
            state["error_message"] = "Tools not available"
            return state

    def _create_working_tool_call(self, state: OutlookAgentState):
        """Create tool calls with WORKING name input logic"""
        current_step = state["current_step"]
        ts = datetime.now().strftime("%H:%M:%S")
        
        # STEP 1: WELCOME
        if current_step == WorkflowStep.WELCOME:
            tool_call = {
                "name": "mobile_ui",
                "args": {
                    "action": "click",
                    "locator": "//*[contains(@text, 'CREATE NEW ACCOUNT')]",
                    "strategy": "xpath",
                    "description": "Click CREATE NEW ACCOUNT"
                },
                "id": f"call_welcome_{int(time.time() * 1000)}"
            }
            content = "💯 WORKING: Click CREATE NEW ACCOUNT"
            
        # STEP 2: EMAIL  
        elif current_step == WorkflowStep.EMAIL:
            if not state.get("email_typed", False):
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type",
                        "locator": "android.widget.EditText",
                        "strategy": "class",
                        "text": state["account_data"].username,
                        "description": "Type email"
                    },
                    "id": f"call_email_type_{int(time.time() * 1000)}"
                }
                content = f"💯 WORKING: Type email {state['account_data'].username}"
            else:
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "next_button",
                        "description": "Next after email"
                    },
                    "id": f"call_email_next_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Click Next after email"
                
        # STEP 3: PASSWORD
        elif current_step == WorkflowStep.PASSWORD:
            if not state.get("password_typed", False):
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type",
                        "locator": "android.widget.EditText",
                        "strategy": "class",
                        "text": state["account_data"].password,
                        "description": "Type password"
                    },
                    "id": f"call_password_type_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Type password"
            else:
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "next_button",
                        "description": "Next after password"
                    },
                    "id": f"call_password_next_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Click Next after password"
                
        # STEP 4: DETAILS
        elif current_step == WorkflowStep.DETAILS:
            acc = state["account_data"].to_dict()
            birth_day = int(acc.get("birth_day", 15))
            birth_month = acc.get("birth_month", "January")
            birth_year = str(acc.get("birth_year", 1995))
            
            all_details_complete = (
                state.get("details_day_value_selected", False) and
                state.get("details_month_value_selected", False) and
                state.get("details_year_typed", False)
            )
            
            if all_details_complete:
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "next_button",
                        "description": "TRANSITION_TO_NAME: Next after all details complete"
                    },
                    "id": f"call_details_transition_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: TRANSITION_TO_NAME → All details complete"
                
            elif not state.get("details_day_selected", False):
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "click",
                        "locator": "//*[contains(@text, 'Day')]",
                        "strategy": "xpath",
                        "description": "Open Day dropdown"
                    },
                    "id": f"call_day_dropdown_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Open Day dropdown"
                
            elif state.get("details_day_selected", False) and not state.get("details_day_value_selected", False):
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "click",
                        "locator": f"//*[@text='{birth_day}']",
                        "strategy": "xpath",
                        "description": f"Select day {birth_day}"
                    },
                    "id": f"call_day_value_{int(time.time() * 1000)}"
                }
                content = f"💯 WORKING: Select day {birth_day}"
                
            elif not state.get("details_month_selected", False):
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "click",
                        "locator": "//*[contains(@text, 'Month')]",
                        "strategy": "xpath",
                        "description": "Open Month dropdown"
                    },
                    "id": f"call_month_dropdown_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Open Month dropdown"
                
            elif state.get("details_month_selected", False) and not state.get("details_month_value_selected", False):
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "click",
                        "locator": f"//*[@text='{birth_month}']",
                        "strategy": "xpath",
                        "description": f"Select month {birth_month}"
                    },
                    "id": f"call_month_value_{int(time.time() * 1000)}"
                }
                content = f"💯 WORKING: Select month {birth_month}"
                
            elif not state.get("details_year_typed", False):
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type",
                        "locator": "android.widget.EditText",
                        "strategy": "class",
                        "text": birth_year,
                        "description": f"Type year {birth_year}"
                    },
                    "id": f"call_year_type_{int(time.time() * 1000)}"
                }
                content = f"💯 WORKING: Type year {birth_year}"
            
            else:
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "next_button",
                        "description": "Next fallback"
                    },
                    "id": f"call_details_fallback_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Next fallback"
                
        # STEP 5: NAME - EXACT COMP.PY METHOD!
        elif current_step == WorkflowStep.NAME:
            first_name = state["account_data"].first_name
            last_name = state["account_data"].last_name
            
            # COMP.PY EXACT SEQUENCE
            if not state.get("name_fields_accessed", False):
                # Step 1: Get all EditText elements first (like comp.py)
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "get_elements",
                        "locator": "android.widget.EditText",
                        "strategy": "class",
                        "description": "Get all EditText elements for names (COMP.PY METHOD)"
                    },
                    "id": f"call_name_elements_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Get EditText elements (COMP.PY METHOD)"
                
            elif not state.get("first_name_typed", False):
                # Step 2: Type first name in first element (edit_texts[0])
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type_element_index",
                        "locator": "android.widget.EditText",
                        "strategy": "class",
                        "element_index": 0,
                        "text": first_name,
                        "description": f"Type first name in element[0] - COMP.PY METHOD"
                    },
                    "id": f"call_firstname_direct_{int(time.time() * 1000)}"
                }
                content = f"💯 WORKING: Type first name '{first_name}' (element[0] - COMP.PY)"
                
            elif not state.get("last_name_typed", False):
                # Step 3: Type last name in second element (edit_texts[1])
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type_element_index",
                        "locator": "android.widget.EditText", 
                        "strategy": "class",
                        "element_index": 1,
                        "text": last_name,
                        "description": f"Type last name in element[1] - COMP.PY METHOD"
                    },
                    "id": f"call_lastname_direct_{int(time.time() * 1000)}"
                }
                content = f"💯 WORKING: Type last name '{last_name}' (element[1] - COMP.PY)"
                
            elif not state.get("name_fallback_tried", False):
                # Step 4: COMP.PY FALLBACK - Use UiSelector instance(1)
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "type",
                        "locator": "new UiSelector().className(\"android.widget.EditText\").instance(1)",
                        "strategy": "uiautomator",
                        "text": last_name,
                        "description": f"COMP.PY FALLBACK: Type last name (instance 1)"
                    },
                    "id": f"call_lastname_fallback_{int(time.time() * 1000)}"
                }
                content = f"💯 WORKING: COMP.PY FALLBACK - Type last name '{last_name}' (instance 1)"
                
            else:
                # Step 5: Both names done, click Next
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "next_button",
                        "description": "Next after names (COMP.PY METHOD SUCCESS)"
                    },
                    "id": f"call_name_next_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Next after names (COMP.PY SUCCESS)"
                
        # STEP 6: CAPTCHA
        elif current_step == WorkflowStep.CAPTCHA:
            if not state.get("captcha_button_found", False):
                tool_call = {
                    "name": "mobile_ui",
                    "args": {
                        "action": "wait_for",
                        "locator": "//android.widget.Button[contains(@text,'Press')]",
                        "strategy": "xpath",
                        "timeout": 10,
                        "description": "Wait for CAPTCHA button"
                    },
                    "id": f"call_captcha_wait_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Wait for CAPTCHA button"
            else:
                tool_call = {
                    "name": "gestures",
                    "args": {
                        "action": "long_press",
                        "locator": "//android.widget.Button[contains(@text,'Press')]",
                        "strategy": "xpath",
                        "duration_ms": 15000,
                        "description": "Long press CAPTCHA 15s"
                    },
                    "id": f"call_captcha_longpress_{int(time.time() * 1000)}"
                }
                content = "💯 WORKING: Long press CAPTCHA 15s"
                
        # STEP 7: AUTH_WAIT 
        elif current_step == WorkflowStep.AUTH_WAIT:
            tool_call = {
                "name": "navigator",
                "args": {
                    "action": "wait_auth",
                    "timeout_seconds": 90,
                    "description": "Wait authentication"
                },
                "id": f"call_auth_wait_{int(time.time() * 1000)}"
            }
            content = "💯 WORKING: Wait authentication"
            
        # STEP 8: POST_AUTH
        elif current_step == WorkflowStep.POST_AUTH:
            tool_call = {
                "name": "navigator",
                "args": {
                    "action": "fast_path",
                    "budget_seconds": 7.0,
                    "description": "Fast path post-auth"
                },
                "id": f"call_post_auth_{int(time.time() * 1000)}"
            }
            content = "💯 WORKING: Fast path post-auth"
            
        # STEP 9: VERIFY
        elif current_step == WorkflowStep.VERIFY:
            tool_call = {
                "name": "mobile_ui",
                "args": {
                    "action": "wait_for",
                    "locator": "//*[@text='Search']",
                    "strategy": "xpath",
                    "timeout": 10,
                    "description": "Wait for inbox"
                },
                "id": f"call_verify_{int(time.time() * 1000)}"
            }
            content = "💯 WORKING: Wait for inbox"
            
        else:
            self._create_fallback_tool_call(state)
            return
            
        print(f"💯 [{ts}] WORKING: {tool_call['name']}.{tool_call['args']['action']}")
        state["messages"].append(AIMessage(content=content, tool_calls=[tool_call]))

    def _create_fallback_tool_call(self, state: OutlookAgentState):
        """Fallback OCR"""
        tool_call = {
            "name": "ocr",
            "args": {"action": "capture_and_read"},
            "id": f"call_fallback_{int(time.time() * 1000)}"
        }
        state["messages"].append(AIMessage(content="💯 WORKING: OCR fallback", tool_calls=[tool_call]))

    def evaluate_node(self, state: OutlookAgentState) -> OutlookAgentState:
        """WORKING evaluation logic"""
        ts = datetime.now().strftime("%H:%M:%S")
        
        if state["current_step"] == WorkflowStep.ERROR:
            return state
            
        print(f"⚖️  [{ts}] EVALUATE: Analyzing...")
        
        try:
            last_message = state["messages"][-1] if state["messages"] else None
            if isinstance(last_message, ToolMessage):
                tool_content = last_message.content or ""
                success = self._analyze_tool_success(tool_content)
                duration_ms = self._extract_duration_from_content(tool_content)
                
                print(f"🔍 [{ts}] Success: {success} | Duration: {duration_ms}ms")
                
                # Record tool call
                tool_name = self._extract_tool_name_from_content(tool_content)
                state = add_tool_call_record(
                    state, tool_name, "working_action", {}, {"content": tool_content[:200]}, duration_ms, success
                )
                
                # Check success
                if self._check_automation_success(tool_content, state):
                    print(f"🎉 [{ts}] SUCCESS - INBOX REACHED!")
                    state = set_success(state)
                    return state
                
                # WORKING TRANSITIONS
                current_step = state["current_step"]
                content_l = tool_content.lower()
                
                if success:
                    state["consecutive_errors"] = 0
                    
                    # WELCOME → EMAIL
                    if current_step == WorkflowStep.WELCOME and ("clicked" in content_l or "create" in content_l):
                        state = set_current_step(state, WorkflowStep.EMAIL, 15)
                        print("📍 WORKING: WELCOME → EMAIL")
                        
                    # EMAIL transitions
                    elif current_step == WorkflowStep.EMAIL:
                        if "typed" in content_l and "email" in content_l:
                            state["email_typed"] = True
                            print("📍 WORKING: Email typed")
                        elif state.get("email_typed") and "next" in content_l:
                            state = set_current_step(state, WorkflowStep.PASSWORD, 25)
                            print("📍 WORKING: EMAIL → PASSWORD")
                            
                    # PASSWORD transitions
                    elif current_step == WorkflowStep.PASSWORD:
                        if "typed" in content_l and "password" in content_l:
                            state["password_typed"] = True
                            print("📍 WORKING: Password typed")
                        elif state.get("password_typed") and "next" in content_l:
                            state = set_current_step(state, WorkflowStep.DETAILS, 35)
                            print("📍 WORKING: PASSWORD → DETAILS")
                            
                    # DETAILS transitions
                    elif current_step == WorkflowStep.DETAILS:
                        if ("open day dropdown" in content_l or "day dropdown" in content_l) and not state.get("details_day_selected"):
                            state["details_day_selected"] = True
                            print("📍 WORKING: Day dropdown opened")
                        elif ("select day" in content_l or "day" in content_l) and "select" in content_l:
                            state["details_day_value_selected"] = True
                            print("📍 WORKING: Day value selected")
                        elif ("open month dropdown" in content_l or "month dropdown" in content_l) and not state.get("details_month_selected"):
                            state["details_month_selected"] = True
                            print("📍 WORKING: Month dropdown opened")
                        elif ("select month" in content_l or "month" in content_l) and "select" in content_l:
                            state["details_month_value_selected"] = True
                            print("📍 WORKING: Month value selected")
                        elif ("type year" in content_l or "year" in content_l) and "typed" in content_l:
                            state["details_year_typed"] = True
                            print("📍 WORKING: Year typed")
                        elif "transition_to_name" in content_l and "all details complete" in content_l:
                            state = set_current_step(state, WorkflowStep.NAME, 50)
                            print("📍 WORKING: DETAILS → NAME (TRANSITION DETECTED!)")
                            
                    # NAME transitions - COMP.PY METHOD DETECTION
                    elif current_step == WorkflowStep.NAME:
                        if ("get edittext elements" in content_l or "comp.py method" in content_l) and "elements" in content_l:
                            state["name_fields_accessed"] = True
                            print("📍 WORKING: EditText elements accessed (COMP.PY METHOD)")
                        elif ("first name" in content_l and "element[0]" in content_l) or ("first name" in content_l and "comp.py" in content_l):
                            state["first_name_typed"] = True
                            print("📍 WORKING: First name typed (COMP.PY METHOD)")
                        elif ("last name" in content_l and "element[1]" in content_l) or ("last name" in content_l and "comp.py" in content_l):
                            state["last_name_typed"] = True
                            print("📍 WORKING: Last name typed (COMP.PY METHOD)")
                        elif ("comp.py fallback" in content_l and "instance 1" in content_l):
                            state["name_fallback_tried"] = True
                            state["last_name_typed"] = True  # Mark as typed via fallback
                            print("📍 WORKING: Last name typed (COMP.PY FALLBACK)")
                        elif ("next after names" in content_l and "comp.py success" in content_l):
                            state = set_current_step(state, WorkflowStep.CAPTCHA, 65)
                            print("📍 WORKING: NAME → CAPTCHA (COMP.PY SUCCESS!)")
                            
                    # CAPTCHA transitions  
                    elif current_step == WorkflowStep.CAPTCHA:
                        if "wait" in content_l and "captcha" in content_l:
                            state["captcha_button_found"] = True
                            print("📍 WORKING: CAPTCHA button found")
                        elif ("long press" in content_l or "15s" in content_l) and "captcha" in content_l:
                            state["captcha_pressed"] = True
                            state = set_current_step(state, WorkflowStep.AUTH_WAIT, 75)
                            print("📍 WORKING: CAPTCHA → AUTH_WAIT")
                        
                    # AUTH_WAIT → POST_AUTH
                    elif current_step == WorkflowStep.AUTH_WAIT and "auth" in content_l:
                        state = set_current_step(state, WorkflowStep.POST_AUTH, 80)
                        print("📍 WORKING: AUTH_WAIT → POST_AUTH")
                        
                    # POST_AUTH → VERIFY
                    elif current_step == WorkflowStep.POST_AUTH and "fast path" in content_l:
                        state = set_current_step(state, WorkflowStep.VERIFY, 90)
                        print("📍 WORKING: POST_AUTH → VERIFY")
                        
                    # VERIFY → SUCCESS
                    elif current_step == WorkflowStep.VERIFY and "inbox" in content_l:
                        state = set_current_step(state, WorkflowStep.CLEANUP, 100)
                        print("📍 WORKING: VERIFY → CLEANUP")
                        
                else:
                    state["consecutive_errors"] = state.get("consecutive_errors", 0) + 1
                    print(f"⚠️ Tool failed, errors: {state['consecutive_errors']}")
                    
        except Exception as e:
            print(f"❌ [{ts}] Evaluation error: {e}")
            state["error_message"] = str(e)
            
        return state

    def cleanup_node(self, state: OutlookAgentState) -> OutlookAgentState:
        """Cleanup"""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"🧹 [{ts}] CLEANUP: Finalizing...")
        
        try:
            if state.get("driver"):
                try:
                    state["driver"].quit()
                except Exception:
                    pass
                    
            if not state.get("end_time"):
                state["end_time"] = time.time()
                
            if state.get("success") and state.get("account_data"):
                final_content = f"🎉 WORKING NAME INPUT SUCCESS!\n📧 {state['account_data'].email}\n🔒 {state['account_data'].password}"
            else:
                final_content = f"❌ Failed: {state.get('error_message', 'Unknown')}"
                
            state["messages"].append(AIMessage(content=final_content))
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            
        return state

    def error_node(self, state: OutlookAgentState) -> OutlookAgentState:
        """Error handling"""
        print("❌ ERROR: Terminal error")
        
        try:
            if state.get("driver"):
                try:
                    state["driver"].quit()
                except Exception:
                    pass
                    
            state["success"] = False
            if not state.get("end_time"):
                state["end_time"] = time.time()
                
            err = state.get("error_message", "Unknown")
            state["messages"].append(AIMessage(content=f"❌ WORKING NAME INPUT failed: {err}"))
            
        except Exception:
            pass
            
        return state

    def route_after_evaluation(self, state: OutlookAgentState) -> Literal["continue", "success", "error", "max_calls"]:
        """Route decisions"""
        if state.get("success", False):
            return "success"
        if state.get("current_step") == WorkflowStep.ERROR:
            return "error"
        if len(state.get("tool_call_history", [])) >= self.max_tool_calls:
            return "max_calls"
        if state.get("consecutive_errors", 0) >= 5:
            return "error"
        return "continue"

    # Helper methods
    def _extract_tool_name_from_content(self, content: str) -> str:
        for tool_name in ["mobile_ui", "gestures", "navigator", "ocr"]:
            if tool_name in content.lower():
                return tool_name
        return "mobile_ui"

    def _extract_duration_from_content(self, content: str) -> int:
        import re
        patterns = [r"(\d+)ms", r"Duration: (\d+)ms"]
        for p in patterns:
            m = re.search(p, content)
            if m:
                try:
                    return int(m.group(1))
                except:
                    continue
        return 0

    def _analyze_tool_success(self, tool_content: str) -> bool:
        up = tool_content.upper()
        success_keywords = ["SUCCESS", "COMPLETED", "FOUND", "CLICKED", "TYPED", "EXISTS", "PRESSED"]
        failure_keywords = ["FAILED", "ERROR", "TIMEOUT", "NOT FOUND", "EXCEPTION"]
        return sum(1 for k in success_keywords if k in up) > sum(1 for k in failure_keywords if k in up)

    def _check_automation_success(self, tool_content: str, state: OutlookAgentState) -> bool:
        low = tool_content.lower()
        return ("search" in low and "inbox" in low) or "search" in low

    def run(self, process_id: str, first_name: str, last_name: str, date_of_birth: str, curp_id: Optional[str] = None) -> Dict[str, Any]:
        """Run WORKING NAME INPUT automation"""
        start_ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{start_ts}] 💯 WORKING NAME INPUT: Starting for {first_name} {last_name}")
        
        try:
            initial_state = create_initial_state(
                process_id=process_id,
                first_name=first_name, 
                last_name=last_name,
                date_of_birth=date_of_birth,
                curp_id=curp_id,
                use_llm=self.use_llm
            )
            
            initial_state["max_tool_calls"] = self.max_tool_calls
            
            if initial_state.get("current_step") == WorkflowStep.ERROR:
                print(f"[{start_ts}] ❌ Driver failed")
                return get_state_summary(initial_state)
            
            final_state = self.graph.invoke(
                initial_state, 
                config={"recursion_limit": self.recursion_limit}
            )
            
            success = final_state.get('success', False)
            print(f"[{start_ts}] 🎉 WORKING NAME INPUT: {'SUCCESS' if success else 'FAILED'}")
            
            if success and final_state.get("account_data"):
                print(f"[{start_ts}] 📧 {final_state['account_data'].email}")
                print(f"[{start_ts}] 🔒 {final_state['account_data'].password}")
                
            return get_state_summary(final_state)
            
        except Exception as e:
            error_msg = f"WORKING NAME INPUT execution failed: {e}"
            print(f"[{start_ts}] ❌ {error_msg}")
            return {
                "process_id": process_id,
                "success": False,
                "error_message": error_msg,
                "progress_percentage": 0,
                "current_step": "error",
                "tool_calls_made": 0,
                "duration_seconds": 0,
                "use_llm": self.use_llm
            }


# CRITICAL: Function name for import
def create_agentic_outlook_agent(
    use_llm: bool = True, 
    provider: str = "groq", 
    max_tool_calls: int = 100,
    recursion_limit: int = 150
) -> WorkingNameInputAgent:
    """Create WORKING NAME INPUT agent"""
    return WorkingNameInputAgent(
        use_llm=use_llm, 
        provider=provider, 
        max_tool_calls=max_tool_calls, 
        recursion_limit=recursion_limit
    )