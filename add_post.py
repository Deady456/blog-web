import json, os, sys, urllib.request, re
from pathlib import Path

POSTS_DIR = Path(__file__).parent / "posts"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"


def call_llm(prompt: str) -> str:
    if not GROQ_API_KEY:
        return json.dumps({"title": "", "content": "<p>No GROQ_API_KEY</p>"})
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps({
            "model": GROQ_MODEL, "max_tokens": 2000,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }).encode(),
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read())["choices"][0]["message"]["content"]


def expand_article(data: dict) -> dict:
    title = data.get("title", "")
    topic = data.get("topic", "")
    channel = data.get("channel", "general")
    prompt = (
        f"Judul video: {title}\n\n"
        f"Niche: {channel}\nTopik: {topic}\n\n"
        f"Tulis artikel blog 400-600 kata dalam bahasa Indonesia. "
        f"Kembangkan dengan penjelasan tambahan relevan, fakta pendukung, kesimpulan. "
        f"Gunakan format HTML paragraf (<p>). "
        f"Beri judul artikel engaging (>40 karakter). "
        f"Kembalikan ONLY valid JSON: {{\"title\": \"...\", \"content\": \"<p>...</p>\"}}"
    )
    try:
        return json.loads(call_llm(prompt))
    except Exception:
        return {"title": title, "content": "<p>Article generation failed.</p>"}


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


def main():
    data = json.loads(sys.stdin.read())
    data["article"] = expand_article(data)
    data["slug"] = slugify(data.get("article", {}).get("title", data.get("title", "untitled")))[:60]
    ts = data.get("ts", "00000000_000000")
    ch = data.get("channel", "unknown")
    filename = f"{ts}_{ch}_{data['slug']}.json"
    POSTS_DIR.mkdir(exist_ok=True)
    (POSTS_DIR / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"blog-web: saved {filename}")


if __name__ == "__main__":
    main()
