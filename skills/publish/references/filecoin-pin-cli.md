# filecoin-pin CLI reference

Condensed reference for filecoin-pin (verified against v2.1.0). The CLI uploads IPFS content to Filecoin storage providers with on-chain payment and daily cryptographic possession proofs. Full docs: https://docs.filecoin.cloud/getting-started/filecoin-pin/

## Install

```bash
npm install -g filecoin-pin   # requires Node 24+
npm install -g filecoin-pin@latest   # bring an existing install to the latest release
filecoin-pin --version
```

Every command checks npm for updates and prints a reminder; suppress with `--no-update-check`.

Exit codes (global contract): `0` success, `1` error, `2` incomplete (a confirmation was declined, a wait for on-chain confirmation timed out after submission, or `login` exited before the grant was confirmed — `--no-wait`, timeout, or fewer scopes granted than requested).

## Credentials

Resolution order for every command: **flags → `PRIVATE_KEY` or `SESSION_KEY`+`WALLET_ADDRESS` in the environment → `--credentials-file <path>` → the saved login session**. `VIEW_ADDRESS` (`--view-address`) forces read-only mode and skips the saved login.

Two auth modes:

| Mode | Credentials | Can do |
|---|---|---|
| Session key (saved login — the skill's default) | `SESSION_KEY` + `WALLET_ADDRESS` (the OWNER's address, not the session address) | `add`, `import`, `rm`, `balance`, `data-set` reads. Cannot deposit. `data-set terminate` is broken under session auth in this build (see data-set section) |
| Owner key (skill uses it only on explicit request) | `PRIVATE_KEY` (`--private-key`) | Everything, including deposits, `payments setup`, `--auto-fund`, and `data-set terminate` |

**Saved login:** `login` saves a session-key credential set to `session.env` in the CLI data dir — macOS `~/Library/Application Support/filecoin-pin/session.env`, Linux `~/.local/share/filecoin-pin/session.env` — owner-readable only (0600). It holds `SESSION_KEY`, `SESSION_ADDRESS`, `NETWORK`, and (once the grant confirms) `WALLET_ADDRESS`. When no flag and no env var supplies a credential, commands auto-load this file, including its `NETWORK` (unless a network flag/env is set). A `session.env` without `WALLET_ADDRESS` (login started but never confirmed) is NOT used — commands fail with `No credentials found.` and point at `login`. `login`, `logout`, `dashboard`, and `server` never auto-load.

Gotchas:

- Any explicit auth flag (`--wallet-address`, `--session-key`, `--private-key`, `--view-address`) disables saved-login auto-load entirely. It's all-or-nothing: passing only `--wallet-address` means you must also pass `--session-key` or `--credentials-file`. Never mix one explicit flag with the saved session.
- With `CI` set in the environment, every command that auto-loads the saved login prints a leading warning (`Warning: CI is set and credentials came from the saved login at <path>. Set PRIVATE_KEY, or SESSION_KEY and WALLET_ADDRESS, explicitly on CI so a stale login is never picked up.`) — even `--version` prints it. Harmless; tolerate or filter it when parsing output.
- `--credentials-file` loads a dotenv-style file (e.g. a console-downloaded credentials file) before other options resolve and never overrides variables already set in the environment. It warns that it ignores `SESSION_ADDRESS` even though login writes that key; cosmetic.
- The `session` subcommands (`create`, `authorize <session-address>`, `revoke <session-address>`, `generate`) are the owner-signed, "advanced" path — they need the wallet private key. On an interactive machine use `login`. There is no `session import` and no `session create --console` in v2; `~/.filecoin-session-key.env` is no longer read by anything.

## login — approve a session key for this machine

```bash
filecoin-pin login [--scopes createDataSet,addPieces,schedulePieceRemovals,terminateService]
                   [--fresh] [--no-browser] [--no-wait] [--timeout <s>] [--network <n>]
```

Default scopes: `createDataSet,addPieces`. Default network mainnet. Console base URL: `https://pay.filecoin.cloud`, override with env `CONSOLE_URL`. `BROWSER=none` suppresses the browser like `--no-browser`.

What happens, in order:

1. The CLI generates a session key (or resumes the saved one; `--fresh` forces a new key) and saves it to `session.env` BEFORE the browser opens — an interrupted login is safe to re-run and reuses the same key.
2. Opens (or with `--no-browser` prints) a console authorize link: `<console>/console/session-keys?authorize=<session-address>&scopes=<ids>&network=<slug>`. The human connects the OWNER wallet in the console and signs the grant. This is the only human step. The link carries no owner identity — the grant lands under whichever wallet the console is connected as.
3. Waits for the on-chain grant (default `--timeout 300` seconds), then writes the owner's `WALLET_ADDRESS` into `session.env` and prints `✓ Authorized! Granted: <scopes>` (a partial grant lists per-scope ✓/✗ with "(owner declined)"). Exit `0` = every requested scope granted; exit `2` = no grant seen in time, `--no-wait`, or fewer scopes than requested (re-run login to resume); exit `1` = error, including a network the console has no pairing page for.

`logout` deletes `session.env` locally only (`Logged out: removed <addr> from <path>` / `Not logged in: no session file at <path>`). The on-chain grant stays until it expires or is revoked. As of v2.1.0 logout prints a deep link that opens the console's revoke dialog on that specific key (`<console>/console/session-keys?revoke=<session-address>&network=<slug>`); it falls back to the plain session-keys page when the session file recorded no network, or the network has no console page.

**Grant-wait reliability.** Through v2.0.1 the wait asked the owner scan for `toBlock: 'latest'`, which the public RPC answers in 23-35s — past viem's 10s request timeout — so three consecutive failures ended the wait with `✗ Could not watch for the authorization.` Worse, a re-run re-anchored the watch at the current chain head, so a grant that had already landed stayed permanently outside the window and `session.env` never received `WALLET_ADDRESS`. v2.1.0 scans to a named head instead and the wait completes normally. On v2.0.1 or older the recovery is to append the owner address by hand — `printf 'WALLET_ADDRESS=<owner-address>\n' >> "<session.env path>"`, append-only, never read the file — then verify with `filecoin-pin balance`.

## balance — the account report

```bash
filecoin-pin balance [--no-update-check]
```

The `payments status` report plus a `dashboard` pointer; works in session mode. Output: a status banner (`● HEALTHY  Funded until <date>  (<n> days)`), a `Network: Filecoin - Mainnet` line, a Wallet block (address, FIL, USDFC, gas warnings), an Account block (`Total deposited`, `Available to withdraw`, `Burn rate`, `Total locked` split into Security Deposit and Usage hold), a Datasets count/size line, and `Top up or manage billing:  filecoin-pin dashboard`.

`dashboard` opens the console billing page (`<console>/console`) in the browser; `--no-browser` prints the link. Needs no credentials.

## payments — owner-key funding operations

Owner mode only: a session key cannot deposit, withdraw, or approve — funding under session auth happens in the console.

```bash
filecoin-pin payments setup --auto      # approve storage service + seed deposit (first-upload setup);
                                        # --deposit <usdfc> / --rate-allowance to override defaults
filecoin-pin payments status            # same report as `balance`
filecoin-pin payments fund --days 60    # set runway to exactly N days (deposits or withdraws)
filecoin-pin payments fund --amount 10  # set deposited total exactly; --mode minimum only tops up
filecoin-pin payments deposit           # one-way deposit (for shares, prefer `add --auto-fund`)
filecoin-pin payments withdraw          # pull funds back to the wallet
```

## add — upload a file or directory

```bash
filecoin-pin add <path> [options]
```

Requires scopes `createDataSet` (new data set) and `addPieces` under session auth. Key options:

- `--dry-run` estimate cost and required deposit, then exit without uploading or moving funds
- `--auto-fund` (OWNER mode only; silently ignored under session auth) deposit USDFC from the wallet before upload whenever the Filecoin Pay balance or lockup would fall short, sized to maintain runway (default 30 days); tune with `--min-runway-days <n>` and `--max-balance <usdfc>` (maximum Filecoin Pay balance after the deposit — current balance + N caps the top-up at N USDFC)
- `--copies <n>` storage copies (default 2)
- `--include-hidden` include dotfiles when packing a directory (a target directory itself starting with `.` always has its descendants traversed)
- `--provider-id <id>` / `--data-set-id <id>` target specific providers / data sets (repeatable; env `PROVIDER_IDS` / `DATA_SET_IDS`). A single `--data-set-id` restricts the add to one copy on that data set's provider, even with the default `--copies 2`.
- `--skip-ipni-verification` do not wait for IPNI advertisement
- `--egress-provider beam|none` CDN egress for piece retrieval; default is `none`. `beam` (FilBeam CDN) locks an extra 1 USDFC per new data set from the owner lockup and prints an egress notice.
- `--metadata key=value` / `--data-set-metadata key=value` attach metadata (repeatable). `--data-set-metadata` also selects data sets: existing data sets whose metadata matches are reused (`Matched existing data sets <ids> via metadata filter`), otherwise new ones are created with that metadata.

**Session-mode funding preflight:** before packing, the CLI checks the storage service is approved and the account can pay for this upload. If not, it exits 1 with the readiness lines, a pre-filled console funding link (`<console>/console?deposit=<n>&operator=fwss&network=<slug>` — deposit & approve is one wallet transaction), and a rerun hint with any secret flag values redacted. Nothing is uploaded. Funding is always a human/console step in session mode.

Progress lines print as steps complete, then a final summary. `File packed with root CID: ...` appears within seconds of starting, before any upload; `[Primary] Stored on provider N`, `IPNI provider records found`, and on-chain confirmation follow over the next minutes:

```
━━━ Add Complete ━━━

Add Details
  File: <path>
  Size: <n> B
  Root CID: <ipfs-root-cid>

Filecoin Storage
  Piece CID: bafkzcib...
  Piece Size: <n> B

Copies
  [Primary] Provider <id>
    Data Set ID: <n>
    Piece ID: <n>
    Retrieval URL: https://<provider>/piece/<piece-cid>
    Explorer: https://pdp.vxb.ai/<network>/piece/<piece-cid>
```

The IPNI verification after upload is warning-only: `IPNI provider records not found` does not fail the add. A partial-copy result (`Got 1/2 copies ... Add completed with errors`) still means the content is stored and retrievable from the successful copy; redundancy is reduced. Repair by targeting an existing healthy data set directly (`--copies 1 --data-set-id <id>`); providers deduplicate stored bytes, so the re-run is nearly instant and only the missing copy does real work. Avoid `--provider-id` for repairs: it creates a brand-new data set even when the provider already holds matching data sets, stacking billing floors.

With the default 2 copies, each copy lands in its own data set on its own provider; the pair is created together and reused together on subsequent adds. `(new data set created)` in the summary marks a fresh one.

## import — upload an existing CAR

```bash
filecoin-pin import <file.car>
```

Same options, scopes, session preflight, and output shape as `add`, but skips packing: the CAR's root becomes the IPFS Root CID. `add` re-chunks and mints a NEW root CID for identical bytes — to mirror content that already has a CID, fetch its CAR and `import` it.

## data-set and rm — inspect, remove, terminate

```bash
filecoin-pin data-set ls                  # data sets for the configured account (--all for every one)
filecoin-pin data-set show <dataSetId>    # details: provider, rails, pieces
filecoin-pin data-set piece-status <dataSetId> [pieceCid]   # reconciled piece status + proofs
filecoin-pin data-set terminate <dataSetId> [--wait]        # end the data set and its payment rails
filecoin-pin rm --data-set-id <id> --piece <pieceCid> [--wait]   # remove one piece
filecoin-pin rm --data-set-id <id> --all [--force]               # remove all pieces
```

`dataset` is an alias for `data-set`.

- `rm` works fully under session auth (scope `schedulePieceRemovals`): the removal goes as an EIP-712 message to the storage provider, who submits the transaction — no owner signer needed. `--wait` blocks until the removal transaction confirms; without it the command returns after scheduling. To report "deleted", use `--wait` then reconcile with `data-set piece-status <id>`.
- **Missing scope** is refused in about a second with the session key named, per-scope detail (`expired at <ISO date>` vs `never granted`), a console remediation link requesting only the missing scopes, `session authorize`/`session create` hints, and exit 1. Safe to surface verbatim to a user. A fully lapsed key gets `Session expired (key <addr>, grants lapsed <date>)` with `Renew it:  filecoin-pin login`.
- **Cross-owner boundary is enforced**: `rm`/`terminate` against a data set owned by another wallet is rejected (`Data set N is not owned by X (owned by Y)`).
- **`data-set terminate` under session auth was fixed in v2.1.0.** Through v2.0.1 it accepted session credentials, passed the `terminateService` scope check, then built the transaction `from: owner` with no local signer and died with a raw `eth_sendTransaction not found` on any public RPC. v2.1.0 routes it through the provider-signed path instead, so a session key with `terminateService` can terminate. Not exercised here — terminating a data set is destructive — so treat it as released-but-unverified and check before relying on it.

Every piece stored through `add` and `import` still carries per-piece metadata `name` (the file's base name) and `ipfsRootCID` (the share-link CID), written on-chain — so a published filename stays public even though nothing surfaces it any more. Those writes are all that is left of piece metadata: v2.0.0 removed `PieceInfo.metadata`, `PieceInfo.rootIpfsCid`, and Root-CID filtering on `piece-status`, so the CLI no longer reads any of it back. `piece-status` returns each active piece's index, status, Piece CID and size, and nothing else. A Root CID therefore cannot be recovered from chain state and a share listing cannot be rebuilt from it — the local ledger is the only record of what was published.

## provider — list and inspect providers

```bash
filecoin-pin provider ls                  # approved providers; --all ignores approval status,
                                          # --endorsed lists only endorsed ones
filecoin-pin provider show <provider>     # details for one provider
filecoin-pin provider ping [provider]     # ping a provider's PDP service; pings all approved
                                          # providers when the argument is omitted, --all ignores
                                          # approval status
```

All three are read-only and need no credentials — they work without a login or a key. `provider ping` is the supported liveness check: it queries the provider's PDP service directly, so prefer it over probing a gateway by hand.

## No JSON output

The CLI has no JSON/machine-readable mode. Parse the labeled summary lines, and tolerate the leading `Warning: CI is set…` line when `CI` is set in the shell:

- IPFS Root CID: the `Root CID:` line under `Add Details` (also `File packed with root CID:` earlier in the stream).
- Dataset ID: the `Data Set ID:` line under `Copies`.
- Fallback: when gateway retrieval URLs are printed, the root is the CID inside them; on runs that end with an IPNI not-found warning no gateway URL is printed, so rely on the labeled lines above. Small single files produce raw `bafkrei...` roots; directories and chunked files produce `bafyb...`. Do not confuse either with the `bafkzcib...` Piece CID.

## Root CID vs Piece CID

- **IPFS Root CID** (`bafyb...` or `bafkrei...`): the root of your content as an IPFS DAG. Use with IPFS gateways and tooling. This is the CID for share links.
- **Piece CID** (`bafkzcib...`): commits the entire CAR that was packed and stored on chain; what storage proofs cover. Use it to pull the exact stored bytes from the provider's `/piece` endpoint.

They are related but distinct; neither can be derived from the other.

## Retrieval URLs

```
https://inbrowser.link/ipfs/<root-cid>     # share link: verifies blocks in the browser before rendering
https://dweb.link/ipfs/<root-cid>          # programmatic fetch, curl, hot-linking
https://<provider-host>/ipfs/<root-cid>    # trustless gateway straight from the storage provider
https://<provider-host>/piece/<piece-cid>  # exact stored CAR bytes (supports byte ranges)
```

Notes:

- Browser navigations to dweb.link and ipfs.io are redirected to inbrowser.link, so inbrowser.link is the link to share with people.
- `curl -sI https://dweb.link/ipfs/<cid>` returns `301` to `https://<cid>.ipfs.dweb.link/`; use `curl -sIL` and check the final status is `200`.
- On dweb.link, `?format=car` (or `Accept: application/vnd.ipld.car`) returns the whole DAG as a CAR; `Accept: application/vnd.ipld.raw` returns a single block.
- Public gateways are rate-limited and best-effort; production retrieval should use verified-fetch, Helia, Kubo, or your own gateway.
- The add summary's `Explorer:` line prints `https://pdp.vxb.ai/<network>/piece/<piece-cid>`, which currently redirects to `https://pdp.filecoin.cloud/...` — both hosts resolve the same PDP Explorer piece page.

## Troubleshooting

**`No credentials found.`** No flag, env var, credentials file, or usable saved login. Run `filecoin-pin login`. If the user already approved a login whose grant-wait never confirmed (v2.0.1 and older — see the login section), append `WALLET_ADDRESS` by hand and verify with `balance`.

**`Session expired (key …)` / scope refusals.** The grant lapsed or was revoked in the console, or the key never had the needed scope. An expired or revoked session means the key is spent — despite the CLI's `Renew it` hint, nothing gets extended: rotate with `filecoin-pin logout` then `filecoin-pin login` (a brand-new key, approved fresh in the console). A missing scope's refusal message carries a console link requesting exactly the missing scopes — surface it verbatim.

**Insufficient USDFC / payment capacity errors.** Check `filecoin-pin balance`. Owner mode: top up with `filecoin-pin payments fund --days 30` (or `--amount <usdfc>`), or retry the upload with `--auto-fund`. Session mode: the add's preflight prints a pre-filled console funding link — the user deposits there; the CLI cannot. The wallet itself must hold USDFC to deposit from, plus FIL for gas (owner mode).

**Not sure what an upload will cost.** `filecoin-pin add <path> --dry-run` prints the cost estimate and required deposit without uploading or moving funds.

**Lockup errors** (allowance or lockup exceeded, new data set cannot lock funds). Each new data set with `beam` egress locks an extra 1 USDFC from the owner's funds. Re-run `filecoin-pin payments setup --auto` (owner mode) to refresh allowances, add funds, or keep the default `--egress-provider none`.

**IPNI timing.** After upload the CLI waits for IPNI provider records before printing retrieval URLs; that wait can conclude with an `IPNI provider records not found` warning without failing the add, and gateway retrieval often works anyway moments later. Public-gateway retrieval can still lag a minute or two behind; retry the gateway a few times before concluding anything is wrong. The `Retrieval URL` in the `Copies` section is the provider's `/piece/<piece-cid>` endpoint and works immediately; the same host also serves `/ipfs/<root-cid>` as a trustless gateway. `--skip-ipni-verification` skips the wait but then gateway retrieval is not yet confirmed.

**Secondary copy failure** (`Got 1/2 copies`). Content is stored on the primary and retrievable; this is degraded redundancy, not data loss. Repair by targeting an existing healthy data set directly: `add <path> --copies 1 --data-set-id <id>` (plus the usual metadata flag, and `--auto-fund` in owner mode), choosing a set on a provider distinct from the one holding copy 1. Avoid `--provider-id` for repairs: it creates a brand-new data set even when the provider already holds matching data sets, stacking billing floors. Re-running the same add with only the metadata filter re-targets the same provider pair — if the failed provider's commit path is broken (repeated `Commit failed`), the re-run fails identically.

**Command exits 2.** A confirmation was declined or a wait timed out after submission (for `login`: the grant was not yet confirmed — re-run to resume; on v2.0.1 and older see the login section). For storage commands, check state with `data-set piece-status` before retrying.
