"""
Quick test script - verify project structure without database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def test(name, passed, details=""):
    """Log test result"""
    status = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
    print(f"{status} {name}")
    if details:
        print(f"   └─ {details}")


def main():
    print(f"\n{BOLD}{BLUE}🧪 FreeMarket - Quick Structure Test{RESET}\n")

    # Test 1: Import config
    try:
        from backend import config
        test("Config module", True, f"ENV={config.ENV}, API={config.API_VERSION}")
    except Exception as e:
        test("Config module", False, str(e)[:50])
        return False

    # Test 2: Import models
    try:
        from backend import models
        test("Models module", True, f"User, Item, Match, Rating defined")
    except Exception as e:
        test("Models module", False, str(e)[:50])
        return False

    # Test 3: Import schemas
    try:
        from backend import schemas
        test("Schemas module", True, f"Pydantic schemas defined")
    except Exception as e:
        test("Schemas module", False, str(e)[:50])
        return False

    # Test 4: Import CRUD
    try:
        from backend import crud
        test("CRUD module", True, f"CRUD operations defined")
    except Exception as e:
        test("CRUD module", False, str(e)[:50])
        return False

    # Test 5: Import matching
    try:
        from backend import matching
        test("Matching module", True, f"Matching algorithms defined")
    except Exception as e:
        test("Matching module", False, str(e)[:50])
        return False

    # Test 6: Import API routers
    try:
        from backend.api import router
        test("API router", True, f"Main API router defined")
    except Exception as e:
        test("API router", False, str(e)[:50])
        return False

    # Test 7: Import health endpoint
    try:
        from backend.api.endpoints import health
        test("Health endpoint", True, f"Health check defined")
    except Exception as e:
        test("Health endpoint", False, str(e)[:50])
        return False

    # Test 8: Import listings exchange endpoint
    try:
        from backend.api.endpoints import listings_exchange
        test("Listings exchange endpoint", True, f"Listings exchange defined")
    except Exception as e:
        test("Listings exchange endpoint", False, str(e)[:50])
        return False

    # Test 9: Import FastAPI app
    try:
        from backend.main import app
        test("FastAPI app", True, f"App created, {len(app.routes)} routes")
    except Exception as e:
        test("FastAPI app", False, str(e)[:50])
        return False

    # Test 10: Check utils
    try:
        from backend.utils import validators, logging_config
        test("Utils modules", True, f"Validators and logging configured")
    except Exception as e:
        test("Utils modules", False, str(e)[:50])
        return False

    print(f"\n{BOLD}{GREEN}✅ All structure tests passed!{RESET}")
    print(f"\n{BLUE}Summary:{RESET}")
    print(f"  - Backend structure: ✅ OK")
    print(f"  - API routes: ✅ OK ({len(app.routes)} total)")
    print(f"  - Modules: ✅ OK")
    print(f"  - Configuration: ✅ OK")
    print(f"\n{YELLOW}Next step: Start the server with Docker or local development{RESET}\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
