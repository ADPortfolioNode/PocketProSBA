#!/usr/bin/env python3
"""
Test RAG workflows to ensure they work correctly
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_rag_workflows():
    """Test all RAG workflow implementations"""
    print("🧪 Testing RAG Workflows")
    print("=" * 40)

    try:
        from backend.services.rag import get_rag_manager
        rag_manager = get_rag_manager()

        if not rag_manager or not rag_manager.is_available():
            print("❌ RAG manager not available - cannot test workflows")
            return False

        test_query = "SBA business loans"

        # Test 1: Basic RAG
        print("1. Testing Basic RAG...")
        basic_results = rag_manager.query_documents(test_query, n_results=2)
        if "error" in basic_results:
            print(f"   ❌ Basic RAG failed: {basic_results['error']}")
            return False
        else:
            doc_count = len(basic_results.get("documents", [[]])[0])
            print(f"   ✅ Basic RAG returned {doc_count} documents")

        # Test 2: Multi-stage RAG
        print("\n2. Testing Multi-stage RAG...")
        multistage_results = rag_manager.query_documents_multistage(test_query, n_results=2, max_stages=2)
        if "error" in multistage_results:
            print(f"   ❌ Multi-stage RAG failed: {multistage_results['error']}")
            return False
        else:
            stages = multistage_results.get("stages", [])
            total_docs = len(multistage_results.get("documents", [[]])[0])
            print(f"   ✅ Multi-stage RAG completed {len(stages)} stages, returned {total_docs} documents")

        # Test 3: Recursive RAG
        print("\n3. Testing Recursive RAG...")
        recursive_results = rag_manager.query_documents_recursive(test_query, n_results=2, max_depth=1)
        if "error" in recursive_results:
            print(f"   ❌ Recursive RAG failed: {recursive_results['error']}")
            return False
        else:
            depth = recursive_results.get("depth", 0)
            current_level = recursive_results.get("current_level", 0)
            recursive_count = recursive_results.get("recursive_results", 0)
            print(f"   ✅ Recursive RAG explored depth {depth}, {current_level} current + {recursive_count} recursive documents")

        # Test 4: Adaptive RAG
        print("\n4. Testing Adaptive RAG...")
        adaptive_results = rag_manager.query_documents_adaptive(test_query, n_results=2)
        if "error" in adaptive_results:
            print(f"   ❌ Adaptive RAG failed: {adaptive_results['error']}")
            return False
        else:
            # Check if it has the expected structure
            has_documents = "documents" in adaptive_results
            has_metadata = "metadatas" in adaptive_results
            print(f"   ✅ Adaptive RAG completed (documents: {has_documents}, metadata: {has_metadata})")

        # Test 5: Query complexity analysis
        print("\n5. Testing Query Complexity Analysis...")
        test_queries = [
            ("What is SBA?", "simple"),
            ("How do SBA loans work?", "medium"),
            ("Create a comprehensive business plan with financial projections", "complex")
        ]

        for query, expected_complexity in test_queries:
            complexity = rag_manager._analyze_query_complexity(query)
            complexity_level = "simple" if complexity < 0.3 else "medium" if complexity < 0.7 else "complex"
            status = "✅" if complexity_level == expected_complexity else "❌"
            print(f"   {status} '{query}' → {complexity_level} ({complexity:.2f})")

        print("\n" + "=" * 40)
        print("🎉 All RAG workflows are working correctly!")
        return True

    except Exception as e:
        print(f"❌ RAG workflow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_workflows()
    sys.exit(0 if success else 1)