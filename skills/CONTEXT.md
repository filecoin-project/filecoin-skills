# engram suite

Language shared by every skill in the suite. Each skill's own CONTEXT.md carries its workflow-specific terms.

## Language

**Pin**:
CLI-mechanics term only: what `filecoin-pin add` does — uploading a file's content to IPFS-addressed storage and committing it to Filecoin so it persists and is retrievable by CID. Never a skill's own voice: skills speak their own verb (share, publish...), the CLI pins. Appears only when naming CLI commands, flags, and reference docs (and when quoting a user's own words like "pin this").
_Avoid_: Pin as any skill's user-facing verb in prose, reports, or step names

**Root CID**:
The IPFS content identifier for a packed file's DAG root; the identifier used in every link handed to a user and the one thing needed to retrieve the content.
_Avoid_: CID (bare), content hash, file hash

**Piece CID**:
The identifier committed on-chain for the entire CAR file that was packed and stored; it names the stored container, not the content, and storage proofs are computed against it, never the root CID.
_Avoid_: Storage CID, commitment hash

**inbrowser.link**:
The canonical link host: a service-worker IPFS gateway. The first page load installs a service worker in the visitor's browser, which then resolves the CID through IPNI routing and fetches the content directly from whichever providers hold it — so the link works as long as any provider serves the bytes, without depending on one gateway operator's backend. Consequence: it needs a real browser context to work, so it suits page views but not raw-byte consumers (curl, embeds, `<video>` tags) — those get the direct public-gateway URL instead.
_Avoid_: Public gateway (reserve for backend-fetching gateways like dweb.link), hosted gateway
