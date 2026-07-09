import json, os, re, hashlib
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
POSTS_DIR = Path("posts")
POSTS_DIR.mkdir(exist_ok=True)

API_KEY = os.environ.get("BLOG_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"


class PostPayload(BaseModel):
    video_id: str = ""
    title: str
    topic: str = ""
    ts: str = ""
    channel: str = ""
    description: str = ""
    tags: list[str] = []


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


def call_llm(user_msg: str) -> str:
    if not GROQ_API_KEY:
        return "<p>No GROQ_API_KEY configured</p>"
    resp = httpx.post(
        f"{GROQ_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": GROQ_MODEL,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": user_msg}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def expand_article(video_data: dict) -> dict:
    topic = video_data.get("topic", video_data.get("title", ""))
    title = video_data.get("title", "")
    desc = video_data.get("description", "")
    niche = video_data.get("channel", "general")

    user_msg = (
        f"Judul video: {title}\n\n"
        f"Deskripsi: {desc}\n\n"
        f"Niche: {niche}\nTopik: {topic}\n\n"
        f"Tulis artikel blog 400-600 kata dalam bahasa Indonesia berdasarkan judul di atas. "
        f"Kembangkan dengan penjelasan tambahan yang relevan, fakta pendukung, dan kesimpulan. "
        f"Gunakan format HTML paragraf (<p>). Beri judul artikel yang engaging (>40 karakter). "
        f"Jangan tambahkan informasi palsu. Kembalikan ONLY valid JSON: "
        f'{{"title": "...", "content": "<p>...</p>"}}'
    )

    try:
        raw = call_llm(user_msg)
    except Exception as e:
        return {"title": title, "content": f"<p>Article generation failed: {e}</p>"}

    article = json.loads(raw)
    article["tags"] = video_data.get("tags", [])
    return article


def load_posts():
    posts = []
    for f in sorted(POSTS_DIR.glob("*.json"), reverse=True):
        data = json.loads(f.read_text(encoding="utf-8"))
        posts.append(data)
    return posts


@app.get("/", response_class=HTMLResponse)
def home(request: Request, page: int = 1):
    all_posts = load_posts()
    per_page = 12
    start = (page - 1) * per_page
    end = start + per_page
    page_posts = all_posts[start:end]
    total_pages = max(1, (len(all_posts) + per_page - 1) // per_page)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "posts": page_posts,
        "page": page,
        "total_pages": total_pages,
    })


@app.get("/post/{slug}", response_class=HTMLResponse)
def post_page(request: Request, slug: str):
    post = None
    for f in POSTS_DIR.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("slug") == slug:
            post = data
            break
    if not post:
        raise HTTPException(404, "Post not found")
    return templates.TemplateResponse("post.html", {
        "request": request,
        "post": post,
    })


@app.get("/api/posts")
def api_posts():
    return load_posts()


@app.post("/api/posts")
async def create_post(payload: PostPayload, request: Request):
    if API_KEY:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {API_KEY}":
            raise HTTPException(401, "Invalid API key")
    data = payload.model_dump()
    slug = slugify(data.get("title", "untitled"))
    unique = f"{data.get('ts', '')}-{slug}"
    data["slug"] = slug
    data["article"] = expand_article(data)
    data["created_at"] = datetime.utcnow().isoformat()

    filename = f"{unique}.json"
    (POSTS_DIR / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")

    base_url = os.environ.get("SITE_URL", "https://example.com")
    post_url = f"{base_url}/post/{slug}"
    return {"url": post_url, "slug": slug}
