#!/usr/bin/env python3
"""
Test OpenAI connection independently.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

async def test_openai_basic():
    """Test basic OpenAI connection."""
    print("Testing basic OpenAI connection...")
    print(f"API Key: {settings.openai_api_key[:20]}...")
    print(f"Model: {settings.openai_model}")

    try:
        # Initialize ChatOpenAI
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_tokens=100,
            request_timeout=30
        )

        # Test simple message
        message = HumanMessage(content="Say hello in Spanish")
        response = await llm.ainvoke([message])

        print("SUCCESS: OpenAI connection working!")
        print(f"Response: {response.content}")
        return True

    except Exception as e:
        print(f"ERROR: OpenAI connection failed: {e}")
        return False

async def test_openai_sql_generation():
    """Test SQL generation with OpenAI."""
    print("\nTesting SQL generation...")

    try:
        from app.database import db_manager
        from langchain.chains import create_sql_query_chain

        # Initialize LLM
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_tokens=500,
            request_timeout=30
        )

        # Create SQL query chain
        query_chain = create_sql_query_chain(llm, db_manager.langchain_db)

        # Test SQL generation
        test_question = "How many tables are in the database?"
        sql_response = await query_chain.ainvoke({"question": test_question})

        print("SUCCESS: SQL generation working!")
        print(f"Question: {test_question}")
        print(f"Generated SQL: {sql_response}")
        return True

    except Exception as e:
        print(f"ERROR: SQL generation failed: {e}")
        return False

async def test_openai_model_alternatives():
    """Test different OpenAI models."""
    print("\nTesting alternative models...")

    models_to_test = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo-preview"
    ]

    for model in models_to_test:
        try:
            print(f"Testing model: {model}")
            llm = ChatOpenAI(
                model=model,
                api_key=settings.openai_api_key,
                temperature=0,
                max_tokens=50,
                request_timeout=30
            )

            message = HumanMessage(content="Hello")
            response = await llm.ainvoke([message])

            print(f"  SUCCESS: {model} works - {response.content[:50]}...")
            return model

        except Exception as e:
            print(f"  FAILED: {model} - {str(e)[:100]}...")
            continue

    return None

async def main():
    """Run all OpenAI tests."""
    print("OpenAI Connection Tests")
    print("=" * 50)

    # Check if .env file exists
    if not Path(".env").exists():
        print("ERROR: .env file not found!")
        print("   Please copy .env.example to .env and configure your settings.")
        sys.exit(1)

    # Test basic connection
    basic_test = await test_openai_basic()

    if not basic_test:
        print("\nTrying alternative models...")
        working_model = await test_openai_model_alternatives()

        if working_model:
            print(f"\nFound working model: {working_model}")
            print("Consider updating your .env file:")
            print(f"OPENAI_MODEL={working_model}")
        else:
            print("\nNo working models found. Please check:")
            print("1. Your API key is valid")
            print("2. Your OpenAI account has credits")
            print("3. Your internet connection")
            return

    # Test SQL generation if basic test passed
    if basic_test:
        await test_openai_sql_generation()

    print("\n" + "=" * 50)
    print("OpenAI tests completed!")

if __name__ == "__main__":
    asyncio.run(main())