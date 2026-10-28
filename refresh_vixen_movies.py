#!/usr/bin/env python3
"""Re-resolve Pornhub Vixen channel viewkeys -> fresh HLS URLs and rewrite movies.m3u"""
import json, re, time, urllib.request
from html import unescape
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
CHANNEL = "https://www.pornhub.com/channels/vixen"
OUT = Path("movies.m3u")
LIMIT = 20

def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.pornhub.com/",
        "Cookie": "accessAgeDisclaimerPH=1; age_verified=1",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def list_channel():
    html = fetch(CHANNEL)
    items = []
    for m in re.finditer(r'<li[^>]*class="[^"]*pcVideoListItem[^"]*"[^>]*>(.*?)</li>', html, re.S|re.I):
        chunk = m.group(1)
        vk = re.search(r'viewkey=([a-zA-Z0-9]+)', chunk)
        title = re.search(r'title="([^"]+)"', chunk) or re.search(r'data-title="([^"]+)"', chunk)
        thumb = re.search(r'data-mediumthumb="([^"]+)"', chunk)
        if not (vk and title):
            continue
        t = unescape(title.group(1)).strip()
        if "VIXEN" not in t.upper():
            continue
        items.append({
            "viewkey": vk.group(1),
            "title": t,
            "thumb": thumb.group(1) if thumb else "",
            "page": f"https://www.pornhub.com/view_video.php?viewkey={vk.group(1)}",
        })
    seen, out = set(), []
    for it in items:
        if it["viewkey"] not in seen:
            seen.add(it["viewkey"]); out.append(it)
    return out[:LIMIT]

def best_stream(html):
    m = re.search(r'"mediaDefinitions"\s*:\s*(\[.*?\])\s*,\s*"isVertical"', html, re.S)
    if not m:
        return None
    try:
        arr = json.loads(m.group(1))
    except Exception:
        return None
    best, score = None, -1
    for s in arr:
        url = (s.get("videoUrl") or "").replace("\\/", "/")
        if not url:
            continue
        q = s.get("quality")
        if isinstance(q, list):
            q = q[0] if q else "0"
        try:
            n = int(re.sub(r"\D", "", str(q)) or 0)
        except Exception:
            n = 0
        sc = n + (5000 if ".m3u8" in url else 0)
        if sc > score:
            score, best = sc, url
    return best

def main():
    items = list_channel()
    ok = []
    for it in items:
        try:
            page = fetch(it["page"])
            url = best_stream(page)
            if url:
                it["stream"] = url
                ok.append(it)
        except Exception as e:
            print("skip", it["viewkey"], e)
        time.sleep(0.5)
    lines = [
        "#EXTM3U",
        "#LABEL: Vixen Movies (Pornhub channel top)",
        f"#REFRESHED: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        f"#ENTRIES: {len(ok)}",
        f"#SOURCE: {CHANNEL}",
        "#NOTE: HLS tokens expire; run refresh_vixen_movies.py or GitHub Action to renew.",
        "",
    ]
    for r in ok:
        title = re.sub(r'^VIXEN\s*', '', r["title"], flags=re.I).strip()
        logo = r.get("thumb") or ""
        logo_attr = f' tvg-logo="{logo}"' if logo else ""
        lines.append(f'#EXTINF:-1 tvg-id="{r["viewkey"]}" tvg-name="{title}"{logo_attr} group-title="Vixen",{title}')
        lines.append(r["stream"])
        lines.append("")
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} with {len(ok)} entries")

if __name__ == "__main__":
    main()
