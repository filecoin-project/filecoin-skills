# private-share

Share a file or folder with one person or agent, encrypted. The skill drives the [filecoin-pin](https://github.com/filecoin-project/filecoin-pin) CLI: it encrypts the content, stores it on Filecoin (mainnet by default), and hands back two items, a Share link and an Access key. The recipient needs both to read the content. The same skill opens a share you received.

> **Status: preview.**

Suite terms (Share link, Access key, Grant, Encrypted root CID) are in [`../CONTEXT.md`](../CONTEXT.md).

## When to use

Use it for a report, a dataset, a folder of notes, or anything else one recipient should read and nobody else. Say "share this privately" or "encrypt and send this to Ana".

Use [`publish`](../publish/) instead for content anyone may read.

## Install

```bash
npx skills add filecoin-project/filecoin-skills --skill private-share
```

Add `-g` to install for every project. It installs on its own; it does not need `session-share`.

## Prerequisites

Receiving needs only Node 24+ and `filecoin-pin` 2.3.0 or later. The agent installs filecoin-pin on first run.

Sending also needs a funded account on Filecoin mainnet (see the [suite README](../../README.md#before-you-start)) and a login that can encrypt:

```bash
filecoin-pin login --scopes createDataSet,addPieces,encrypt
```

Before you approve: with `encrypt` in the scopes, the console issues a Grant (`fgr1_…`) that gives this session key permanent read access to every encrypted upload under your group key, including later ones. Revoking or expiring the key does not take that back.

Approve the session key in the console with your owner wallet, then copy the Grant the console shows and finish in your own terminal, not in the chat:

```bash
pbpaste | filecoin-pin login --grant -     # Linux: wl-paste --no-newline, or xclip -o -selection clipboard
```

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

## What it costs

Each upload is paid storage on Filecoin; making a link for an existing upload costs nothing. Ask for a dry run and the agent shows the cost without uploading. When the console asks you to deposit, most of the number is a refundable lockup hold rather than a charge; [`publish`'s cost breakdown](../publish/README.md#what-it-costs) explains the split, and it is the same for encrypted uploads.

## Safety

- **Two items, two channels.** The link and the Access key go to the recipient separately. Either one alone opens nothing. If you ask for an open link, the key goes inside the link instead: one item, readable by anyone who has it.
- **The Access key is shown once.** The agent never writes it to a file or a log.
- **Keys stay out of the chat.** The agent never asks for your wallet key, session key or Grant, and never repeats an Access key after handing it over.
- **Exactly what you name.** The agent shares only the paths you name, and stops for your explicit yes before sharing a folder with anything unintended in it — credential or key files, `node_modules`, build output.

## Limits

- **Shares can't be revoked.** Whoever holds the link and the key can read the content for as long as it is stored.
- **Stored while paid, deletable.** Encrypted content stays on Filecoin while your account pays for it; removing a piece ends the storage and reduce the payment. Every share of new content is a paid upload.
- **Size is visible.** Names and folder structure are encrypted, but the total size is public, the encrypted bytes are fetchable by anyone with the CID (they open only with the key), and the upload is an on-chain record tied to your wallet.
- **A size cap applies** per upload, set by the installed CLI rather than by this skill. The agent doesn't measure against it up front: if the upload refuses with a size error, it quotes the error and stops. A folder packs into one piece, so the whole tree counts against the cap.
- **Mainnet by default.** Calibration only when you ask for it, for testing.
- **Integrity, not identity.** A successful `get --share` proves the content is exactly what the link names. It does not prove who made it.

## Troubleshooting

- **The agent says the installed CLI has no share links** — share links need filecoin-pin 2.3.0 or later: `npm install -g filecoin-pin@latest`.
- **Upload stored but not confirmed** — the content reached the provider but the on-chain commit is pending. The agent gives you a `piece-status` command to check later; the link stays the same.
- **The recipient sees "not found yet"** — a fresh upload is usually retrievable within minutes; indexing can occasionally lag longer. Retry; if it keeps failing, confirm you both use the same network (a calibration share needs `--network calibration`).

## License

Dual-licensed under [MIT](../../LICENSE-MIT) and [Apache 2.0](../../LICENSE-APACHE).
