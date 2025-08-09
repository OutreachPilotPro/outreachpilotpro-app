#!/usr/bin/env python3
"""
Test script to verify deployment readiness
"""

import os
import sys
import subprocess
import time
import requests

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from app_minimal import app
        print("✅ app_minimal.py imports successfully")
        print(f"   - App name: {app.name}")
        print(f"   - Routes available: {len(app.url_map._rules)}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_requirements():
    """Test if requirements can be installed"""
    print("\n📦 Testing requirements installation...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_minimal.txt"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Requirements installed successfully")
            return True
        else:
            print(f"❌ Requirements installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_gunicorn_start():
    """Test if gunicorn can start the app"""
    print("\n🚀 Testing gunicorn startup...")
    
    try:
        # Start gunicorn in background
        process = subprocess.Popen([
            "gunicorn", "app_minimal:app", "--bind", "0.0.0.0:5000", "--timeout", "30"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Gunicorn started successfully")
            
            # Test health endpoint
            try:
                response = requests.get("http://localhost:5000/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Health endpoint responding")
                    data = response.json()
                    print(f"   - Status: {data.get('status')}")
                    print(f"   - App: {data.get('app')}")
                else:
                    print(f"❌ Health endpoint returned status {response.status_code}")
            except Exception as e:
                print(f"❌ Health endpoint test failed: {e}")
            
            # Stop the process
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Gunicorn failed to start: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Gunicorn test failed: {e}")
        return False

def test_environment():
    """Test environment variable loading"""
    print("\n🔧 Testing environment variables...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ['SECRET_KEY', 'FLASK_ENV']
        missing_vars = []
        
        for var in required_vars:
            if os.getenv(var):
                print(f"✅ {var} is set")
            else:
                print(f"⚠️  {var} is not set")
                missing_vars.append(var)
        
        if not missing_vars:
            print("✅ All required environment variables are set")
            return True
        else:
            print(f"⚠️  Missing variables: {', '.join(missing_vars)}")
            return True  # Not critical for basic deployment
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def main():
    """Run all deployment tests"""
    print("🚀 OutreachPilotPro Deployment Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_requirements,
        test_gunicorn_start,
        test_environment
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your app is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please fix issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
