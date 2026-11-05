"""fuelprice.ph에서 가솔린·디젤 평균가를 읽어 docs/index.html 카드와 docs/data.json을 만든다."""
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.fuelprice.ph/"
OUT = Path(__file__).parent / "docs"
FUELS = {"Gasoline": "Gasoline (RON 91)", "Diesel": "Diesel"}


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def parse(page: str) -> dict:
    soup = BeautifulSoup(page, "html.parser")

    # 기준일: "as of November 3, 2026"
    sub = soup.select_one(".hero-sub")
    m = re.search(r"as of (.+?\d{4})", clean(sub.get_text()) if sub else "")
    as_of = m.group(1) if m else ""

    items = []
    for row in soup.select("a.hf-row"):
        name_el = row.select_one(".hf-name")
        if not name_el:
            continue
        name = clean(name_el.find(string=True, recursive=False))
        if name not in FUELS:
            continue
        val = row.select_one(".hf-val")
        price = re.search(r"₱\s*([\d,]+\.\d+)", val.get_text() if val else "")
        rng = row.select_one(".hf-range")
        chg = row.select_one(".hf-chg")
        chg_text = clean(chg.get_text()) if chg else ""
        direction = "up" if "up" in row.get("class", []) else "down" if "down" in row.get("class", []) else "flat"
        items.append({
            "name": name,
            "label": FUELS[name],
            "price": price.group(1) if price else None,
            "range": clean(rng.get_text()).replace("Range", "").strip() if rng else "",
            "change": chg_text,
            "direction": direction,
        })

    if len(items) < 2 or any(i["price"] is None for i in items):
        raise ValueError("가격 카드를 찾지 못했습니다. 사이트 구조가 바뀌었을 수 있습니다.")
    return {"as_of": as_of, "items": items}


def render(data: dict) -> str:
    kst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")
    cards = []
    for it in data["items"]:
        arrow = {"up": "▲", "down": "▼"}.get(it["direction"], "■")
        cards.append(f"""
    <a class="card" href="https://www.fuelprice.ph/" target="_blank" rel="noopener">
      <div class="left">
        <div class="name">{html.escape(it['label'])}</div>
        <div class="range">Range {html.escape(it['range'])}</div>
      </div>
      <div class="right">
        <div class="price">₱{html.escape(it['price'])}<span>/L</span></div>
        <div class="chg {it['direction']}">{arrow} {html.escape(it['change'])}</div>
      </div>
    </a>""")
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PH Fuel Price</title>
<style>
  :root {{ --bg:#fff; --fg:#1f2328; --mute:#6b7280; --line:#e5e7eb; --up:#c62828; --down:#2e7d32; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#191919; --fg:#e8e8e8; --mute:#9b9b9b; --line:#2f2f2f; --up:#ef5350; --down:#66bb6a; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:12px; background:var(--bg); color:var(--fg);
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Malgun Gothic",sans-serif; }}
  .head {{ font-size:13px; color:var(--mute); margin:0 2px 8px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:10px; }}
  .card {{ display:flex; justify-content:space-between; align-items:center; gap:12px;
          padding:14px 16px; border:1px solid var(--line); border-radius:12px;
          color:inherit; text-decoration:none; }}
  .name {{ font-size:17px; font-weight:700; }}
  .range {{ font-size:12px; color:var(--mute); margin-top:4px; }}
  .right {{ text-align:right; }}
  .price {{ font-size:24px; font-weight:800; font-variant-numeric:tabular-nums; }}
  .price span {{ font-size:13px; font-weight:400; color:var(--mute); }}
  .chg {{ font-size:12px; font-weight:600; margin-top:2px; }}
  .chg.up {{ color:var(--up); }} .chg.down {{ color:var(--down); }}
  .foot {{ font-size:11px; color:var(--mute); margin:8px 2px 0; }}
</style>
</head>
<body>
  <div class="head">필리핀 평균 주유소 가격 · {html.escape(data['as_of'])} 기준</div>
  <div class="grid">{''.join(cards)}
  </div>
  <div class="foot">출처: fuelprice.ph · 갱신 {kst}</div>
</body>
</html>
"""


def main():
    if len(sys.argv) > 1:  # 테스트용: 저장된 HTML 파일로 실행
        page = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        r = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0 (fuel-widget; weekly)"})
        r.raise_for_status()
        page = r.text
    data = parse(page)
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(render(data), encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    main()
