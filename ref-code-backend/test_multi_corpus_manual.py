#!/usr/bin/env python3
"""
Manual test script for rag_multi_query functionality.
Tests querying multiple corpora and displays results.
"""
import sys
sys.path.insert(0, 'backend')

from src.rag_agent.tools.rag_multi_query import rag_multi_query
from src.rag_agent.tools.list_corpora import list_corpora
from unittest.mock import Mock

def main():
    print("\n" + "="*70)
    print("TESTING: Multi-Corpus RAG Query")
    print("="*70)
    
    # Create mock tool context
    ctx = Mock()
    ctx.state = {}
    
    # Step 1: List available corpora
    print("\n1. Listing available corpora...")
    corpora_result = list_corpora()
    
    if corpora_result['status'] != 'success':
        print(f"❌ Error listing corpora: {corpora_result['message']}")
        return
    
    corpora = corpora_result['corpora']
    print(f"✅ Found {len(corpora)} corpora:")
    corpus_names = []
    for corpus in corpora:
        name = corpus['display_name']
        corpus_names.append(name)
        print(f"   - {name}")
    
    if len(corpus_names) < 2:
        print(f"\n⚠️  Warning: Only {len(corpus_names)} corpus available.")
        print("   Multi-corpus testing works best with 2+ corpora.")
        if len(corpus_names) == 0:
            print("   No corpora available to test!")
            return
    
    # Step 2: Test single corpus query
    print(f"\n2. Testing SINGLE corpus query ('{corpus_names[0]}')...")
    print(f"   Query: 'What is artificial intelligence?'")
    
    single_result = rag_multi_query(
        corpus_names=[corpus_names[0]],
        query="What is artificial intelligence?",
        tool_context=ctx,
        top_k=3
    )
    
    print(f"   Status: {single_result['status']}")
    print(f"   Results: {single_result['results_count']}")
    if single_result['results_count'] > 0:
        print(f"   Top result score: {single_result['results'][0]['score']:.3f}")
        print(f"   From corpus: {single_result['results'][0]['corpus_source']}")
    
    # Step 3: Test multi-corpus query
    if len(corpus_names) >= 2:
        print(f"\n3. Testing MULTI-CORPUS query ({corpus_names[0]} + {corpus_names[1]})...")
        print(f"   Query: 'What is artificial intelligence?'")
        
        multi_result = rag_multi_query(
            corpus_names=corpus_names[:2],  # First 2 corpora
            query="What is artificial intelligence?",
            tool_context=ctx,
            top_k=5
        )
        
        print(f"   Status: {multi_result['status']}")
        print(f"   Corpora queried: {multi_result['corpora_queried']}")
        print(f"   Total results: {multi_result['results_count']}")
        
        if 'results_by_corpus' in multi_result:
            print(f"   Results by corpus:")
            for corpus, count in multi_result['results_by_corpus'].items():
                print(f"     - {corpus}: {count} results")
        
        if multi_result['results_count'] > 0:
            print(f"\n   Top 3 results (sorted by relevance):")
            for i, result in enumerate(multi_result['results'][:3], 1):
                print(f"     {i}. Score: {result['score']:.3f} | From: {result['corpus_source']}")
                print(f"        Text: {result['text'][:100]}...")
    
    # Step 4: Test all corpora
    if len(corpus_names) > 2:
        print(f"\n4. Testing ALL corpora query ({len(corpus_names)} corpora)...")
        print(f"   Query: 'machine learning'")
        
        all_result = rag_multi_query(
            corpus_names=corpus_names,
            query="machine learning",
            tool_context=ctx,
            top_k=10
        )
        
        print(f"   Status: {all_result['status']}")
        print(f"   Total results: {all_result['results_count']}")
        print(f"   Results by corpus: {all_result.get('results_by_corpus', {})}")
    
    print("\n" + "="*70)
    print("✅ Multi-corpus query testing complete!")
    print("="*70)
    
    print("\n📊 Summary:")
    print(f"   - Available corpora: {len(corpus_names)}")
    print(f"   - Single corpus query: {'✅ Working' if single_result['results_count'] > 0 else '⚠️ No results'}")
    if len(corpus_names) >= 2:
        print(f"   - Multi corpus query: {'✅ Working' if multi_result['results_count'] > 0 else '⚠️ No results'}")
        print(f"   - Corpus attribution: {'✅ Working' if all('corpus_source' in r for r in multi_result.get('results', [])) else '❌ Missing'}")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
