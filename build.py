import json, shutil
from pathlib import Path

POSTS_DIR = Path(__file__).parent / "posts"
OUT_DIR = Path(__file__).parent / "_site"
ASSETS_SRC = Path(__file__).parent / "assets"
ASSETS_DST = OUT_DIR / "assets"

HEADER = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<nav class="nav"><div class="container"><a href="/" class="logo">Blog</a></div></nav>
<main class="container">
"""

FOOTER = """</main>
<footer class="footer"><div class="container"><p>&copy; 2026 Blog</p></div></footer>
</body>
</html>"""

AD_SLOT = '<div class="ad-slot"><p style="text-align:center;padding:20px;background:#f5f5f5;border:1px dashed #ccc;">[Adsterra Ad]</p></div>'


def load_posts():
    posts = []
    for f in sorted(POSTS_DIR.glob("*.json"), reverse=True):
        posts.append(json.loads(f.read_text(encoding="utf-8")))
    return posts


def build_index(posts):
    cards = ""
    for p in posts:
        a = p.get("article", {})
        title = a.get("title", p.get("title", ""))
        slug = p.get("slug", "")
        vid = p.get("video_id", "")
        ts = p.get("ts", "")
        ch = p.get("channel", "")
        excerpt = a.get("content", "")[:150]
        excerpt_clean = excerpt.replace("<p>", "").replace("</p>", " ").replace("<br>", " ").strip()
        thumb = f'<img src="https://img.youtube.com/vi/{vid}/mqdefault.jpg" alt="{title}">' if vid else ""
        cards += f"""
<article class="post-card">
  {('<div class="post-thumb">' + thumb + '</div>') if thumb else ''}
  <div class="post-body">
    <h2><a href="/post/{slug}.html">{title}</a></h2>
    <p class="post-meta">{ts} &middot; {ch}</p>
    <p class="post-excerpt">{excerpt_clean[:200]}...</p>
  </div>
</article>"""

    html = HEADER.format(title="Blog - Artikel & Video")
    html += "<h1>Artikel & Video Terbaru</h1><div class=\"post-grid\">" + cards + "</div>"
    html += FOOTER
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"  index.html ({len(posts)} posts)")


def build_post(p):
    a = p.get("article", {})
    title = a.get("title", p.get("title", ""))
    content = a.get("content", "<p>No content</p>")
    vid = p.get("video_id", "")
    ts = p.get("ts", "")
    ch = p.get("channel", "")
    slug = p.get("slug", "")

    embed = f'<div class="video-embed"><iframe width="100%" height="400" src="https://www.youtube.com/embed/{vid}" frameborder="0" allowfullscreen></iframe></div>' if vid else ""

    html = HEADER.format(title=title)
    html += f"""
<article class="post-full">
  <h1>{title}</h1>
  <p class="post-meta">{ts} &middot; {ch}</p>
  {embed}
  {AD_SLOT}
  <div class="post-content">{content}</div>
  {AD_SLOT}
</article>
<a href="/" class="back-link">&larr; Back to articles</a>"""
    html += FOOTER
    (OUT_DIR / "post" / f"{slug}.html").write_text(html, encoding="utf-8")
    print(f"  post/{slug}.html")


def main():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "post").mkdir(parents=True)
    shutil.copytree(ASSETS_SRC, ASSETS_DST)

    _redirects = Path(__file__).parent / "_redirects"
    if _redirects.exists():
        shutil.copy(_redirects, OUT_DIR / "_redirects")

    posts = load_posts()
    print(f"Building {len(posts)} posts...")
    build_index(posts)
    for p in posts:
        slug = p.get("slug", "")
        if slug:
            build_post(p)
    print("Done.")


if __name__ == "__main__":
    main()
