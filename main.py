#!/usr/bin/env python3
"""
Mobile Outlook Agent - Main Runner Script
Test and run Outlook account creation automation
Updated with LLM integration support
"""

import argparse
import sys
import os
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.graph import create_outlook_agent
from agent.state import create_initial_state
from data.constants import generate_demo_data, SAMPLE_USERS
from drivers.appium_client import create_outlook_driver
from llm.llm_client import get_llm_client, test_llm_providers

def test_appium_connection():
    """Test Appium server connection and device setup"""
    print("🔌 Testing Appium connection...")

    try:
        client = create_outlook_driver()
        if client:
            device_info = client.get_device_info()
            print("✅ Appium connection successful!")
            print(f"📱 Device: {device_info.get('device_name', 'Unknown')}")
            print(f"📊 Platform: {device_info.get('platform_name')} {device_info.get('platform_version')}")
            print(f"📐 Screen: {device_info.get('screen_size', {})}")
            print(f"📱 Current Activity: {device_info.get('current_activity', 'Unknown')}")

            # Cleanup
            client.quit_driver()
            return True
        else:
            print("❌ Failed to create Appium driver")
            return False

    except Exception as e:
        print(f"❌ Appium connection failed: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure Appium server is running: appium")
        print("2. Check Android device is connected: adb devices")
        print("3. Ensure USB debugging is enabled")
        print("4. Install Outlook app on device")
        return False

def test_llm_integration():
    """Test LLM integration and providers"""
    print("🤖 Testing LLM integration...")
    print("=" * 50)

    try:
        # Test LLM client initialization
        llm_client = get_llm_client()

        available_providers = llm_client.get_available_providers()
        print(f"📋 Available providers: {available_providers}")

        if not available_providers:
            print("⚠️ No LLM providers available!")
            print("\n🔧 TO ENABLE LLM PROVIDERS:")
            print("Set these environment variables:")
            print("  export GROQ_API_KEY='your_groq_key'")
            print("  export ANTHROPIC_API_KEY='your_anthropic_key'") 
            print("  export OPENAI_API_KEY='your_openai_key'")
            print("  export GOOGLE_API_KEY='your_google_key'")
            return False

        # Test each available provider
        test_prompt = "Explain mobile app automation in one sentence."

        for provider in available_providers:
            print(f"\n🧪 Testing {provider.upper()}...")

            result = llm_client.generate_response(
                prompt=test_prompt,
                provider=provider,
                temperature=0.1
            )

            if result["success"]:
                print(f"✅ {provider}: {result['response'][:100]}...")
                print(f"   Model: {result.get('model', 'Unknown')}")

                metadata = result.get('metadata', {})
                if metadata:
                    usage = metadata.get('usage', {})
                    if usage:
                        print(f"   Usage: {usage}")
            else:
                print(f"❌ {provider}: {result['error']}")

        # Test error analysis feature
        print(f"\n🔍 Testing error analysis...")
        analysis = llm_client.analyze_error_context(
            error_message="Element not found",
            step="email_input",
            context={"retry_count": 2, "last_selector": "//input[@type='email']"}
        )

        if analysis["success"]:
            print("✅ Error analysis working")
            print(f"   Analysis: {analysis.get('analysis', {}).get('cause', 'N/A')}")
        else:
            print(f"❌ Error analysis failed: {analysis.get('error')}")

        return True

    except Exception as e:
        print(f"❌ LLM integration test failed: {e}")
        return False

def run_single_automation(first_name: str, last_name: str, date_of_birth: str, 
                         curp_id: str = None, use_llm: bool = True) -> Dict[str, Any]:
    """Run single Outlook account creation"""
    print("🚀 Starting single Outlook automation...")
    print(f"👤 User: {first_name} {last_name}")
    print(f"📅 DOB: {date_of_birth}")
    print(f"🆔 CURP: {curp_id or 'None'}")
    print(f"🤖 LLM Integration: {'Enabled' if use_llm else 'Disabled'}")
    print("=" * 50)

    try:
        # Create agent with LLM support
        agent = create_outlook_agent(use_llm=use_llm)

        # Run automation
        result = agent.run(
            process_id="MANUAL_RUN",
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            curp_id=curp_id
        )

        # Print results
        print("\n" + "=" * 50)
        print("🎯 AUTOMATION RESULTS:")
        print(f"✅ Success: {result.get('success', False)}")
        print(f"📊 Progress: {result.get('progress_percentage', 0)}%")
        print(f"📍 Final Step: {result.get('current_step', 'Unknown')}")

        if result.get('error_message'):
            print(f"❌ Error: {result.get('error_message')}")

        if result.get('account_email'):
            print(f"📧 Email: {result.get('account_email')}")

        # Print logs
        logs = result.get('logs', [])
        if logs:
            print("\n📋 EXECUTION LOGS:")
            for log in logs[-10:]:  # Last 10 logs
                print(f"  {log}")

        return result

    except Exception as e:
        print(f"💥 Automation failed: {e}")
        return {
            "success": False,
            "error_message": str(e),
            "progress_percentage": 0
        }

def run_demo_automation(use_llm: bool = True):
    """Run demo automation with sample data"""
    print("🎮 Running demo automation...")

    # Use first sample user
    demo_data = SAMPLE_USERS[0]
    print(f"📋 Using sample data: {demo_data}")

    return run_single_automation(
        first_name=demo_data["first_name"],
        last_name=demo_data["last_name"], 
        date_of_birth=demo_data["date_of_birth"],
        curp_id=demo_data["curp_id"],
        use_llm=use_llm
    )

def run_random_demo(use_llm: bool = True):
    """Run demo with randomly generated data"""
    print("🎲 Generating random demo data...")

    demo_data = generate_demo_data()
    print(f"📋 Generated data: {demo_data}")

    return run_single_automation(
        first_name=demo_data["first_name"],
        last_name=demo_data["last_name"],
        date_of_birth=demo_data["date_of_birth"],
        curp_id=demo_data["curp_id"],
        use_llm=use_llm
    )

def start_api_server():
    """Start FastAPI server"""
    print("🌐 Starting API server...")
    print("📱 Make sure Appium server is running: appium")
    print("🔌 Make sure Android device is connected")
    print("📲 Make sure Outlook app is installed")
    print("🤖 LLM integration available via API endpoints")
    print("\n🚀 Starting server on http://localhost:8000")

    try:
        import uvicorn
        from backend.main import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("❌ uvicorn not installed. Install with: pip install uvicorn")
    except Exception as e:
        print(f"❌ Server start failed: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Mobile Outlook Agent with LLM Integration")
    parser.add_argument("--mode", choices=["test", "demo", "random", "server", "manual", "test-llm"],
                       default="demo", help="Execution mode")
    parser.add_argument("--first-name", help="First name for manual mode")
    parser.add_argument("--last-name", help="Last name for manual mode") 
    parser.add_argument("--date-of-birth", help="Date of birth (YYYY-MM-DD) for manual mode")
    parser.add_argument("--curp-id", help="CURP ID (optional)")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM integration")

    args = parser.parse_args()

    use_llm = not args.no_llm

    print("📱 Mobile Outlook Agent with LLM Integration")
    print("=" * 50)

    if args.mode == "test":
        print("🔌 Testing Appium connection...")
        success = test_appium_connection()
        sys.exit(0 if success else 1)

    elif args.mode == "test-llm":
        print("🤖 Testing LLM integration...")
        success = test_llm_integration()
        sys.exit(0 if success else 1)

    elif args.mode == "demo":
        print("🎮 Demo mode - using sample data")
        result = run_demo_automation(use_llm=use_llm)
        sys.exit(0 if result.get("success") else 1)

    elif args.mode == "random":
        print("🎲 Random demo mode")
        result = run_random_demo(use_llm=use_llm)
        sys.exit(0 if result.get("success") else 1)

    elif args.mode == "server":
        print("🌐 API server mode")
        start_api_server()

    elif args.mode == "manual":
        if not all([args.first_name, args.last_name, args.date_of_birth]):
            print("❌ Manual mode requires --first-name, --last-name, and --date-of-birth")
            sys.exit(1)

        print("✋ Manual mode")
        result = run_single_automation(
            first_name=args.first_name,
            last_name=args.last_name,
            date_of_birth=args.date_of_birth,
            curp_id=args.curp_id,
            use_llm=use_llm
        )
        sys.exit(0 if result.get("success") else 1)

if __name__ == "__main__":
    main()
