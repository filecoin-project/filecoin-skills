---
name: private-share
description: Use when the user wants to share a file or folder privately with one person or agent, or says "share this privately", "encrypt and share this", "send this encrypted", "private link", "share this with <name> privately", "only <name> should read this", "make a share link for <CID>". Also use when the user has a Filecoin Share link and Access key to open, or says "open this share", "download this share link", "I got a share link and a key", "decrypt this share". Encrypts with the filecoin-pin CLI on Filecoin (mainnet by default) and hands back a Share link and a separate Access key.
---

# private-share

Encrypt a file or folder, store it on Filecoin mainnet with the `filecoin-pin` CLI, and hand back a Share link and an Access key for one recipient. Or open a share someone sent. Drive the CLI directly, with no wrapper scripts.

## Route the request

Read only the file the request needs:

- Sharing something (encrypt, send, make a link): `references/send.md`.
- Opening a share (the user has a link with `#v1/` and a `fak1_…` key): `references/receive.md`.

`references/filecoin-pin-cli.md` holds the commands, credentials and errors. `send.md` points to it.

## Red lines

- Mainnet by default. Calibration only when the user asks for it, for testing, with `--network calibration` on every command.
- Share exactly the paths the user named, and only when the user asks.
- Wallet keys, session keys and Grants never enter the conversation, command output you show, logs, or files you write. Check secrets files with boolean tests only (`test -f`, `grep -q`).
- Show the Access key once, labelled, apart from the link. Tell the user to send the two by different channels. Never write the key to a file, ledger or log, and never repeat it later.
- Always make restricted links (`--restricted`, `--get-share-link-restricted`), so the link and the Access key stay apart.
- Run `add --encrypt` once per request (a `--dry-run` before it doesn't count: it uploads nothing). Never run it again after it fails, exits `2`, or seems stuck, and never stop a running one to start over: every run uploads and pays again under a new CID. The only exception is the funding stop, which exits before anything is packed. Otherwise follow Troubleshooting in `references/filecoin-pin-cli.md`, or tell the user.
- Single-quote every Share link in a shell: it contains `#` and `&`.
- "Not altered" means integrity: every block matched the CID and the envelope rejected changes. Never claim it proves who made the content.
