# engram-share

An agent skill that turns a local HTML, Markdown, or MP4 file into a durable, publicly retrievable link by storing it on Filecoin mainnet through the `filecoin-pin` CLI, then reporting a browser-viewable URL back to the user. Suite-shared terms (Pin, Root CID, Piece CID, inbrowser.link) live in `../CONTEXT.md`.

## Language

**Share**:
The end-to-end unit of work this skill performs, and the skill's only user-facing verb: packing one file or one directory (a bundle), storing it on Filecoin, verifying it is retrievable, and recording it in the ledger — the thing a single invocation produces.
_Avoid_: Upload, publish, pin (the skill shares; "pin" is reserved for CLI mechanics — see Pin)

**Copy**:
One full storage instance of a share's content held by a single storage provider in its own data set; the skill's redundancy unit — a share normally consists of two copies on two distinct providers.
_Avoid_: Replica (for the stored instance itself — reserve "replica" for the general concept of redundancy), instance

**Data set targeting**:
Choosing which existing data set (or none) an add should land in, done either by metadata filter (`--data-set-metadata source=engram-share`, which matches or creates skill-owned data sets transparently) or by explicit `--data-set-id` when repairing or substituting around a specific provider; the two mechanisms are mutually exclusive within a single add and pointing at the wrong one either stacks new billing floors or silently reuses the wrong provider.
_Avoid_: Provider targeting, provider pinning (an explicit `--provider-id` always creates a new data set — reserved for deliberate redundancy-set creation, never reuse)

**Compact dataset**:
A data set whose ID is at or above the network's compact-storage cutover (mainnet: `1559`, per synapse-sdk#925) — it uses the newer, more storage-efficient `PieceV2` layout. Below the cutover is a legacy data set: still fully retrievable, just less efficient. New data sets created today are always compact (the chain has long since passed the cutover); the distinction only matters when an existing data set predates it.
_Avoid_: New-format/old-format dataset (compact/legacy are the protocol's own terms, from the linked issue)

**Degraded share**:
A share that ended its session with only one copy stored instead of the required two, because fewer than two distinct healthy providers were reachable at add time; it is still fully retrievable, just under-replicated, and is marked `DEGRADED 1/2` in the local index until repaired.
_Avoid_: Failed share, partial upload, incomplete share

**Provider gateway liveness**:
A point-in-time check of whether a storage provider's own retrieval endpoint is answering at all (any HTTP status, including 404, counts as up; a timeout or 503 counts as down), used to decide which existing data sets are safe to target for a repair or substitution — distinct from checking whether a specific CID resolves.
_Avoid_: Provider health, uptime check, provider status

**Trace**:
A share's path back to its physical whereabouts on Filecoin: the PDP Explorer piece page (`pdp.filecoin.cloud/mainnet/piece/<pieceCid>`) listing every data set and provider holding the piece and its live proving status — the engram's memory trace, followable. "Trace this share" is the rendered index's link to it.
_Avoid_: Locate, find the piece, explorer link

**Share ledger**:
The local, private source of truth (`~/.engram/shares.json`): one JSON record per share — file, date, root CID, piece CID, data set IDs, network, note. Appended at share time. Browsing it as a rendered page and checking it against Filecoin are `engram-library`'s job — see `../engram-library/CONTEXT.md` — never read by this skill's own machine logic.
_Avoid_: Registry, manifest, database, index (the rendered view now belongs to `engram-library`, named "library" there)

**Staged verification**:
The two-stage reporting flow for a share link: stage one hands back the root CID as an explicitly labeled *propagating, not yet verified* link the moment it appears in the add's output, and stage two upgrades that label once IPNI indexing and a provider gateway both confirm the content actually resolves.
_Avoid_: Link verification, retrieval check (these name the underlying probes, not the two-stage reporting contract)