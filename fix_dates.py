#!/usr/bin/env python3
import re
import pathlib

# Fecha y hora deseada
NEW_DATE = "2025-07-17 12:05:57 -0400"

# Directorio con los posts
POSTS_DIR = pathlib.Path("temp")

def fix_date_in_file(file_path):
    text = file_path.read_text(encoding="utf-8")
    # Reemplaza cualquier línea que empiece con 'date:'
    new_text = re.sub(r'^date:\s+.*$', f'date:   {NEW_DATE}', text, flags=re.MULTILINE)
    if new_text != text:
        file_path.write_text(new_text, encoding="utf-8")
        print(f"[OK] Fecha cambiada en: {file_path}")
    else:
        print(f"[INFO] No se encontró date: en {file_path}")

def main():
    if not POSTS_DIR.exists():
        print(f"No existe el directorio {POSTS_DIR}")
        return
    for md in POSTS_DIR.glob("*.markdown"):
        fix_date_in_file(md)
    for md in POSTS_DIR.glob("*.md"):
        fix_date_in_file(md)

if __name__ == "__main__":
    main()

