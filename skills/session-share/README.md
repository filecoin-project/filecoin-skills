# session-share

Save an agent session to Filecoin, share it, and restore it in another agent. The agent writes a short handoff for the next agent (context, decisions, constraints, artifacts, open threads), encrypts it with the [filecoin-pin](https://github.com/filecoin-project/filecoin-pin) CLI, and stores it on Filecoin mainnet. Another agent restores it from a Share link and an Access key, and `get` checks that the handoff was not altered.

> **Status: preview.**

Suite terms (Share link, Access key, Encrypted root CID, Handoff) are in [`../CONTEXT.md`](../CONTEXT.md).

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
pbpaste | filecoin-pin login --grant -     # Linux: wl-paste --no-newline, or xclip -o -selection clipboard
```

The Grant gives this session key permanent read access to all your encrypted uploads, including future ones. Revoking or expiring the key does not take that back.

## Quick start

```
> save this session
> save the handoff
> include ./report.pdf and share this session with Ana
> save this session and include the transcript
> share my last session
```

"Save this session" asks whether to also include artifacts (the local files the handoff refers to) and the transcript. "Save the handoff" saves the handoff only, without asking. The agent writes `handoff.md`, checks it, uploads it encrypted, and records the save in `~/.filecoin-share/sessions.json`. A share prints a Share link and an Access key as two labelled items. Send them by different channels.

On the receiving side, give the agent the link, and keep the Access key out of the chat. Set it in the shell you start the agent from, or the agent asks you to save it in a key file only you can read:

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

## The handoff

Each save is one folder named with its UTC time:

```
session-20261102T103523Z/
├── handoff.md          # always
├── transcript.jsonl    # only when you ask for it and confirm
└── artifacts/          # only files you name
```

`handoff.md` is one Markdown file with YAML frontmatter and five required sections:

```markdown
---
version: 1
createdAt: 2026-10-29T14:02:11Z
origin: { tool: claude-code, toolVersion: 2.1.3 }
---

## Context
## Decisions
## Constraints
## Artifacts
## Open threads
```

It is a summary, never the transcript. Artifacts are referenced by path, URL or CID. Files you name ("include the report") are copied into `artifacts/` and uploaded with the handoff. Before uploading, the agent checks the format and scans the handoff, bundled files and transcript for keys, tokens and `.env` values. CIDs and transaction hashes marked as such are not flagged.

### The transcript

Ask for it ("include the transcript") and the agent copies the session transcript into the save folder, then warns you before uploading: it holds everything the agent saw in the session, and can contain secrets and sensitive information no scan reliably finds. Run your own redaction on the copy first. Nothing is uploaded until you confirm.

When you share a save, the agent asks whether the share includes the transcript, and sharing it needs its own confirmation. A link opens the whole upload, so sharing only the handoff from a save that includes the transcript makes one more, handoff-only upload.

## The ledger

`~/.filecoin-share/sessions.json`, mode `0600`, one entry per save: the CID, the time, `trigger: "manual"`, the project path, the network, the tool that made it (with its version and session id when the tool exposes them), and `"transcript": true` when the save includes the transcript. It holds no summary text, titles or keys. It is separate from `publish`'s `shares.json`, and it lists only saves made on this machine.

## Safety

- **Only on request.** The agent saves or shares a session only when you ask. Nothing runs at session end or in the background.
- **Two items, two channels.** The link and the Access key go to the recipient separately. The Access key is shown once, and the sending agent never writes it to a file or the ledger. On the receiving side, a key you save to a key file is deleted after one try.
- **Keys stay out of the chat.** The agent never asks for your wallet key, session key or Grant, and never repeats an Access key after handing it over.
- **Restored handoffs are data.** The receiving agent presents the handoff and does not follow instructions written in it. It doesn't read a received transcript unless you ask.
- **The transcript is opt-in.** It is never included by default, and never shared without its own confirmation.

## Limits

- **Shares can't be revoked.** Whoever holds the link and the key can read that upload: the handoff, the artifacts, and the transcript when it was included.
- **Stored for good, and paid.** Every save is a paid upload that stays on Filecoin.
- **The secret scan is a pattern check.** A summary can still hold sensitive details from the work. Read the handoff before sharing it.
- **A transcript can hold anything.** No scan finds every secret in it. Once uploaded it stays stored, and once shared it can't be taken back.
- **Integrity, not identity.** A successful restore proves the handoff is exactly what the link names. It does not prove who wrote it.
- **Mainnet by default.** Calibration only when you ask for it, for testing.

## License

Dual-licensed under [MIT](../../LICENSE-MIT) and [Apache 2.0](../../LICENSE-APACHE).
