#!/usr/bin/env python3
"""
CLI for executing AI agents in the JewelVault system.

Usage:
    python run_agent.py "Restock low inventory products"
    python run_agent.py "Update prices based on gold increase" --dry-run
    python run_agent.py "Create 1ct round diamond VS1 G color 18K white gold ring"
    python run_agent.py "Detect anomalies" --agent anomaly_action
"""
import argparse
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.base import db_session, engine
from app.agents.claude_service import ClaudeService
from app.agents.agent_orchestrator import AgentOrchestrator
from app.models.agent_audit import AgentAuditLog
from app.db.base import Base


def print_result(result: dict, verbose: bool = False):
    """Pretty print agent execution result."""
    print("\n" + "=" * 60)
    print("AGENT EXECUTION RESULT")
    print("=" * 60)

    status_icon = "✓" if result.get("status") == "success" else "✗"
    print(f"Status: {status_icon} {result.get('status', 'unknown').upper()}")
    print(f"Agent: {result.get('agent', 'unknown')}")

    if result.get("intent"):
        print(f"Intent: {result.get('intent')}")

    print(f"\nAction Taken: {result.get('action_taken', 'None')}")

    if result.get("error"):
        print(f"\nError: {result.get('error')}")

    if result.get("dry_run"):
        print("\n[DRY RUN MODE - No database changes made]")

    if result.get("actions"):
        print(f"\nActions ({len(result['actions'])}):")
        for i, action in enumerate(result["actions"], 1):
            if hasattr(action, "to_dict"):
                action = action.to_dict()
            print(f"\n  {i}. {action.get('action_type', 'Unknown')}")
            print(f"     Description: {action.get('description', 'N/A')}")
            print(f"     Entity: {action.get('entity_type', 'N/A')}")
            if action.get("entity_id"):
                print(f"     Entity ID: {action.get('entity_id')}")
            if verbose and action.get("data"):
                print(f"     Data: {json.dumps(action.get('data'), indent=6, default=str)}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Execute AI agents for JewelVault inventory management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_agent.py "Restock low inventory products"
  python run_agent.py "Update prices based on gold increase" --dry-run
  python run_agent.py "Create 1ct round diamond VS1 G color"
  python run_agent.py "Detect anomalies" --agent anomaly_action
  python run_agent.py "Process sale for customer John" --agent sales_execution
        """
    )

    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Natural language query describing the action"
    )

    parser.add_argument(
        "--agent",
        type=str,
        default=None,
        help="Specific agent to use (optional, auto-detected if not provided)"
    )

    parser.add_argument(
        "--action",
        type=str,
        default=None,
        help="Specific action for direct agent execution"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without making database changes"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including action data"
    )

    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all available agents"
    )

    parser.add_argument(
        "--health",
        action="store_true",
        help="Check system health"
    )

    args = parser.parse_args()

    # Handle list-agents
    if args.list_agents:
        print("\nAvailable Agents:")
        print("-" * 40)
        agents = [
            ("inventory_manager", "Manages inventory reordering and dead stock"),
            ("pricing_update", "Updates prices based on metal market changes"),
            ("sales_execution", "Processes sales, returns, and cancellations"),
            ("product_creation", "Creates products from natural language"),
            ("recommendation_execution", "Generates and attaches product recommendations"),
            ("ar_session", "Logs and analyzes AR try-on sessions"),
            ("anomaly_action", "Detects and responds to anomalies"),
        ]
        for name, desc in agents:
            print(f"  {name:25} - {desc}")
        print()
        return 0

    # Handle health check
    if args.health:
        print("\nSystem Health Check:")
        print("-" * 40)

        # Check database
        try:
            with Session(engine) as db:
                db.execute("SELECT 1")
            print("  Database: ✓ Connected")
        except Exception as e:
            print(f"  Database: ✗ Error - {e}")

        # Check Claude API
        try:
            claude = ClaudeService()
            print(f"  Claude API: ✓ Connected ({claude.default_model})")
        except ValueError as e:
            print(f"  Claude API: ✗ Error - {e}")
        except Exception as e:
            print(f"  Claude API: ✗ Error - {e}")

        print()
        return 0

    # Validate query
    if not args.query:
        parser.print_help()
        print("\nError: Query is required")
        return 1

    # Execute agent
    try:
        # Initialize database session
        db = db_session()

        try:
            orchestrator = AgentOrchestrator(db)

            if args.agent:
                # Direct execution
                result = orchestrator.run_direct(
                    agent_name=args.agent,
                    action=args.action or args.query,
                    dry_run=args.dry_run,
                )
            else:
                # Intent-based execution
                result = orchestrator.run(
                    query=args.query,
                    dry_run=args.dry_run,
                )

            print_result(result, verbose=args.verbose)

            return 0 if result.get("status") == "success" else 1

        finally:
            db.close()

    except Exception as e:
        print(f"\nError: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
