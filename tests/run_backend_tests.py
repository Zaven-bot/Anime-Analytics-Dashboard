#!/usr/bin/env python3
"""
Backend API Unit Test Runner
Runs comprehensive unit tests for FastAPI endpoints, services, and models
"""

import subprocess
import sys
import os
from pathlib import Path

def run_backend_tests():
    """Run backend API unit tests"""
    
    # Set up paths
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    backend_dir = project_root / "services" / "backend"
    
    print("🧪 Running Backend API Unit Tests")
    print("=" * 50)
    
    # Change to project root for imports to work
    os.chdir(project_root)
    
    # Add backend to Python path
    env = os.environ.copy()
    current_path = env.get('PYTHONPATH', '')
    if current_path:
        env['PYTHONPATH'] = f"{backend_dir}:{current_path}"
    else:
        env['PYTHONPATH'] = str(backend_dir)
    
    # Test commands to run
    test_commands = [
        {
            "name": "API Analytics Tests",
            "command": ["python", "-m", "pytest", "tests/unit/test_api_analytics.py", "-v"],
            "description": "Testing analytics endpoint logic and responses"
        },
        {
            "name": "API Health Tests", 
            "command": ["python", "-m", "pytest", "tests/unit/test_api_health.py", "-v"],
            "description": "Testing health check endpoints and system status"
        },
        {
            "name": "Redis Caching Tests",
            "command": ["python", "-m", "pytest", "tests/unit/test_redis_caching.py", "-v"],
            "description": "Testing Redis caching behavior and fallbacks"
        },
        {
            "name": "Dependency Injection Tests",
            "command": ["python", "-m", "pytest", "tests/unit/test_dependency_injection.py", "-v"],
            "description": "Testing FastAPI dependency injection system"
        },
        {
            "name": "Response Models Tests",
            "command": ["python", "-m", "pytest", "tests/unit/test_response_models.py", "-v"],
            "description": "Testing Pydantic response models and validation"
        }
    ]
    
    results = []
    
    for test_suite in test_commands:
        print(f"\n🔄 {test_suite['name']}")
        print(f"   {test_suite['description']}")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                test_suite["command"],
                env=env,
                capture_output=False,  # Show real-time output
                text=True,
                timeout=300  # 5 minute timeout per test suite
            )
            
            results.append({
                "name": test_suite["name"],
                "success": result.returncode == 0,
                "returncode": result.returncode
            })
            
            if result.returncode == 0:
                print(f"✅ {test_suite['name']} - PASSED")
            else:
                print(f"❌ {test_suite['name']} - FAILED (exit code: {result.returncode})")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_suite['name']} - TIMEOUT")
            results.append({
                "name": test_suite["name"],
                "success": False,
                "returncode": -1
            })
        except Exception as e:
            print(f"💥 {test_suite['name']} - ERROR: {e}")
            results.append({
                "name": test_suite["name"],
                "success": False,
                "returncode": -2
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - {result['name']}")
    
    print(f"\nResults: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All backend API tests passed!")
        return 0
    else:
        print(f"\n💥 {total - passed} test suite(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = run_backend_tests()
    sys.exit(exit_code)
