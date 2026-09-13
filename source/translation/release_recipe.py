"""Load frozen release recipes, optionally split into reviewable message banks."""
import json
import re
from pathlib import Path


def load_recipe(path):
    path = Path(path).resolve()
    metadata = json.loads(path.read_text())
    if 'message_files' not in metadata:
        return metadata
    if 'messages' in metadata:
        raise ValueError('Recipe cannot contain both inline and external messages')
    messages, seen = [], set()
    for name in metadata['message_files']:
        match = re.fullmatch(r'messages-(en|it)/(\d{4})\.json', name)
        if not match or match[1] != metadata['language'] or name in seen:
            raise ValueError('Invalid or duplicate message bank path')
        seen.add(name)
        selected = (path.parent / name).resolve()
        try:
            selected.relative_to(path.parent)
        except ValueError:
            raise ValueError('Message bank path escapes recipe directory') from None
        rows = json.loads(selected.read_text())
        if not isinstance(rows, list) or any(row['bank'] != int(match[2]) for row in rows):
            raise ValueError('Message bank file contains an unrelated bank')
        messages.extend(rows)
    # Preserve key order so the frozen recipe fingerprint is unchanged.
    return {('messages' if key == 'message_files' else key):
            (messages if key == 'message_files' else value) for key, value in metadata.items()}
