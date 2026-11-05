---
name: private-share
description: Use when the user wants to share a file or folder privately with one person or agent, or says "share this privately", "encrypt and share this", "send this encrypted", "private link", "share this with <name> privately", "only <name> should read this", "make a share link for <CID>". Also use when the user has a Filecoin Share link and Access key to open, or says "open this share", "download this share link", "I got a share link and a key", "decrypt this share", or wants back their own earlier encrypted upload ("restore my encrypted upload", "get my encrypted file back"). Encrypts with the filecoin-pin CLI on Filecoin (mainnet by default) and hands back a Share link and a separate Access key.
---

# private-share

Encrypt a file or folder, store it on Filecoin (mainnet by default) with the `filecoin-pin` CLI, and hand back a Share link and an Access key for one recipient. Or open a share someone sent. Drive the CLI directly, with no wrapper scripts.

## Route the request

Read only the file the request needs:

- Sharing something (encrypt, send, make a link): `references/send.md`.
- Opening a share (the user has a link with `#v1/` and a `fak1_…` key): `references/receive.md`.
- Restoring your own earlier encrypted upload (a CID, no link): `get` in `references/filecoin-pin-cli.md`.

`references/filecoin-pin-cli.md` holds the commands, credentials and errors; read that and `filecoin-pin --help`, never the web. `send.md` and `receive.md` point to it. Suite terms (Share link, Access key, Grant, Encrypted root CID) are defined in `../CONTEXT.md`.

## Red lines

Hard rules; the owning section carries the full rule. Skim before every share.

- Mainnet by default. Calibration only when the user asks for it, for testing, with `--network calibration` on every command (`references/filecoin-pin-cli.md`, Network).
- Share exactly the paths the user named, and only when the user asks. A folder with anything that looks unintended in it stops for an explicit yes (`references/send.md`, step 2).
- With the owner wallet, run `add --dry-run` first and show the user the cost before the real upload (`references/send.md`, step 3).
- Wallet keys, session keys and Grants never enter the conversation, command output you show, logs, or files you write. Check secrets files with boolean tests only (`test -f`, `grep -q`) (`references/filecoin-pin-cli.md`, Credentials).
- Show the Access key once, labeled, apart from the link. Tell the user to send the two by different channels, and that this conversation's history now holds the key. Never write the key you hand over to a file or a log, and never repeat it later. (Receiving is different: the user may write a key they received to a short-lived key file, as in `references/filecoin-pin-cli.md`, The Access key.)
- Run `add --encrypt` once per upload — each named path is its own upload, a `--dry-run` isn't one. Never re-run it to recover from a failure, an exit `2`, or a stuck run, and never stop a running one: every re-run uploads and pays again under a new CID. The one self-service exception, the funding stop, and all recovery steps: `references/filecoin-pin-cli.md`, add and Troubleshooting.
- Single-quote every Share link in a shell: it contains `#` and `&` (`references/receive.md`, step 3).
- "Not altered" means integrity: every block matched the CID and the envelope rejected changes. Never claim it proves who made the content (`references/receive.md`, step 4).
