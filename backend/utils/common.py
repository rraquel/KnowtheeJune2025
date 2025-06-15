import re
def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.strip().lower()).strip('_')