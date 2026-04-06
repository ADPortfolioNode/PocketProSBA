import time
import pytest
from cache import set_cache, get_cache

def test_cache_performance(benchmark):
    def setup():
        set_cache('test_key', 'value')
    
    benchmark.pedantic(get_cache, args=('test_key',), setup=setup, rounds=100)
