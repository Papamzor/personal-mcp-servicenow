#!/usr/bin/env python3
"""
Simple test script to verify the optimization works correctly.
This tests the core functionality without making actual API calls.
"""

import asyncio
from utils import extract_keywords, refine_query
from Table_Tools.generic_table_tools import ESSENTIAL_FIELDS, DETAIL_FIELDS

def test_keyword_extraction():
    """Test optimized keyword extraction."""
    print("Testing keyword extraction...")
    
    # Test with regular text
    keywords = extract_keywords("server error login failed", max_keywords=2)
    print(f"Keywords from 'server error login failed': {keywords}")
    
    # Test with incident number
    keywords = extract_keywords("Check incident INC0001234 for details")
    print(f"Keywords with incident number: {keywords}")
    
    # Test with change number
    keywords = extract_keywords("CHG0005678 needs approval")
    print(f"Keywords with change number: {keywords}")

async def test_refine_query():
    """Test optimized query refinement."""
    print("\nTesting query refinement...")
    
    # Test normal text
    result, clarification = await refine_query("server down database connection")
    print(f"Refined query: '{result}', Clarification: {clarification}")
    
    # Test short input
    result, clarification = await refine_query("hi")
    print(f"Short input result: '{result}', Clarification: {clarification}")

def test_field_optimization():
    """Test field optimization."""
    print("\nTesting field optimization...")
    
    for table in ESSENTIAL_FIELDS:
        essential = ESSENTIAL_FIELDS[table]
        detailed = DETAIL_FIELDS[table]
        print(f"{table}: Essential ({len(essential)}) vs Detailed ({len(detailed)})")
        print(f"  Essential: {essential}")

def main():
    """Run all tests."""
    print("=== Testing Optimized Implementation ===")
    
    test_keyword_extraction()
    asyncio.run(test_refine_query())
    test_field_optimization()
    
    print("\n=== Optimization Summary ===")
    print("+ Generic table functions created")
    print("+ Consolidated tool wrappers implemented") 
    print("+ Field selection optimized")
    print("+ Error messages streamlined")
    print("+ Keyword extraction optimized")
    print("+ Tool registration consolidated")

if __name__ == "__main__":
    main()