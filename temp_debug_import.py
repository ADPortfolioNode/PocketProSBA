import sys, traceback
sys.path.insert(0, r'E:\\2026build\\PocketProSBA')
sys.path.insert(0, r'E:\\2026build\\PocketProSBA\\backend')
sys.path.insert(0, r'E:\\2026build\\PocketProSBA\\src')
try:
    import backend.app
    print('backend.app imported successfully')
except Exception:
    traceback.print_exc()
