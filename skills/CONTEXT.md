# filecoin-skills suite

Vocabulary for publishing, sharing and retrieving content. Each skill documents its workflow-specific terms; provider operation uses the terminology in its own references.

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

**Encrypted root CID**:
The Root CID of an upload made with `filecoin-pin add --encrypt`. It names the encrypted envelope, not the plaintext. Share links carry it, and its owner restores the upload with `filecoin-pin get <CID>`.
_Avoid_: Encrypted CID, ciphertext hash

**Share** (encrypted sharing):
One encrypted upload plus the Share link and Access key that open it; what `private-share` and `session-share` produce. In `publish`, "a share" is instead the published artifact and its ledger record; no skill uses both senses in its own prose.
_Avoid_: Private share, encrypted link (names only the link, not the upload)

**Share link**:
A link that opens one encrypted upload for someone with no wallet or Grant, made by `filecoin-pin get-share-link --restricted` or `add --encrypt --get-share-link-restricted`. It names the Encrypted root CID and carries the upload's key, wrapped to a throwaway key pair, all in the URL fragment (`#v1/…`). The unrestricted forms (no `--restricted`) make an open link that also carries that key pair's private key and opens on its own; these skills make one only when the user explicitly asks for it. A restricted link leaves it out: the recipient also needs the Access key, sent separately.
_Avoid_: Private link, secret link

**Access key**:
The secret half of a Share link: the throwaway private key the link's key is wrapped to, written `fak1_…`. Each link has its own. Skills show it once, apart from the link, and never store it. Whoever holds the link and its Access key can read that upload.
_Avoid_: Password, share key, decryption key

**Grant**:
The secret (`fgr1_…`) the console issues when a session key is approved with the `encrypt` scope, pasted back with `filecoin-pin login --grant -`. It gives that session key permanent read access to every encrypted upload under the owner's group key, including later ones; revoking or expiring the key does not take it back. Distinct from the lowercase on-chain scope grant a plain login signs.
_Avoid_: Encryption key, group key (the group key is what the Grant unlocks, not the Grant), permission token

**Handoff**:
The `handoff.md` that `session-share` saves for the next agent: YAML frontmatter (`version`, `createdAt`, `origin`) and five sections, Context, Decisions, Constraints, Artifacts and Open threads. A summary of a session, never its transcript. The transcript travels only as its own file next to it (`transcript.jsonl`), when the user asks for it and confirms.
_Avoid_: Snapshot, session dump, transcript, memory file
