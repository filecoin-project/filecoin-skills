#!/usr/bin/env python3
"""Reconcile the engram library: merge Filecoin-observed piece state into a
sync preview -- never the real catalog directly.

Usage:
  reconcile.py <shares.json> <observed.json> <scope>   # compute + write preview only
  reconcile.py --apply <shares.json>                   # apply the existing preview
  reconcile.py --selftest

scope is "verify" (only data sets already named by the catalog were checked) or
"discover" (every data set the active wallet owns was enumerated).

observed.json is a JSON object built by the calling skill from filecoin-pin's
`data-set piece-status` / `data-set show` output (the CLI has no JSON mode, so
the agent parses the labeled text first):
  {"checkedDatasetIds": [int, ...], "pieces": [
    {"rootCid": str, "pieceCid": str, "name": str, "datasetId": int,
     "providerId": int|null, "sourceValue": str, "network": str}, ...
  ]}
checkedDatasetIds is the full set of data-set IDs this check actually
inspected, computed by the skill BEFORE any piece-status call (verify: every
data-set ID already named by the catalog; discover: every ID from `data-set
ls --all`) -- never inferred from which pieces turned out to be active. A
data set that was checked but reported zero pieces for a record still
belongs in checkedDatasetIds, so that record correctly degrades instead of
silently staying stale forever.

Field-level authority: Filecoin owns pieceCid, datasets, copy count, and
live/removal state. The local catalog owns file, date, note, files, and shape
-- reconcile never touches those for an existing record. A catalog record
whose rootCid is missing from every dataset the check covered is never
deleted or downgraded; it is flagged via `lastCheck` so the renderer can
surface it under Attention, and its note is left exactly as the user wrote it.

Recovered records (rootCid observed on a KNOWN source, no matching catalog
record) are appended with `catalogSource: "filecoin"` and `recoveredAt`; date
is omitted rather than invented -- the renderer must not fabricate one.
Pieces on an UNKNOWN source (discover scope only) are excluded from the
catalog entirely and returned separately for the scratch file.

Known sources = "engram-share" plus any sourceValue already observed on a
dataset ID that appears in an existing record's `datasets` array.

Two-stage by design, no exceptions: the first call NEVER writes shares.json,
not even for a single small change. It writes the full candidate result to
`.sync-preview.json` in the ledger directory so the skill can render and show
it before anything touches the real catalog. Only `--apply` (run after the
user has seen the preview and said yes) backs up shares.json and atomically
replaces it with the preview's content.
"""
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

KNOWN_BASE_SOURCES = {"engram-share"}


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def reconcile(catalog, pieces, checked_dataset_ids, scope, now=None):
    """Pure merge: returns (new_catalog, scratch_unknown, summary). No I/O."""
    now = now or _now_iso()
    catalog = [dict(r) for r in catalog]  # copy each record so the merge never mutates the caller's list
    by_root = {r["rootCid"]: r for r in catalog}
    checked_dataset_ids = set(checked_dataset_ids)
    known_dataset_ids = {d for r in catalog for d in (r.get("datasets") or [])}
    known_sources = set(KNOWN_BASE_SOURCES)
    for p in pieces:
        if p.get("datasetId") in known_dataset_ids and p.get("sourceValue"):
            known_sources.add(p["sourceValue"])

    pieces_by_root = {}
    for p in pieces:
        pieces_by_root.setdefault(p["rootCid"], []).append(p)

    matched, updated, recovered, not_found = [], [], [], []
    scratch = []

    for root_cid, record in by_root.items():
        existing_datasets = set(record.get("datasets") or [])
        checked_existing = existing_datasets & checked_dataset_ids
        if not checked_existing:
            continue  # this check never touched any dataset this record names
        live_ids = {p["datasetId"] for p in pieces_by_root.get(root_cid, [])}
        merged = sorted((existing_datasets - checked_dataset_ids) | (live_ids & checked_dataset_ids))
        if not merged:
            record["lastCheck"] = {"at": now, "status": "not_found"}
            not_found.append(root_cid)
            continue
        changed = merged != sorted(existing_datasets)
        record["datasets"] = merged
        if not record.get("pieceCid"):
            pc = next((p["pieceCid"] for p in pieces_by_root.get(root_cid, []) if p.get("pieceCid")), None)
            if pc:
                record["pieceCid"] = pc
                changed = True
        record["lastCheck"] = {"at": now, "status": "ok"}
        (updated if changed else matched).append(root_cid)

    for root_cid, ps in pieces_by_root.items():
        if root_cid in by_root:
            continue
        piece = ps[0]
        source = piece.get("sourceValue") or ""
        if source not in known_sources:
            scratch.append(piece)
            continue
        new_record = {
            "file": piece.get("name") or "",
            "date": None,
            "rootCid": root_cid,
            "pieceCid": piece.get("pieceCid"),
            "datasets": sorted({p["datasetId"] for p in ps}),
            "network": piece.get("network") or "mainnet",
            "note": "",
            "catalogSource": "filecoin",
            "dataSetSource": source,
            "recoveredAt": now,
        }
        catalog.append(new_record)
        by_root[root_cid] = new_record
        recovered.append(root_cid)

    summary = {
        "scope": scope,
        "at": now,
        "matched": len(matched),
        "updated": len(updated),
        "recovered": len(recovered),
        "attentionNotFound": not_found,
        "unknownSourcePieces": len(scratch),
    }
    return catalog, scratch, summary


def _backup(shares_path):
    ledger_dir = os.path.dirname(os.path.abspath(shares_path))
    backups_dir = os.path.join(ledger_dir, ".backups")
    os.makedirs(backups_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = os.path.join(backups_dir, f"shares-{stamp}.json")
    shutil.copy2(shares_path, dest)
    return dest


def _atomic_write(path, data):
    dir_ = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".shares-", suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _preview_path(shares_path):
    ledger_dir = os.path.dirname(os.path.abspath(shares_path))
    return os.path.join(ledger_dir, ".sync-preview.json")


def write_preview(shares_path, observed_path, scope):
    catalog = json.load(open(shares_path)) if os.path.exists(shares_path) else []
    observed = json.load(open(observed_path))
    new_catalog, scratch, summary = reconcile(
        catalog, observed["pieces"], observed["checkedDatasetIds"], scope
    )

    ledger_dir = os.path.dirname(os.path.abspath(shares_path))
    _atomic_write(_preview_path(shares_path), new_catalog)

    scratch_path = os.path.join(ledger_dir, ".discovery-scratch.json")
    if scope == "discover":
        _atomic_write(scratch_path, {"at": summary["at"], "pieces": scratch})
    elif os.path.exists(scratch_path):
        os.remove(scratch_path)  # a verify-scope run supersedes any stale discover scratch

    last_check_path = os.path.join(ledger_dir, ".last-check.json")
    _atomic_write(last_check_path, {"scope": scope, "at": summary["at"]})
    return summary


def main():
    summary = write_preview(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(summary, indent=2))


def apply_preview(shares_path):
    """Copy the sync preview over the real catalog. Only call this after the
    user has seen the rendered preview and explicitly said to keep it."""
    preview_path = _preview_path(shares_path)
    if not os.path.exists(preview_path):
        print(f"No sync preview found at {preview_path} -- run a check first.", file=sys.stderr)
        sys.exit(1)
    new_catalog = json.load(open(preview_path))
    if os.path.exists(shares_path):
        backup = _backup(shares_path)
    else:
        backup = None
    _atomic_write(shares_path, new_catalog)
    print(json.dumps({"applied": True, "records": len(new_catalog), "backup": backup}, indent=2))


def _selftest():
    catalog = [
        {"file": "a.html", "date": "2026-09-01", "rootCid": "rootA", "pieceCid": "pieceA",
         "datasets": [1, 2], "network": "mainnet", "note": ""},
        {"file": "b.html", "date": "2026-09-02", "rootCid": "rootB", "pieceCid": "pieceB",
         "datasets": [1, 2], "network": "mainnet", "note": ""},
        {"file": "c.html", "date": "2026-09-03", "rootCid": "rootC", "pieceCid": "",
         "datasets": [1], "network": "mainnet", "note": "DEGRADED 1/2"},
        {"file": "f.html", "date": "2026-08-20", "rootCid": "rootF", "pieceCid": "pieceF",
         "datasets": [2], "network": "mainnet", "note": ""},
    ]
    checked_dataset_ids = [1, 2, 9]
    pieces = [
        {"rootCid": "rootA", "pieceCid": "pieceA", "name": "a.html", "datasetId": 1,
         "providerId": 10, "sourceValue": "engram-share", "network": "mainnet"},
        {"rootCid": "rootA", "pieceCid": "pieceA", "name": "a.html", "datasetId": 2,
         "providerId": 20, "sourceValue": "engram-share", "network": "mainnet"},
        {"rootCid": "rootB", "pieceCid": "pieceB", "name": "b.html", "datasetId": 1,
         "providerId": 10, "sourceValue": "engram-share", "network": "mainnet"},
        # rootB missing from dataset 2 -> degraded, still 1 live copy
        {"rootCid": "rootD", "pieceCid": "pieceD", "name": "recovered.html", "datasetId": 1,
         "providerId": 10, "sourceValue": "engram-share", "network": "mainnet"},
        {"rootCid": "rootE", "pieceCid": "pieceE", "name": "unrelated.car", "datasetId": 9,
         "providerId": 90, "sourceValue": "some-other-app", "network": "mainnet"},
        # rootF omitted entirely: dataset 2 was checked and reported no piece for it at all
    ]
    new_catalog, scratch, summary = reconcile(
        catalog, pieces, checked_dataset_ids, "verify", now="2026-09-04T00:00:00Z"
    )
    by_root = {r["rootCid"]: r for r in new_catalog}

    assert by_root["rootA"]["datasets"] == [1, 2], "confirmed record keeps both copies"
    assert by_root["rootA"]["lastCheck"]["status"] == "ok"
    assert by_root["rootB"]["datasets"] == [1], "degraded to one live copy"
    assert "rootC" in [r["rootCid"] for r in new_catalog], "untouched record stays in the catalog"
    assert by_root["rootD"]["catalogSource"] == "filecoin", "known-source piece recovered"
    assert by_root["rootD"]["date"] is None, "never fabricate a date"
    assert "rootE" not in by_root, "unknown-source piece never enters the catalog"
    assert scratch and scratch[0]["rootCid"] == "rootE", "unknown-source piece goes to scratch"
    assert summary["matched"] == 1 and summary["updated"] == 1 and summary["recovered"] == 1

    # rootC's dataset 1 IS in this check's coverage but rootC never appears in the observed
    # pieces at all -> not found
    assert by_root["rootC"]["lastCheck"]["status"] == "not_found"
    assert by_root["rootC"]["note"] == "DEGRADED 1/2", "reconcile never rewrites the user's note"

    # Regression: dataset 2 was checked (it's in checked_dataset_ids) but reported zero pieces
    # for rootF at all -- coverage comes from the explicit checked_dataset_ids list, not from
    # which pieces happened to turn up, so this must flag as not_found, not be silently skipped.
    assert by_root["rootF"]["lastCheck"]["status"] == "not_found"
    assert by_root["rootF"]["datasets"] == [2], "not_found record's datasets left untouched"
    assert set(summary["attentionNotFound"]) == {"rootC", "rootF"}

    _selftest_preview_then_apply(catalog, checked_dataset_ids, pieces)


def _selftest_preview_then_apply(catalog, checked_dataset_ids, pieces):
    """Verifies the two-stage write behavior: write_preview() must never
    touch shares.json, and apply_preview() must be the only thing that does,
    with a backup first."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        shares_path = os.path.join(d, "shares.json")
        observed_path = os.path.join(d, "observed.json")
        original = json.dumps(catalog)
        with open(shares_path, "w") as f:
            f.write(original)
        with open(observed_path, "w") as f:
            json.dump({"checkedDatasetIds": checked_dataset_ids, "pieces": pieces}, f)

        write_preview(shares_path, observed_path, "verify")
        assert open(shares_path).read() == original, "preview must never touch shares.json"
        preview_path = _preview_path(shares_path)
        assert os.path.exists(preview_path), "preview file must be written"
        preview_catalog = json.load(open(preview_path))
        assert len(preview_catalog) == 5, "preview contains the merged result (4 existing + 1 recovered)"
        assert os.path.exists(os.path.join(d, ".last-check.json"))

        apply_preview(shares_path)
        applied = json.load(open(shares_path))
        assert len(applied) == 5, "apply copies the preview's content into shares.json"
        backups = os.listdir(os.path.join(d, ".backups"))
        assert len(backups) == 1, "apply backs up the pre-apply shares.json first"
        assert json.loads(open(os.path.join(d, ".backups", backups[0])).read()) == catalog, "backup matches pre-apply content"

    print("selftest OK")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
    elif len(sys.argv) > 1 and sys.argv[1] == "--apply":
        apply_preview(sys.argv[2])
    else:
        main()
