# engram-library

An agent skill that turns the local share ledger into a browsable HTML library, and can check it against Filecoin itself. Suite-shared terms (Pin, Root CID, Piece CID, inbrowser.link) live in `../CONTEXT.md`; the share ledger and its fields (`note`, `datasets`, `pieceCid`...) are `engram-share`'s vocabulary, defined in `../engram-share/CONTEXT.md`.

## Language

**Library**:
This skill's only user-facing verb and its output: `~/.engram/library.html`, a rendered, browsable view of the share ledger grouped into Current, Attention, and History. Regenerated on every run; never hand-edited.
_Avoid_: Index (the older, single-table view `engram-share` used to render; superseded by the library)

**Storage-read-only**:
This skill's operating boundary: it may read and write the local share ledger and the rendered library, but it never adds, removes, repairs, terminates, or funds anything on Filecoin. Every Filecoin interaction it makes is an inspection (`data-set ls`, `data-set show`, `data-set piece-status`), never a mutation.
_Avoid_: Read-only (imprecise — the local catalog IS written; "storage" is the part that's read-only)

**Verify catalog**:
The check that inspects only the data sets the share ledger already names. Confirms what the catalog claims is still true, finds degraded or missing copies, and recovers pieces the ledger lost track of — never discovers data outside the ledger's own data sets.
_Avoid_: Sync, refresh (too vague about what's being checked against what)

**Discover wallet**:
The check that enumerates every data set the active wallet owns, not just the ones the ledger already names. Splits results into known sources (reconciled into the sync preview) and unknown sources (listed separately, never merged in even after apply). A superset of Verify catalog's scope, and the only way to find Filecoin-only pieces the ledger never recorded.
_Avoid_: Audit, scan (used loosely elsewhere; this skill's two checks have exactly these two names, never interchanged)

**Catalog source**:
Per-record language for where a library row's information came from: `local` (written by `engram-share` at share time) or `synced from Filecoin` (added by a check that found a piece the ledger didn't have). Distinct from the protocol's own `source` data-set metadata key, which this skill calls **data-set source** to avoid the collision — data-set source names the on-chain tag (`engram-share`, or something else entirely); catalog source names the ledger row's own provenance.
_Avoid_: Source (alone — always qualify as catalog source or data-set source)

**Recovered record**:
A row a check adds to the sync preview because Filecoin held a piece the local catalog didn't know about, on a data set already reconciled as a known source. Carries only what the chain can prove — name, Root CID, Piece CID, data sets — and no invented date, note, or file list; a real share date is never fabricated to fill the gap. Stays a preview-only row, never touching the real ledger, until the user explicitly applies it.
_Avoid_: Restored, imported (imply the row previously existed locally; it didn't)

**Known source / unknown source**:
A data-set source (see Catalog source) is known if it's `engram-share` or already implied by a data set the ledger already names; anything else is unknown. Verify catalog only ever sees known sources by construction. Discover wallet sees both — known sources reconcile into the sync preview, unknown sources are listed under "Other Filecoin storage" and never enter the ledger at all, applied or not.
_Avoid_: Trusted/untrusted (this is about ledger membership, not a security judgment)

**Current / Attention / History**:
The library's three sections, computed at render time from the ledger alone. **Current**: healthy, nothing to look at. **Attention**: fewer than two live copies, a check found the piece missing everywhere it looked, or the note says `DEGRADED`. **History**: the note says `DELETED` or names a supersession. A record's section can change every render as its note or datasets change; the categorization itself is never stored.
_Avoid_: Healthy/unhealthy (binary; loses the distinct meaning of History)

**Check line**:
The one line at the top of the library stating whether it reflects a Filecoin check and when. Present only when a check has actually run (`~/.engram/.last-check.json` exists) — a library that has never been checked says so plainly, never implying verification that didn't happen.
_Avoid_: Verified as of... (too strong when no check has run)

**Sync preview**:
The candidate result of a check, written to `~/.engram/.sync-preview.json` and rendered to `~/.engram/sync-preview.html` — never the real ledger, never `library.html`. Every Verify catalog or Discover wallet run lands here first, no matter how small the change; only an explicit user yes moves it into `shares.json` via `reconcile.py --apply`. A recovered count far larger than the current ledger is exactly the case this exists to catch before it becomes 500 unnamed rows in someone's personal library.
_Avoid_: Draft, staged changes (this names the specific file and the specific gate, not a generic workflow state)
