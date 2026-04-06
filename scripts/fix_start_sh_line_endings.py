from pathlib import Path

path = Path('start.sh')
text = path.read_text(encoding='utf-8', errors='replace')
# Normalize to LF line endings
text = text.replace('\r\n', '\n').replace('\r', '\n')
# Ensure the shebang line is correct
lines = text.split('\n')
if lines:
    lines[0] = '#!/usr/bin/env bash'
text = '\n'.join(lines)
path.write_text(text, encoding='utf-8')
print('Normalized start.sh line endings and shebang.')
