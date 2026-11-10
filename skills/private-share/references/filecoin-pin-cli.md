# filecoin-pin CLI reference for encrypted sharing

The commands this skill runs, condensed. Verified against filecoin-pin v2.3.0, the first release with share links. When this file and `filecoin-pin <command> --help` disagree, the help output wins. This file ships identically in `private-share` and `session-share`: a fix here must land in both copies.

The CLI prints each value this skill needs on a labeled line. Find values by their shape, not by exact wording: the link contains `#v1/`, the Access key starts with `fak1_`, the Piece CID starts with `bafkzcib`, and the IPFS root CID (the Encrypted root CID for an encrypted upload) starts with `bafyb` (directories and chunked files) or `bafkrei` (single files up to 1 MiB).

## Install and version check

```bash
command -v filecoin-pin || npm install -g filecoin-pin@latest   # needs Node 24+; always latest, so CLI improvements deploy
filecoin-pin get --help | grep -q -- '--share' && echo sharing-ok
```

No `sharing-ok` (the second line prints nothing): the installed filecoin-pin predates share links. Run `npm install -g filecoin-pin@latest` and check again. If `npm install -g` fails with a permission error (`EACCES`), install to a user prefix instead: `npm install -g --prefix "$HOME/.local" filecoin-pin@latest`, then use `$HOME/.local/bin/filecoin-pin`. Still no `sharing-ok`: stop and tell the user the installed CLI has no share links and filecoin-pin 2.3.0 or later is needed.

Exit codes for every command: `0` success, `1` error, `2` incomplete (a wait timed out, a login is not finished, or a confirmation was declined).

## Network

Mainnet by default. Use calibration only when the user asks for it, for testing. Then pass `--network calibration` to every command (`login`, `balance`, `add`, `get-share-link`, `get`), and tell the recipient to pass it too: the link doesn't name its network.

The saved login records its own `NETWORK`. Before the first upload in a session, run `filecoin-pin balance --no-update-check` (with `--network calibration` when testing) and check that the network it reports matches. A mismatch: stop and tell the user.

## Clipboard command

Secrets (the Grant, the Access key) reach the CLI through the clipboard, so they never enter the chat. Find the paste command for this machine before asking the user to use it:

```bash
case "$(uname -s)" in
  Darwin) echo pbpaste ;;
  Linux)
    if [ -n "${WAYLAND_DISPLAY:-}" ] && command -v wl-paste >/dev/null; then echo 'wl-paste --no-newline'
    elif [ -n "${DISPLAY:-}" ] && command -v xclip >/dev/null; then echo 'xclip -o -selection clipboard'
    elif [ -n "${DISPLAY:-}" ] && command -v xsel >/dev/null; then echo 'xsel --clipboard --output'
    else echo none; fi ;;
  *) echo none ;;
esac
```

Below, `<paste>` is the command it printed. `none` means no clipboard (a headless or SSH session): use the no-clipboard fallback where one is given.

## Credentials

Sending and restoring your own uploads need one of two credentials. Receiving a share needs none.

| Mode | Where it comes from | Use |
|---|---|---|
| Session key with a Grant | `filecoin-pin login --scopes createDataSet,addPieces,encrypt`, saved in `session.env` | Default |
| Owner wallet | `PRIVATE_KEY` in the environment | Only when the user asks for it |

Before choosing the mode, check the environment with a boolean test: `test -n "$PRIVATE_KEY" && echo owner-mode`. `owner-mode` means the CLI will pay with the owner wallet even when a saved login exists; treat the whole run as owner wallet mode.

The saved login lives in `session.env` in the CLI data dir: macOS `~/Library/Application Support/filecoin-pin/session.env`, Linux `~/.local/share/filecoin-pin/session.env`. It holds the session private key and the Grant. Check it with boolean tests only, never print it:

```bash
f="$HOME/Library/Application Support/filecoin-pin/session.env"   # Linux: $HOME/.local/share/filecoin-pin/session.env
grep -q '^WALLET_ADDRESS=' "$f" && grep -q '^GROUP_KEY_GRANT=' "$f" && echo login-ok
```

`login-ok` means the login can encrypt. Otherwise run the login:

1. Before anything opens, tell the user once what they are about to approve: with `encrypt` in the scopes, the console issues a Grant that gives this session key permanent read access to every encrypted upload under the owner's group key, including later ones — expiry and revoking the key do not take it back. Then run `filecoin-pin login --scopes createDataSet,addPieces,encrypt` (add `--no-browser` on a headless machine). The CLI opens or prints a console link. Give it to the user on its own line. 🔴 CHECKPOINT — the user connects the owner wallet in the console and approves; nothing proceeds until they do.
2. The console then shows a Grant (`fgr1_…`). The Grant is a secret: the user must not paste it into the chat. Ask them to copy the Grant and run this, in the session with a leading `!` or in their own terminal:

   ```bash
   <paste> | filecoin-pin login --grant -
   ```

   No clipboard (`none`): they run `filecoin-pin login --grant -` in their own terminal and paste the Grant at its prompt.

3. Run the `login-ok` check again.

Owner wallet mode runs only when the user asks for it. They set `PRIVATE_KEY` in the environment themselves. Never ask for the key, never read a key file with a command that prints bytes, and never write one.

Other credential flags (`--private-key`, `--session-key`, `--wallet-address`) turn off the saved login entirely. Don't pass them.

## add — encrypt and upload

```bash
filecoin-pin add <path> --encrypt --get-share-link-restricted --egress-provider none --no-update-check
```

- `--encrypt` packs the file or folder, encrypts it, and uploads the envelope (the encrypted container holding the packed content) as a file named `encrypted.fee`. Names, file sizes and folder structure stay inside the ciphertext. Public: the total size, the ciphertext itself (anyone can fetch it by its CID; it opens only with the key), and the on-chain record that this wallet stored this piece at this time.
- `--get-share-link-restricted` makes a restricted Share link right after the upload is stored: the link plus a separate Access key. The CLI checks the flag before uploading. If the share fails after a successful upload, `add` only warns: run `get-share-link <CID> --restricted` to retry. The CLI's own warning omits `--restricted` (fixed in filecoin-project/filecoin-pin#813, unreleased); add it, don't copy the hint as printed, or the retry makes an open link.
- Never use plain `--get-share-link`. It prints an open link that carries its own key, so anyone who sees the link can read the content.
- Leave out the share flag to store without sharing.
- Never pass `--no-ipfs`. A Share link fetches the upload by its IPFS root CID, so a `--no-ipfs` upload can't be shared.
- `--egress-provider none` is already the CLI's default; the flag stays explicit so a stray `EGRESS_PROVIDER` in the environment can never flip it.
- The root CID in the summary is the Encrypted root CID. The packing step prints the same value earlier.
- Owner wallet mode doesn't check that the account can pay. 🔴 CHECKPOINT — run the same command with `--dry-run` first: it prints the cost and uploads nothing. Show the cost to the user, and run the real upload only after they say yes.
- Session key mode also checks funding before packing. When the account can't pay, it stops with a pre-filled console funding link. This is the funding stop, and it has a recognizable shape: session-key mode, exit 1, a console funding link in the output, and no `Piece CID` line — nothing was packed or uploaded. Hand the link to the user, wait for them to fund, and run the same command again. This is the only case where you run `add` again yourself. Any other exit 1 is not the funding stop; owner wallet mode has no funding stop at all.
- An upload takes one to a few minutes. Let it finish: a slow upload is not a failed one. Never stop it to start again.
  - With a share flag, run it in the foreground with a long timeout (10 minutes). Its output holds the Access key, and a background run saves the whole output to a file.
  - Without a share flag, you can run it in the background and poll the output.
- **Never run `add --encrypt` again to recover from a failed or stuck upload.** Every run encrypts with a new random salt, so it makes a different CID and a second full, paid upload. Follow "Upload stored but not confirmed" in Troubleshooting instead.

## get-share-link — share an earlier upload

```bash
filecoin-pin get-share-link <encrypted-root-cid> --restricted --no-update-check
```

Always pass `--restricted`: without it the link carries its own key. Works with the owner wallet or a session key with a Grant. It reads the upload's header back from a storage provider (at most about 1 MiB) and writes nothing locally. Every run makes a new link with its own Access key.

## Share link output

With `--restricted`, `add` and `get-share-link` print the Share link and the Access key as two labeled values, with a reminder to send them by different channels. The link starts with the viewer URL — a browser page that decrypts in the visitor's browser; everything after `#v1/` travels in the URL fragment, which a browser never sends to the server. The Access key starts with `fak1_`.

The CLI never loads the viewer site. If a recipient opens the link in a browser instead of with this skill, the site before `#v1/` is what they are trusting: a tampered link can point at a lookalike page that asks for the Access key. A recipient in doubt should open the share with the CLI.

## get — restore your own upload

```bash
filecoin-pin get <encrypted-root-cid> <output-dir> --no-update-check
```

Needs the owner wallet or a session key with a Grant. `get` finds providers through IPNI and the owner's own data sets, checks every block against the CID, decrypts, and saves the content under its original name. It never overwrites: a taken name gets a number, like `report(1).pdf`. It prints the saved path at the end.

## get --share — open a share

No CID argument: the link names the upload. No credentials — a saved login on this machine is never needed to decrypt a share, though the CLI may load it, use its saved address when looking up providers, and mention it in its output; that is harmless. Mainnet by default; add `--network calibration` for a calibration share. Quote the link: it contains `#` and `&`. Always pass `<output-dir>`: without it the CLI saves into the current directory.

### The Access key

The Access key is a secret: whoever holds it and the link can read the share. Keep it out of the chat and out of every command you write; the only exception is case 3, when the user already pasted it. Never ask the user to paste it, and never pass it with `--access-key` (a flag shows up in `ps` and shell history). Use the first case that applies:

1. **Already in the environment.** The user set it before starting the agent (`read -rs SHARE_ACCESS_KEY && export SHARE_ACCESS_KEY`). Check without printing it, then run the plain command; the CLI reads the variable:

   ```bash
   test -n "$SHARE_ACCESS_KEY" && echo key-set
   filecoin-pin get --share '<link>' <output-dir> --no-update-check
   ```

2. **In a key file.** No `key-set`: ask the user to copy the Access key and run this in the session, with the leading `!`. It writes the clipboard to a file only they can read, in a fresh private temp folder, and prints the file's path — the path is not a secret, the key never shows:

   ```
   ! d="$(mktemp -d)" && (umask 077; <paste> > "$d/access-key") && echo "$d/access-key"
   ```

   No clipboard (`none`): ask them to run this in their own terminal instead, and tell you the path it prints. The key is pasted at a hidden prompt, so it never shows on screen or in shell history, and it works in any POSIX shell:

   ```bash
   d="$(mktemp -d)"; printf 'Paste the Access key, then press Enter: '; stty -echo; IFS= read -r k; rc=$?; stty echo; printf '\n'; [ "$rc" -eq 0 ] && (umask 077; printf %s "$k" > "$d/access-key") && echo "$d/access-key"; unset k rc
   ```

   With the printed path, check it without reading it, then open the share and delete the folder in the same command, whatever the result:

   ```bash
   test -s '<path>' && echo key-file
   SHARE_ACCESS_KEY="$(cat '<path>')" filecoin-pin get --share '<link>' <output-dir> --no-update-check; rm -f '<path>'; rmdir "$(dirname '<path>')" 2>/dev/null
   ```

   This file is the one place the key touches disk: the user writes it into a folder only they can read, and it is gone after one try. To retry (a wrong key, or "not found yet"), ask the user to save the key again — or, for repeated retries, to set `SHARE_ACCESS_KEY` in their own shell as in case 1.

3. **Pasted into the chat anyway.** It is already in this conversation's history, so use it rather than asking again: `SHARE_ACCESS_KEY='fak1_…' filecoin-pin get --share '<link>' <output-dir> --no-update-check`. This also puts it in shell history; tell the user once that anyone who can read this conversation or that history can open the share, and that a new link and key (`get-share-link` again) is the only way to take that back. Never repeat the key in your replies.

The CLI opens the payload with the key before downloading, so a wrong key fails fast. Then it downloads, checks every block against the CID, decrypts (the envelope rejects any change to the ciphertext), and prints the saved path.

## Troubleshooting

**Upload stored but not confirmed.** `add` exits `2`, or reports that the commit on a provider timed out, after the upload reached the provider. The transaction was submitted and may still confirm. Don't upload again:

1. Keep the Encrypted root CID, the data set ID and the Piece CID from the output.
2. If the user asked to share, run `get-share-link <encrypted-root-cid> --restricted` once. It uploads nothing, and the link stays the same once the upload is confirmed.
   - It works: hand over the link and the Access key as usual, with this warning: the content is on the provider but not yet confirmed on chain. Until it is, it isn't proven or paid for, and the provider may remove it.
   - It fails: say the link can be made once the piece is confirmed.
3. Check the piece once:

   ```bash
   filecoin-pin data-set piece-status <data-set-id> <piece-cid>
   ```

   Always pass the Piece CID: without it, the command opens an interactive pager that fails in an agent shell.

   - `active` or `onchain orphaned`: committed on chain. `onchain orphaned` only means the provider's own list hasn't caught up.
   - `offchain orphaned` (the provider holds it, the chain doesn't), or not listed: not committed yet.
4. Don't poll. Give the user the `piece-status` command to check later, with the CID and the data set ID. A share link already handed over needs nothing more. If the user still needs a link and step 2 failed, run `get-share-link` again once the piece is committed.

**Upload interrupted, or a stuck run you have no output for** (the user pressed Ctrl-C, the terminal died, or the run happened outside this conversation). First check whether it is still running: `pgrep -fl '[f]ilecoin-pin add' || echo not-running` (the brackets stop `pgrep` from matching its own shell). Still running: it is not failed — let it finish, never kill it. `not-running` and you have the run's output: follow what it shows — a summary with the CID and IDs means "Upload stored but not confirmed" above; output that ends before anything reached a provider means nothing was uploaded. `not-running` with no output to recover the CID and IDs from: there is nothing to resume — "resume" would be a new `add`, which is a new paid upload under a new CID. Stop and tell the user exactly that; run `add` again only when they, knowing it, ask.

**Only the second copy failed** (`Got 1/2 copies`). The content is stored on the first provider, and the share works. Report it as degraded redundancy (1/2 copies), not a failure. Don't repair it by uploading again: `add --encrypt` makes a new CID, and a plain `add` would upload the content unencrypted. The envelope isn't kept after `add` exits, so there is nothing to re-add as is. Tell the user the share works with one copy; if they want two, the only way today is a new encrypted upload (a new CID and a new share), made only when they ask.

**Upload failed before it was stored** (for example `Failed to create upload session`, or a provider answering 503). Don't run `add` again. Tell the user the upload failed, with the error line, and that running it again uploads under a new CID. Run it again only when the user asks.

`No credentials found.` No usable login. Run the login above.

`Encrypted uploads need the owner wallet (set PRIVATE_KEY) or a session key with a group key Grant …` The login has no Grant. Run the login above with `encrypt` in `--scopes`.

`Session expired (key …)`. The session key can no longer be used. With the user's agreement, run `filecoin-pin logout`, then the login above.

A missing scope: the CLI names the session key, the missing scopes, and a console link. Give the link to the user as is.

`get --share` errors print one labeled line each. The common ones:

- malformed or truncated link: the CLI says the link names no valid CID, or isn't a v1 Share link. Ask the user to copy the whole link again;
- wrong Access key: ask the user to check they copied the whole key, starting with `fak1_`;
- link for another upload: the link was edited or mixed up with another one;
- not found yet: the upload is new and still propagating. A fresh upload is usually retrievable within minutes; retry. Still not found after a few retries over several minutes: indexing is lagging (the CLI's own message suggests about 20 minutes as the slow case), and it is worth confirming the network with the sender — a calibration share opens only with `--network calibration`, and the link doesn't name its network;
- incomplete download: retry the same command. If it keeps failing, tell the user and try again later.
