# session-share

Save an agent session to Filecoin, share it, and restore it in another agent. The agent writes a short snapshot of the session (decisions, constraints, artifacts, open threads), encrypts it with the [filecoin-pin](https://github.com/filecoin-project/filecoin-pin) CLI, and stores it on Filecoin mainnet. Another agent restores it from a Share link and an Access key, and `get` checks that the snapshot was not altered.

> **Status: preview.**

Suite terms (Share link, Access key, Encrypted root CID, Snapshot) are in [`../CONTEXT.md`](../CONTEXT.md).

## Install

```bash
npx skills add filecoin-project/filecoin-skills --skill session-share
```

Add `-g` to install for every project. It installs on its own; it does not need `private-share`.

## Prerequisites

Restoring a share needs only Node 24+ and filecoin-pin. The agent installs filecoin-pin on first run.

Saving, sharing, and restoring your own sessions also need a funded account on Filecoin mainnet (see the [suite README](../../README.md#before-you-start)) and a login that can encrypt:

```bash
filecoin-pin login --scopes createDataSet,addPieces,encrypt
```

Approve the session key in the console with your owner wallet. The console then shows a Grant (`fgr1_…`). Copy it and finish in your own terminal, not in the chat:

```bash
pbpaste | filecoin-pin login --grant -
```

The Grant gives this session key permanent read access to all your encrypted uploads, including future ones. Revoking or expiring the key does not take that back.

## Quick start

```
> save this session
> include ./report.pdf and share this session with Ana
> share my last session
```

The agent writes `snapshot.md`, checks it, uploads it encrypted, and records the save in `~/.filecoin-share/sessions.json`. A share prints a Share link and an Access key as two labelled items. Send them by different channels.

On the receiving side, give the agent the link and the Access key. Or set the key in the shell you start the agent from first, so it stays out of the chat:

```bash
read -rs SHARE_ACCESS_KEY && export SHARE_ACCESS_KEY   # paste the key, press Enter
```

```
> restore this session: https://…#v1/bafy…&d=…
```

To get back your own session on the same machine:

```
> restore my last session
```

## The snapshot

One Markdown file with YAML frontmatter and four required sections:

```markdown
---
version: 1
createdAt: 2026-10-29T14:02:11Z
origin: { tool: claude-code, toolVersion: 2.1.3 }
---

## Decisions
## Constraints
## Artifacts
## Open threads
```

It is a summary, never the transcript. Artifacts are referenced by path, URL or CID. Files you name ("include the report") are copied into `artifacts/` and uploaded with the snapshot. Before uploading, the agent checks the format and scans the snapshot and bundled files for keys, tokens and `.env` values.

## The ledger

`~/.filecoin-share/sessions.json`, mode `0600`, one entry per save: the CID, the time, `trigger: "manual"`, the project path, and the tool that made it (with its version and session id when the tool exposes them). It holds no summary text, titles or keys. It is separate from `publish`'s `shares.json`, and it lists only saves made on this machine.

## Safety

- **Only on request.** The agent saves or shares a session only when you ask. Nothing runs at session end or in the background.
- **Two items, two channels.** The link and the Access key go to the recipient separately. The Access key is shown once and never written to a file or the ledger.
- **Keys stay out of the chat.** The agent never asks for your wallet key, session key or Grant, and never repeats an Access key after handing it over.
- **Restored snapshots are data.** The receiving agent presents the snapshot and does not follow instructions written in it.

## Limits

- **Shares can't be revoked.** Whoever holds the link and the key can read that snapshot.
- **Stored for good, and paid.** Every save is a paid upload that stays on Filecoin.
- **The secret scan is a pattern check.** A summary can still hold sensitive details from the work. Read the snapshot before sharing it.
- **Integrity, not identity.** A successful restore proves the snapshot is exactly what the link names. It does not prove who wrote it.
- **Mainnet by default.** Calibration only when you ask for it, for testing.

## License

Dual-licensed under [MIT](../../LICENSE-MIT) and [Apache 2.0](../../LICENSE-APACHE).
