"""GasWatch PH(gaswatchph.com)의 메트로 마닐라 주간 평균가를 읽어 docs/index.html 카드와 docs/data.json을 만든다."""
import html
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

SITE = "https://gaswatchph.com/"
OUT = Path(__file__).parent / "docs"
UA = {"User-Agent": "fuel-widget/1.0 (weekly personal Notion widget)"}


def fetch_data_js() -> str:
    home = requests.get(SITE, timeout=30, headers=UA)
    home.raise_for_status()
    m = re.search(r'src="/?(js/data\.js[^"]*)"', home.text)
    url = SITE + (m.group(1) if m else "js/data.js")
    r = requests.get(url, timeout=60, headers=UA)
    r.raise_for_status()
    return r.text


def parse(js: str) -> dict:
    start = js.find("const PRICE_HISTORY")
    if start < 0:
        raise ValueError("PRICE_HISTORY를 찾지 못했습니다. 사이트 구조가 바뀌었을 수 있습니다.")
    body = js[start:]
    weeks = re.findall(r'week:\s*"(\d{4}-\d{2}-\d{2})"', body)[:2]
    labels = re.findall(r'label:\s*"([^"]+)"', body)[:2]
    diesel = [float(x) for x in re.findall(r"dieselAvg:\s*([\d.]+)", body)[:2]]
    gas = [float(x) for x in re.findall(r"unleadedAvg:\s*([\d.]+)", body)[:2]]
    if len(weeks) < 2 or len(diesel) < 2 or len(gas) < 2:
        raise ValueError("주간 평균값을 찾지 못했습니다. 사이트 구조가 바뀌었을 수 있습니다.")

    def item(label, now, prev):
        chg = round(now - prev, 2)
        return {
            "label": label,
            "price": f"{now:.2f}",
            "change": f"{'+' if chg > 0 else '−' if chg < 0 else '±'}₱{abs(chg):.2f} vs last wk",
            "direction": "up" if chg > 0 else "down" if chg < 0 else "flat",
        }

    wk = date.fromisoformat(weeks[0])
    return {
        "week": weeks[0],
        "as_of": f"{wk.strftime('%b')} {wk.day}, {wk.year} ({labels[0]})",
        "items": [
            item("Gasoline (RON 91)", gas[0], gas[1]),
            item("Diesel", diesel[0], diesel[1]),
        ],
    }


def render(data: dict) -> str:
    kst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")
    cards = []
    for it in data["items"]:
        arrow = {"up": "▲", "down": "▼"}.get(it["direction"], "■")
        cards.append(f"""
    <a class="card" href="https://gaswatchph.com/price-history" target="_blank" rel="noopener">
      <div class="name">{html.escape(it['label'])}</div>
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
  .right {{ text-align:right; }}
  .price {{ font-size:24px; font-weight:800; font-variant-numeric:tabular-nums; }}
  .price span {{ font-size:13px; font-weight:400; color:var(--mute); }}
  .chg {{ font-size:12px; font-weight:600; margin-top:2px; }}
  .chg.up {{ color:var(--up); }} .chg.down {{ color:var(--down); }}
  .foot {{ font-size:11px; color:var(--mute); margin:8px 2px 0; }}
</style>
</head>
<body>
  <div class="head">메트로 마닐라 평균 주유소 가격 · {html.escape(data['as_of'])}</div>
  <div class="grid">{''.join(cards)}
  </div>
  <div class="foot">출처: GasWatch PH · 갱신 {kst}</div>
</body>
</html>
"""


def main():
    js = Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else fetch_data_js()
    data = parse(js)
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(render(data), encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    main()
