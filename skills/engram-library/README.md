# engram-library

Browse what `engram-share` has stored, and check it against Filecoin itself. Turns "show my engram shares" into a branded, browsable `~/.engram/library.html`, and "check my shares on Filecoin" into a real inspection of the storage providers holding them — never a guess from the local record alone.

Storage-read-only: this skill renders and reconciles the local share ledger, but it never adds, removes, repairs, terminates, or funds anything on Filecoin. `engram-share` owns every write; this skill only ever reads.

## Status

**Beta.** Show mode is verified against a real production ledger. Verify catalog, Discover wallet, and Apply sync are verified only by construction — `reconcile.py --selftest` plus a cold subagent read-through of `SKILL.md` — never yet an end-to-end run against the live `filecoin-pin` CLI with a funded wallet. Treat those three modes as unverified until that first real run happens.

## What the skill does

- Renders `~/.engram/shares.json` into `~/.engram/library.html`, grouped into Current, Attention, and History so degraded or superseded shares don't hide in a flat list. History shows a delete/supersede date parsed from the note instead of a dead Link/Trace pair.
- The rendered library is interactive on its own — search, a sortable date column, and pagination — with no server, no build step, and no dependency beyond a browser.
- A "Check against Filecoin" button next to the freshness line copies the trigger phrase to the clipboard, since a static file can't reach an agent by itself.
- On request, verifies the ledger against Filecoin: inspects the data sets it already names, confirms copy counts and Piece CIDs, and flags anything it can't find without ever deleting the local record.
- On request, discovers everything the active wallet's data sets hold on Filecoin — including pieces the ledger lost track of — separating known sources from unknown ones, which are never merged in.
- Every check lands in a preview first — `~/.engram/.sync-preview.json`, rendered to `~/.engram/sync-preview.html` — never the real ledger, no matter how small the change. Nothing touches `shares.json` until you say yes.
- Never fabricates a share date, note, or file list for a piece it recovers from chain; it carries only what Filecoin can prove.
- Backs up the ledger before applying a preview and replaces it atomically, so a crash mid-write can never corrupt it.

## Install

```bash
npx skills add jennijuju/engram --skill engram-library
npm install -g filecoin-pin
```

Show works with no credentials at all. Verify and Discover prefer a wallet address only (`--view-address`, no signing key touched); if none is already configured, they fall back to whatever key `engram-share` already uses, per its own setup.

## Layout

| Path | What it is |
|---|---|
| `SKILL.md` | The skill itself; this is what the agent follows. |
| `CONTEXT.md` | Glossary of this skill's workflow language (catalog source, verify catalog, discover wallet, recovered record...). Suite-shared terms live in `../CONTEXT.md`; the share ledger itself is `engram-share`'s vocabulary, in `../engram-share/CONTEXT.md`. |
| `library-template.html` | The engram-branded shell `render.py` fills with Current/Attention/History sections. |
| `render.py` | Pure, offline view: renders `~/.engram/shares.json` (+ optional `.last-check.json`, `.discovery-scratch.json`) into the library. Never makes a network call. stdlib-only. |
| `reconcile.py` | The merge engine for Verify catalog and Discover wallet: field-level authority merge, always writing a preview first (`.sync-preview.json`) — real ledger writes only happen via `--apply`, with a timestamped backup and atomic write. Run `python3 reconcile.py --selftest` to check it. stdlib-only. |

## Iterating

Same loop as `engram-share`: implement, have an independent agent cold-run the updated `SKILL.md` and try to break it, fix findings, then commit.

## License

Dual-licensed under [MIT](../../LICENSE-MIT) and [Apache 2.0](../../LICENSE-APACHE), like filecoin-pin itself.
