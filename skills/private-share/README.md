# private-share

Share a file or folder with one person or agent, encrypted. The skill drives the [filecoin-pin](https://github.com/filecoin-project/filecoin-pin) CLI: it encrypts the content, stores it on Filecoin mainnet, and hands back two items, a Share link and an Access key. The recipient needs both to read the content. The same skill opens a share you received.

> **Status: preview.**

Suite terms (Share link, Access key, Encrypted root CID) are in [`../CONTEXT.md`](../CONTEXT.md).

## When to use

Use it for a report, a dataset, a folder of notes, or anything else one recipient should read and nobody else. Say "share this privately" or "encrypt and send this to Ana".

Use [`publish`](../publish/) instead for content anyone may read.

## Install

```bash
npx skills add filecoin-project/filecoin-skills --skill private-share
```

Add `-g` to install for every project.

## Prerequisites

Receiving needs only Node 24+ and filecoin-pin. The agent installs filecoin-pin on first run.

Sending also needs a funded account on Filecoin mainnet (see the [suite README](../../README.md#before-you-start)) and a login that can encrypt:

```bash
filecoin-pin login --scopes createDataSet,addPieces,encrypt
```

Approve the session key in the console with your owner wallet. The console then shows a Grant (`fgr1_…`). Copy it and finish in your own terminal, not in the chat:

```bash
pbpaste | filecoin-pin login --grant -     # Linux: wl-paste --no-newline, or xclip -o -selection clipboard
```

The Grant gives this session key permanent read access to all your encrypted uploads, including future ones in the datasets tagged with the same group key. Revoking or expiring the key does not take that back.

## Quick start

Send:

```
> share ./report.pdf privately with Ana
```

The agent uploads, then shows:

```
Share link (send by one channel, e.g. email):
https://…#v1/bafy…&d=…

Access key (send by a different channel, e.g. a chat message):
fak1_…
```

Receive: give the agent the link, and keep the Access key out of the chat. Set it in the shell you start the agent from (`read -rs` takes it without echoing it), or the agent asks you to save it in a key file only you can read:

```bash
read -rs SHARE_ACCESS_KEY && export SHARE_ACCESS_KEY   # paste the key, press Enter
```

```
> open this share into ./inbox: https://…#v1/bafy…&d=…
```

The agent runs `filecoin-pin get --share`, which checks every block against the CID and decrypts. It reports where it saved the content.

## Safety

- **Two items, two channels.** The link and the Access key go to the recipient separately. Either one alone opens nothing.
- **The Access key is shown once.** The agent never writes it to a file, a ledger or a log.
- **Keys stay out of the chat.** The agent never asks for your wallet key, session key or Grant, and never repeats an Access key after handing it over.
- **Exactly what you name.** The agent shares only the paths you name and warns before sharing a folder with `.env` files, keys or `node_modules` in it.

## Limits

- **Shares can't be revoked.** Whoever holds the link and the key can read the content for as long as it is stored.
- **Stored for good.** Encrypted content stays on Filecoin. Every share of new content is a paid upload.
- **Size is visible.** Names and folder structure are encrypted, but the total size is public.
- **Mainnet by default.** Calibration only when you ask for it, for testing.
- **Integrity, not identity.** A successful `get --share` proves the content is exactly what the link names. It does not prove who made it.

## License

Dual-licensed under [MIT](../../LICENSE-MIT) and [Apache 2.0](../../LICENSE-APACHE).
