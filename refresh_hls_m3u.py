#!/usr/bin/env python3
"""Probe working HLS sources and rewrite working_hls_live.m3u. Push to GitHub or serve locally."""
import urllib.request, ssl, json, os, sys
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

CHANNELS = [
    ("Babes TV", "http://88.212.7.11/live/test_basbes_hd_hevc/playlist.m3u8", "Adult TV"),
    ("Brazzers TV Europe", "http://88.212.7.11/live/test_brazzers_hd_hevc/playlist.m3u8", "Adult TV"),
    ("Digital Desire", "http://88.212.7.11/live/test_desire_hd_hevc/playlist.m3u8", "Adult TV"),
    ("Dorcel TV HD", "http://88.212.7.11/live/test_dorcel_hd_hevc/playlist.m3u8", "Adult TV"),
    ("DUSK", "http://88.212.7.11/live/test_dusk_sd_hevc/playlist.m3u8", "Adult TV"),
    ("Erox", "http://88.212.7.11/live/test_erox_hd_hevc/playlist.m3u8", "Adult TV"),
    ("Eroxxx HD", "http://88.212.7.11/live/test_eroxxx_hd_hevc/playlist.m3u8", "Adult TV"),
    ("Extasy TV", "http://88.212.7.11/live/test_extasy_hd_hevc/playlist.m3u8", "Adult TV"),
    ("Leo TV HD", "http://88.212.7.11/live/test_leo_hd_hevc/playlist.m3u8", "Adult TV"),
    ("Reality Kings TV", "http://88.212.7.11/live/test_realitykings_sd_hevc/playlist.m3u8", "Adult TV"),
    ("Miami TV Models", "https://59ec5453559f0.streamlock.net/miamitvmodels/smil:529634/playlist.m3u8", "Adult TV"),
    ("PassionXXX HD", "https://5f22d76e220e1.streamlock.net/canale9/canale9/playlist.m3u8", "Adult TV"),
    ("Rough", "http://cdn.adultiptv.net/rough.m3u8", "Adult Themes"),
    ("Gangbang", "http://cdn.adultiptv.net/gangbang.m3u8", "Adult Themes"),
    ("Compilation", "http://cdn.adultiptv.net/compilation.m3u8", "Adult Themes"),
    ("Brunette", "http://cdn.adultiptv.net/brunette.m3u8", "Adult Themes"),
    ("Blonde", "http://cdn.adultiptv.net/blonde.m3u8", "Adult Themes"),
    ("Anal", "http://cdn.adultiptv.net/anal.m3u8", "Adult Themes"),
    ("Live Cams", "http://cdn.adultiptv.net/livecams.m3u8", "Adult Themes"),
    ("Russian", "http://cdn.adultiptv.net/russian.m3u8", "Adult Themes"),
    ("Threesome", "http://cdn.adultiptv.net/threesome.m3u8", "Adult Themes"),
    ("Cuckold", "http://cdn.adultiptv.net/cuckold.m3u8", "Adult Themes"),
    ("Hardcore", "http://cdn.adultiptv.net/hardcore.m3u8", "Adult Themes"),
    ("Teen", "http://cdn.adultiptv.net/teen.m3u8", "Adult Themes"),
    ("Blowjob", "http://cdn.adultiptv.net/blowjob.m3u8", "Adult Themes"),
    ("POV", "http://cdn.adultiptv.net/pov.m3u8", "Adult Themes"),
    ("Latina", "http://cdn.adultiptv.net/latina.m3u8", "Adult Themes"),
    ("Interracial", "http://cdn.adultiptv.net/interracial.m3u8", "Adult Themes"),
    ("Big Ass", "http://cdn.adultiptv.net/bigass.m3u8", "Adult Themes"),
    ("Fetish", "http://cdn.adultiptv.net/fetish.m3u8", "Adult Themes"),
]

MIAMI_OPTS = {
    "http-origin": "https://miamitv.com",
    "http-referrer": "https://miamitv.com/",
    "http-user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def probe(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
            data = r.read(500)
            return r.getcode() == 200 and (b"#EXTM3U" in data or b"#EXT-X" in data or len(data) > 40)
    except Exception:
        return False

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "working_hls_live.m3u"
    alive = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(probe, c[1]): c for c in CHANNELS}
        for f in as_completed(futs):
            c = futs[f]
            if f.result():
                alive.append(c)
    alive.sort(key=lambda x: (x[2], x[0]))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "#EXTM3U",
        "#LABEL: Working Adult HLS (auto-refresh ready)",
        f"#REFRESHED: {now}",
        f"#ENTRIES: {len(alive)}",
        "#NOTE: Pure HLS only — no MPD / no Widevine. Dead links stripped.",
        "",
    ]
    for name, url, group in alive:
        lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
        if name == "Miami TV Models":
            for k, v in MIAMI_OPTS.items():
                lines.append(f"#EXTVLCOPT:{k}={v}")
        lines.append(url)
        lines.append("")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out} with {len(alive)}/{len(CHANNELS)} live channels @ {now}")

if __name__ == "__main__":
    main()
