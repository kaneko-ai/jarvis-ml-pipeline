import os
import re

files = [
    r"jarvis_core\retrieval\semantic_dedup.py",
    r"jarvis_core\retrieval\hyde.py",
    r"jarvis_core\performance\mobile.py",
    r"jarvis_core\lab\automation.py",
    r"jarvis_core\integrations\obsidian_sync.py",
    r"jarvis_core\integrations\obsidian_sync_v2.py",
    r"jarvis_core\infrastructure\ecosystem.py",
    r"jarvis_core\graphrag\engine.py",
    r"jarvis_core\index\dedup.py",
    r"jarvis_core\eval\ab_testing.py",
    r"jarvis_core\config\feature_flags.py",
]

base_dir = r"c:\Users\kaneko yu\Documents\jarvis-work\jarvis-ml-pipeline"

for rel_path in files:
    path = os.path.join(base_dir, rel_path)
    if not os.path.exists(path):
        print(f"Skipping {path}, not found")
        continue

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern: hashlib.md5(...).hexdigest()
    # We want to insert usedforsecurity=False inside the md5() call.
    # We handle the case where .encode() is used.

    pattern = r"hashlib\.md5\((.+?)\)\.hexdigest\(\)"

    def replacer(match):
        inner = match.group(1)
        if "usedforsecurity" in inner:
            return match.group(0)

        # If inner ends with .encode(), we append simply
        return f"hashlib.md5({inner}, usedforsecurity=False).hexdigest()"

    new_content = re.sub(pattern, replacer, content)

    if new_content != content:
        print(f"Patching {rel_path}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    else:
        print(f"No changes needed for {rel_path}")
