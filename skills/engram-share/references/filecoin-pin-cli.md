# filecoin-pin CLI reference

Condensed reference for filecoin-pin (verified against v1.2.0). The CLI uploads IPFS content to Filecoin storage providers with on-chain payment and daily cryptographic possession proofs. Full docs: https://docs.filecoin.cloud/getting-started/filecoin-pin/

## Install

```bash
npm install -g filecoin-pin   # requires Node 24+
filecoin-pin --version
```

Every command checks npm for updates and prints a reminder; suppress with `--no-update-check`.

Exit codes: `0` success, `1` error, `2` incomplete (confirmation declined or confirmation wait timed out after submission).

## Authentication

Two modes. All commands accept these as flags or environment variables.

**Private key (standard):**

```bash
export PRIVATE_KEY=0x...        # wallet and signer, funded with FIL (gas) + USDFC (storage)
# or per-command: --private-key <key>
```

**Session key (delegated):** an owner wallet authorizes a separate keypair on-chain so uploads can run without the wallet key present. Session keys cover data operations only (add, delete, dataset management); payment operations (deposits, allowances, `payments setup`, `--auto-fund`) are owner-only and must happen from the owner wallet — in practice via the Filecoin Pay console.

```bash
filecoin-pin session create --console          # browser pairing: generate locally, authorize in the console (RECOMMENDED)
filecoin-pin session import                    # import a console-issued key (masked prompts; validates on-chain first)
filecoin-pin session create                    # owner-key single-party: generate + authorize in one step (prints SESSION_KEY)
filecoin-pin session generate                  # keypair only, no chain interaction (two-party flow)
filecoin-pin session authorize <session-address>   # owner authorizes an externally generated address
filecoin-pin session revoke <session-address>      # revoke later (or revoke in the console)

export WALLET_ADDRESS=0x...    # owner wallet address
export SESSION_KEY=0x...       # the session key PRIVATE key, not the session address
# or per-command: --wallet-address <addr> --session-key <private-key>
# or source ~/.filecoin-session-key.env (written by create --console / import; chmod 600)
```

**`session create --console` (browser pairing):** requires no key of any kind. It generates the keypair locally, saves it to `~/.filecoin-session-key.env` immediately, prints the session address, opens `<console>/console/session-keys?authorize=<address>` in the browser (default console `https://pay.filecoin.cloud`, mainnet only — other networks need `--console-url` / `CONSOLE_URL`), then polls the SessionKeyRegistry until the owner approves (10-minute timeout, ~5 s interval). Before polling it prints the expected network — the console must be on the same one. On approval it records `WALLET_ADDRESS` + expiry in the env file and prints `Authorized by: <owner>`; the session private key never appears on stdout. A timed-out run exits non-zero and a re-run resumes the same unregistered key (`--fresh` forces a new one). If no browser can open (SSH/headless), it prints the URL and keeps polling. Combining `--console` with `--private-key`/`PRIVATE_KEY`, `--session-key`, or `--validity-days` is an error — validity and permissions are chosen in the console form.

**`session import`:** for keys created in the console's own flow. Prompts interactively for the owner address (plain) and the session private key (masked); there is deliberately no `--key` flag, so the key never transits argv or shell history. It verifies the authorization on-chain (`authorizationExpiry` per required permission), aborts without writing if missing or expired, and otherwise writes `~/.filecoin-session-key.env` (0600). Alternatively, the console's "Download .env" file is already in the right format — save it directly as `~/.filecoin-session-key.env` and `chmod 600` it.

**Precedence** when several sources exist: explicit env vars (`SESSION_KEY`+`WALLET_ADDRESS`, or `PRIVATE_KEY`) > `~/.filecoin-session-key.env` > legacy `~/.filecoin-pin.env`; session auth wins over a root key with a one-line notice.

**View-only:** `--view-address <address>` (env `VIEW_ADDRESS`) inspects an account without signing.

## Environment variables

```bash
PRIVATE_KEY=0x...          # standard auth
WALLET_ADDRESS=0x...       # session auth: owner address
SESSION_KEY=0x...          # session auth: session private key
RPC_URL=wss://...          # override RPC endpoint (chain derived by probing eth_chainId)
PROVIDER_IDS=...           # pin to specific provider(s)
DATA_SET_IDS=...           # pin into specific data set(s)
SKIP_IPNI_VERIFICATION=... # skip IPNI advertisement check after upload
EGRESS_PROVIDER=beam|none  # CDN egress for piece retrieval (default beam)
FILECOIN_PIN_TELEMETRY_DISABLED=true   # disable telemetry (or DO_NOT_TRACK=1)
```

A common pattern is keeping `PRIVATE_KEY=0x...` in `~/.filecoin-pin.env` (chmod 600) and sourcing it before running commands.

## payments — one-time setup and funding

Required before the first upload.

```bash
filecoin-pin payments setup --auto      # automatic: approve storage service + seed deposit
                                        # sized from on-chain pricing; add --deposit <usdfc> or
                                        # --rate-allowance "1TiB/month" to override defaults
filecoin-pin payments status            # wallet FIL/USDFC, Filecoin Pay balance, locked reserve,
                                        # daily cost, how much storage current funding covers
                                        # (--include-rails for rail detail)
filecoin-pin payments fund --days 60    # set runway to exactly N days (deposits or withdraws)
filecoin-pin payments fund --amount 10  # set deposited total to exactly this USDFC
                                        # --mode minimum only tops up, never withdraws
filecoin-pin payments deposit           # one-way deposit, never withdraws (for shares, prefer
                                        # `add --auto-fund` over manual deposits)
filecoin-pin payments withdraw          # pull funds back to the wallet
```

## add — upload a file or directory

```bash
filecoin-pin add <path> [options]
```

Key options:

- `--dry-run` estimate cost and required deposit, then exit without uploading or moving funds
- `--auto-fund` deposit USDFC from the wallet before upload whenever the Filecoin Pay balance or lockup would fall short, sized to maintain runway (default 30 days); tune with `--min-runway-days <n>` and `--max-balance <usdfc>` (maximum Filecoin Pay balance after the deposit — setting it to current balance + N caps the top-up at N USDFC). Use this on every share instead of running `payments deposit` manually; the skill workflow caps automatic top-ups at 5 USDFC per share this way and requires user permission beyond that.
- `--copies <n>` storage copies (default 2)
- `--include-hidden` include dotfiles when packing a directory
- `--provider-id <id>` / `--data-set-id <id>` target specific providers / data sets (repeatable). Each copy needs a reachable target: a single `--data-set-id` restricts the add to one copy on that data set's provider, even with the default `--copies 2`.
- `--skip-ipni-verification` do not wait for IPNI advertisement
- `--egress-provider beam|none` CDN egress for piece retrieval; `beam` (default) locks an extra 1 USDFC per new data set from the owner lockup
- `--metadata key=value` / `--data-set-metadata key=value` attach metadata (repeatable). `--data-set-metadata` also selects data sets: existing data sets whose metadata matches are reused (`Matched existing data sets <ids> via metadata filter`), otherwise new ones are created with that metadata (`No existing data sets matched --data-set-metadata; SDK will create a new data set`). The default data-set `source` key ("filecoin-pin") can be overridden this way, e.g. `--data-set-metadata source=my-app`.

Progress lines are printed as steps complete, then a final summary. `File packed with root CID: ...` appears within seconds of starting, before any upload; `[Primary] Stored on provider N`, `IPNI provider records found`, and on-chain confirmation follow over the next minutes:

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
```

A partial-copy result (`Got 1/2 copies ... Add completed with errors`) still means the content is stored and retrievable from the successful copy; redundancy is reduced. Repair by re-running the add with `--auto-fund` and a second provider reachable (both data-set targets, or metadata selection): providers deduplicate stored bytes, so the re-run is nearly instant and only the missing copy does real work. Note the deduplication is at the storage layer only — a data set that already lists the piece gains a duplicate piece entry on re-add.

With the default 2 copies, each copy lands in its own data set on its own provider; the pair is created together and reused together on subsequent adds. `(new data set created)` in the summary marks a fresh one.

## import — upload an existing CAR

```bash
filecoin-pin import <file.car>
```

Same options and output shape as `add`, but skips packing: the CAR's root becomes the IPFS Root CID.

## data-set — inspect and manage

```bash
filecoin-pin data-set ls                  # data sets for the configured account (--all for every one)
filecoin-pin data-set show <dataSetId>    # details: provider, rails, pieces
filecoin-pin data-set piece-status <dataSetId> [pieceCid]   # reconciled piece status + proofs
filecoin-pin data-set terminate <dataSetId>                 # end the data set and its payment rails
filecoin-pin rm --data-set-id <id> --piece <pieceCid>       # remove one piece
filecoin-pin rm --data-set-id <id> --all --force            # remove all pieces
```

`dataset` is an alias for `data-set`.

Every piece stored through `add` automatically carries per-piece metadata `name` (the file's base name — public, on-chain) and `ipfsRootCID` (the share-link CID); `piece-status` prints both for each active piece, which is enough to rebuild a share listing from chain state alone.

## No JSON output

The CLI has no JSON/machine-readable mode. Parse the labeled summary lines:

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

## Troubleshooting

**Insufficient USDFC / payment capacity errors.** Check `filecoin-pin payments status`. Top up with `filecoin-pin payments fund --days 30` (or `--amount <usdfc>`), or retry the upload with `--auto-fund` which deposits as part of the add. The wallet itself must hold USDFC to deposit from, plus FIL for gas.

**Not sure what an upload will cost.** `filecoin-pin add <path> --dry-run` prints the cost estimate and required deposit without uploading or moving funds.

**Lockup errors** (allowance or lockup exceeded, new data set cannot lock funds). Each new data set with the default `beam` egress locks an extra 1 USDFC from the owner's funds. Re-run `filecoin-pin payments setup --auto` to refresh allowances, add funds via `payments fund`, or pass `--egress-provider none` to skip the CDN lockup.

**IPNI timing.** After upload the CLI waits for IPNI provider records before printing retrieval URLs; that wait can conclude with an `IPNI provider records not found` warning without failing the add, and gateway retrieval often works anyway moments later. Public-gateway retrieval can still lag a minute or two behind; retry the gateway a few times before concluding anything is wrong. The `Retrieval URL` in the `Copies` section is the provider's `/piece/<piece-cid>` endpoint and works immediately; the same host also serves `/ipfs/<root-cid>` as a trustless gateway. `--skip-ipni-verification` skips the wait but then gateway retrieval is not yet confirmed.

**Secondary copy failure** (`Got 1/2 copies`). Content is stored on the primary and retrievable; this is degraded redundancy, not data loss. Repair by targeting an existing healthy data set directly: `add <path> --copies 1 --data-set-id <id> --auto-fund` (plus the usual metadata flag), choosing a set on a provider distinct from the one holding copy 1. Avoid `--provider-id` for repairs: it creates a brand-new data set even when the provider already holds matching data sets (observed 2026-08-27, data set 1533 created instead of matching 1444), stacking billing floors. Re-running the same add with only the metadata filter re-targets the same provider pair — if the failed provider's commit path is broken (repeated `Commit failed`), the re-run fails identically after ~5 minutes (observed 2026-08-07); reserve the plain re-run for transient failures like timeouts.

**Command exits 2.** A confirmation was declined or the wait for on-chain confirmation timed out after submission; check state with `data-set piece-status` before retrying.
