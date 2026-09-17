# filecoin-skills

Official skills that let agents store, verify, and retrieve data with Filecoin.

Agents are constantly producing work that has to outlive the moment it was made in. It either gets **shared** — a report, a dashboard, a build, a dataset, handed to a person as a link that keeps working — or it gets **remembered**, as session memory and records the next agent or session can pick up from.

Both need the same thing underneath: a storage layer that is persistent, portable, open, and verifiable. Not a bucket in someone's cloud, and not an archive you wait on.

That's what these skills give your agents. *Warm* storage means retrievable now, not thawed from cold: you publish, and the link works.

Today that's one skill: [`publish`](./skills/publish/) puts any file or folder behind a public, verified CID link. Skills private, encrypted content and for agent memory will follow.

## Skills

| Skill | Status | What it does |
|---|---|---|
| [`publish`](./skills/publish/) | stable | Publish any local file or folder to Filecoin Warm Storage and get a public, verified CID link. |

## Install

```bash
npx skills add filecoin-project/filecoin-skills --skill publish
```

Add `-g` to install for every project instead of just the current one.

Works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode, and other [skills.sh](https://skills.sh/)-compatible agents.

## Before you start

Every skill in this suite writes to Filecoin **mainnet**. There is no Calibration/testnet mode, so setup is the same regardless of which skill you install:

- **Node 24+**
- **[`filecoin-pin`](https://github.com/filecoin-project/filecoin-pin)** — installed automatically on first run, or `npm install -g filecoin-pin`
- **A funded wallet**, in two browser steps:
  1. **FIL** for gas — [bridge to Filecoin via Squid Router](https://app.squidrouter.com/?fromChain=base&toChain=filecoin&fromToken=usdc&toToken=fil). Well under 1 FIL is plenty.
  2. **USDFC** for storage — <https://pay.filecoin.cloud/console> swaps, authorizes the Warm Storage Service, and deposits in one guided flow. **~5 USDFC** is a comfortable start.

Each skill's own README covers its specific setup and usage.

## Concepts

[`skills/CONTEXT.md`](./skills/CONTEXT.md) is the shared glossary for the suite — worth two minutes before your first publish. The one that catches everyone: a **Root CID** is your content and belongs in a link you share; a **Piece CID** names the stored container and will hand people a download instead.

## Safety

These skills spend real money and talk to your wallet. Across the suite:

- **No silent spend.** Funding shortfalls stop the run and hand you a console link to approve yourself.
- **No private keys.** Default auth is a scoped session key that cannot move funds. Deposits are always your step, in the console.
- **Public by default.** Content published to Filecoin is readable by anyone with the CID and effectively permanent. Skills for private, encrypted content are in the works.

## Links

- [Filecoin Onchain Cloud docs](https://docs.filecoin.cloud/getting-started/filecoin-pin/)
- [Revoke session keys](https://pay.filecoin.cloud/console/session-keys)
- [This suite on skills.sh](https://skills.sh/filecoin-project/filecoin-skills)

## License

Dual-licensed under [MIT](./LICENSE-MIT) and [Apache 2.0](./LICENSE-APACHE).