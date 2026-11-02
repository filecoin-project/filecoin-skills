# filecoin-skills

Official skills that let agents store, verify, and retrieve data with Filecoin, or operate a Filecoin storage provider.

Agents are constantly producing work that has to outlive the moment it was made in. It either gets **shared** — a report, a dashboard, a build, a dataset, handed to a person as a link that keeps working — or it gets **remembered**, as session memory and records the next agent or session can pick up from.

Both need the same thing underneath: a storage layer that is persistent, portable, open, and verifiable. Not a bucket in someone's cloud, and not an archive you wait on.

That's what these skills give your agents. *Warm* storage means retrievable now, not thawed from cold: you publish, and the link works.

[`publish`](./skills/publish/) puts any file or folder behind a public, verified CID link. [`filecoin-pdp-agent`](./skills/filecoin-pdp-agent/) lets an agent use your spare hardware and storage capacity to deploy and operate a Curio PDP provider and earn storage payments on your behalf. [`private-share`](./skills/private-share/) encrypts a file or folder for one recipient, and [`session-share`](./skills/session-share/) saves an agent session as an encrypted snapshot another agent can restore.

## Skills

| Skill | Status | What it does |
|---|---|---|
| [`publish`](./skills/publish/) | stable | Publish any local file or folder to Filecoin Warm Storage and get a public, verified CID link. |
| [`private-share`](./skills/private-share/) | preview | Encrypt a file or folder, share it with one recipient as a Share link plus a separate Access key, and open shares you receive. |
| [`session-share`](./skills/session-share/) | preview | Save the current session as an encrypted handoff, share it, and restore it in another agent. |
| [`filecoin-pdp-agent`](./skills/filecoin-pdp-agent/) | preview | Deploy and operate a Curio PDP provider, with periodic health and earnings checks, recovery, and upgrades. |

## Install

Choose a skill:

```bash
npx skills add filecoin-project/filecoin-skills --skill publish
# Or share encrypted content and sessions:
npx skills add filecoin-project/filecoin-skills --skill private-share
npx skills add filecoin-project/filecoin-skills --skill session-share
# Or run a storage provider:
npx skills add filecoin-project/filecoin-skills --skill filecoin-pdp-agent
```

Add `-g` to install for every project instead of just the current one.

Works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode, and other [skills.sh](https://skills.sh/)-compatible agents.

## Before you start

For `publish`, setup uses Filecoin **mainnet** and requires:

- **Node 24+**
- **[`filecoin-pin`](https://github.com/filecoin-project/filecoin-pin)** — installed automatically on first run, or `npm install -g filecoin-pin`
- **A funded wallet**, in two browser steps:
  1. **FIL** for gas — [bridge to Filecoin via Squid Router](https://app.squidrouter.com/?fromChain=base&toChain=filecoin&fromToken=usdc&toToken=fil). Well under 1 FIL is plenty.
  2. **USDFC** for storage — <https://pay.filecoin.cloud/console> swaps, authorizes the Warm Storage Service, and deposits in one guided flow. **~5 USDFC** is a comfortable start.

For `private-share` and `session-share`, sending needs the same setup plus a login that can encrypt (`filecoin-pin login --scopes createDataSet,addPieces,encrypt`). Receiving needs only Node 24+ and `filecoin-pin`.

For `filecoin-pdp-agent`, provide access to a compatible host and allocate storage and operating funds. The agent follows the selected Curio release's deployment procedure. See its [setup and control model](./skills/filecoin-pdp-agent/README.md); the `publish` prerequisites above do not apply. Each skill's README covers its specific setup and usage.

## Concepts

[`skills/CONTEXT.md`](./skills/CONTEXT.md) is the shared glossary for publishing and retrieving content — worth two minutes before your first publish. The one that catches everyone: a **Root CID** is your content and belongs in a link you share; a **Piece CID** names the stored container and will hand people a download instead.

## Safety

Permissions and funding depend on the skill. For `publish`:

- **No silent spend.** Funding shortfalls stop the run and hand you a console link to approve yourself.
- **No private keys.** Default auth is a scoped session key that cannot move funds. Deposits are always your step, in the console.
- **Public by default.** Content published to Filecoin is readable by anyone with the CID and effectively permanent. Use `private-share` or `session-share` for content only one recipient should read.

For `private-share` and `session-share`, the Share link and the Access key go to the recipient by different channels. The agent shows the Access key once and never stores it, and saves or shares only when you ask.

`filecoin-pdp-agent` operates a provider and its dedicated funded wallet through local tools, within your delegated resources and spending limits. It requires first-run risk acceptance and keeps secret values out of model context. See its [control model and setup guide](./skills/filecoin-pdp-agent/README.md).

## Links

- [Filecoin Onchain Cloud docs](https://docs.filecoin.cloud/getting-started/filecoin-pin/)
- [Revoke session keys](https://pay.filecoin.cloud/console/session-keys)
- [This suite on skills.sh](https://skills.sh/filecoin-project/filecoin-skills)

## License

Dual-licensed under [MIT](./LICENSE-MIT) and [Apache 2.0](./LICENSE-APACHE).
