---
name: engram-library
status: beta
description: Use when the user wants to browse, list, or search what they've shared with engram-share, or says "show my engram shares", "show my library", "open my engrams", "what have I shared", "list all shares"; also when they want to check that against Filecoin itself — "check my shares on Filecoin", "verify my engrams", "is this still stored", "discover my wallet's Filecoin storage", "rebuild my library from chain", "find pieces I lost track of". Storage-read-only: renders and reconciles the local catalog, never adds, removes, repairs, or funds anything.
---

# engram-library

> **Beta.** Show mode is verified against a real ledger. Verify catalog / Discover wallet / Apply sync are verified only by construction (selftest + a cold dry run), never yet end-to-end against the live `filecoin-pin` CLI with a funded wallet — say so before running any of those three for the first time.

Renders `~/.engram/shares.json` (the share ledger `engram-share` writes — see `../engram-share/CONTEXT.md`) into a browsable `~/.engram/library.html`, and can check that ledger against Filecoin itself. Two skills, one file: this one only ever reads and reconciles the ledger; only `engram-share` ever adds, repairs, or removes a share. See `../CONTEXT.md` for suite-shared terms and `CONTEXT.md` for this skill's own language (Catalog source, Verify catalog, Discover wallet, Current/Attention/History).

## Red lines

- Never call `add`, `import`, `rm`, `data-set terminate`, or any `payments` command — every CLI call this skill makes is an inspection (Storage-read-only).
- Never write `~/.engram/shares.json` directly from a check — every merge lands in `~/.engram/.sync-preview.json` first, no exceptions for small changes (step 4).
- Never run `reconcile.py --apply` without the user's explicit yes to the rendered preview (step 5).
- Never invent a date, note, or file list for a recovered record — carry only what Filecoin can prove (step 4).
- Never merge an unknown-source piece into the preview — list it separately, always (step 4).
- Never rewrite a ledger record's `note`, `file`, `date`, `files`, or `shape` during a check — those are `engram-share`'s fields (step 4).
- Never delete or downgrade a ledger record because a check didn't find it — flag it, never remove it (step 4).
- Always back up `shares.json` before applying, every apply, no exceptions (step 5).
- Never resolve a wallet address and run a check silently — say which address is in play, or ask for one, before every Verify/Discover run (step 1).

## Choosing the mode

Four things this skill can do, from four different phrasings:

- **Show** (default, and by far the most common ask): bare "show/open/search my engram shares (or library)", "what have I shared", "list all shares". Local-only, no CLI, no credentials, seconds. Go to step 2.
- **Verify catalog**: "check/verify/refresh my shares on Filecoin", "is X still stored", "confirm my shares are actually there". Checks only the data sets the ledger already names. Go to step 3.
- **Discover wallet**: "discover/rebuild my library from chain", "find pieces I lost track of", "what does my wallet actually hold on Filecoin". Enumerates every data set the active wallet owns, not just the ledger's own. Go to step 3, with the wider scope noted there.
- **Apply sync**: "merge my Filecoin sync into my engram library", "apply that preview", "merge with local" — the sync-preview page's own button copies the first phrase verbatim. Skip straight to step 5 if `~/.engram/.sync-preview.json` exists and is recent; if it's missing or clearly stale, say so and offer to run Verify catalog first instead of applying nothing meaningful.

If the phrasing is ambiguous, default to Show — it costs nothing to run and the user can ask for a check next.

## 1. Preflight (verify/discover only)

Show needs none of this. `command -v filecoin-pin`; missing → `npm install -g filecoin-pin` (Node 24+). `../engram-share/references/filecoin-pin-cli.md` is the CLI reference this skill also reads; if `filecoin-pin --version` doesn't match its "verified against" line, that's `engram-share`'s file to regenerate (its step 1), not this skill's — flag it and continue, the flags this skill needs (`data-set ls`, `data-set show`, `data-set piece-status`) are stable across recent versions.

**Auth, read-only and transparent:** this skill only ever calls inspection subcommands, so prefer `--view-address <address>` — it inspects an account without touching key material at all, and it's the only auth mode this skill should ever need. Resolve it in this order, and always tell the user which address is in play before running a check — never resolve and proceed silently:

1. **Already configured** — check in the same precedence `filecoin-pin` itself uses (`../engram-share/references/filecoin-pin-cli.md`'s Precedence note) plus `engram-share`'s own file set (its Keys/Workflow section): explicit `SESSION_KEY`+`WALLET_ADDRESS` or `PRIVATE_KEY` env vars, then `~/.filecoin-session-key.env` (carries its own `WALLET_ADDRESS`), then `~/.engram.env` / `~/.filecoin-pin.env` / `~/.filecoin.env` in that order (each just a bare `PRIVATE_KEY`). Check only with boolean/count tests (`test -f`, `grep -qE '^(export )?PRIVATE_KEY='`) — never read file contents (Secrets handling). Once a source resolves, derive the address with one `filecoin-pin payments status` call for a bare `PRIVATE_KEY`, or read `WALLET_ADDRESS` straight out of `~/.filecoin-session-key.env`. Found one → say so plainly, address masked per `../engram-share/SKILL.md`'s Keys section (`0x1234…6789`, never the full address in chat): "Using the wallet already configured for engram-share: 0x1234…6789 — say if that's wrong."
2. **Nothing configured** — ask, don't fall through: "I don't have a wallet configured yet. Give me a public address to inspect (view-only, no key needed), or set up `~/.filecoin-pin.env` yourself if you'd rather I use a stored key." Wait for their answer.

Once an address is known (either way), use `--view-address` for every call this skill makes. Never reach for a signing-capable key just because the inspection commands would technically accept one — a user-supplied public address is the preferred path even when a signing key exists elsewhere.

## 2. Show

Read `~/.engram/shares.json` (create nothing if it's missing or `[]` — say "no shares yet, use engram-share to create one" and stop). Run:

```bash
python3 <skill-dir>/render.py ~/.engram/shares.json <skill-dir>/library-template.html ~/.engram/library.html
```

Report the path (open it in a browser tab if the harness has one) and render.py's own summary line in plain language — "42 current, 4 need attention, 10 in history" reads better than a bare row count. Done; no further steps.

The library itself is interactive without needing another agent turn: each section has a search box, a sortable Date (or Delete date) column, and pagination once it has more than 8 rows — all client-side, no server. A "Check against Filecoin" button sits next to the check-line; the page can't reach an agent on its own, so clicking it only copies the trigger phrase to the clipboard for the user to paste — mention this once so a user who opens the file directly (not through an agent) knows the live check exists and how to reach it.

## 3. Verify catalog / Discover wallet

Both checks build the same kind of observed-pieces list and end at the same preview (step 4). They differ only in scope, and both start by fixing the exact set of data-set IDs this check covers — before any piece-status call runs, not inferred afterward from whatever turns up:

**Verify catalog** — the checked-ID set is the distinct data-set IDs already in every ledger record's `datasets` array. For each one, run `filecoin-pin data-set show <id>` once (provider ID, the data-set's `source` metadata value) and `filecoin-pin data-set piece-status <id>` once (every active piece: its `name` and `ipfsRootCID` metadata, per the CLI reference's data-set section, plus the Piece CID). Run these in parallel across IDs — nothing here needs to be sequential.

**Discover wallet** — the checked-ID set is every data-set ID from `filecoin-pin data-set ls --all` (not just the ledger's IDs), then the same `show` + `piece-status` pair per ID as above.

The CLI has no JSON output (see the reference's "No JSON output" section) — parse the labeled lines yourself. Build one JSON object with the checked-ID set plus one piece entry per active piece observed, shaped exactly:

```json
{"checkedDatasetIds": [1548, 1549], "pieces": [
  {"rootCid": "...", "pieceCid": "...", "name": "...", "datasetId": 1548, "providerId": 32, "sourceValue": "engram-share", "network": "mainnet"}
]}
```

`checkedDatasetIds` must include every ID this check touched, even one that came back with zero active pieces — a data set that was checked and is now empty is exactly the "is this still stored" case reconcile.py needs to flag, and it can only do that if the ID says "checked" independent of what pieces happened to show up.

Write it to a scratch file (anywhere under `/tmp`, discarded after step 4) and call:

```bash
python3 <skill-dir>/reconcile.py ~/.engram/shares.json <observed.json> verify   # or: discover
```

## 4. Preview the result — never write the ledger directly

This step never touches `~/.engram/shares.json`. Not for one small change, not for a hundred — the merge always lands in a preview first, and only step 5 (on the user's yes) can touch the real ledger. Read this section before explaining anything to the user; it's the field-level authority contract, not just an implementation detail.

`reconcile.py` computes what the merge WOULD produce and writes the full candidate catalog to `~/.engram/.sync-preview.json` — never to `shares.json`. Filecoin owns `pieceCid`, `datasets`, copy count, and live/removed state for every record whose data set(s) this check covered; the local catalog owns `file`, `date`, `note`, `files`, and `shape` — the merge never touches those, so a `DEGRADED 1/2` or `superseded by...` note the user wrote stays exactly as written even after a check confirms or contradicts it. A record whose Root CID never showed up in anything this check covered gets `lastCheck.status: "not_found"` and stays in the catalog, never deleted or downgraded. A record a check never touched at all (its data sets were outside this check's scope) is left completely alone.

A Root CID observed on a **known** data-set source (`engram-share`, or any source value already implied by a data set the ledger already names) with no matching ledger record becomes a **recovered record**: `file` from the piece's `name` metadata (or the bare Root CID when no name was ever set — bulk/programmatic uploads often skip it, and that's a real, expected shape, not a parsing bug), `rootCid`/`pieceCid`/`datasets` from what was observed, `catalogSource: "filecoin"`, `recoveredAt` set — `date` is left `null`, never invented. A Root CID on an **unknown** source (discover only — verify's scope is by construction always known) never enters the preview at all; `reconcile.py` writes it to `~/.engram/.discovery-scratch.json` instead.

Render the preview so the user can actually see it before deciding anything:

```bash
python3 <skill-dir>/render.py ~/.engram/.sync-preview.json <skill-dir>/library-template.html ~/.engram/sync-preview.html
```

`reconcile.py` prints a JSON summary (`matched`, `updated`, `recovered`, `attentionNotFound`, `unknownSourcePieces`) — read it, then report in plain language: how many confirmed, how many recovered (name the ones with real names; if most of a large recovered batch have no name at all, say so plainly rather than listing bare CIDs), how many need attention and why, and — discover only — how many pieces exist on sources the library doesn't manage. **A recovered count that dwarfs the current ledger size is a signal to slow down, not a reason to auto-apply** — say so, and let step 5 be the user's real decision, not a formality.

## 5. Apply — 🔴 CHECKPOINT: only on explicit yes

🔴 **STOP before running `--apply`.** Ask plainly: "Apply these changes to your library?" Wait for a real yes — not silence, not a prior "sounds good" about something else, not an inferred yes from ambiguous phrasing. Then:

```bash
python3 <skill-dir>/reconcile.py --apply ~/.engram/shares.json
```

This backs up the current ledger to `~/.engram/.backups/shares-<UTC-timestamp>.json`, then replaces `shares.json` with the preview's content via a temp file and atomic rename — a crash mid-write can never corrupt the ledger. `~/.engram/.last-check.json` was already written in step 4, so the library's header already says truthfully whether and when a check ran; nothing extra to do for that here. Regenerate the real view exactly as in step 2 and tell the user it's applied.

**If the user says no** (or only wants part of it — reconcile.py applies the whole preview, all-or-nothing, no partial apply yet): leave `shares.json` untouched. The preview file stays on disk until the next check overwrites it; nothing is lost by declining.

## Failures

**No credential resolves at all**: same first-run gate as `engram-share` — tell the user to set up `~/.filecoin-pin.env` themselves; this skill never writes one. Show still works with zero credentials.

**A `data-set show`/`piece-status` call errors on one ID** (provider unreachable, data set terminated): skip that ID, keep going on the rest, and say plainly which ID(s) were skipped — a partial check is still worth reconciling, and skipped IDs simply mean their records keep whatever `lastCheck` they already had (never treated as "not found").

**Discover finds an enormous number of data sets**: run the `show`/`piece-status` calls in parallel batches rather than one giant sequential sweep, and report progress if it's taking a while — nothing here is time-sensitive enough to need blocking the user on a single long poll.
