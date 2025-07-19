#!/usr/bin/env python3
import os
import re
import zipfile
import tempfile
import shutil
import unicodedata
import pathlib
from urllib.parse import unquote

# -------- CONFIGURACIÓN --------
POST_DATE = "2025-09-27"   # Fecha por defecto de los posts
POST_CATEGORY = "writeups" # Categoría por defecto
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

ROOT = pathlib.Path(__file__).resolve().parent
POSTS_DIR = ROOT / "_posts"
IMAGES_DIR = ROOT / "assets" / "images"

# -------- FUNCIONES --------
def slugify(name: str) -> str:
    """Crea un slug limpio a partir de un nombre."""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return name or "post"

def sanitize_img(name: str) -> str:
    base, ext = os.path.splitext(os.path.basename(name))
    base = unquote(base)
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")
    if not base:
        base = "img"
    ext = ext.lower() if ext else ".png"
    if ext not in IMG_EXTS:
        ext = ".png"
    return f"{base}{ext}"

def build_new_img_name(slug: str, orig_path: str) -> str:
    return f"{slug}_{sanitize_img(orig_path)}"

# Patrones para imágenes Markdown y HTML
MD_IMG_RE = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)')
HTML_IMG_RE = re.compile(r'<img\s+[^>]*src=["\'](?P<src>[^"\']+)["\'](?P<rest>[^>]*)>', re.IGNORECASE)

def replace_markdown_images(text, mapping, slug):
    def _sub(m):
        alt = m.group('alt')
        src = unquote(m.group('src').strip())
        key = os.path.basename(src).lower()
        new_fn = mapping.get(key)
        if not new_fn:
            return m.group(0)
        new_path = f"/assets/images/{slug}/{new_fn}"
        return f"![{alt}]({{{{ '{new_path}' | relative_url }}}})"
    return MD_IMG_RE.sub(_sub, text)

def replace_html_images(text, mapping, slug):
    def _sub(m):
        src = unquote(m.group('src').strip())
        rest = m.group('rest') or ""
        key = os.path.basename(src).lower()
        new_fn = mapping.get(key)
        if not new_fn:
            return m.group(0)
        new_path = f"/assets/images/{slug}/{new_fn}"
        return f"<img src=\"{{{{ '{new_path}' | relative_url }}}}\"{rest}>"
    return HTML_IMG_RE.sub(_sub, text)

def find_first_markdown(path: pathlib.Path):
    for p in path.rglob("*"):
        if p.suffix.lower() in (".md", ".markdown"):
            return p
    return None

def collect_images(path: pathlib.Path):
    imgs = []
    for p in path.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            imgs.append(p)
    return imgs

def process_zip(zip_path: pathlib.Path, date=POST_DATE, category=POST_CATEGORY):
    slug = slugify(zip_path.stem)
    print(f"== Procesando {zip_path.name} -> slug: {slug}")

    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="notion_zip_"))
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        # Buscar markdown
        md_in = find_first_markdown(tmpdir)
        if not md_in:
            print(f"  [WARN] No se encontró archivo markdown en {zip_path.name}")
            return

        post_title = md_in.stem or slug

        # Preparar destino imágenes
        img_dest_dir = IMAGES_DIR / slug
        img_dest_dir.mkdir(parents=True, exist_ok=True)

        # Copiar imágenes + mapping
        mapping = {}
        for img_path in collect_images(tmpdir):
            new_name = build_new_img_name(slug, img_path.name)
            shutil.copy2(img_path, img_dest_dir / new_name)
            mapping[img_path.name.lower()] = new_name
            mapping[sanitize_img(img_path.name).lower()] = new_name

        # Leer markdown original
        md_text = md_in.read_text(encoding="utf-8")

        # Reemplazar referencias de imágenes
        md_text = replace_markdown_images(md_text, mapping, slug)
        md_text = replace_html_images(md_text, mapping, slug)

        # Crear front matter
        front_matter = f"""---
layout: post
title: "{post_title}"
date: {date}
categories: {category}
---

"""
        final_text = front_matter + md_text

        # Guardar post
        post_filename = f"{date}-{slug}.markdown"
        POSTS_DIR.mkdir(exist_ok=True)
        out_path = POSTS_DIR / post_filename
        out_path.write_text(final_text, encoding="utf-8")

        print(f"  [OK] Post: {out_path}")
        print(f"  [OK] Imágenes: {img_dest_dir}")
    finally:
        shutil.rmtree(tmpdir)

def main():
    import sys
    if len(sys.argv) < 2:
        print("Uso: python3 process_notion_zips.py <directorio_con_zips>")
        return
    zips_dir = pathlib.Path(sys.argv[1]).expanduser().resolve()
    if not zips_dir.is_dir():
        print(f"No existe el directorio: {zips_dir}")
        return
    # Ordenar de más viejo a más nuevo
    for zp in sorted(zips_dir.glob("*.zip"), key=lambda x: x.stat().st_mtime):
        process_zip(zp)



if __name__ == "__main__":
    main()

