# Send an encrypted share

Commands, output formats and errors are in `filecoin-pin-cli.md` next to this file.

## 1. Check the CLI and credentials

Run the version check, the credentials check and the network check from `filecoin-pin-cli.md`. Log in with `encrypt` if the credentials check fails.

## 2. Check the scope

Share exactly the paths the user named, one share per path. A folder becomes one share with everything inside it. Dotfiles are skipped unless the user asks for them (`--include-hidden`).

Before sharing a folder, list it (`find <dir> -maxdepth 2`) and warn about anything that looks unintended: `.env` files, keys, `node_modules`, build output. The recipient can read everything in the share, and a share can't be revoked.

## 3. Upload and share

New content:

```bash
filecoin-pin add <path> --encrypt --get-share-link-restricted --egress-provider none --no-update-check
```

An earlier encrypted upload, named by its Encrypted root CID:

```bash
filecoin-pin get-share-link <encrypted-root-cid> --restricted
```

If `add` stored the upload but warned that the share failed, run `get-share-link --restricted` with the `Root CID:` from the summary. With calibration, add `--network calibration` to both commands.

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
