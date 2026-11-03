# Send an encrypted share

Commands, output formats and errors are in `filecoin-pin-cli.md` next to this file.

## 1. Check the CLI and credentials

Run the version check and the network check from `filecoin-pin-cli.md`. If the user chose the owner wallet (`PRIVATE_KEY`), skip the credentials check: it only looks at the saved login. Otherwise run it, and log in with `encrypt` if it fails.

## 2. Check the scope

Share exactly the paths the user named, one share per path. A folder becomes one share with everything inside it. Dotfiles are skipped unless the user asks for them (`--include-hidden`).

Before sharing a folder, list it (`find <dir> -maxdepth 2`) and warn about anything that looks unintended: `.env` files, keys, `node_modules`, build output. The recipient can read everything in the share, and a share can't be revoked.

## 3. Upload and share

New content:

```bash
filecoin-pin add <path> --encrypt --get-share-link-restricted --egress-provider none --no-update-check
```

With the owner wallet, run it with `--dry-run` first, show the user the cost, and run the real upload only after they say yes (see `add` in `filecoin-pin-cli.md`). With the share flag, run it in the foreground: its output holds the Access key.

An earlier encrypted upload, named by its Encrypted root CID:

```bash
filecoin-pin get-share-link <encrypted-root-cid> --restricted
```

If `add` stored the upload but warned that the share failed, run `get-share-link --restricted` with the root CID from the summary. With calibration, add `--network calibration` to both commands.

If `add` fails or exits `2`, never run it again to recover: follow Troubleshooting in `filecoin-pin-cli.md`. A second run makes a new CID and pays for a second upload.

## 4. Hand over the link and the Access key

Show the two items once, labelled, each on its own line, in this shape:

```
Share link (send by one channel, e.g. email):
https://…#v1/…

Access key (send by a different channel, e.g. a chat message):
fak1_…
```

Then tell the user:

- whoever holds both can read this content, and the share can't be revoked;
- the recipient opens it in a browser through the link, or with this skill (`filecoin-pin get --share`);
- the Access key is not saved anywhere, so they should send it now. A new key later means a new link (`get-share-link` again).

After this reply, never repeat the Access key, and never write it to a file, a ledger or a log. Mention the Encrypted root CID so the user can make another link later.
