#!/usr/bin/env python3
"""
Mobile Outlook Agent - Agentic Version Entry Point
Enhanced mobile automation with LLM-driven tool orchestration, OCR capabilities, and comprehensive logging
"""

import argparse
import sys
import os
import uuid
import traceback
from typing import Dict, Any
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print application banner with agentic features."""
    print("📱 Mobile Outlook Agent - Agentic Version with OCR & LLM")
    print("=" * 65)
    print("🤖 Features: LLM Decision Making | OCR Screen Reading | Tool Orchestration")
    print("🔧 Tools: mobile_ui | gestures | ocr | navigator")
    print("🧠 LLM Providers: Groq | Gemini | OpenAI | Anthropic")
    print("👁️ OCR Engines: Tesseract | PaddleOCR | EasyOCR")

def print_mode_info(args):
    """Print detailed mode information."""
    timestamp = datetime.now().strftime("%H:%M:%S")

    if args.mode == "manual":
        print(f"\n✋ Manual Mode - Single Account Creation")
        print(f"🚀 Starting agentic automation at {timestamp}...")
        print(f"👤 Target User: {args.first_name} {args.last_name}")
        print(f"📅 Date of Birth: {args.date_of_birth}")
        if args.curp_id:
            print(f"🆔 CURP ID: {args.curp_id}")
        llm_status = "🤖 Enabled" if not args.no_llm else "🔄 Disabled (Rule-based)"
        print(f"🧠 LLM Integration: {llm_status}")
        print(f"🏗️ LLM Provider: {args.llm_provider.upper()}")
        print(f"👁️ OCR Engine: {args.ocr_engine}")
        print("=" * 65)

    elif args.mode == "demo":
        print(f"\n🎬 Demo Mode - Showcase Automation")
        print(f"🚀 Running demo automation at {timestamp}...")
        print(f"👤 Demo User: Demo User (1995-01-15)")
        llm_status = "🤖 Enabled" if not args.no_llm else "🔄 Disabled"
        print(f"🧠 LLM Integration: {llm_status}")
        print(f"🏗️ LLM Provider: {args.llm_provider.upper()}")
        print("=" * 65)

    elif args.mode == "test-llm":
        print(f"\n🧪 LLM Testing Mode")
        print(f"🔍 Testing all available LLM providers at {timestamp}...")
        print("🎯 This will verify API connectivity and response quality")
        print("=" * 65)

    elif args.mode == "server":
        print(f"\n🌐 API Server Mode")  
        print(f"🚀 Starting FastAPI server at {timestamp}...")
        print(f"📊 Features: Real-time monitoring | Tool tracing | Export capabilities")
        print("=" * 65)

    elif args.mode == "test":
        print(f"\n🔧 System Testing Mode")
        print(f"🧪 Running comprehensive system tests at {timestamp}...")
        print("=" * 65)

def run_manual_automation(args) -> Dict[str, Any]:
    """Run manual single-user automation with full agentic capabilities."""

    print("🏗️ [MANUAL] Initializing agentic automation system...")

    try:
        # Import agentic agent
        from agent.graph import create_agentic_outlook_agent

        # Create agent with LLM configuration
        use_llm = not args.no_llm
        agent = create_agentic_outlook_agent(
            use_llm=use_llm,
            provider=args.llm_provider
        )

        print(f"✅ [MANUAL] Agentic agent created successfully")
        print(f"🤖 [MANUAL] LLM Integration: {'Enabled' if use_llm else 'Disabled'}")
        print(f"🏗️ [MANUAL] Provider: {args.llm_provider}")

        # Generate process ID
        process_id = f"manual_{uuid.uuid4().hex[:8]}"
        print(f"🔍 [MANUAL] Process ID: {process_id}")

        # Log start time
        start_time = datetime.now()
        print(f"⏰ [MANUAL] Start time: {start_time.strftime('%H:%M:%S')}")

        print("\n🚀 [MANUAL] Beginning agentic automation workflow...")
        print("📊 [MANUAL] Tool calls will be logged with detailed banners")
        print("👁️ [MANUAL] OCR will be used for intelligent screen understanding")
        print("🤖 [MANUAL] LLM will make strategic decisions about next actions")
        print("-" * 65)

        # Execute automation
        result = agent.run(
            process_id=process_id,
            first_name=args.first_name,
            last_name=args.last_name,
            date_of_birth=args.date_of_birth,
            curp_id=args.curp_id
        )

        # Log completion
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n⏰ [MANUAL] End time: {end_time.strftime('%H:%M:%S')}")
        print(f"⏱️ [MANUAL] Total duration: {duration:.1f} seconds")

        return result

    except ImportError as e:
        error_msg = f"Failed to import required modules: {e}"
        print(f"❌ [MANUAL] {error_msg}")
        print("💡 [MANUAL] Make sure all dependencies are installed: pip install -r requirements.txt")
        return create_error_result(process_id, error_msg)

    except Exception as e:
        error_msg = f"Automation system error: {e}"
        print(f"❌ [MANUAL] {error_msg}")
        print("🔍 [MANUAL] Full error details:")
        traceback.print_exc()
        return create_error_result(process_id, error_msg)

def run_demo_automation(args) -> Dict[str, Any]:
    """Run demo automation with predefined user."""

    print("🎬 [DEMO] Setting up demo automation...")

    # Set demo user data
    demo_args = argparse.Namespace(**vars(args))
    demo_args.first_name = "Demo"
    demo_args.last_name = "User"  
    demo_args.date_of_birth = "1995-01-15"
    demo_args.curp_id = None

    print("👤 [DEMO] Demo user configured: Demo User (1995-01-15)")

    # Run automation with demo data
    return run_manual_automation(demo_args)

def run_llm_tests(args) -> Dict[str, Any]:
    """Test all available LLM providers."""

    print("🧪 [TEST] Initializing LLM provider testing...")

    try:
        from llm.llm_client import test_llm_providers

        print("🔍 [TEST] Testing LLM connectivity and response quality...")
        results = test_llm_providers()

        print("\n📊 [TEST] LLM Test Results:")
        print("=" * 50)

        working_providers = []
        failed_providers = []

        for provider, result in results.items():
            success = result.get("success", False)
            status_icon = "✅" if success else "❌"

            if success:
                working_providers.append(provider)
                response_preview = result.get("response", "")[:80] + "..." if len(result.get("response", "")) > 80 else result.get("response", "")
                model_info = f"({result.get('model', 'unknown')})" if result.get('model') else ""
                print(f"{status_icon} {provider.upper():12} {model_info}")
                print(f"    Response: {response_preview}")

            else:
                failed_providers.append(provider)
                error_info = result.get("error", "Unknown error")[:100]
                print(f"{status_icon} {provider.upper():12} - ERROR")
                print(f"    Error: {error_info}")

            print()

        print("=" * 50)
        print(f"✅ Working Providers: {', '.join(working_providers) if working_providers else 'None'}")
        print(f"❌ Failed Providers: {', '.join(failed_providers) if failed_providers else 'None'}")

        if working_providers:
            print(f"\n💡 [TEST] Recommended: Use '{working_providers[0]}' as primary provider")
            print(f"🔧 [TEST] Set environment variable: export GROQ_API_KEY=your_key")
        else:
            print(f"\n⚠️ [TEST] No LLM providers are working - automation will use rule-based fallback")

        return {
            "test_type": "llm_providers",
            "total_tested": len(results),
            "working_count": len(working_providers),
            "failed_count": len(failed_providers),
            "working_providers": working_providers,
            "failed_providers": failed_providers,
            "detailed_results": results
        }

    except Exception as e:
        error_msg = f"LLM testing failed: {e}"
        print(f"❌ [TEST] {error_msg}")
        traceback.print_exc()
        return {"error": error_msg, "test_type": "llm_providers"}

def run_system_tests(args) -> Dict[str, Any]:
    """Run comprehensive system tests."""

    print("🔧 [TEST] Running comprehensive system tests...")

    try:
        from test_system import main as run_system_tests_main

        print("🧪 [TEST] Executing test suite...")
        test_result = run_system_tests_main()

        return {
            "test_type": "system_comprehensive",
            "success": test_result == 0,
            "exit_code": test_result
        }

    except ImportError:
        print("⚠️ [TEST] test_system.py not found, running basic connectivity tests...")

        # Basic connectivity tests
        tests_passed = 0
        total_tests = 3

        # Test 1: Import core modules
        try:
            from agent.graph import create_agentic_outlook_agent
            from llm.llm_client import get_llm_client
            from tools.tool_registry import get_tool_registry
            print("✅ [TEST] Core modules import successfully")
            tests_passed += 1
        except Exception as e:
            print(f"❌ [TEST] Core module import failed: {e}")

        # Test 2: LLM client initialization
        try:
            llm_client = get_llm_client()
            available_providers = llm_client.get_available_providers()
            print(f"✅ [TEST] LLM client initialized - {len(available_providers)} providers available")
            tests_passed += 1
        except Exception as e:
            print(f"❌ [TEST] LLM client initialization failed: {e}")

        # Test 3: Tool registry initialization
        try:
            tool_registry = get_tool_registry()
            print("✅ [TEST] Tool registry initialized successfully")  
            tests_passed += 1
        except Exception as e:
            print(f"❌ [TEST] Tool registry initialization failed: {e}")

        print(f"\n📊 [TEST] Basic tests: {tests_passed}/{total_tests} passed")

        return {
            "test_type": "system_basic",
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "success": tests_passed == total_tests
        }

    except Exception as e:
        error_msg = f"System testing failed: {e}"
        print(f"❌ [TEST] {error_msg}")
        return {"error": error_msg, "test_type": "system_comprehensive"}

def run_api_server(args):
    """Start the FastAPI server."""

    print("🌐 [SERVER] Starting agentic automation API server...")

    try:
        import uvicorn
        from backend.main import app

        host = getattr(args, 'host', '0.0.0.0')
        port = getattr(args, 'port', 8000)

        print(f"🚀 [SERVER] Server starting on http://{host}:{port}")
        print(f"📖 [SERVER] API Documentation: http://{host}:{port}/docs")
        print(f"📊 [SERVER] Features: Tool tracing | Conversation logs | Export capabilities")
        print(f"🔧 [SERVER] Press Ctrl+C to stop server")

        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )

    except ImportError as e:
        print(f"❌ [SERVER] Failed to import server dependencies: {e}")
        print("💡 [SERVER] Install with: pip install uvicorn fastapi")
        return 1

    except Exception as e:
        print(f"❌ [SERVER] Server startup failed: {e}")
        traceback.print_exc()
        return 1

def create_error_result(process_id: str, error_message: str) -> Dict[str, Any]:
    """Create standardized error result."""
    return {
        "process_id": process_id,
        "success": False,
        "error_message": error_message,
        "progress_percentage": 0,
        "current_step": "error",
        "tool_calls_made": 0,
        "duration_seconds": 0
    }

def print_results(results: Dict[str, Any]):
    """Print detailed automation results with enhanced formatting."""

    print("\n" + "=" * 65)
    print("🎯 AUTOMATION RESULTS")
    print("=" * 65)

    success = results.get("success", False)
    status_icon = "🎉" if success else "💥"

    print(f"{status_icon} Status: {'SUCCESS' if success else 'FAILED'}")
    print(f"📊 Progress: {results.get('progress_percentage', 0)}%")
    print(f"📍 Final Step: {results.get('current_step', 'Unknown')}")

    if results.get('process_id'):
        print(f"🔍 Process ID: {results['process_id']}")

    # Account information
    if results.get('account_email'):
        print(f"📧 Created Account: {results['account_email']}")
        if results.get('account_password'):
            print(f"🔑 Password: {results['account_password']}")

    # Performance metrics
    if results.get('duration_seconds'):
        duration = results['duration_seconds']
        print(f"⏱️ Total Duration: {duration:.1f} seconds")

    tool_calls = results.get('tool_calls_made', 0)
    if tool_calls > 0:
        print(f"🛠️ Tool Calls Made: {tool_calls}")

        successful_calls = results.get('successful_tool_calls', 0)
        failed_calls = results.get('failed_tool_calls', 0)
        if successful_calls or failed_calls:
            print(f"   ✅ Successful: {successful_calls}")
            print(f"   ❌ Failed: {failed_calls}")
            if tool_calls > 0:
                success_rate = (successful_calls / tool_calls) * 100
                print(f"   📈 Success Rate: {success_rate:.1f}%")

    # LLM usage
    if results.get('use_llm') is not None:
        llm_status = "🤖 Used" if results['use_llm'] else "🔄 Rule-based"
        print(f"🧠 LLM Decision Making: {llm_status}")

    # Error details
    if not success and results.get("error_message"):
        print(f"\n❌ Error Details:")
        print(f"   {results['error_message']}")

    # Recent tool calls summary
    if results.get("recent_tool_calls"):
        print(f"\n🔧 Recent Tool Activity:")
        for i, call in enumerate(results["recent_tool_calls"][-5:], 1):
            tool_name = call.get("tool_name", "unknown")
            action = call.get("action", "unknown")
            call_success = call.get("success", False)
            duration = call.get("duration_ms", 0)
            call_icon = "✅" if call_success else "❌"
            print(f"   {i}. {call_icon} {tool_name}.{action} ({duration}ms)")

    print("=" * 65)

def print_test_results(results: Dict[str, Any]):
    """Print test results with appropriate formatting."""

    test_type = results.get("test_type", "unknown")

    if test_type == "llm_providers":
        # Already printed in run_llm_tests
        return

    elif test_type in ["system_comprehensive", "system_basic"]:
        print("\n📊 SYSTEM TEST RESULTS:")
        print("=" * 40)

        if results.get("success"):
            print("✅ All system tests passed")
        else:
            if "tests_passed" in results:
                print(f"⚠️ {results['tests_passed']}/{results['total_tests']} tests passed")
            else:
                print("❌ System tests failed")

        if results.get("error"):
            print(f"Error: {results['error']}")

def main():
    """Main entry point with comprehensive argument parsing."""

    parser = argparse.ArgumentParser(
        description="Mobile Outlook Agent - Agentic Version with LLM & OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Manual automation with LLM intelligence
  python main.py --mode manual --first-name John --last-name Smith --date-of-birth 1995-05-15

  # Demo automation (predefined user)  
  python main.py --mode demo

  # Manual without LLM (rule-based fallback)
  python main.py --mode manual --first-name Jane --last-name Doe --date-of-birth 1990-01-01 --no-llm

  # Test LLM providers
  python main.py --mode test-llm

  # Run system tests
  python main.py --mode test

  # Start API server
  python main.py --mode server

  # Use different LLM provider
  python main.py --mode manual --first-name Test --last-name User --date-of-birth 1985-12-25 --llm-provider gemini
        """
    )

    parser.add_argument(
        "--mode",
        choices=["manual", "demo", "test-llm", "test", "server"],
        required=True,
        help="Execution mode: manual (single automation), demo (preset user), test-llm (test providers), test (system tests), server (API server)"
    )

    # User data arguments
    parser.add_argument("--first-name", help="First name for account creation")
    parser.add_argument("--last-name", help="Last name for account creation") 
    parser.add_argument("--date-of-birth", help="Date of birth in YYYY-MM-DD format")
    parser.add_argument("--curp-id", help="CURP ID (optional)")

    # LLM configuration
    parser.add_argument(
        "--no-llm",
        action="store_true", 
        help="Disable LLM integration (use rule-based automation)"
    )

    parser.add_argument(
        "--llm-provider",
        choices=["groq", "gemini", "openai", "anthropic"],
        default="groq",
        help="LLM provider to use for decision making (default: groq)"
    )

    # OCR configuration
    parser.add_argument(
        "--ocr-engine",
        choices=["tesseract", "paddleocr", "easyocr"],
        default="tesseract", 
        help="OCR engine preference (default: tesseract)"
    )

    # Server configuration
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")

    # Debug options
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Print banner and mode info
    print_banner()
    print_mode_info(args)

    # Validate required arguments for automation modes
    if args.mode in ["manual"]:
        if not all([args.first_name, args.last_name, args.date_of_birth]):
            print("❌ Error: --first-name, --last-name, and --date-of-birth are required for manual mode")
            print("💡 Example: python main.py --mode manual --first-name John --last-name Smith --date-of-birth 1995-05-15")
            return 1

        # Validate date format
        try:
            datetime.strptime(args.date_of_birth, "%Y-%m-%d")
        except ValueError:
            print("❌ Error: --date-of-birth must be in YYYY-MM-DD format")
            print("💡 Example: --date-of-birth 1995-05-15")
            return 1

    try:
        # Route to appropriate handler
        if args.mode == "manual":
            results = run_manual_automation(args)
            print_results(results)
            return 0 if results.get("success", False) else 1

        elif args.mode == "demo":
            results = run_demo_automation(args)
            print_results(results)
            return 0 if results.get("success", False) else 1

        elif args.mode == "test-llm":
            results = run_llm_tests(args)
            print_test_results(results)
            return 0 if results.get("working_count", 0) > 0 else 1

        elif args.mode == "test":
            results = run_system_tests(args)
            print_test_results(results)
            return 0 if results.get("success", False) else 1

        elif args.mode == "server":
            return run_api_server(args)

        else:
            print(f"❌ Error: Unknown mode '{args.mode}'")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️ Operation interrupted by user (Ctrl+C)")
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.debug:
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
