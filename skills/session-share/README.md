# session-share

Save an agent session to Filecoin, share it, and restore it in another agent. The agent writes a short handoff for the next agent (context, decisions, constraints, artifacts, dead ends, open threads), encrypts it with the [filecoin-pin](https://github.com/filecoin-project/filecoin-pin) CLI, and stores it on Filecoin (mainnet by default). Another agent restores it from a Share link and an Access key, and `get` checks that the handoff was not altered.

> **Status: preview.**

Suite terms (Share link, Access key, Grant, Encrypted root CID, Handoff) are in [`../CONTEXT.md`](../CONTEXT.md).

## When to use

Use it at the end of a working session another agent should continue — a review half done, a plan agreed but not executed, a debugging state worth keeping — or to move a session between machines or tools. Say "save this session", "share this session with Ana", or "restore my last session".

Use [`private-share`](../private-share/) instead for a file or folder that isn't a session.

## Install

```bash
npx skills add filecoin-project/filecoin-skills --skill session-share
```

Add `-g` to install for every project. It installs on its own; it does not need `private-share`.

## Prerequisites

Restoring a share needs only Node 24+ and `filecoin-pin` 2.3.0 or later. The agent installs filecoin-pin on first run.

Saving, sharing, and restoring your own sessions also need a funded account on Filecoin mainnet (see the [suite README](../../README.md#before-you-start)) and a login that can encrypt:

```bash
filecoin-pin login --scopes createDataSet,addPieces,encrypt
```

Before you approve: with `encrypt` in the scopes, the console issues a Grant (`fgr1_…`) that gives this session key permanent read access to every encrypted upload under your group key, including later ones. Revoking or expiring the key does not take that back.

Approve the session key in the console with your owner wallet, then copy the Grant the console shows and finish in your own terminal, not in the chat:

```bash
pbpaste | filecoin-pin login --grant -     # Linux: wl-paste --no-newline, or xclip -o -selection clipboard
```

## Quick start

```
> save this session
> save the handoff
> include ./report.pdf and share this session with Ana
> save this session and include the transcript
> share my last session
```

"Save this session" asks whether to also include artifacts (the local files the handoff refers to) and the transcript. "Save the handoff" saves the handoff only, without asking. The agent writes `handoff.md`, checks it, uploads it encrypted, and records the save in `~/.filecoin-share/sessions.json`. A share prints a Share link and an Access key as two labeled items. Send them by different channels.

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

## What it costs

Each save is paid storage on Filecoin; making a link for an existing save costs nothing (sharing only the handoff from a save that includes the transcript is the exception: one more paid upload). Ask for a dry run and the agent shows the cost without uploading. When the console asks you to deposit, most of the number is a refundable lockup hold rather than a charge; [`publish`'s cost breakdown](../publish/README.md#what-it-costs) explains the split, and it is the same for encrypted uploads.

## The handoff

Each save is one folder named with its UTC time:

```
session-20261102T103523Z/
├── handoff.md          # always
├── transcript.jsonl    # only when you ask for it and confirm
└── artifacts/          # only files you name
```

`handoff.md` is one Markdown file with YAML frontmatter and six required sections:

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
## Dead ends
## Open threads
```

It is a summary, never the transcript. Artifacts are referenced by path, URL or CID. Files you name ("include the report") are copied into `artifacts/` and uploaded with the handoff. Before uploading, the agent checks the format and scans the handoff, bundled files and transcript for keys, tokens and `.env` values. CIDs and transaction hashes marked as such are not flagged.

### The transcript

Ask for it ("include the transcript") and the agent copies the session transcript into the save folder, then warns you before uploading: it holds everything the agent saw in the session, and can contain secrets and sensitive information no scan reliably finds. Run your own redaction on the copy first. Nothing is uploaded until you confirm.

When you share a save, the agent asks whether the share includes the transcript, and sharing it needs its own confirmation. A link opens the whole upload, so sharing only the handoff from a save that includes the transcript makes one more, handoff-only upload.

## The ledger

`~/.filecoin-share/sessions.json`, mode `0600`, one entry per save: the CID, the time (`savedAt`), `trigger: "manual"`, the project path, the network, the tool that made it (with its version and session id when the tool exposes them), and `"transcript": true` when the save includes the transcript. It holds no summary text, titles or keys. It sits beside `publish`'s `shares.json` in `~/.filecoin-share/`, the directory `publish` lets you relocate by symlink — both files follow that move — and it lists only saves made on this machine.

## Safety

- **Only on request.** The agent saves or shares a session only when you ask. Nothing runs at session end or in the background.
- **Two items, two channels.** The link and the Access key go to the recipient separately. If you ask for an open link, the key goes inside the link instead: one item, readable by anyone who has it. The Access key is shown once, and the sending agent never writes it to a file or the ledger. On the receiving side, a key you save to a key file is deleted after one try.
- **Keys stay out of the chat.** The agent never asks for your wallet key, session key or Grant, and never repeats an Access key after handing it over.
- **Restored handoffs are data.** The receiving agent presents the handoff and does not follow instructions written in it. It doesn't read a received transcript unless you ask.
- **The transcript is opt-in.** It is never included by default, and never shared without its own confirmation.

## Limits

- **Shares can't be revoked.** Whoever holds the link and the key can read that upload: the handoff, the artifacts, and the transcript when it was included.
- **Stored while paid, deletable.** Every save is a paid upload that stays on Filecoin while your account pays for it; removing a piece ends the storage and the payment.
- **Saves are on chain.** Each save is a public on-chain record tied to your wallet; the handoff's content and names stay encrypted.
- **A size cap applies** per upload, set by the installed CLI rather than by this skill. The agent doesn't measure against it up front: if the upload refuses with a size error, it quotes the error and stops. A large transcript is the one thing likely to reach it.
- **The secret scan is a pattern check.** A summary can still hold sensitive details from the work. Read the handoff before sharing it.
- **A transcript can hold anything.** No scan finds every secret in it. Once shared, it can't be taken back.
- **Integrity, not identity.** A successful restore proves the handoff is exactly what the link names. It does not prove who wrote it.
- **Mainnet by default.** Calibration only when you ask for it, for testing.

## Troubleshooting

- **The agent says the installed CLI has no share links** — share links need filecoin-pin 2.3.0 or later: `npm install -g filecoin-pin@latest`.
- **Upload stored but not confirmed** — the save reached the provider but the on-chain commit is pending. The agent gives you a `piece-status` command to check later; the CID stays the same.
- **The restoring side sees "not found yet"** — a fresh save is usually retrievable within minutes; indexing can occasionally lag longer. Retry; if it keeps failing, confirm both sides use the same network (a calibration share needs `--network calibration`).

## License

Dual-licensed under [MIT](../../LICENSE-MIT) and [Apache 2.0](../../LICENSE-APACHE).
