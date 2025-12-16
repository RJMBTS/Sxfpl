name: Sxfpl

on:
  schedule:
    - cron: "*/30 * * * *"
  workflow_dispatch:

concurrency:
  group: australia-live
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install requests

      - name: Generate Australia Live Playlist
        env:
          IPTV_USER: ${{ secrets.IPTV_USER }}
          IPTV_PASS: ${{ secrets.IPTV_PASS }}
        run: |
          python << 'EOF'
          import requests, os, re
          from datetime import datetime, timedelta, timezone

          HOST_URL = "https://webhop.live"
          USERNAME = os.getenv("IPTV_USER")
          PASSWORD = os.getenv("IPTV_PASS")

          if not USERNAME or not PASSWORD:
              raise SystemExit("❌ IPTV_USER or IPTV_PASS not set")

          PLAYLIST_URL = f"{HOST_URL}/get.php?username={USERNAME}&password={PASSWORD}&type=m3u_plus&output=ts"
          OUTPUT_DIR = "Sxfpl"
          OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Au.m3u")
          os.makedirs(OUTPUT_DIR, exist_ok=True)

          def is_australia_group(line):
              return re.search(r'group-title="[^"]*australia[^"]*"', line, re.IGNORECASE)

          def is_live(url, line):
              return (
                  "/live/" in url.lower()
                  or url.lower().endswith(".ts")
                  or "24/7" in line
                  or "live" in line.lower()
              )

          def set_group(meta):
              meta = re.sub(r'group-title=".*?"', '', meta)
              return f'{meta} group-title="RJM | Australia Live"'

          r = requests.get(PLAYLIST_URL, timeout=30)
          r.raise_for_status()
          lines = r.text.splitlines()

          items = []
          DEFAULT_LOGO = "https://simgbb.com/avatar/dw9KLnpdGh3y.jpg"

          for i in range(len(lines)):
              line = lines[i]
              if not line.startswith("#EXTINF"):
                  continue
              if not is_australia_group(line):
                  continue
              if i + 1 >= len(lines):
                  continue

              url = lines[i + 1].strip()
              if not is_live(url, line):
                  continue

              line = re.sub(r'tvg-name=".*?"', '', line)
              line = re.sub(r'group-title=".*?"', '', line)
              line = line.replace('tvg-id=""', '')

              meta, name = line.rsplit(",", 1)

              if 'tvg-logo=' not in meta:
                  meta += f' tvg-logo="{DEFAULT_LOGO}"'

              meta = set_group(" ".join(meta.split()))
              name = " ".join(name.replace("_", " ").replace("-", " ").split()).title()

              items.append((f"{meta},{name}", url))

          now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
          header = [
              '#EXTM3U billed-msg="RJM Tv - RJMBTS Network"',
              "# RJMS - RJMBTS Network",
              "# Scripted & Updated by Kittujk",
              f"# Last Updated: {now.strftime('%Y-%m-%d %H:%M:%S IST')}",
              ""
          ]

          with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
              f.write("\n".join(header + [x for item in items for x in item]))

          print(f"Generated {OUTPUT_FILE} with {len(items)} channels")
          EOF

      - name: Commit & Push
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add Sxfpl/Au.m3u
          git commit -m "Update Australia Live IPTV (Au.m3u)" || echo "No changes to commit"
          git push
