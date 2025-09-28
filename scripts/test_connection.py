#!/usr/bin/env python3
"""
Test database and OpenAI connections.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from app.database import db_manager
from app.services import AIService

async def test_database_connection():
    """Test database connection and list tables."""
    print("Testing database connection...")

    try:
        # Test basic connection
        tables = db_manager.get_available_tables()
        print(f"Database connected successfully!")
        print(f"Found {len(tables)} tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")

        # Test a simple query
        result = db_manager.execute_query("SELECT 1 as test")
        print(f"Query execution test: {result}")

        return True

    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def test_claude_connection():
    """Test Claude connection and AI service."""
    print("\nTesting Claude connection...")

    try:
        ai_service = AIService(db_manager)

        # Test SQL generation
        test_query = "¿Cuántas tablas hay en la base de datos?"
        sql_query = await ai_service.generate_sql_query(test_query)
        print(f"Claude connected successfully!")
        print(f"Test query: '{test_query}'")
        print(f"Generated SQL: {sql_query[:100]}...")

        return True

    except Exception as e:
        print(f"Claude connection failed: {e}")
        return False

async def test_full_workflow():
    """Test the complete query workflow."""
    print("\nTesting complete workflow...")

    try:
        from app.services import QueryService
        from app.models.requests import HumanQueryRequest

        ai_service = AIService(db_manager)
        query_service = QueryService(db_manager, ai_service)

        # Test request
        request = HumanQueryRequest(
            human_query="¿Cuántos productos hay en total?",
            limit_results=5
        )

        response = await query_service.process_human_query(request)
        print(f"Complete workflow test successful!")
        print(f"Answer: {response.answer[:100]}...")
        print(f"Execution time: {response.execution_time:.3f}s")

        return True

    except Exception as e:
        print(f"Workflow test failed: {e}")
        return False

async def main():
    """Run all connection tests."""
    print("Intelligent Agent - Connection Tests")
    print("=" * 50)

    # Check if .env file exists
    if not Path(".env").exists():
        print("ERROR: .env file not found!")
        print("   Please copy .env.example to .env and configure your settings.")
        sys.exit(1)

    tests = [
        ("Database Connection", test_database_connection),
        ("Claude Connection", test_claude_connection),
        ("Full Workflow", test_full_workflow),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR: {test_name} failed with unexpected error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")

    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nAll tests passed! Your Intelligent Agent is ready to use.")
        print("   Run 'python scripts/run_dev.py' to start the development server.")
    else:
        print("\nSome tests failed. Please check your configuration.")

    # Close database connections
    db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())