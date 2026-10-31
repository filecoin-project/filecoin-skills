# filecoin-pin CLI reference for encrypted sharing

The commands this skill runs, condensed. When this file and `filecoin-pin <command> --help` disagree, the help output wins.

The CLI prints each value this skill needs on a labelled line. Find values by their shape, not by exact wording: the link contains `#v1/`, the Access key starts with `fak1_`, the Piece CID starts with `bafkzcib`, and the IPFS root CID (the Encrypted root CID for an encrypted upload) starts with `bafybei` or, for content up to 1 MiB, `bafkrei`.

## Install and version check

```bash
command -v filecoin-pin || npm install -g filecoin-pin@latest   # needs Node 24+
filecoin-pin get --help | grep -q -- '--share' && echo sharing-ok
```

If the second line prints nothing, run `npm install -g filecoin-pin@latest` and check again. Still nothing: the installed filecoin-pin has no share links. Stop and tell the user.

Exit codes for every command: `0` success, `1` error, `2` incomplete (a wait timed out or a login is not finished).

## Network

Mainnet by default. Use calibration only when the user asks for it, for testing. Then pass `--network calibration` to every command (`login`, `balance`, `add`, `get-share-link`, `get`), and tell the recipient to pass it too: the link doesn't name its network.

The saved login records its own `NETWORK`. Before the first upload in a session, run `filecoin-pin balance --no-update-check` (with `--network calibration` when testing) and check that the network it reports matches. A mismatch: stop and tell the user.

## Credentials

Sending and restoring your own uploads need one of two credentials. Receiving a share needs none.

| Mode | Where it comes from | Use |
|---|---|---|
| Session key with a Grant | `filecoin-pin login --scopes createDataSet,addPieces,encrypt`, saved in `session.env` | Default |
| Owner wallet | `PRIVATE_KEY` in the environment | Only when the user asks for it |

The saved login lives in `session.env` in the CLI data dir: macOS `~/Library/Application Support/filecoin-pin/session.env`, Linux `~/.local/share/filecoin-pin/session.env`. It holds the session private key and the Grant. Check it with boolean tests only, never print it:

```bash
f="$HOME/Library/Application Support/filecoin-pin/session.env"   # Linux: $HOME/.local/share/filecoin-pin/session.env
grep -q '^WALLET_ADDRESS=' "$f" && grep -q '^GROUP_KEY_GRANT=' "$f" && echo login-ok
```

`login-ok` means the login can encrypt. Otherwise run the login:

1. `filecoin-pin login --scopes createDataSet,addPieces,encrypt` (add `--no-browser` on a headless machine). The CLI opens or prints a console link. Give it to the user on its own line. The user connects the owner wallet in the console and approves.
2. The console then shows a Grant (`fgr1_…`). The Grant is a secret: the user must not paste it into the chat. Ask them to finish in their own terminal, after copying the Grant:

   ```bash
   pbpaste | filecoin-pin login --grant -     # Linux: xclip -o -selection clipboard | filecoin-pin login --grant -
   ```

3. Run the `login-ok` check again.

A Grant gives the session key permanent read access to every upload under the owner's group key, including future ones. Expiry and revoking the key do not take it back. Tell the user this once, when they first log in with `encrypt`.

Owner wallet mode runs only when the user asks for it. They set `PRIVATE_KEY` in the environment themselves. Never ask for the key, never read a key file with a command that prints bytes, and never write one.

Other credential flags (`--private-key`, `--session-key`, `--wallet-address`) turn off the saved login entirely. Don't pass them.

## add: encrypt and upload

```bash
filecoin-pin add <path> --encrypt --get-share-link-restricted --egress-provider none --no-update-check
```

- `--encrypt` packs the file or folder, encrypts it, and uploads the envelope as `encrypted.fee`. Names, file sizes and folder structure stay inside the ciphertext. The total size is public.
- `--get-share-link-restricted` makes a restricted Share link right after the upload is stored: the link plus a separate Access key. The CLI checks the flag before uploading. If the share fails after a successful upload, `add` only warns: run `get-share-link <CID> --restricted` to retry.
- Never use plain `--get-share-link`. It prints an open link that carries its own key, so anyone who sees the link can read the content.
- Leave out the share flag to store without sharing.
- Never pass `--no-ipfs`. A Share link fetches the upload by its IPFS root CID, so a `--no-ipfs` upload can't be shared.
- The root CID in the summary is the Encrypted root CID. The packing step prints the same value earlier.
- Owner wallet mode doesn't check that the account can pay for this upload. Run the same command with `--dry-run` first: it prints the cost and uploads nothing. Show the cost to the user before the real run.
- Session key mode checks funding before packing. When the account can't pay, it exits 1 with a pre-filled console funding link. Hand the link to the user, wait for them to fund, and run the same command again. This is the only case where you run `add` again yourself: it stops before packing, so nothing was uploaded.
- An upload takes one to a few minutes. Run it in the background and poll the output. Let it finish: a slow upload is not a failed one. Never stop it to start again.
- **Never run `add --encrypt` again to recover from a failed or stuck upload.** Every run encrypts with a new random salt, so it makes a different CID and a second full, paid upload. Follow "Upload stored but not confirmed" in Troubleshooting instead.

## get-share-link: share an earlier upload

```bash
filecoin-pin get-share-link <encrypted-root-cid> --restricted
```

Always pass `--restricted`: without it the link carries its own key. Works with the owner wallet or a session key with a Grant. It reads the upload's header back from a storage provider (at most about 1 MiB) and writes nothing locally. Every run makes a new link with its own Access key.

## Share link output

With `--restricted`, `add` and `get-share-link` print the Share link and the Access key as two labelled values, with a reminder to send them by different channels. The link starts with the viewer URL and carries everything in the fragment after `#v1/`. The Access key starts with `fak1_`.

## get: restore your own upload

```bash
filecoin-pin get <encrypted-root-cid> <output-dir>
```

Needs the owner wallet or a session key with a Grant. `get` finds providers through IPNI and the owner's own data sets, checks every block against the CID, decrypts, and saves the content under its original name. It never overwrites: a taken name gets a number, like `report(1).pdf`. It prints the saved path at the end.

## get --share: open a share

No CID argument: the link names the upload. No credentials. Mainnet by default; add `--network calibration` for a calibration share. Quote the link: it contains `#` and `&`.

### The Access key

The Access key is a secret: whoever holds it and the link can read the share. Keep it out of the chat and out of every command you write. Never ask the user to paste it, and never pass it with `--access-key` (a flag shows up in `ps` and shell history). Use the first case that applies:

1. **Already in the environment.** The user set it before starting the agent (`read -rs SHARE_ACCESS_KEY && export SHARE_ACCESS_KEY`). Check without printing it, then run the plain command; the CLI reads the variable:

   ```bash
   test -n "$SHARE_ACCESS_KEY" && echo key-set
   filecoin-pin get --share '<link>' <output-dir>
   ```

2. **In a key file.** No `key-set`: ask the user to save the key in a file only they can read, by running this in their own terminal. The key is pasted at a hidden prompt, so it never shows on screen or in shell history:

   ```bash
   mkdir -p ~/.filecoin-share && read -rs k && printf %s "$k" > ~/.filecoin-share/access-key && chmod 600 ~/.filecoin-share/access-key && unset k
   ```

   When they say it's done, check it without reading it, open the share, and delete the file once the share opened:

   ```bash
   test -s ~/.filecoin-share/access-key && echo key-file
   SHARE_ACCESS_KEY="$(cat ~/.filecoin-share/access-key)" filecoin-pin get --share '<link>' <output-dir>
   rm -f ~/.filecoin-share/access-key
   ```

   After a wrong-key error, keep the file deleted and ask the user to save the key again.

3. **Pasted into the chat anyway.** It is already in this conversation's history, so use it: `SHARE_ACCESS_KEY='fak1_…' filecoin-pin get --share '<link>' <output-dir>`. Tell the user once that anyone who can read this conversation's history can open the share. Never repeat the key in your replies.

The CLI opens the payload with the key before downloading, so a wrong key fails fast. Then it downloads, checks every block against the CID, decrypts (the envelope rejects any change to the ciphertext), and prints the saved path.

## Troubleshooting

**Upload stored but not confirmed.** `add` exits `2`, or reports that the commit on a provider timed out, after the upload reached the provider. The transaction was submitted and may still confirm. Don't upload again:

1. Keep the Encrypted root CID, the data set ID and the Piece CID from the output.
2. Every few minutes, check the piece:

   ```bash
   filecoin-pin data-set piece-status <data-set-id> <piece-cid>
   ```

   Always pass the Piece CID: without it, the command opens an interactive pager that fails in an agent shell.

3. Once the piece is listed as `active`, it is confirmed. Not listed, or `offchain orphaned` (the provider holds it, the chain doesn't yet), means not yet. When it is, make the share with `get-share-link <encrypted-root-cid> --restricted`. It reads the upload's header from the provider; nothing is uploaded again.
4. Still unconfirmed after about 30 minutes: tell the user the content is stored but not confirmed, give them the CID and the data set ID, and stop. Retry `get-share-link` later; don't upload again.

**Only the second copy failed** (`Got 1/2 copies`). The content is stored on the first provider, and the share works. Report it as reduced redundancy, not a failure. Repair only if the user asks: `add` is not the repair (a new run means a new CID). Point them to the publish skill's repair steps, or the CLI's `data-set` commands.

**Upload failed before it was stored** (for example `Failed to create upload session`, or a provider answering 503). Don't run `add` again. Tell the user the upload failed, with the error line, and that running it again uploads under a new CID. Run it again only when the user asks.

`No credentials found.` No usable login. Run the login above.

`Encrypted uploads need the owner wallet (set PRIVATE_KEY) or a session key with a group key Grant …` The login has no Grant. Run the login above with `encrypt` in `--scopes`.

`Session expired (key …)`. The session key is spent. With the user's agreement, run `filecoin-pin logout`, then the login above.

A missing scope prints the key, the missing scopes and a console link. Give the link to the user as is.

`get --share` errors, each with its own message:

- wrong Access key: ask the user to check they copied the whole key, starting with `fak1_`;
- link for another upload: the link was edited or mixed up with another one;
- not found yet: the upload is new and indexing can take about 20 minutes. Wait and retry;
- incomplete download: retry later.
