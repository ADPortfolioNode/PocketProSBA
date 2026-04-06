import os
import importlib.util
import sys

SIMPLE_STORE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'simple_vector_store.py'))
spec = importlib.util.spec_from_file_location('simple_vector_store', SIMPLE_STORE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SimpleVectorStore = module.SimpleVectorStore


def test_add_and_count_and_get_all():
    store = SimpleVectorStore()
    assert store.count() == 0
    store.add_document('d1', 'hello world', {'k': 'v'})
    assert store.count() == 1
    docs = store.get_all_documents()
    assert any(d['id'] == 'd1' and 'hello' in d['text'] for d in docs)


def test_search_returns_relevant():
    store = SimpleVectorStore()
    store.add_document('d1', 'small business loan programs', {})
    store.add_document('d2', 'how to bake bread', {})
    results = store.search('loan programs', n_results=2)
    assert results['ids'][0][0] == 'd1'


def test_delete_document():
    store = SimpleVectorStore()
    store.add_document('d1', 'some text', {})
    assert store.count() == 1
    assert store.delete_document('d1') is True
    assert store.count() == 0
    assert store.delete_document('missing') is False
