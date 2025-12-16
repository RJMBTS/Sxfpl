import requests
import os
import re
from datetime import datetime, timedelta, timezone

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def is_australia_group(extinf_line):
    return re.search(r'group-title="[^"]*australia[^"]*"', extinf_line, re.IGNORECASE)

def is_live_stream(stream_url, extinf_line):
    return (
        "/live/" in stream_url.lower()
        or stream_url.lower().endswith(".ts")
        or "24/7" in extinf_line
        or "live" in extinf_line.lower()
    )

def set_group_title(meta_data):
    meta_data = re.sub(r'group-title=".*?"', '', meta_data)
    return f'{meta_data} group-title="RJM | Australia Live"'

# --------------------------------------------------
# Main
# --------------------------------------------------
def generate_australia_live(playlist_url, output_file):
    print(f"Downloading playlist from: {playlist_url}")

    try:
        response = requests.get(playlist_url, timeout=30)
        response.raise_for_status()
        content = response.text
    except requests.exceptions.RequestException as e:
        print(f"Error downloading playlist: {e}")
        return

    lines = content.splitlines()
    items = []

    DEFAULT_LOGO = "https://simgbb.com/avatar/dw9KLnpdGh3y.jpg"

    for i in range(len(lines)):
        line = lines[i]

        if not line.startswith("#EXTINF"):
            continue

        # -------- AUSTRALIA ONLY --------
        if not is_australia_group(line):
            continue

        if i + 1 >= len(lines):
            continue

        stream_url = lines[i + 1].strip()

        # -------- LIVE ONLY --------
        if not is_live_stream(stream_url, line):
            continue

        # -------- CLEAN META --------
        line = line.replace('tvg-id=""', '')
        line = re.sub(r'tvg-name=".*?"', '', line)
        line = re.sub(r'group-title=".*?"', '', line)

        parts = line.rsplit(",", 1)
        if len(parts) != 2:
            continue

        meta_data, name = parts

        # -------- LOGO --------
        if 'tvg-logo=""' in meta_data:
            meta_data = meta_data.replace('tvg-logo=""', f'tvg-logo="{DEFAULT_LOGO}"')
        elif 'tvg-logo=' not in meta_data:
            meta_data = f'{meta_data} tvg-logo="{DEFAULT_LOGO}"'

        meta_data = " ".join(meta_data.split())
        meta_data = set_group_title(meta_data)

        # -------- NAME CLEAN --------
        name = name.replace("_", " ").replace("-", " ").replace(".", "")
        name = " ".join(name.split()).title()

        items.append((f"{meta_data},{name}", stream_url))

    save_file(output_file, items)

# --------------------------------------------------
# Save
# --------------------------------------------------
def save_file(filename, items):
    now_ist = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    timestamp = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")

    content = [
        '#EXTM3U billed-msg="RJM Tv - RJMBTS Network"',
        "# RJMS - RJMBTS Network",
        "# Scripted & Updated by Kittujk",
        f"# Last Updated: {timestamp}",
        "",
    ]

    for info, url in items:
        content.append(info)
        content.append(url)

    if items:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        print(f"Saved {filename}: {len(items)} Australia LIVE channels")
    else:
        print("No Australia LIVE channels found")

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
HOST_URL = "https://webhop.live"
USERNAME = os.getenv("IPTV_USER", "juno123")
PASSWORD = os.getenv("IPTV_PASS", "juno123")

PLAYLIST_URL = (
    f"{HOST_URL}/get.php?"
    f"username={USERNAME}&password={PASSWORD}"
    "&type=m3u_plus&output=ts"
)

OUTPUT_DIR = "Queen"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Australia_Live.m3u")

if __name__ == "__main__":
    generate_australia_live(PLAYLIST_URL, OUTPUT_FILE)
