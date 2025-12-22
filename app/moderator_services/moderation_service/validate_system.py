#!/usr/bin/env python3
"""
Pre-deployment System Validator
Checks all components before production deployment
"""

import os
import sys
import importlib.util
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check(condition, message):
    """Print check result"""
    if condition:
        print(f"  {Colors.GREEN}✓{Colors.END} {message}")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.END} {message}")
        return False

def warn(message):
    """Print warning"""
    print(f"  {Colors.YELLOW}⚠{Colors.END} {message}")

def section(title):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def validate_structure():
    """Validate directory structure"""
    section("1. Directory Structure")

    required_dirs = [
        "app",
        "app/api",
        "app/core",
        "app/models",
        "app/services",
        "app/infra",
        "app/utils",
        "app/workers",
        "logs",
        "logs/audit",
        "cache",
        "models_weights",
        "tests",
        "docs"
    ]

    all_ok = True
    for dir_path in required_dirs:
        exists = os.path.isdir(dir_path)
        all_ok &= check(exists, f"Directory: {dir_path}")

    return all_ok

def validate_files():
    """Validate required files exist"""
    section("2. Required Files")

    required_files = {
        # Core files
        "app/main.py": "Main FastAPI app",
        "app/__init__.py": "App package init",

        # API routes
        "app/api/routes_moderation.py": "Moderation routes",
        "app/api/routes_health.py": "Health check routes",

        # Core modules
        "app/core/config.py": "Configuration",
        "app/core/decision_engine.py": "Decision engine",
        "app/core/hashing.py": "Content hashing",
        "app/core/policy.yaml": "Policy configuration",

        # Services
        "app/services/master_pipeline.py": "Master pipeline",
        "app/services/text_rules.py": "Rule-based filtering",
        "app/services/text_detoxify.py": "Toxicity detection",
        "app/services/nsfw_detector.py": "NSFW detection",
        "app/services/video_processor.py": "Video processing",

        # Infrastructure
        "app/infra/queue_client.py": "Queue client",
        "app/utils/logging.py": "Logging utilities",

        # Models
        "app/models/schemas.py": "Pydantic schemas",

        # Config files
        "requirements.txt": "Python dependencies",
        "Dockerfile": "Docker image",
        "docker-compose.yml": "Docker Compose",
        ".env": "Environment config",
        ".env.example": "Environment template",

        # Documentation
        "README.md": "README",
        "docs/API.md": "API documentation"
    }

    all_ok = True
    for file_path, description in required_files.items():
        exists = os.path.isfile(file_path)
        all_ok &= check(exists, f"{description}: {file_path}")

        if exists:
            # Check file is not empty
            size = os.path.getsize(file_path)
            if size == 0:
                warn(f"{file_path} is empty")

    return all_ok

def validate_python_syntax():
    """Validate Python syntax in all files"""
    section("3. Python Syntax Validation")

    python_files = list(Path("app").rglob("*.py"))
    errors = []

    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), str(file_path), 'exec')
            check(True, f"{file_path}")
        except SyntaxError as e:
            check(False, f"{file_path}: {e}")
            errors.append(str(file_path))

    return len(errors) == 0

def validate_imports():
    """Validate critical imports"""
    section("4. Python Dependencies")

    critical_deps = [
        ("fastapi", "FastAPI framework"),
        ("pydantic", "Data validation"),
        ("redis", "Redis client"),
        ("detoxify", "Toxicity detection"),
        ("torch", "PyTorch"),
        ("cv2", "OpenCV"),
        ("transformers", "Transformers"),
    ]

    all_ok = True
    for module_name, description in critical_deps:
        try:
            __import__(module_name)
            check(True, f"{description} ({module_name})")
        except ImportError:
            check(False, f"{description} ({module_name}) - Run: pip install -r requirements.txt")
            all_ok = False

    return all_ok

def validate_config():
    """Validate configuration"""
    section("5. Configuration")

    all_ok = True

    # Check .env exists
    env_exists = os.path.isfile(".env")
    all_ok &= check(env_exists, ".env file exists")

    if env_exists:
        with open(".env", 'r') as f:
            content = f.read()
            all_ok &= check("REDIS_URL" in content, "REDIS_URL configured")
            all_ok &= check("LOG_LEVEL" in content, "LOG_LEVEL configured")

    # Check policy.yaml
    policy_exists = os.path.isfile("app/core/policy.yaml")
    all_ok &= check(policy_exists, "policy.yaml exists")

    return all_ok

def validate_integration():
    """Validate component integration"""
    section("6. Component Integration")

    all_ok = True

    try:
        # Try importing main app
        sys.path.insert(0, os.path.abspath('.'))
        from app.main import app
        check(True, "Main app imports successfully")

        # Check routes are registered
        routes = [r.path for r in app.routes]
        all_ok &= check("/moderate/realtime" in routes, "Moderation route registered")
        all_ok &= check("/health" in routes, "Health route registered")

    except Exception as e:
        check(False, f"Main app import failed: {e}")
        all_ok = False

    return all_ok

def validate_docker():
    """Validate Docker setup"""
    section("7. Docker Configuration")

    all_ok = True

    # Check Dockerfile
    if os.path.isfile("Dockerfile"):
        with open("Dockerfile", 'r') as f:
            content = f.read()
            all_ok &= check("FROM python" in content, "Valid Python base image")
            all_ok &= check("EXPOSE 8000" in content, "Port 8000 exposed")
            all_ok &= check("uvicorn" in content, "Uvicorn command present")
    else:
        all_ok = False
        check(False, "Dockerfile missing")

    # Check docker-compose.yml
    if os.path.isfile("docker-compose.yml"):
        with open("docker-compose.yml", 'r') as f:
            content = f.read()
            all_ok &= check("moderation:" in content, "Moderation service defined")
            all_ok &= check("redis:" in content, "Redis service defined")
    else:
        all_ok = False
        check(False, "docker-compose.yml missing")

    return all_ok

def validate_php_client():
    """Validate PHP client"""
    section("8. PHP Client Integration")

    php_client = "../ModerationServiceClient.php"

    if os.path.isfile(php_client):
        with open(php_client, 'r') as f:
            content = f.read()
            check("class ModerationServiceClient" in content, "PHP client class defined")
            check("moderateRealtime" in content, "moderateRealtime method exists")
            check("MODERATION_SERVICE_URL" in content, "Service URL configurable")
        return True
    else:
        check(False, f"PHP client not found at {php_client}")
        return False

def main():
    """Run all validations"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}AdSphere Moderation Service - System Validator{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    results = {
        "Structure": validate_structure(),
        "Files": validate_files(),
        "Syntax": validate_python_syntax(),
        "Dependencies": validate_imports(),
        "Configuration": validate_config(),
        "Integration": validate_integration(),
        "Docker": validate_docker(),
        "PHP Client": validate_php_client()
    }

    # Summary
    section("Validation Summary")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {name}: {status}")

    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")

    if passed == total:
        print(f"{Colors.GREEN}✓ ALL CHECKS PASSED ({passed}/{total}){Colors.END}")
        print(f"{Colors.GREEN}System is READY for deployment!{Colors.END}")
        print(f"\n{Colors.BLUE}Next Steps:{Colors.END}")
        print("  1. Start the service: ./start.sh")
        print("  2. Run integration tests: python3 test_integration.py")
        print("  3. Configure PHP to use: http://localhost:8002")
        return 0
    else:
        print(f"{Colors.RED}✗ CHECKS FAILED ({total - passed}/{total} failed){Colors.END}")
        print(f"\n{Colors.YELLOW}Fix the issues above before deployment{Colors.END}")
        return 1

if __name__ == "__main__":
    exit(main())

