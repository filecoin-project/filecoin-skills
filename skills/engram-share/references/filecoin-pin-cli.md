# filecoin-pin CLI reference

Condensed reference for filecoin-pin (command surface verified against **v2.0.1** by reading `--help` for every command and subcommand; the `Add Complete` output shapes below are carried over from v1.2.0 and have NOT been re-verified against a live mainnet add). The CLI uploads IPFS content to Filecoin storage providers with on-chain payment and daily cryptographic possession proofs. Full docs: https://docs.filecoin.cloud/getting-started/filecoin-pin/

## Install

```bash
npm install -g filecoin-pin   # requires Node 24+
filecoin-pin --version
```

Every command checks npm for updates and prints a reminder; suppress with `--no-update-check`.

Exit codes: `0` success, `1` error, `2` incomplete (confirmation declined or confirmation wait timed out after submission).

## Command surface

```
add <path>              upload a file or directory
import <file>           upload an existing CAR
payments                setup / status / fund / deposit / withdraw
data-set|dataset        ls / show / piece-status / terminate
provider                ls / show / ping
remove|rm               remove stored pieces
session                 create / authorize / revoke / generate
server                  run a local IPFS Pinning Service API server
```

## Authentication

Two modes. Every command accepts them as flags or environment variables.

**Private key (owner, standard):**

```bash
export PRIVATE_KEY=0x...        # wallet and signer, funded with FIL (gas) + USDFC (storage)
# or per-command: --private-key <key>
```

**Session key (delegated):** an owner wallet authorizes a separate keypair on-chain so uploads can run without the owner key present.

```bash
export WALLET_ADDRESS=0x...    # owner wallet address
export SESSION_KEY=0x...       # the session key PRIVATE key, not the session address
# or per-command: --wallet-address <addr> --session-key <private-key>
```

**Credentials from a file** — the supported way to keep keys out of argv and shell history:

```bash
filecoin-pin add ./file.html --credentials-file ~/.filecoin-pin.env
```

`--credentials-file <path>` loads a dotenv-style file (e.g. `SESSION_KEY`, `WALLET_ADDRESS`, `PRIVATE_KEY`) before other options are resolved, and does **not** override variables already set in the environment. It is available on every command, including as a global flag. The CLI does not read any dotfile implicitly — either export the variables or pass `--credentials-file`.

**View-only:** `--view-address <address>` (env `VIEW_ADDRESS`) inspects an account without signing.

>  **No browser pairing in the released CLI — and when it arrives it is `login`, not `--console`.** In v2.0.1 `session` is exactly `create`, `authorize`, `revoke`, `generate`: there is no `session create --console` and no `session import`. Session keys are authorized with an owner key (single-party `create`) or the two-party `generate` + `authorize` flow below.
>
> Two pieces are in flight. Neither is released, so neither may be documented as available — but do not re-add `--console` either, because that is not the shape it is taking:
>
> 1. **Console session-keys page** (FilOzone/filecoin-pay-explorer #346→#380, open): generates the key in the browser, authorizes it on chain, and offers a `.env` download containing `SESSION_KEY` and `WALLET_ADDRESS` whose own header says to use it with `filecoin-pin --credentials-file <file>`. That format is already consumable today — no CLI change needed.
> 2. **`filecoin-pin login` / `logout`** (filecoin-project/filecoin-pin #699→#703, draft): generates or resumes a session key, prints and opens the console authorize link, waits for the grant, and writes a 0600 session file the CLI then auto-loads. Default scopes are `createDataSet,addPieces`.
>
> When `login` ships, it becomes the recommended first-run path and `session` becomes the owner-signed advanced path. Until it exists in the installed version, do not reference it in user instructions.

### session subcommands

```bash
filecoin-pin session create                        # generate (or reuse) a session key and authorize it on-chain
filecoin-pin session generate                      # keypair only, no chain interaction (consumer side, two-party flow)
filecoin-pin session authorize <session-address>    # owner authorizes an externally generated address (two-party flow)
filecoin-pin session revoke <session-address>       # revoke permissions for an authorized session address
```

`session create` options: `--validity-days <days>` (max 365, default `10`), `--scopes <ids>`, `--session-key <key>` (reuse an existing session private key, env `SESSION_KEY`), `--private-key <key>` (owner key for signing, env `PRIVATE_KEY`), `--network`, `--rpc-url`, `--credentials-file`. It needs an owner key to sign the authorization.

`session authorize <session-address>` takes `--validity-days`, `--scopes`, `--private-key` (owner), `--network`, `--rpc-url`, `--credentials-file`. `session revoke <session-address>` takes `--scopes` (default: all), `--private-key`, `--network`, `--rpc-url`, `--credentials-file`. `session generate` takes no options.

**Scopes** (`--scopes`, comma-separated; **default: all**):

| scope | grants |
|---|---|
| `createDataSet` | create new data sets |
| `addPieces` | upload pieces into a data set |
| `schedulePieceRemovals` | schedule piece removal |
| `terminateService` | terminate a data set / its rails |

Sharing needs `createDataSet,addPieces`. Granting the default (all) hands a session key the ability to remove pieces and terminate service — pass `--scopes` explicitly.

**Payments under a session key are unverified.** The payments commands accept `--session-key`/`--wallet-address` at the CLI level, but the scope set above contains no payments scope, and v2 added per-command scope gating with console-first remediation (filecoin-pin#687). Do not assume `payments setup`/`fund`/`deposit` or `add --auto-fund` work with a session key: fund from the owner wallet, then share with the session key. Confirm against a funded wallet before relying on either behaviour.

## Common options

Available across commands: `--network <mainnet|calibration|devnet>` (default `mainnet`; mutually exclusive with `--rpc-url`; `devnet` reads config from foc-devnet via `FOC_DEVNET_BASEDIR`/`DEVNET_INFO_PATH`/`DEVNET_USER_INDEX`), `--rpc-url <url>`, `--credentials-file <path>`, `--view-address <address>`, `-v/--verbose`, `--no-update-check`.

## Environment variables

```bash
PRIVATE_KEY=0x...          # owner auth
WALLET_ADDRESS=0x...       # session auth: owner address
SESSION_KEY=0x...          # session auth: session private key
VIEW_ADDRESS=0x...         # view-only mode
NETWORK=mainnet            # mainnet | calibration | devnet
RPC_URL=wss://...          # override RPC endpoint (mutually exclusive with NETWORK)
PROVIDER_IDS=...           # target specific provider(s)
DATA_SET_IDS=...           # target specific data set(s)
SKIP_IPNI_VERIFICATION=... # skip IPNI advertisement check after upload
EGRESS_PROVIDER=beam|none  # CDN egress for piece retrieval (default: none)
FILECOIN_PIN_TELEMETRY_DISABLED=true   # disable telemetry (or DO_NOT_TRACK=1)
```

## payments — one-time setup and funding

Required before the first upload.

```bash
filecoin-pin payments setup --auto      # approve storage service + seed deposit, sized from on-chain
                                        # pricing; override with --deposit <usdfc> (target Filecoin Pay
                                        # balance) or --rate-allowance "1TiB/month" (default 1TiB/month)
filecoin-pin payments status            # wallet FIL/USDFC, Filecoin Pay balance, locked reserve,
                                        # daily cost, how much storage current funding covers
                                        # (--include-rails for rail detail)
filecoin-pin payments fund --days 60    # set runway to exactly N days (deposits or withdraws)
filecoin-pin payments fund --amount 10  # set deposited total to exactly this USDFC
                                        # --mode exact (default) matches the target exactly, depositing
                                        # or withdrawing; --mode minimum only deposits when below target
filecoin-pin payments deposit --amount 10.5   # one-way deposit, never withdraws (for shares, prefer
                                              # `add --auto-fund` over manual deposits)
filecoin-pin payments withdraw          # pull funds back to the wallet
```

## add — upload a file or directory

```bash
filecoin-pin add <path> [options]
```

Key options:

- `--dry-run` estimate cost and required deposit, then exit without uploading or moving funds
- `--auto-fund` deposit USDFC from the wallet before upload whenever the Filecoin Pay balance or lockup would fall short, sized to maintain runway (default 30 days); tune with `--min-runway-days <n>` and `--max-balance <usdfc>` (maximum Filecoin Pay balance after the deposit — setting it to current balance + N caps the top-up at N USDFC). Both require `--auto-fund`. Use this instead of running `payments deposit` manually; the skill workflow caps automatic top-ups at 5 USDFC per share this way and requires user permission beyond that.
- `--copies <n>` storage copies (default 2)
- `--include-hidden` include dotfiles when packing a directory
- `--provider-id <id>` / `--data-set-id <id>` target specific providers / data sets (repeatable). Each copy needs a reachable target: a single `--data-set-id` restricts the add to one copy on that data set's provider, even with the default `--copies 2`.
- `--skip-ipni-verification` do not wait for IPNI advertisement (automatic on devnet)
- `--egress-provider beam|none` CDN egress for piece retrieval. **Default is `none` as of v2.0.0.** `beam` (FilBeam CDN) draws egress from the owner lockup and locks an extra 1 USDFC per new data set, so pass it only when the user explicitly asks for CDN egress.
- `--metadata key=value` / `--data-set-metadata key=value` attach metadata (repeatable, value may be empty). `--data-set-metadata` also selects data sets: existing data sets whose metadata matches are reused (`Matched existing data sets <ids> via metadata filter`), otherwise new ones are created with that metadata. The default data-set `source` key ("filecoin-pin") can be overridden this way, e.g. `--data-set-metadata source=my-app`. As of v2.0.0 the CLI reuses existing matching data sets by default.
- `--erc8004-type <registration|validationrequest|validationresponse|feedback>` and `--erc8004-agent <id>` (DID, address, …) tag the piece as an ERC-8004 agent artifact. New in v2.0.0.

Progress lines are printed as steps complete, then a final summary. `File packed with root CID: ...` appears within seconds of starting, before any upload; `[Primary] Stored on provider N`, IPNI confirmation, and on-chain confirmation follow over the next minutes:

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

A partial-copy result (`Got 1/2 copies ... Add completed with errors`) still means the content is stored and retrievable from the successful copy; redundancy is reduced. See Troubleshooting for the repair path.

With the default 2 copies, each copy lands in its own data set on its own provider; the pair is created together and reused together on subsequent adds. `(new data set created)` in the summary marks a fresh one.

## import — upload an existing CAR

```bash
filecoin-pin import <file.car>
```

Same options and output shape as `add`, but skips packing: the CAR's root becomes the IPFS Root CID.

## data-set — inspect and manage

```bash
filecoin-pin data-set ls                  # data sets for the configured account
                                          # --all for every one; --provider-id <id> to filter;
                                          # --data-set-metadata key=value to filter by metadata
filecoin-pin data-set show <dataSetId>    # details: provider, rails, pieces
filecoin-pin data-set piece-status <dataSetId> [pieceCid]   # reconciled piece status + proofs
filecoin-pin data-set terminate <dataSetId>                 # end the data set and its payment rails
filecoin-pin rm --data-set-id <id> --piece <pieceCid>       # remove one piece
filecoin-pin rm --data-set-id <id> --all --force            # remove all pieces (--force skips the prompt)
```

`dataset` is an alias for `data-set`; `remove` is an alias for `rm`. `rm` also takes `--wait` (wait for transaction confirmation before exiting).

**Piece metadata is no longer readable (BREAKING in v2.0.0, filecoin-pin#683).** `add` and `import` still *write* per-piece metadata, but the CLI no longer queries it back: `PieceInfo.metadata` and `PieceInfo.rootIpfsCid` were removed, along with IPFS-Root-CID filtering on `data-set piece-status` and the exported `enrichPieceMetadata()`. `piece-status` therefore does **not** return a piece's `name` or `ipfsRootCID`, so chain state alone can no longer be used to rebuild a share listing or to map a Piece CID back to a Root CID (the two are not derivable from each other). Data **set** metadata reads still work and are still displayed. Upstream considers dropping features that depended on piece-metadata reads acceptable (filecoin-pin#668), because the underlying storage is being removed from FWSS.

## provider — list and inspect providers

```bash
filecoin-pin provider ls                  # approved providers; --all ignores approval status,
                                          # --endorsed lists only endorsed providers
filecoin-pin provider show <provider>     # details for one provider
filecoin-pin provider ping [provider]     # ping a provider's PDP service; --all pings all active
                                          # providers. Pings all approved providers when omitted.
```

`provider ping` is the supported liveness check — prefer it over hand-rolled gateway `curl` probes.

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
- Full guide: https://github.com/filecoin-project/filecoin-pin/blob/master/documentation/retrieval.md

## Troubleshooting

**Insufficient USDFC / payment capacity errors.** Check `filecoin-pin payments status`. Top up with `filecoin-pin payments fund --days 30` (or `--amount <usdfc>`), or retry the upload with `--auto-fund` which deposits as part of the add. The wallet itself must hold USDFC to deposit from, plus FIL for gas.

**Not sure what an upload will cost.** `filecoin-pin add <path> --dry-run` prints the cost estimate and required deposit without uploading or moving funds.

**Lockup errors** (allowance or lockup exceeded, new data set cannot lock funds). Egress defaults to `none` in v2, so this is usually an allowance problem rather than a CDN lockup: re-run `filecoin-pin payments setup --auto` to refresh allowances, or add funds via `payments fund`. If the add was run with `--egress-provider beam`, each new data set also locks an extra 1 USDFC from the owner's funds — drop back to `none` to skip that.

**IPNI timing.** As of v2.0.0 the CLI confirms indexing via the provider's Curio piece-status endpoint (filecoin-pin#689). The wait can still conclude with an `IPNI provider records not found` warning without failing the add, and gateway retrieval often works anyway moments later. Public-gateway retrieval can lag a minute or two behind; retry a few times before concluding anything is wrong. The `Retrieval URL` in the `Copies` section is the provider's `/piece/<piece-cid>` endpoint and works immediately; the same host also serves `/ipfs/<root-cid>` as a trustless gateway. `--skip-ipni-verification` skips the wait (and is automatic on devnet) but then gateway retrieval is not yet confirmed.

**Provider seems down.** `filecoin-pin provider ping <provider>` (or `--all`) checks the PDP service directly.

**Secondary copy failure** (`Got 1/2 copies`). Content is stored on the primary and retrievable; this is degraded redundancy, not data loss. Repair by targeting an existing healthy data set directly: `add <path> --copies 1 --data-set-id <id> --auto-fund` (plus the usual metadata flag), choosing a set on a provider distinct from the one holding copy 1. Avoid `--provider-id` for repairs: it creates a brand-new data set even when the provider already holds matching data sets (observed 2026-08-27, data set 1533 created instead of matching 1444), stacking billing floors. Re-running the same add with only the metadata filter re-targets the same provider pair — if the failed provider's commit path is broken (repeated `Commit failed`), the re-run fails identically after ~5 minutes (observed 2026-08-07); reserve the plain re-run for transient failures like timeouts.

**Command exits 2.** A confirmation was declined or the wait for on-chain confirmation timed out after submission; check state with `data-set piece-status` before retrying.
