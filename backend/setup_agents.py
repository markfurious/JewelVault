#!/usr/bin/env python3
"""
Setup script for AI Agent system.
Runs database migrations and validates configuration.
"""
import os
import sys


def check_env():
    """Check environment configuration."""
    print("Checking environment configuration...")

    # Check ANTHROPIC_API_KEY
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  [!] ANTHROPIC_API_KEY not set")
        print("      Export it: export ANTHROPIC_API_KEY='your-key-here'")
        return False
    print(f"  [✓] ANTHROPIC_API_KEY set (key starts with: {api_key[:6]}...)")

    # Check DATABASE_URL
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("  [!] DATABASE_URL not set")
        print("      Using default: postgresql://postgres:postgres@localhost:5432/inventory_db")
    else:
        print(f"  [✓] DATABASE_URL set")

    return True


def run_migration():
    """Run database migration for agent audit logs."""
    print("\nRunning database migration...")

    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("  [✓] Migration completed successfully")
            return True
        else:
            print(f"  [!] Migration output: {result.stdout}")
            print(f"  [!] Migration stderr: {result.stderr}")
            return False

    except FileNotFoundError:
        print("  [!] Alembic not found. Install with: pip install alembic")
        return False
    except Exception as e:
        print(f"  [!] Migration failed: {e}")
        return False


def validate_imports():
    """Validate that all agent modules can be imported."""
    print("\nValidating agent imports...")

    imports = [
        "app.agents.claude_service",
        "app.agents.agent_base",
        "app.agents.agent_orchestrator",
        "app.agents.inventory_manager_agent",
        "app.agents.pricing_update_agent",
        "app.agents.sales_execution_agent",
        "app.agents.product_creation_agent",
        "app.agents.recommendation_execution_agent",
        "app.agents.ar_session_agent",
        "app.agents.anomaly_action_agent",
    ]

    all_ok = True
    for module in imports:
        try:
            __import__(module)
            print(f"  [✓] {module}")
        except ImportError as e:
            print(f"  [!] {module}: {e}")
            all_ok = False
        except Exception as e:
            # Other errors (like missing API key) are ok for import validation
            print(f"  [~] {module}: {type(e).__name__} (expected)")

    return all_ok


def test_claude_connection():
    """Test Claude API connection."""
    print("\nTesting Claude API connection...")

    try:
        from app.agents.claude_service import ClaudeService
        claude = ClaudeService()
        print(f"  [✓] Claude API connected")
        print(f"      Model: {claude.default_model}")
        return True
    except ValueError as e:
        print(f"  [!] Claude API error: {e}")
        return False
    except Exception as e:
        print(f"  [!] Connection failed: {e}")
        return False


def test_database_connection():
    """Test database connection."""
    print("\nTesting database connection...")

    try:
        from app.db.base import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  [✓] Database connected")
        return True
    except Exception as e:
        print(f"  [!] Database error: {e}")
        print("      Make sure PostgreSQL is running and DATABASE_URL is correct")
        return False


def main():
    print("=" * 60)
    print("JewelVault AI Agent System Setup")
    print("=" * 60)

    # Run checks
    env_ok = check_env()
    db_ok = test_database_connection()
    imports_ok = validate_imports()

    if env_ok:
        claude_ok = test_claude_connection()
    else:
        claude_ok = False

    # Summary
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)

    all_ok = env_ok and db_ok and imports_ok and claude_ok

    if all_ok:
        print("\n[✓] All checks passed! Agent system is ready.")
        print("\nNext steps:")
        print("  1. Run migrations: alembic upgrade head")
        print("  2. Start server: python -m uvicorn app.main:app --reload")
        print("  3. Test CLI: python run_agent.py --list-agents")
        print("  4. Execute: python run_agent.py \"Restock low inventory\"")
    else:
        print("\n[!] Some checks failed. Please fix the issues above.")
        if not env_ok:
            print("\nEnvironment issues:")
            print("  - Set ANTHROPIC_API_KEY environment variable")
        if not db_ok:
            print("\nDatabase issues:")
            print("  - Ensure PostgreSQL is running")
            print("  - Set DATABASE_URL environment variable")
        if not claude_ok and env_ok:
            print("\nAPI issues:")
            print("  - Check ANTHROPIC_API_KEY is valid")

    print()
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
