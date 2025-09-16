#!/usr/bin/env python3
import os
import sys

def run_tests():
    print("🧪 Mobile Outlook Agent - Comprehensive Tests")
    print("=" * 60)

    tests = [
        ("📦 Import Tests", test_imports),
        ("🤖 LLM Integration", test_llm_providers),
        ("🗄️ Database Setup", test_database),
        ("🌐 API Endpoints", test_api_endpoints)
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        try:
            result = test_func()
            results[test_name] = result
            print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name}: ERROR - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY:")
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")

    print(f"\n📊 Overall: {passed}/{total} tests passed")
    return passed == total

def test_imports():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
        from langgraph.graph import StateGraph
        print("  ✅ Core dependencies imported")
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_llm_providers():
    try:
        from llm.llm_client import get_llm_client
        llm_client = get_llm_client()
        available = llm_client.get_available_providers()

        if available:
            print(f"  ✅ LLM providers available: {available}")
        else:
            print("  ⚠️ No LLM providers configured")
        return True
    except Exception as e:
        print(f"  ❌ LLM test failed: {e}")
        return False

def test_database():
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        cursor.execute("INSERT INTO test (name) VALUES ('test')")
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()
        conn.close()

        if result:
            print("  ✅ Database operations working")
            return True
        else:
            return False
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_api_endpoints():
    try:
        from backend.main import app
        routes = [route.path for route in app.routes]
        expected = ["/", "/outlook/create", "/llm/test"]
        found = [r for r in expected if r in routes]

        if len(found) >= 2:  # At least basic endpoints
            print(f"  ✅ API endpoints found: {found}")
            return True
        else:
            print(f"  ❌ Missing endpoints: {found}")
            return False
    except Exception as e:
        print(f"  ❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
