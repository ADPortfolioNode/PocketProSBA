import chromadb
import pathlib

p = pathlib.Path(chromadb.__file__).parent / 'utils' / 'embedding_functions.py'
print(p)
text = p.read_text()
for i, line in enumerate(text.splitlines(), 1):
    if 'DefaultEmbeddingFunction' in line or 'onnxruntime' in line or 'onnx' in line.lower() or 'use_onnx' in line.lower() or 'disable' in line.lower():
        print(i, line)
