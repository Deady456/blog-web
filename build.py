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
<nav class="nav"><div class="container"><div class="nav-inner"><a href="/" class="logo"><span>//</span> blog</a><div class="nav-links"><a href="/">Beranda</a><div class="dropdown"><a href="#" class="dropbtn">Topic &#9662;</a><div class="dropdown-content">{topic_links}</div></div></div></div></div></nav>
<main class="container">
"""

FOOTER = """</main>
<footer class="footer"><div class="container"><p>&copy; 2026 blog.kampungisekai.my.id</p></div></footer>
</body>
</html>"""

AD_SLOT = '<div class="ad-slot"><p>[Adsterra Banner]</p></div>'


def load_posts():
    posts = []
    for f in sorted(POSTS_DIR.glob("*.json"), reverse=True):
        posts.append(json.loads(f.read_text(encoding="utf-8")))
    return posts


def channel_link(ch):
    return f'<a href="/topic/{ch}.html" class="channel">{ch}</a>'


def post_card(p):
    a = p.get("article", {})
    title = a.get("title", p.get("title", ""))
    slug = p.get("slug", "")
    vid = p.get("video_id", "")
    ts = p.get("ts", "")
    ch = p.get("channel", "")
    excerpt = a.get("content", "")[:150]
    excerpt_clean = excerpt.replace("<p>", "").replace("</p>", " ").replace("<br>", " ").strip()
    badge = '<span class="play-badge">&#9654; YouTube</span>' if vid else ""
    thumb = f'<div class="post-thumb"><img src="https://img.youtube.com/vi/{vid}/mqdefault.jpg" alt="{title}" loading="lazy">{badge}</div>' if vid else ""
    return f"""
<article class="post-card">
  {thumb}
  <div class="post-body">
    <h2><a href="/post/{slug}.html">{title}</a></h2>
    <p class="post-meta">{channel_link(ch)} {ts}</p>
    <p class="post-excerpt">{excerpt_clean[:200]}...</p>
  </div>
</article>"""


def build_index(posts):
    channels = sorted(set(p.get("channel", "") for p in posts if p.get("channel")))
    topic_links = "\n".join(f'<a href="/topic/{ch}.html">{ch}</a>' for ch in channels)
    cards = "\n".join(post_card(p) for p in posts)
    html = HEADER.format(title="Blog - Artikel & Video", topic_links=topic_links)
    html += '<h1>Artikel & <span>Video</span> Terbaru</h1><div class="post-grid">' + cards + "</div>"
    html += FOOTER
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"  index.html ({len(posts)} posts)")
    return channels


def build_post(p, topic_links):
    a = p.get("article", {})
    title = a.get("title", p.get("title", ""))
    content = a.get("content", "<p>No content</p>")
    vid = p.get("video_id", "")
    ts = p.get("ts", "")
    ch = p.get("channel", "")
    slug = p.get("slug", "")

    embed = f'<div class="video-embed"><iframe width="100%" height="400" src="https://www.youtube.com/embed/{vid}" frameborder="0" allowfullscreen></iframe></div>' if vid else ""

    html = HEADER.format(title=title, topic_links=topic_links)
    html += f"""
<article class="post-full">
  <h1>{title}</h1>
  <p class="post-meta">{channel_link(ch)} {ts}</p>
  {embed}
  {AD_SLOT}
  <div class="post-content">{content}</div>
  {AD_SLOT}
</article>
<a href="/" class="back-link">&larr; Kembali ke artikel</a>"""
    html += FOOTER
    (OUT_DIR / "post" / f"{slug}.html").write_text(html, encoding="utf-8")
    print(f"  post/{slug}.html")


def build_topic(ch, posts, topic_links):
    cards = "\n".join(post_card(p) for p in posts)
    title = f"Topic: {ch}"
    html = HEADER.format(title=title, topic_links=topic_links)
    html += f'<h1>Topic: <span>{ch}</span></h1><div class="post-grid">' + cards + "</div>"
    html += FOOTER
    topic_dir = OUT_DIR / "topic"
    topic_dir.mkdir(exist_ok=True)
    (topic_dir / f"{ch}.html").write_text(html, encoding="utf-8")
    print(f"  topic/{ch}.html ({len(posts)} posts)")


def main():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "post").mkdir(parents=True)
    shutil.copytree(ASSETS_SRC, ASSETS_DST)

    posts = load_posts()
    print(f"Building {len(posts)} posts...")
    channels = build_index(posts)
    topic_links = "\n".join(f'<a href="/topic/{ch}.html">{ch}</a>' for ch in channels)
    for p in posts:
        slug = p.get("slug", "")
        if slug:
            build_post(p, topic_links)
    for ch in channels:
        ch_posts = [p for p in posts if p.get("channel") == ch]
        if ch_posts:
            build_topic(ch, ch_posts, topic_links)
    print("Done.")


if __name__ == "__main__":
    main()
