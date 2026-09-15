# publish

Publish what your agent just made. Turns "get me a shareable link for this file" into a durable, verified IPFS link backed by Filecoin storage. The skill drives the [filecoin-pin](https://github.com/filecoin-project/filecoin-pin) CLI end to end: funding, storage, verification, and a local record of everything published.

Say "publish this", "share this file", or "pin this" and the agent hands back a browser link like `https://inbrowser.link/ipfs/<cid>` — first the moment the CID is known (labeled as propagating), then confirmed once IPNI indexing and a provider gateway both serve it. Because the link is content-addressed and the bytes are committed to Filecoin with cryptographic proofs of possession, it isn't hosted at anyone's pleasure: it's a link that is traced and remembered.

## What the skill does

- Shares any single file, or a whole directory as one browsable bundle link, to Filecoin mainnet via `filecoin-pin add` — two storage copies on two distinct providers by default. The size cap comes live from the CLI's synapse SDK, not from the skill.
- Reports the share link in two stages: immediately when the root CID prints, verified after IPNI and a provider gateway check pass. Verification always runs.
- Reuses a skill-owned pair of data sets (tagged `source=filecoin-share` — an opaque constant that never changes) so data set creation and lockup costs are paid once, not per share.
- Authenticates through the CLI's saved login, and only that by default: `filecoin-pin login` pairs this machine with the Filecoin Cloud console, where you approve a scoped session key with your wallet — no private key ever touches the agent, and funding is your console step (session keys can't deposit). The login stays saved and reused until you ask the agent to log out, and you can revoke the key completely any time on the console's session-keys page. A private-key mode (your root funding wallet's key in `~/.filecoin-pin.env`, self-funding via `--auto-fund` capped at 5 USDFC of automatic top-up per share) exists but is used only when you explicitly ask for it.
- Keeps a private local ledger at `~/.filecoin-share/shares.json` (source of truth: root + piece CIDs, data sets, notes). Relocate with a symlink: `mv ~/.filecoin-share <dest> && ln -s <dest> ~/.filecoin-share`. The ledger is a private local record — it stays on this machine, never stored on-chain or shared.
- Never exposes key material: keys load only inside the shell that runs the CLI, and secrets files are treated as write-only — never printed, paged, or sliced.

## Install

Requires Node 24+ and a funded wallet (FIL for gas, USDFC for storage).

```bash
npx skills add filecoin-project/filecoin-skills --skill publish
npm install -g filecoin-pin
```

Then authenticate once: run `filecoin-pin login` and approve the session key in the Filecoin Cloud console with your wallet. That's the only default path — the agent will use a wallet private key (`~/.filecoin-pin.env` with `PRIVATE_KEY=0x...`, `chmod 600`, self-funding shares) only if you explicitly ask it to. It will not write key files for you and will never ask you to paste a key into a conversation.

That's it — nothing else to set up by hand.

## Layout

| Path | What it is |
|---|---|
| `SKILL.md` | The skill itself; this is what the agent follows. |
| `CONTEXT.md` | Glossary of this skill's workflow language (share, copy, degraded share, share ledger...). Suite-shared terms (Pin, Root CID, Piece CID, inbrowser.link) live in `../CONTEXT.md`. |
| `references/filecoin-pin-cli.md` | Tracked in git, so it's visible and reviewable on install. Can still drift from whatever CLI version you have installed: the skill checks the "verified against vX.Y.Z" line at the top against `filecoin-pin --version` every run (step 1 of SKILL.md) and regenerates the file itself if they differ. |

## Iterating

Every change follows the same loop the skill was built with: implement, have an independent agent cold-run the updated SKILL.md and try to break it, fix findings, then commit. The skill stays mainnet-only: the only mentions of calibration/testnet allowed in SKILL.md are inside the ban that forbids them.

## License

Dual-licensed under [MIT](../../LICENSE-MIT) and [Apache 2.0](../../LICENSE-APACHE), like filecoin-pin itself.
