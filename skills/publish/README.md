# publish

Publish what your agent just made. Turns "get me a shareable link for this file" into a durable, verified IPFS link backed by Filecoin storage. The skill drives the [filecoin-pin](https://github.com/filecoin-project/filecoin-pin) CLI end to end: funding, storage, verification, and a local record of everything published.

Say "publish this", "share this file", or "pin this" and the agent hands back a browser link like `https://inbrowser.link/ipfs/<cid>` — first the moment the CID is known (labeled as propagating), then confirmed once IPNI indexing and a provider gateway both serve it. Because the link is content-addressed and the bytes are committed to Filecoin with cryptographic proofs of possession, it isn't hosted at anyone's pleasure: it's a link that is traced and remembered.

## When to use

**Use it for** — a dashboard, HTML page, report, image, video, dataset, or a whole build folder; any artifact you want live at a durable link without standing up a host. Name several paths at once and each one gets its own link.

**Publish the folder, not a zip.** A directory is packed as a single bundle: the link opens as a browsable listing, and every file inside is reachable at `…/ipfs/<root-cid>/<filename>`. Zip it first and you get one opaque file instead — no folder view, no per-file links, just a download.

**Don't use it for** — private or client-gated content (everything published is public), full apps with a backend, or anything that needs to stay at the *same* URL as it changes. CIDs are immutable: new bytes mean a new link.

> **Private content is coming.** A version of these skills for private, encrypted publishing is in the works. Until then, treat everything published here as public.

## Install

```bash
npx skills add filecoin-project/filecoin-skills --skill publish
```

Add `-g` to install for every project instead of just this one.

Works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode, and other skills.sh-compatible agents.

## Prerequisites

- **Node 24+**
- **`filecoin-pin` CLI** — installed automatically on first run, or `npm install -g filecoin-pin`
- **A wallet with FIL and USDFC on Filecoin mainnet.** This skill is mainnet-only; there is no Calibration/testnet mode.

**Getting funded — two steps, both in the browser:**

1. **Get FIL** (for gas) → [bridge to Filecoin via Squid Router](https://app.squidrouter.com/?fromChain=base&toChain=filecoin&fromToken=usdc&toToken=fil). Well under 1 FIL is plenty.
2. **Get USDFC and set up payments** → <https://pay.filecoin.cloud/console>. The console swaps FIL to USDFC, authorizes the Warm Storage Service, and deposits — one guided flow, one wallet transaction. **~5 USDFC** is a comfortable start.

Then authorize this machine once:

```bash
filecoin-pin login
```

Connect your **owner wallet** in the console and sign. ⚠️ Confirm which wallet the console is connected as before signing — the grant lands under whichever one is connected. The session persists; you sign once — the login stays saved and reused until you ask the agent to log out, and you can revoke the key completely any time on the console's [session-keys page](https://pay.filecoin.cloud/console/session-keys).

## Quick start

```
> publish ./demo/index.html
```

That's the whole happy path. The agent checks funding, uploads, verifies, and hands back the link. First publish takes a few minutes (it creates your storage data sets); later ones are faster.

A folder becomes one bundle, and several paths become several shares — run in parallel, so a batch costs about the wall-clock of a single publish:

```
> publish ./site/
> publish ./report.html ./data.csv ./build/
```

## What it costs

Ask for a **dry run** before publishing anything and the agent estimates the cost without uploading or moving funds.

When you're asked to deposit, most of the number is not a charge. It splits three ways:

- **Lockup** — a refundable hold (your data sets' 30-day reserve plus security deposit), returned if those data sets are ever terminated. This is the bulk of the ask.
- **Storage rate** — the actual recurring cost, a small amount per month. A skill-owned pair of data sets carries a floor of roughly **0.04 USDFC/month**.
- **One-time fees** — small.

Setup is paid once: your first publish creates the two data sets, and later publishes reuse them at no extra cost until their billed floor is exhausted.

**~5 USDFC** is a comfortable start — <https://pay.filecoin.cloud/console> swaps, authorizes, and deposits in one flow. The FIL for gas comes from [bridging to Filecoin via Squid Router](https://app.squidrouter.com/?fromChain=base&toChain=filecoin&fromToken=usdc&toToken=fil); well under 1 FIL is plenty.

If the console shows months of runway and *still* asks for a top-up, that's the lockup hold at work, not a contradiction.

## What you get back

A link, plus the receipt details:

```
━━━ Add Complete ━━━

Network: Filecoin - Mainnet

Add Details
  Root CID: bafkreiftjkhycq5445q6p2pcxlstwfkgepl3xmxq3aj5fiwlwgd6i55pvu

Filecoin Storage
  Piece CID: bafkzcibd6ebqld7r6uq342kfpndaettyzymveiktepzcieymx672npmmlzf57ai7
  Explorer:  https://pdp.vxb.ai/mainnet/piece/bafkzcibd...

Copies
  [Primary]   Provider 1  ·  Data Set ID: 1625
  [Secondary] Provider 7  ·  Data Set ID: 1626
```

Your link is the **Root CID**: `https://inbrowser.link/ipfs/<root-cid>`

It arrives twice — first labeled *propagating* the moment the CID is known, then **verified** once IPNI indexing and a provider gateway both serve it. Every publish is also appended to a private local ledger at `~/.filecoin-share/shares.json` — the source of truth for root and piece CIDs, data set IDs, and notes. Ask the agent "what have I published?" to read it back. It stays on this machine: never stored on-chain, never shared. Relocate it with a symlink:

```bash
mv ~/.filecoin-share <dest> && ln -s <dest> ~/.filecoin-share
```

## How it works

Agent makes an artifact → skill runs `filecoin-pin add` → stored on Filecoin Warm Storage as **two copies on two distinct providers** → root CID returned → opens at any IPFS gateway.

Data sets are tagged `source=filecoin-share` — an opaque constant that never changes — and reused, so creation and lockup costs are paid on your first publish, not every time.

## Safety

This skill spends real money and talks to your wallet. What it will and won't do:

- ✅ **Never spends silently.** Funding shortfalls stop the run and hand you a pre-filled console link to approve yourself.
- ✅ **Never sees your private key.** Default auth is a scoped session key (`createDataSet`, `addPieces`) that is structurally incapable of moving funds. Deposits are always your console step.
- ✅ **Never writes or asks for key material.** Secrets files are treated as write-only — never printed, pasted, or logged.
- ⚠️ **Publishes exactly what you name**, and warns before bundling anything that looks unintended (`node_modules`, build junk, secrets-shaped files).

A private-key mode exists for self-funding publishes — your root funding wallet's key in `~/.filecoin-pin.env`, depositing via `--auto-fund` with automatic top-up capped at 5 USDFC per publish. It is used **only** if you explicitly ask for it.

## Limits

- **Public by default.** Anyone with the CID can read it.
- **Effectively permanent.** You can unpin content, but that doesn't erase what has already propagated. There is no true delete.
- **Filenames are public**, written on-chain as piece metadata — and in a folder, every name in the tree.
- **Immutable links.** Edit the file and you get a new CID. No "always-latest" URL.
- **A size cap applies** per file or folder. The skill reads it live from the installed CLI at publish time rather than hardcoding it here, so it rises with new releases. A folder packs into one piece, so the whole tree counts against the cap.
- **Markdown serves as plain text** in browsers — publish HTML if you want it rendered.
- **Relative links break in a single-file publish.** An HTML page that pulls in siblings (`<img src="logo.png">`) publishes fine and renders broken. Publish its folder as a bundle instead; self-contained files make the best single-file links.

## Troubleshooting

**`No credentials found.` / `Session expired`** — No usable login. Run `filecoin-pin login`. If a session expired or was revoked, it can't be renewed despite the CLI's wording — rotate it: `filecoin-pin logout` then `filecoin-pin login`.

**Publish stops asking for funds** — Expected. Session keys can't deposit. The CLI exits with a pre-filled console link; deposit there and re-run. Note that most of the amount asked for is a *refundable* lockup, not a charge.

**Gateway not resolving yet** — Normal propagation lag. `dweb.link` returning 429/504 for 10–20 minutes after publishing is expected; the provider gateway serves immediately. Use `inbrowser.link` — that's the canonical share link.

Docs, console, and CLI links live in the [suite README](https://github.com/filecoin-project/filecoin-skills#links).

## License

Dual-licensed under [MIT](../../LICENSE-MIT) and [Apache 2.0](../../LICENSE-APACHE), like `filecoin-pin` itself.
