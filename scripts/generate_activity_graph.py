#!/usr/bin/env python3
"""Build a self-contained SVG from the public GitHub contribution calendar."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import date
import html
import re

USERNAME = "Devisri-2409"
URL = f"https://github.com/users/{USERNAME}/contributions"
COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []
        self.months = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and a.get("data-date"):
            try:
                d = date.fromisoformat(a["data-date"])
                level = int(a.get("data-level", "0"))
                self.days.append((d, max(0, min(4, level))))
            except (ValueError, TypeError):
                pass
        if tag == "svg":
            label = a.get("aria-label", "")
            match = re.search(r"([A-Z][a-z]+)\s+contributions", label)
            if match:
                self.months.append(match.group(1))

req = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urlopen(req, timeout=30) as response:
    page = response.read().decode("utf-8", "replace")

parser = CalendarParser()
parser.feed(page)
days = sorted({d: level for d, level in parser.days}.items())
if len(days) < 100:
    raise SystemExit(f"Could not parse GitHub contribution calendar reliably (found {len(days)} days).")

# Arrange the calendar into Sunday-first week columns.
first_sunday = days[0][0].toordinal() - ((days[0][0].weekday() + 1) % 7)
last_sunday = days[-1][0].toordinal() - ((days[-1][0].weekday() + 1) % 7)
weeks = (last_sunday - first_sunday) // 7 + 1
cell, gap, left, top = 11, 3, 34, 35
step = cell + gap
width, height = left + weeks * step + 12, top + 7 * step + 34
level_by_date = dict(days)
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contribution activity for {USERNAME}">',
    '<rect width="100%" height="100%" rx="10" fill="#0d1117"/>',
    '<text x="10" y="20" font-family="Arial,sans-serif" font-size="13" font-weight="600" fill="#e6edf3">GitHub Activity</text>'
]
month_seen = set()
for d, level in days:
    col = (d.toordinal() - first_sunday) // 7
    row = (d.weekday() + 1) % 7
    x, y = left + col * step, top + row * step
    month_key = (d.year, d.month)
    if d.day <= 7 and month_key not in month_seen:
        parts.append(f'<text x="{x}" y="31" font-family="Arial,sans-serif" font-size="9" fill="#9da7b3">{html.escape(d.strftime("%b"))}</text>')
        month_seen.add(month_key)
    title = html.escape(f"{d.isoformat()}: GitHub contribution level {level}")
    parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{COLORS[level]}"><title>{title}</title></rect>')
for label, row in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
    parts.append(f'<text x="1" y="{top + row * step + 8}" font-family="Arial,sans-serif" font-size="8" fill="#9da7b3">{label}</text>')
parts.append('<text x="10" y="%d" font-family="Arial,sans-serif" font-size="9" fill="#9da7b3">Less</text>' % (height - 8))
for i, color in enumerate(COLORS):
    parts.append(f'<rect x="{width - 98 + i * 14}" y="{height - 18}" width="10" height="10" rx="2" fill="{color}"/>')
parts.append('</svg>')
out = Path("assets/github-activity.svg")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(parts), encoding="utf-8")
print(f"Generated {out} with {len(days)} days across {weeks} weeks.")
