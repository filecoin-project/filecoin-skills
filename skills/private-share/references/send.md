# Send an encrypted share

Commands, output formats and errors are in `filecoin-pin-cli.md` next to this file.

## 1. Check the CLI and credentials

Run the version check:

```bash
command -v filecoin-pin || npm install -g filecoin-pin@latest   # needs Node 24+; always latest, so CLI improvements deploy
filecoin-pin get --help | grep -q -- '--share' && echo sharing-ok
```

No `sharing-ok`: follow "Install and version check" in `filecoin-pin-cli.md`. Then run the network check from the same file. If the user chose the owner wallet (`PRIVATE_KEY`), skip the credentials check: it only looks at the saved login. Otherwise run it, and log in with `encrypt` in `--scopes` if it fails (the login steps are under Credentials there).

## 2. Check the scope

Share exactly the paths the user named, one share per path. A folder becomes one share with everything inside it. Dotfiles are skipped unless the user asks for them (`--include-hidden`) — except when the folder's own name starts with a dot: then the CLI packs the dotfiles inside it regardless.

Before sharing a folder, list it (`find '<dir>' -maxdepth 2`, with the path quoted) and check for anything that looks unintended: credential and key files (`credentials.json`, `*.pem`, `*.key`, `id_rsa*`, `serviceAccount.json`), `node_modules`, build output — and dotfiles like `.env` when `--include-hidden` or a dot-named folder is in play.

🔴 CHECKPOINT — anything unintended in the listing: show those paths, say that the recipient can read everything in the share and that a share can't be revoked, and wait for an explicit yes before going on.

## 3. Upload and share

New content:

```bash
filecoin-pin add <path> --encrypt --get-share-link-restricted --data-set-metadata source=private-share-skill --egress-provider none --no-update-check
```

With the owner wallet, run it with `--dry-run` first and show the user the cost. 🔴 CHECKPOINT — run the real upload only after they say yes (see `add` in `filecoin-pin-cli.md`). With the share flag, run the real upload in the foreground: its output holds the Access key.

An earlier encrypted upload, named by its Encrypted root CID:

```bash
filecoin-pin get-share-link <encrypted-root-cid> --restricted --no-update-check
```

If `add` stored the upload but warned that the share failed, run `get-share-link --restricted` with the Encrypted root CID from the summary. With calibration, add `--network calibration` to both commands.

If `add` fails or exits `2`, never run it again to recover: follow Troubleshooting in `filecoin-pin-cli.md`. A second run makes a new CID and pays for a second upload.

## 4. Hand over the link and the Access key

Show the two items once, labeled, each on its own line, in this shape:

```
Share link (send by one channel, e.g. email):
https://…#v1/…

Access key (send by a different channel, e.g. a chat message):
fak1_…
```

Then tell the user:

- whoever holds both can read this content, and the share can't be revoked;
- this conversation's history now holds the Access key: anyone who can read this chat or its transcript can open the share;
- the recipient opens it with this skill (`filecoin-pin get --share`), or in a browser through the link — tell them that the site before `#v1/` is the viewer page they are trusting, so a link that looks off should be opened with the CLI instead. The link is usually retrievable within minutes; "not found yet" on the recipient's side means indexing is still catching up — wait and retry, not a broken link;
- the Access key is not saved anywhere, so they should send it now. A new key later means a new link (`get-share-link` again).

After this reply, never repeat the Access key, and never write it to a file or a log. Mention the Encrypted root CID and tell the user to note it: this skill keeps no ledger, and without that CID another link to the same upload can't be made later.
