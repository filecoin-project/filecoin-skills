#!/usr/bin/env python3
"""Render the engram library: shares.json (+ optional .last-check.json,
.discovery-scratch.json) -> library.html.

Usage: render.py <shares.json> <library-template.html> <out.html>

Pure view over the local catalog -- makes no network calls and never mutates
shares.json. Categorizes each record into Current / Attention / History from
fields reconcile.py and engram-share already wrote (note text, datasets
count, lastCheck), so a stale library.html never claims a check that never
happened: the check-line only appears when .last-check.json exists.

Each table gets client-side search, a sortable date column, and pagination
via the static <script> in library-template.html; this script only needs to
emit `data-date` / `data-search` attributes and the `.table-wrap` markup the
script looks for.
"""
import base64
import html
import json
import os
import re
import sys

shares_path, template_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
ledger_dir = os.path.dirname(os.path.abspath(shares_path))
assets = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(template_path)), "..", "..", "assets"))

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def b64(name):
    return base64.b64encode(open(os.path.join(assets, name), "rb").read()).decode()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def categorize(record):
    note = (record.get("note") or "").upper()
    if "DELETED" in note or "SUPERSEDED" in note:
        return "history"
    n = len(record.get("datasets") or [])
    not_found = (record.get("lastCheck") or {}).get("status") == "not_found"
    if n < 2 or "DEGRADED" in note or not_found:
        return "attention"
    return "current"


def attention_reason(record):
    """Plain-language reason a record landed in Attention, mirroring
    categorize()'s exact triggers so the label can never disagree with the
    section it's shown in."""
    note = (record.get("note") or "").upper()
    n = len(record.get("datasets") or [])
    not_found = (record.get("lastCheck") or {}).get("status") == "not_found"
    reasons = []
    if not_found:
        reasons.append("not found in last Filecoin check")
    if n < 2:
        reasons.append(f"only {n} {'copy' if n == 1 else 'copies'}")
    if "DEGRADED" in note:
        reasons.append("marked degraded")
    return "; ".join(reasons) if reasons else "needs review"


def delete_date(note):
    """Best-effort delete/supersede date parsed straight out of the note text
    (e.g. "DELETED 2026-09-02", "superseded by ... (2026-09-04)"). Never
    fabricated -- an unparseable note just leaves this column blank."""
    m = DATE_RE.search(note or "")
    return m.group(0) if m else ""


def sort_key(record):
    return record.get("date") or ""  # missing date sorts first ascending -> last once reversed


def search_blob(record, extra=""):
    bits = [
        record.get("file") or "",
        record.get("note") or "",
        record.get("rootCid") or "",
        "synced from filecoin" if record.get("catalogSource") == "filecoin" else "local",
        " ".join(str(d) for d in (record.get("datasets") or [])),
        extra,
    ]
    return html.escape(" ".join(bits).lower())


def short_cid(cid):
    return f"{cid[:8]}\u2026{cid[-4:]}" if len(cid) > 14 else cid


def name_cell(record, show_date=True, extra_tag=""):
    raw_name = record.get("file")
    name = html.escape(raw_name) if raw_name else short_cid(record.get("rootCid", ""))
    if record.get("shape") == "bundle":
        n = record.get("fileCount") or len(record.get("files") or [])
        name = f'{name}/ <span class="copies">{n} files</span>'
    if record.get("catalogSource") == "filecoin":
        name = f'{name}<span class="tag">Recovered</span>'
    name = f"{name}{extra_tag}"
    meta_bits = []
    if show_date and record.get("date"):
        meta_bits.append(record["date"])
    meta_bits.append(
        "Catalog source: synced from Filecoin" if record.get("catalogSource") == "filecoin"
        else "Catalog source: local"
    )
    return f'<div class="file-cell">{name}<span class="meta">{" · ".join(meta_bits)}</span></div>'


def link_cell(record):
    cid = record.get("rootCid", "")
    if not cid:
        return ""
    short = short_cid(cid)
    return f'<a href="https://inbrowser.link/ipfs/{cid}" title="https://inbrowser.link/ipfs/{cid}">{short}</a>'


def trace_cell(record):
    piece = record.get("pieceCid")
    if not piece or record.get("network", "mainnet") != "mainnet":
        return ""
    n = len(record.get("datasets") or [])
    copies = f' <span class="copies">{n} {"copy" if n == 1 else "copies"}</span>' if n else ""
    return f'<a href="https://pdp.filecoin.cloud/mainnet/piece/{piece}">Trace this share</a>{copies}'


def data_source_value(record):
    if record.get("catalogSource") == "filecoin":
        return record.get("dataSetSource") or "filecoin"
    return "local"


def row_html(record, category):
    """Current / Attention row: File, Date, Link, Trace, Note. Date has its own
    column here, so name_cell leaves it out of the meta line to avoid showing
    it twice; History keeps it in the meta line since History's own date
    column shows something different (delete_date, below)."""
    cls = ' class="attention"' if category == "attention" else ""
    d = record.get("date") or ""
    reason = attention_reason(record) if category == "attention" else ""
    extra_tag = f'<span class="tag warn">{html.escape(reason)}</span>' if reason else ""
    return (
        f'<tr{cls} data-date="{d}" data-source="{html.escape(data_source_value(record))}" '
        f'data-search="{search_blob(record, extra=reason)}">'
        f"<td>{name_cell(record, show_date=False, extra_tag=extra_tag)}</td><td>{html.escape(d)}</td>"
        f"<td>{link_cell(record)}</td><td>{trace_cell(record)}</td>"
        f'<td>{html.escape(record.get("note") or "")}</td></tr>'
    )


def history_row_html(record):
    """History row: File, Delete date, Note -- no Link/Trace, the share is gone."""
    note = record.get("note") or ""
    d = delete_date(note)
    return (
        f'<tr class="history" data-date="{d}" data-source="{html.escape(data_source_value(record))}" '
        f'data-search="{search_blob(record)}">'
        f"<td>{name_cell(record)}</td><td>{d}</td>"
        f'<td>{html.escape(note)}</td></tr>'
    )


def table_wrap(title, records, category):
    if not records:
        return ""
    records = sorted(records, key=sort_key, reverse=True)
    if category == "history":
        rows = "\n".join(history_row_html(r) for r in records)
        date_header = "Delete date"
        head = f"<tr><th>File</th><th class=\"sortable\" data-sort=\"date\">{date_header} <span class=\"sort-indicator\">\u21c5</span></th><th>Note</th></tr>"
        no_match = '<tr class="no-match" style="display:none"><td colspan="3">No items.</td></tr>'
        table_class = "history-table"
    else:
        rows = "\n".join(row_html(r, category) for r in records)
        head = (
            "<tr><th>File</th><th class=\"sortable\" data-sort=\"date\">Date <span class=\"sort-indicator\">\u21c5</span></th>"
            "<th>Link</th><th>Trace</th><th>Note</th></tr>"
        )
        no_match = '<tr class="no-match" style="display:none"><td colspan="5">No items.</td></tr>'
        table_class = "rows-table"
    return (
        f'<h2 class="section">{title} <span class="count">{len(records)}</span></h2>\n'
        '<div class="table-wrap">\n'
        f'<table class="{table_class}"><thead>{head}</thead>\n'
        f"<tbody>\n{rows}\n{no_match}\n</tbody></table>\n"
        '<div class="pager"><button class="prev">‹ Prev</button>'
        '<span class="pageinfo"></span><button class="next">Next ›</button></div>\n'
        "</div>"
    )


def discovery_section_html(scratch):
    pieces = scratch.get("pieces") or []
    if not pieces:
        return ""
    by_source = {}
    for p in pieces:
        by_source.setdefault(p.get("sourceValue") or "unknown", []).append(p)
    parts = [
        "<div class=\"discovery\">",
        '<h2 class="section">Other Filecoin storage</h2>',
        "<p>Data sets the active wallet owns that this library does not manage. "
        "Nothing here was added to the catalog automatically.</p>",
    ]
    for source, items in sorted(by_source.items()):
        rows = "\n".join(
            f'<tr><td>{html.escape(p.get("name") or p.get("rootCid",""))}</td>'
            f'<td>data set {p.get("datasetId")}</td><td>{html.escape(source)}</td></tr>'
            for p in items
        )
        parts.append(
            f"<h3>{html.escape(source)}</h3><table><thead><tr><th>Name</th><th>Data set</th>"
            f"<th>Data-set source</th></tr></thead><tbody>\n{rows}\n</tbody></table>"
        )
    parts.append("</div>")
    return "\n".join(parts)


shares = load_json(shares_path, [])
last_check = load_json(os.path.join(ledger_dir, ".last-check.json"), None)
scratch = load_json(os.path.join(ledger_dir, ".discovery-scratch.json"), {})

buckets = {"current": [], "attention": [], "history": []}
for record in shares:
    buckets[categorize(record)].append(record)

sections = "\n".join(
    part for part in (
        table_wrap("Current", buckets["current"], "current"),
        table_wrap("Attention", buckets["attention"], "attention"),
        table_wrap("History", buckets["history"], "history"),
    )
    if part
) or "<p>No shares yet. Use engram-share to create one.</p>"

is_preview = os.path.basename(shares_path) == ".sync-preview.json"

if is_preview:
    if last_check:
        scope_label = "Verify catalog" if last_check["scope"] == "verify" else "Discover wallet"
        check_line = f"Preview of a {scope_label} run · {last_check['at']} · not yet applied to your library"
    else:
        check_line = "Preview of the last Filecoin check · not yet applied to your library"
    sync_button = (
        '<button class="sync-btn" id="syncBtn" data-copy="merge my Filecoin sync into my engram library">'
        '\U0001f501 Copy prompt: \u201cmerge my Filecoin sync into my engram library\u201d'
        '</button>'
    )
else:
    if last_check:
        scope_label = "Verified against Filecoin" if last_check["scope"] == "verify" else "Discovered from wallet"
        check_line = f"{scope_label} \u00b7 last checked {last_check['at']}"
    else:
        check_line = "Not checked against Filecoin yet — showing the local catalog."
    sync_button = (
        '<button class="sync-btn" id="syncBtn" data-copy="check my shares on Filecoin">'
        '\U0001f4cb Copy prompt: \u201ccheck my shares on Filecoin\u201d'
        '</button>'
    )

tpl = open(template_path).read()
tpl = (
    tpl.replace("{{SATOSHI_B64}}", b64("Satoshi-Variable.ttf"))
    .replace("{{ROSE_B64}}", b64("rose.png"))
    .replace("{{WASH_B64}}", b64("wash.png"))
    .replace("{{LOGO_B64}}", b64("engram-mark-transparent.png"))
    .replace("{{CHECK_LINE}}", check_line)
    .replace("{{SYNC_BUTTON}}", sync_button)
    .replace("{{SECTIONS}}", sections)
    .replace("{{DISCOVERY_SECTION}}", discovery_section_html(scratch))
)
open(out_path, "w").write(tpl)
print(
    f"rendered {len(buckets['current'])} current / {len(buckets['attention'])} attention / "
    f"{len(buckets['history'])} history -> {out_path}"
)
