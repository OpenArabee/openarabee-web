#!/usr/bin/env python3
"""Generate abwab.html from the reference tables of openarabee-core.

    python tools/build_abwab.py ../openarabee-core

Every linguistic value on the page comes from reference/*.json of that checkout;
abwab.html must not be edited by hand.
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent
TEN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
# Arabic interface texts of the 3D view (explanations, not data)
UI = {"floor": "الماضي على {n} أحرف", "digits": {"3": "٣", "4": "٤", "5": "٥", "6": "٦"},
      "columns": {"thulathi": "الثلاثي", "mulhaq": "الملحق بالرباعي", "rubai": "الرباعي"},
      "bab": "الباب", "model": "موزونه:", "use": "بناؤه:", "more": "التفاصيل في الجدول"}
STATUS_TEXT = {"source-verified": "checked against the print", "draft": "draft"}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def ar(s: str, cls: str = "") -> str:
    return f'<span class="ar {cls}" lang="ar" dir="rtl">{esc(s)}</span>'


def statuses(node, out=None):
    out = set() if out is None else out
    if isinstance(node, dict):
        if "src" in node and "status" in node:
            out.add(node["status"])
        for v in node.values():
            statuses(v, out)
    elif isinstance(node, list):
        for v in node:
            statuses(v, out)
    return out


def build(core: Path) -> str:
    abwab = json.loads((core / "reference/abwab.bina-35.json").read_text(encoding="utf-8"))
    forms = {f["id"]: f for f in json.loads((core / "reference/forms.wright.json").read_text(encoding="utf-8"))["forms"]}
    commit = subprocess.run(["git", "-C", str(core), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    by_form: dict[str, list[int]] = {}
    for b in abwab["abwab"]:
        for w in b["western"]:
            if w["relation"] in ("exact", "vowel-class"):
                by_form.setdefault(w["value"], []).append(b["number"])

    tiles = []
    for fid in TEN:
        nums = by_form.get(fid, [])
        label = "abwāb " + "–".join(str(n) for n in (nums[0], nums[-1])) if len(nums) > 1 else f"bāb {nums[0]}"
        tiles.append(f'<a class="tile" href="#bab-{nums[0]}"><span class="num">{fid}</span>{ar(forms[fid]["pattern"]["value"], "big")}<span class="sub">{label}</span></a>')

    groups = {g["id"]: g for g in abwab["groups"]}
    sections, current, rows = [], None, []

    def flush():
        if current is None:
            return
        g = groups[current]
        sections.append(f'<section><h3>{ar(g["label_ar"]["value"])} <span class="en">{esc(g["label_en"])} · {g["count"]}</span></h3><div class="rows">{"".join(rows)}</div></section>')

    for b in abwab["abwab"]:
        if b["group"] != current:
            flush(); current = b["group"]; rows = []
        w, m = b["wazn"], b["mawzun"]
        masdar = "، ".join(x["value"] for x in m.get("masdar", []))
        west = []
        for x in b["western"]:
            cls = "form ten" if x["value"] in TEN else "form"
            note = {"exact": "", "vowel-class": "", "subsumed": " <span class=\"rel\">not numbered separately</span>", "model-verb": " <span class=\"rel\">Wright’s place for this verb</span>"}[x["relation"]]
            west.append(f'<span class="{cls}">{x["value"]}</span>{note}')
        st = statuses({k: b[k] for k in ("wazn", "mawzun", "examples")} | {"bina": b["bina"]["ar"]})
        status = "source-verified" if st == {"source-verified"} else "draft" if st == {"draft"} else "partly checked"
        page = w["past"]["src"][0]["loc"]
        rows.append(
            f'<article class="row" id="bab-{b["number"]}">'
            f'<div class="n">{b["number"]}</div>'
            f'<div class="pat">{ar(w["past"]["value"] + " " + w["imperfect"]["value"], "big")}'
            f'<div class="model">{ar(m["past"]["value"] + " " + m["imperfect"]["value"])}{" · " + ar(masdar) if masdar else ""}</div>'
            f'<div class="use">{ar(b["bina"]["ar"]["value"])} <span class="en">{esc(b["bina"].get("en", ""))}</span></div></div>'
            f'<div class="meta"><div>{" ".join(west)}</div>'
            f'<div class="src">{esc(page)} · <span class="st st-{status.split()[0]}">{STATUS_TEXT.get(status, status)}</span></div></div>'
            f'</article>')
    flush()

    DIA = set("\u064b\u064c\u064d\u064e\u064f\u0650\u0652\u0670")
    def letters(word):  # letters of the past form; a doubled letter counts twice
        return sum(2 if ch == "\u0651" else 1 for ch in word if ch not in DIA) - word.count("\u0651")
    def col(gid):
        return "mulhaq" if gid.startswith("mulhaq") else "rubai" if gid.startswith("rubai") else "thulathi"
    viz = {"ui": UI, "abwab": [{
        "n": b["number"], "col": col(b["group"]), "letters": letters(b["wazn"]["past"]["value"]),
        "past": b["wazn"]["past"]["value"], "impf": b["wazn"]["imperfect"]["value"],
        "model": b["mawzun"]["past"]["value"], "modelImpf": b["mawzun"]["imperfect"]["value"],
        "masdar": "، ".join(x["value"] for x in b["mawzun"].get("masdar", [])),
        "use": b["bina"]["ar"]["value"], "group": groups[b["group"]]["label_ar"]["value"],
        "forms": [{"id": x["value"], "ten": x["value"] in TEN} for x in b["western"]],
        "ten": any(x["value"] in TEN and x["relation"] in ("exact", "vowel-class") for x in b["western"]),
        "page": b["wazn"]["past"]["src"][0]["loc"]} for b in abwab["abwab"]]}
    shape = {}
    for v in viz["abwab"]:
        shape[(v["col"], v["letters"])] = shape.get((v["col"], v["letters"]), 0) + 1
    expected = {("thulathi", 3): 6, ("thulathi", 4): 3, ("thulathi", 5): 5, ("thulathi", 6): 4, ("rubai", 4): 1, ("rubai", 5): 1,
                ("rubai", 6): 2, ("mulhaq", 4): 6, ("mulhaq", 5): 5, ("mulhaq", 6): 2}
    assert shape == expected, shape
    data = json.dumps(viz, ensure_ascii=False).replace("</", "<\\/")

    return TEMPLATE.replace("{{DATA}}", data).replace("{{TILES}}", "".join(tiles)).replace("{{SECTIONS}}", "\n".join(sections)).replace("{{COMMIT}}", commit)


TEMPLATE = """<!doctype html>
<!-- Generated by tools/build_abwab.py from openarabee-core. Do not edit by hand. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The 35 abwāb and the ten Forms · OpenArabee</title>
<meta name="description" content="All 35 verb patterns (abwāb) of Matn al-Bināʾ with their model verbs, set beside the Western numbered Forms, each with its page reference and verification status.">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
<link rel="icon" href="assets/icon-32.png" sizes="32x32" type="image/png">
<style>
  :root { color-scheme: light; --navy:#0A2A45; --gold:#C29A52; --gold-deep:#8A6A2C; --paper:#FBF8F1; --card:#FFFFFF; --rule:#E6DECB; --soft:#46586A; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--paper); color:var(--navy); font:1.0625rem/1.6 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; }
  .wrap { max-width:52rem; margin:0 auto; padding:0 1.5rem 3rem; }
  header { padding:2.5rem 0 0; }
  header img { display:block; width:min(13rem,60%); height:auto; }
  h1 { margin:2.2rem 0 0; font:400 clamp(1.9rem,5.5vw,2.6rem)/1.15 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif; text-wrap:balance; }
  h2 { margin:3rem 0 .3rem; font:400 1.6rem/1.2 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif; }
  h3 { margin:2.4rem 0 .6rem; font-size:1.35rem; font-weight:400; display:flex; flex-wrap:wrap; align-items:baseline; gap:.3rem .9rem; }
  p { margin:.9rem 0 0; color:var(--soft); max-width:43rem; }
  .ar { font-family:"Amiri","Scheherazade New","Noto Naskh Arabic","Geeza Pro","Traditional Arabic","Times New Roman",serif; }
  .ar.big { font-size:1.75rem; line-height:1.5; }
  .en { font:.8125rem/1.4 system-ui,sans-serif; letter-spacing:.03em; color:var(--gold-deep); }
  a { color:var(--navy); text-decoration-color:var(--gold); text-underline-offset:.2em; }
  a:focus-visible { outline:2px solid var(--gold); outline-offset:3px; border-radius:4px; }
  .tiles { display:grid; grid-template-columns:repeat(5,1fr); gap:.6rem; margin-top:1.2rem; direction:ltr; }
  .tile { display:flex; flex-direction:column; align-items:center; padding:.6rem .3rem .7rem; background:var(--card); border:1px solid var(--rule); border-radius:.6rem; text-decoration:none; }
  .tile:hover { border-color:var(--gold); }
  .tile .num { font:600 .8125rem/1 system-ui,sans-serif; color:#fff; background:var(--navy); border-radius:999px; padding:.25rem .55rem; }
  .tile .sub { font-size:.75rem; color:var(--soft); }
  .rows { background:var(--card); border:1px solid var(--rule); border-radius:.75rem; }
  .row { display:grid; grid-template-columns:2.4rem 1fr auto; gap:.2rem 1rem; padding:.8rem 1.1rem; border-top:1px solid var(--rule); scroll-margin-top:1rem; }
  .row:first-child { border-top:0; }
  .row:target { background:#FBF3E0; }
  .n { font:400 1.3rem/2.4rem "Iowan Old Style",Palatino,Georgia,serif; color:var(--gold-deep); }
  .model { font-size:1.2rem; color:var(--soft); }
  .use { margin-top:.15rem; font-size:1.05rem; }
  .use .en { display:block; letter-spacing:0; color:var(--soft); }
  .meta { text-align:right; font-size:.8125rem; color:var(--soft); display:flex; flex-direction:column; justify-content:space-between; gap:.4rem; min-width:9.5rem; }
  .form { display:inline-block; font:600 .8125rem/1 system-ui,sans-serif; padding:.28rem .55rem; border-radius:999px; border:1px solid var(--navy); color:var(--navy); }
  .form.ten { background:var(--navy); color:#fff; }
  .rel { display:block; margin:.15rem 0 .3rem; }
  .st-source-verified { color:#2F6B3A; } .st-draft, .st-partly { color:var(--gold-deep); }
  .legend { font-size:.9375rem; }
  #viz-section h2 { font-family:"Amiri","Scheherazade New","Noto Naskh Arabic","Geeza Pro","Traditional Arabic","Times New Roman",serif; font-size:1.9rem; }
  .vizp { font-size:1.25rem; line-height:1.9; color:var(--navy); }
  .vizbar { display:flex; flex-wrap:wrap; align-items:center; gap:.6rem 1rem; margin-top:1rem; }
  #viz-ten { font:inherit; font-size:1rem; padding:.35rem .9rem; border-radius:999px; border:1px solid var(--navy); background:var(--card); color:var(--navy); cursor:pointer; }
  #viz-ten[aria-pressed="true"] { background:var(--navy); color:#fff; }
  #viz-ten:focus-visible { outline:2px solid var(--gold); outline-offset:3px; }
  .vizhint { font-size:.9375rem; color:var(--soft); }
  #viz { margin-top:.8rem; aspect-ratio:1.08; max-height:46rem; width:100%; background:var(--card); border:1px solid var(--rule); border-radius:.75rem; overflow:hidden; }
  #viz canvas { display:block; width:100%; height:100%; cursor:grab; }
  #viz-detail { margin-top:.8rem; padding:.9rem 1.1rem; background:var(--card); border:1px solid var(--rule); border-radius:.75rem; min-height:4rem; }
  .d-num { font-size:1rem; color:var(--gold-deep); }
  .d-pat { font-size:2.2rem; line-height:1.5; }
  .d-model, .d-use { font-size:1.3rem; line-height:1.7; }
  .d-foot { display:flex; flex-wrap:wrap; align-items:center; gap:.5rem .8rem; margin-top:.5rem; font-size:.9375rem; }
  .en-note { font-size:.9375rem; }
  footer { margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--rule); font-size:.9375rem; color:var(--soft); }
  @media (max-width:40rem) {
    .tiles { grid-template-columns:repeat(2,1fr); }
    .row { grid-template-columns:2rem 1fr; }
    .meta { grid-column:2; text-align:left; flex-direction:row; flex-wrap:wrap; align-items:center; min-width:0; }
    .rel { display:inline; margin:0; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header><a href="./"><img src="assets/logo.svg" alt="OpenArabee" width="517" height="110"></a></header>
  <main>
    <h1>The 35 abwāb and the ten Forms</h1>
    <p>The classical primer <i>Matn Bināʾ al-afʿāl</i> sorts the Arabic verb into 35 patterns (<i>abwāb</i>), each with a model verb. Western grammars number the patterns as Forms. This page sets the two side by side. Every row gives the page of the printed source, and says how far it has been checked.</p>

    <section id="viz-section" lang="ar" dir="rtl">
      <h2 class="ar">البناء كلّه في نظرة واحدة</h2>
      <p class="ar vizp">كلّ بطاقة بابٌ من الأبواب الخمسة والثلاثين: الوزن وتحته موزونه. الطابق يدلّ على عدد حروف الماضي، من ثلاثة أحرف في الأسفل إلى ستة في الأعلى، فكلّما صعدت طابقًا زاد الفعل حرفًا. والأعمدة ثلاثة: الثلاثي، والرباعي، وبينهما الملحق بالرباعي. قال صاحب المتن: «معنى الإلحاق اتحاد المصدرين» (ص ٥٦٥).</p>
      <div class="vizbar">
        <button type="button" id="viz-ten" aria-pressed="false">أظهر الأوزان العشرة</button>
        <span class="vizhint">اسحب للتدوير · انقر بطاقة لتفاصيلها</span>
      </div>
      <div id="viz"></div>
      <div id="viz-detail" aria-live="polite"><div class="d-num">انقر بطاقة في البناء.</div></div>
      <p class="en-note" lang="en" dir="ltr">Each card is one of the 35 abwāb. The floor is the number of letters of the past form (three at the bottom, six at the top); the columns are triliteral, attached (mulḥaq) and quadriliteral verbs. Dark cards are the ten Forms. The same content is in the list below.</p>
    </section>
    <script type="application/json" id="abwab-data">{{DATA}}</script>
    <script type="importmap">{"imports": {"three": "./assets/vendor/three.module.js"}}</script>
    <script type="module" src="assets/abwab3d.js"></script>

    <h2>The ten Forms <span class="ar" lang="ar" dir="rtl">الأوزان العشرة</span></h2>
    <p class="legend">Forms I to X after Wright’s <i>Grammar</i>, each linked to its place among the abwāb. Form I covers the first six abwāb, which differ only in their vowels.</p>
    <div class="tiles">{{TILES}}</div>

    <h2>All 35 abwāb</h2>
    <p class="legend">Each row: the pattern, then the model verb with its verbal noun, then what the text says the pattern is used for. On the right the Western Form (<span class="form ten">I</span> to <span class="form ten">X</span> are the ten Forms above; <span class="form">XI</span> and beyond are the rare and the four-letter Forms), the page in the 1949 Cairo printing, and the status.</p>
{{SECTIONS}}
  </main>
  <footer>
    Source of the abwāb: <i>Matn Bināʾ al-afʿāl</i>, in <i>Majmūʿ muhimmāt al-mutūn</i>, 4th printing, Cairo 1369/1949. Forms: Wright, <i>A Grammar of the Arabic Language</i>, 3rd ed., vol. I, §35 and §68. “Checked against the print” means compared with the page images by an AI model and confirmed by a second copy of the text; no expert has reviewed the table yet. The Western column is still a draft.
    Generated from <a href="https://github.com/OpenArabee/openarabee-core/tree/main/reference">the reference tables</a> (version {{COMMIT}}). Data: <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.
    <a href="https://github.com/OpenArabee/openarabee-core/issues/new/choose">Suggest a correction</a>.
  </footer>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    core = Path(sys.argv[1]) if len(sys.argv) > 1 else WEB.parent / "openarabee-core"
    (WEB / "abwab.html").write_text(build(core), encoding="utf-8")
    print("wrote abwab.html")
