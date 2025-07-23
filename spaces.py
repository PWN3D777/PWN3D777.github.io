#!/usr/bin/env python3
"""
Reformatea archivos Markdown en _posts/:

- Asegura línea en blanco después de encabezados (#, ##, ...).
- Asegura línea en blanco antes y después de imágenes Markdown ![...](...).
- Colapsa múltiples líneas en blanco en una sola.
- Inserta <link rel="stylesheet" href="{{ '/assets/css/imagesstyle.css' | relative_url }}">
  al final del archivo si no existe ya.
- Preserva front matter YAML.
- No toca contenido dentro de fences de código (``` o ~~~).
- Hace respaldo <filename>.bak antes de escribir.

Uso:
    python3 format_posts_and_add_css.py
    # opcional: --dry-run para ver qué cambiaría sin escribir
"""

import os
import re
import shutil
import argparse
from pathlib import Path

# --- Configuración ---
POSTS_DIR = Path("_posts")
CSS_LINK_LINE = "<link rel=\"stylesheet\" href=\"{{ '/assets/css/imagesstyle.css' | relative_url }}\">"
# Considera .md y .markdown
EXTS = {".md", ".markdown"}

# Regex
RE_HEADER = re.compile(r'^(#{1,6})\s+\S')              # encabezados Markdown
RE_IMAGE = re.compile(r'!\[[^\]]*\]\([^)]+\)')         # patrón básico imágenes
RE_FENCE  = re.compile(r'^(```|~~~)')                  # bloques de código cercados

def split_front_matter(lines):
    """
    Detecta front matter YAML al inicio (--- ... ---).
    Devuelve (front_lines, content_lines).
    Si no hay front matter, front_lines = [].
    """
    if not lines:
        return [], []
    if lines[0].strip() != '---':
        return [], lines[:]
    front = [lines[0]]
    # buscar cierre
    for i in range(1, len(lines)):
        front.append(lines[i])
        if lines[i].strip() == '---':
            return front, lines[i+1:]
    # si nunca cierra, tratamos todo como contenido para no destruir archivo
    return [], lines[:]

def ensure_blank_after(current_lines, idx):
    """
    Inserta línea en blanco después de current_lines[idx] si la siguiente
    línea (ya existente) no es blank y no es EOF.
    Trabaja sobre lista mutable.
    """
    if idx + 1 < len(current_lines):
        if current_lines[idx + 1].strip() != "":
            current_lines.insert(idx + 1, "\n")
            return True
    return False

def process_content_lines(lines):
    """
    Reformatea contenido:
      - Inserta blank line después de encabezado.
      - Inserta blank line antes y después de imagen.
      - Colapsa múltiples blanks consecutivos.
      - Respeta fences de código.
    Devuelve nueva lista de líneas.
    """
    out = []
    in_code = False

    # Usamos iteración manual para poder mirar adelante/atrás
    i = 0
    L = len(lines)
    while i < L:
        line = lines[i]

        # detectar inicio / cierre de code fence
        if RE_FENCE.match(line.strip()):
            in_code = not in_code
            out.append(line)
            i += 1
            continue

        if in_code:
            out.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Imagen Markdown
        if RE_IMAGE.search(stripped):
            # asegurar línea en blanco anterior (si la previa no es blank y hay previa)
            if out and out[-1].strip() != "":
                out.append("\n")
            out.append(line if line.endswith("\n") else line + "\n")
            # asegurar línea en blanco siguiente: miramos la siguiente línea original
            if i + 1 < L and lines[i+1].strip() != "":
                out.append("\n")
            i += 1
            continue

        # Encabezado
        if RE_HEADER.match(stripped):
            # asegurar blank antes (excepto si es primera línea de contenido)
            if out and out[-1].strip() != "":
                out.append("\n")
            out.append(line if line.endswith("\n") else line + "\n")
            # blank después si próxima no está vacía
            if i + 1 < L and lines[i+1].strip() != "":
                out.append("\n")
            i += 1
            continue

        # Línea en blanco: colapsar múltiples
        if stripped == "":
            # solo añadir una línea en blanco si la última no fue blank
            if not out or out[-1].strip() != "":
                out.append("\n")
            i += 1
            continue

        # Línea normal de texto
        out.append(line if line.endswith("\n") else line + "\n")
        i += 1

    return out

def append_css_link_if_missing(lines):
    """
    Asegura que la línea del CSS esté presente (en cualquier parte). Si no,
    la agrega con dos saltos antes para separar del contenido.
    """
    # Buscar sin necesidad de coincidir exactamente: busco substring 'imagesstyle.css'
    needle = "imagesstyle.css"
    joined = "".join(lines)
    if needle in joined:
        return lines
    # agregar 2 saltos y la línea
    if lines and lines[-1].strip() != "":
        lines.append("\n")
    lines.append("\n")
    lines.append(CSS_LINK_LINE + "\n")
    return lines

def process_file(path: Path, dry_run=False):
    with path.open(encoding="utf-8") as f:
        original = f.readlines()

    front, content = split_front_matter(original)

    new_content = process_content_lines(content)
    new_content = append_css_link_if_missing(new_content)

    new_lines = front + new_content

    if new_lines == original:
        return False  # sin cambios

    if dry_run:
        print(f"[DRY] Cambiaría: {path}")
        return True

    # respaldo
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)

    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.writelines(new_lines)

    print(f"[OK] Reformateado: {path} (backup: {backup.name})")
    return True

def main():
    ap = argparse.ArgumentParser(description="Reformatea Markdown en _posts/ y añade CSS link.")
    ap.add_argument("--dry-run", action="store_true", help="Muestra archivos que cambiarían sin escribir.")
    args = ap.parse_args()

    if not POSTS_DIR.is_dir():
        print(f"ERROR: No existe directorio {POSTS_DIR}")
        return

    changed_any = False
    for p in POSTS_DIR.rglob("*"):
        if p.suffix.lower() in EXTS and p.is_file():
            changed = process_file(p, dry_run=args.dry_run)
            changed_any = changed_any or changed

    if args.dry_run:
        if not changed_any:
            print("No habría cambios.")
        else:
            print("Revisa la lista arriba. Ejecuta sin --dry-run para aplicar.")
    else:
        if not changed_any:
            print("No hubo cambios (todos ya formateados o ya tenían el link).")

if __name__ == "__main__":
    main()

