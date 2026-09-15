---
name: publish
description: Use when the user wants a shareable or durable browser link for something an agent made, or says "publish this", "publish this file", "publish this folder", "publish this report", "share this file", "share these files", "share this folder", "share as a bundle", "one link for all of these", "pin this", "send someone this file", "make this public", "get me a public link", "ipfs link". Any single file, or a directory shared as one bundle link — the size cap comes from the installed CLI's synapse SDK, checked at share time. Asked to show or list existing shares, read the local ledger at ~/.filecoin-share/shares.json; this skill only creates and repairs shares.
---

# publish

One command from a local file to a durable, verified browser link: store the file on Filecoin mainnet through the `filecoin-pin` CLI, hand back `https://inbrowser.link/ipfs/<root-cid>`, and record the share in the local index. The CLI is the single seam — drive it directly, no wrapper scripts. Flags, output formats, and troubleshooting live in `references/filecoin-pin-cli.md`; read that, never the web.

The skill publishes — "share" and "publish" are the same user-facing verb here; the CLI pins. "Pin" appears only in CLI commands and quoted user phrases, never in your own reports.

## Red lines

Hard rules; each owning section carries the full rule. Skim before every share.

- Mainnet only; calibration is never an option (Network).
- Share exactly the paths the user named — every add carries only those paths (a share or repair may take several adds), and nothing else is ever pinned (Scope gate).
- Secrets files are write-only; key material never enters conversation, output, or logs (Keys).
- `--provider-id` never as a reuse mechanism — it always creates a new data set and stacks billing floors; deliberate redundancy-set creation is its only use (step 4).
- Never create a new data set to upgrade off a legacy one without the user's explicit permission — it's a real new billing floor, same gate as raising the auto-fund cap (step 4).
- A compact-pair upgrade is forward-only: past shares and the legacy pair are never touched, moved, or re-added — only new shares target the new pair (step 4).
- Never plan a 1-copy share; two copies on two distinct providers, degraded only temporarily (step 4).
- Never run `payments deposit` manually (step 3).
- Never raise the 5 USDFC auto-fund cap without the user's explicit permission (Owner-key mode).
- The saved login is the only default auth. The private-key path — the root funding wallet's own key — exists solely when the user explicitly asks for it: never source a key file, offer owner-key mode proactively, or hunt for a private key to work around a funding shortfall (step 2).
- Login scopes: request only `createDataSet,addPieces` (plus `schedulePieceRemovals` when the session will delete); never `terminateService` (step 2).
- Preserve a valid saved login: never `logout` or delete `session.env` on your own. `logout` runs only on the user's explicit ask, or as the announced first half of invalid-session recovery (step 2).
- Every add passes `--egress-provider none` unless the user explicitly names the add-on (step 5).
- Never report an unverified link without its "propagating" label, and never stop at stage one (step 6).
- Never poll a public gateway before the IPNI rung passes — it seeds a negative cache (step 7).
- Never put a Piece CID in a share link (step 8).
- Never store the share ledger on-chain; only files the user explicitly asked to share are ever stored (step 9).

## Scope gate

Two shapes of share, and the user's named paths dispatch them automatically — never ask the user to pick a mode and never wait for the word "batch": one file → single-file share; one directory → bundle (the whole tree as one link); several independent paths (any mix of files and directories) → a batch, one share per named path run IN PARALLEL per step 5, each directory becoming its own bundle and each file its own link — never merged into one bundle just because they were named together.

- **Single file** — any type. What the link does in a browser varies by type, so set expectations when handing it over: HTML renders as a page; Markdown is served as plain text (suggest HTML if the user wants it to render); MP4 plays (gateways stream with byte-range support); images render; archives, binaries, and other data arrive as a download. A self-contained file makes the best link — one that references local siblings (an HTML page with relative `src` assets) should be shared as a bundle instead or it will render broken.
- **Bundle** — a directory shared as ONE link: `filecoin-pin add <dir>` packs it into a single DAG, and the link renders as a browsable folder listing with every file inside reachable at `…/ipfs/<root-cid>/<filename>`. Pass the directory ITSELF to `add` — an archive (zip/tar) made first pins as one opaque file: no folder view, no per-file links, and the user gets a download instead of a browsable bundle. Any file types are fine inside a bundle (the bundle is the artifact); dotfiles are skipped unless `--include-hidden`. Warn before bundling anything that looks unintended (build junk, secrets-shaped files, `node_modules`) — the whole tree becomes public.

Size gate, every share — the cap is the synapse SDK's client-side upload maximum, read from the installed CLI at share time, never a number hardcoded here (new releases raise it, and the skill must inherit it without an edit). Measure first: single file `stat -f %z` (macOS) / `stat -c %s` (Linux); bundle `du -sk <dir>` — a bundle packs into ONE piece, so the whole tree counts. Then read the cap from the installed package: `grep -o 'MAX_UPLOAD_SIZE: [0-9_]*' "$(npm root -g)/filecoin-pin/node_modules/@filoz/synapse-core/dist/src/utils/constants.js"` (strip `_` separators from the number). If a future release moves that file or constant, skip the pre-check and let the add's own enforcement rule — it fails fast with an "exceeds maximum allowed size" error before any bytes move; quote that error verbatim. (Providers also publish a per-provider on-chain `Max Piece Size` via `filecoin-pin provider show`; deliberately NOT gated on for now.) Packing adds CAR framing on top of raw bytes — treat a file within ~1% of the cap as over. Over the cap → decline with the measured size and the cap, there is no "just this once": oversized MP4 → suggest trimming or re-encoding; oversized HTML → slim embedded media; oversized bundle → split it or drop the heavy files. Under the cap, mention that large files can buffer on best-effort gateways.

Filename privacy: the base name is published on-chain as piece metadata where anyone can read it — and in a bundle, every file and folder name inside the tree is public as part of the DAG. If any name reveals something sensitive, warn and suggest a neutral rename before sharing. Contents are public anyway; this check is about the names.

## Network: mainnet only

This skill operates exclusively on Filecoin mainnet: never offer, configure, or fall back to a calibration/testnet endpoint, and never source an env file that points the CLI at one. If the configured RPC or key targets calibration, stop and tell the user.

## Keys: write-only secrets

Never expose a private key or env-var value into the session, chat, logs, or any file the user did not ask for: never ask the user to paste a key, never `echo`/`env`/`printenv` or interpolate key material into output. Load keys only inside the shell that runs the CLI. Mask wallet addresses you display; call the key "the configured key" when debugging.

Secrets files (`~/.filecoin-pin.env`, `~/.filecoin.env`, the CLI's saved login `session.env`, any user-designated key file) are write-only from your perspective: inspect them ONLY with boolean or count checks (`test -f`, `grep -qE '^(export )?PRIVATE_KEY=' file`, `wc -l < file`) and branch on exit codes — a byte-emitting read (`cat`, `sed`, `head`, unqualified `grep`) plus one wrong format assumption leaks a whole bare-hex key. Unknown format = every byte is secret. Bare-key files (single hex line) are valid: load with `PRIVATE_KEY="$(cat file)"` prefixed to the CLI command, never echoed. One deliberate exception: APPENDING a line to `session.env` (`printf 'WALLET_ADDRESS=…\n' >> file`) is a write, not a read, and is allowed where step 2 calls for it.

## Workflow

### 1. Preflight

`command -v filecoin-pin`; missing → `npm install -g filecoin-pin` (needs Node 24+; engine/syntax errors → `node --version`, tell the user to upgrade). Installed → always try to bring it to the latest release: compare `filecoin-pin --version` with `npm view filecoin-pin version`, and if behind run `npm install -g filecoin-pin@latest`; npm unreachable or the update fails → continue on the installed version and say so. `references/filecoin-pin-cli.md` is what step 7 onward reads and is tracked in git so it's visible on install, but it can drift from whatever CLI version ends up running: compare `filecoin-pin --version` against the "verified against vX.Y.Z" line at the top of the reference file, and if they differ (or the file is missing), regenerate it now, once, before continuing — run `filecoin-pin --help` and each subcommand's `--help` (`login`, `balance`, `add`, `payments`, `data-set`, `rm`), condense into one section per command plus a Troubleshooting section (funding shortfalls, login grant-wait failures, lockup errors, IPNI timing), and update the version line at the top. Done when the binary resolves at the latest reachable release and the reference file's version line matches it.

### 2. Authenticate

One auth mode by default: the CLI-saved login. Pass NO credential flags or env vars and source NO key files — the private-key path (the ROOT FUNDING WALLET's private key: the owner wallet that holds the FIL/USDFC and owns every data set, not the login's disposable session key) exists only when the user explicitly asks to use that wallet key (Owner-key mode, end of this step).

**Already logged in:** the saved login is a session key the user approved in the Filecoin console, saved by `filecoin-pin login` at `session.env` in the CLI data dir (macOS `~/Library/Application Support/filecoin-pin/session.env`, Linux `~/.local/share/filecoin-pin/session.env`). Usable when it holds an owner address: check with `grep -q '^WALLET_ADDRESS=' <path>` — boolean only, the file also holds the session private key (Keys). When usable, step 2 is done — step 3's `balance` call doubles as the live verification. The CLI auto-loads the file (and its network) itself, and any explicit `--wallet-address`/`--session-key` flag would disable that auto-load entirely, all-or-nothing. The saved login covers the whole share flow (`add`, `balance`, `rm`, `data-set` reads) but cannot deposit — funding is the user's console step (step 3).

If `CI` is set in the shell, every command that auto-loads the saved login prints a leading `Warning: CI is set and credentials came from the saved login…` line — harmless; tolerate it when parsing CLI output.

**First run (no usable saved login):** run `filecoin-pin login` — no key material ever enters the conversation or a file you write:

1. Run `filecoin-pin login` — the CLI opens the console authorization page in the user's browser itself and prints the same link; add `--no-browser` only when there is no local browser to open (remote or headless session). Default scopes `createDataSet,addPieces` are exactly what sharing needs; add `schedulePieceRemovals` via `--scopes` only when this session will also delete pieces; never request `terminateService` — it is unusable under session auth. The CLI generates a session key and saves it to `session.env` BEFORE the browser opens, so an interrupted login is safe to re-run and resumes the same key.
2. 🔴 CHECKPOINT — the user signs; nothing proceeds until they do. Whether or not a browser opened, relay the console link to the user ON ITS OWN LINE, plainly labeled as the one action needed — never buried mid-paragraph. The one human step: connect the OWNER wallet in the console and sign the grant. Tell them to confirm which wallet the console is connected as before signing — the link carries no owner identity, and the grant lands under whichever wallet is connected.
3. The CLI waits (default `--timeout 300`) for the on-chain grant, then writes `WALLET_ADDRESS` into `session.env`. Exit 0 = every requested scope granted; exit 2 = not confirmed yet (`--no-wait`, timeout, or fewer scopes — re-run to resume); exit 1 = error. Known v2.0.1 blocker: the grant-wait polls `eth_getLogs` on a public RPC and often aborts (`Could not watch for the authorization. Your key is saved; rerun…`), and a re-run watches only from the current chain head — so the wait can permanently miss a grant that actually landed.
4. If the user says they approved but `session.env` still has no `WALLET_ADDRESS` (commands fail with `No credentials found.`): append the owner address yourself — `printf 'WALLET_ADDRESS=<owner-address>\n' >> "<session.env path>"` (append-only write; never read the file). The address is public — ask the user for it if you don't have it; never the key.
5. Verify: `filecoin-pin balance --no-update-check` succeeds and shows `Network: Filecoin - Mainnet`. Step 2 is done. Tell the user once: this key stays saved and is reused for future shares until they ask to log out, and they can revoke it completely any time on the console's session-keys page (`https://pay.filecoin.cloud/console/session-keys`).

**Owner-key mode — 🛑 STOP: only on the user's explicit ask.** The root funding wallet's key is a far bigger secret than the session key — never offered proactively, never a workaround for a funding shortfall. When the user explicitly says to use their wallet key: resolve `PRIVATE_KEY` from (1) the environment; (2) `~/.filecoin-pin.env`; (3) `~/.filecoin.env` — each env file sourced in the CLI's shell (`set -a; source …; set +a`), ensure `chmod 600`; (4) a user-designated key file, often bare-hex — verify shape by count/boolean checks only, load per Keys. An env `PRIVATE_KEY` outranks the saved login in the CLI's own resolution, so once a key file is sourced the wallet key is what runs. If they ask for it but nothing is configured: they create `~/.filecoin-pin.env` themselves containing `PRIVATE_KEY=0x...` for a funded wallet (FIL for gas, USDFC for storage), then `chmod 600` it — never offer to write the key file, and never ask for the key in the conversation. Owner-key mode is the one mode that can deposit: step 3's setup and step 5's `--auto-fund` variant apply only here.

**Session lifecycle:** preserve a valid saved login — it is reused across sessions and shares; never run `logout` unprompted. On the user's explicit ask, `filecoin-pin logout` deletes `session.env` locally only — the on-chain grant stays until it expires, so remind them that revoking the key completely happens on the console's session-keys page (`https://pay.filecoin.cloud/console/session-keys`).

**Invalid session** (commands fail with `Session expired (key …)` and the CLI's hint `Renew it: filecoin-pin login`; a console-revoked grant reads the same): the old key is spent — despite the CLI's word "renew", nothing gets extended, and the keys are already unusable. Recovery is a key ROTATION: tell the user the session is no longer valid, then run `filecoin-pin logout` followed by `filecoin-pin login` — logout deletes the dead key's file, login generates a brand-new key, and the same one human console step approves it. Mention the dead key can also be removed completely from the console's session-keys page. A missing scope is NOT an invalid session: the key still works, it just lacks a grant — the refusal names the key with per-scope `expired at`/`never granted` detail and a console remediation link requesting only the missing scopes; surface that message verbatim and hand the link to the user, no logout.

### 3. Payment check

`filecoin-pin balance --no-update-check` (the `payments status` report; `balance` is the front door). Gate: `Network: Filecoin - Mainnet`, or stop per Network. Then:

**Default (saved login):** deposits, `payments setup`, and `--auto-fund` are owner-only — the CLI cannot move funds with a session key. `balance`'s wallet-level warnings (e.g. `⚠ Insufficient FIL for gas fees`) are IGNORABLE in this mode: the storage provider submits the transactions and deposits happen in the console, so the wallet's own FIL/USDFC never gates a share — never stop to tell the user to buy FIL here. If `balance` shows no Filecoin Pay funds or an unapproved service, don't try to fix it locally and don't reach for a key: `add`'s own session-mode preflight checks approval and ability to pay before packing and, on shortfall, exits 1 with a pre-filled console funding link (deposit & approve is one wallet transaction). 🔴 CHECKPOINT — the deposit is the user's to make: hand that link (or the one from `filecoin-pin dashboard --no-browser`) to the user on its own line, wait for their "done", re-run `balance`, and proceed. ALWAYS explain what the number is when asking for funds: the preflight's "needs ~X" is NOT the price of the file — most of it is `Lockup (held while active)`, a refundable hold (the pair's 30-day reserve plus security deposit) that comes back if the data sets are ever terminated; the recurring cost is the small `Storage rate` per month, plus small `One-time fees`. Fetch those line items with a `--dry-run` (~5s) while the user funds. A console showing months of runway next to a top-up ask is this hold at work, not a contradiction — say so before the user has to ask.

**Owner-key mode (explicit ask only):** note the Account block's `Total deposited` balance — step 5's cap math uses it. If the account is unconfigured or has no Filecoin Pay balance, run `filecoin-pin payments setup --auto` once — it approves the storage service and seeds a deposit so the first upload does not fail cryptically; skip it when funds and allowances already show. Shortfalls during a share are `--auto-fund`'s job on the add, never a manual `payments deposit`.

**Wallet has no FIL or no USDFC at all** (owner-key setup or `--auto-fund` fails on wallet balance, not Filecoin Pay balance — the CLI reports the shortfall but not where to get funds): stop and tell the user plainly what the wallet needs and where to get it. Easiest: the Filecoin Pay console at `https://pay.filecoin.cloud/console` swaps to USDFC and deposits in one guided flow. Alternatives: mint USDFC against FIL at `https://app.usdfc.net` (Secured Finance, redeemable anytime) or swap FIL→USDFC on SushiSwap; the FIL itself (gas — well under 1 FIL covers many shares) comes from any major exchange. A few USDFC covers many shares; re-run `balance` when they say it's done.

### 4. Target the skill's data sets

Every add passes `--data-set-metadata source=filecoin-share`. Treat the tag value as an opaque constant that MUST never change — it is the on-chain key to every data set this skill has ever created, and a different value orphans them all. The CLI find-or-creates: matches existing skill data sets (`Matched existing data sets … via metadata filter`) or creates one per storage copy, each on a different provider. The priority order is fixed: reuse existing data sets first (they cost nothing extra until their billed floor is exhausted), create a new one only when reuse cannot deliver both copies — redundancy outranks the creation cost, so a new set on a fresh provider beats going degraded.

**Filter matches ZERO** (first share under this login/owner): expected whenever the account has never held skill-tagged sets — even when `data-set ls` shows live sets from other CLI use (`source="filecoin-pin"` or anything else). Untagged sets are NEVER borrowed to dodge the creation cost — a share outside the tag is invisible to every future match, check, and repair. The add will plan a brand-new tagged pair, whose 30-day reserve can exceed the available balance even on an otherwise funded account. Don't pre-empt with a dry-run — run the real add directly: its preflight is the same check, and when funds suffice the share simply proceeds. If the preflight refuses, that's the step 3 funding round-trip — hand over the pre-filled link, and while the user funds, run `--dry-run` to fetch the line items for step 3's cost explanation. After they fund, the same add re-runs unchanged.

**Compact vs. legacy** (synapse-sdk#925): mainnet data sets with ID `1559` or higher use the newer, more efficient `PieceV2` storage layout ("compact" — see CONTEXT.md); below `1559` is "legacy," still fully retrievable, just less efficient. This never affects a user with no existing skill data set — a freshly created set is always compact, no action needed. It matters in two cases:
1. **Choosing among multiple matching sets**: when the metadata filter matches more than one live data set on a needed provider, prefer a compact one (`id >= 1559`) over a legacy one — same reuse-is-free economics, just the more efficient set first.
2. **The skill's own working pair predates the cutover**: check the pair's IDs against `1559` before targeting them. If they're legacy and the wallet has comfortably more than one share's worth of funds beyond the current balance, offer a one-time upgrade — explain the ongoing cost delta (a new pair adds its own floor, ~0.04 USDFC/month) and that the old pair keeps working untouched either way. 🔴 CHECKPOINT: create the new pair only on the user's explicit yes; from then on it's the preferred target for new shares (existing shares' records and the old pair are left exactly as they are — this is a going-forward preference, never a migration of past shares).

**Filter matches more than the pair** (skill data sets accumulate over time; the CLI refuses non-interactively: `Add failed: --data-set-metadata matched N data sets … but expected 2`): fall back to explicit targeting — pick two live sets on two distinct providers (liveness probe below), one add per copy with `--copies 1 --data-set-id <id>`, run in parallel.

Two hard rules, happy path and repair alike:

1. **Two copies on two distinct providers, always.** Never plan a 1-copy share to save cost. When the usual pair can't host both copies (a provider down), fall through in order: another EXISTING skill data set on a distinct healthy provider first (reuse is free); a NEW data set on a healthy provider only when no existing set can take the copy — the extra floor is the price of the redundancy promise. Only when no second distinct healthy provider is reachable at all does the share go out degraded: report it and set `"note": "DEGRADED 1/2"` on the share's ledger record — the note is the repair queue — never hold the session open waiting for a provider to recover.
2. **Reuse goes through `--data-set-id`, never `--provider-id`.** An existing data set is always reused by naming it: `--data-set-id <id>`, one add per copy (one `--data-set-id` restricts the add to that set's provider). `--provider-id` can NOT reuse — it always mints a brand-new data set even when that provider already holds skill data, so reaching for it "to reuse provider N's set" silently stacks a billing floor instead. Its only legitimate use is the last resort of rule 1: deliberately creating a redundancy set at a healthy provider that holds no skill data set, the new floor accepted knowingly.

**Picking a set** (repair, substitution, or the multi-match fallback): candidate IDs come from `~/.filecoin-share/shares.json` and recent add output — but a candidate is valid only if the CURRENT login's owner owns it. After a login or owner change the ledger's IDs can all belong to a previous wallet, and an add against another owner's set fails the CLI's cross-owner check (`Data set N is not owned by X`). Cross-check every candidate against `filecoin-pin data-set ls` — the active account's own sets, authoritative for ownership (it can lag on sets created moments ago; one you just created this session still counts). `data-set show <id>` tells you each set's provider. Among live, owned candidates on a needed provider, prefer a compact one (`id >= 1559`) per the rule above. Probe the provider's gateway once — `curl -sIL -o /dev/null -m 8 -w '%{http_code}' <provider-host>/ipfs/<any-known-cid>`; any HTTP answer including 404 = up, 503 or the 8s timeout = down, no retries — and take any live set on a provider you need.

### 5. Share

Cost preview on request: `filecoin-pin add <path> --dry-run`, report without uploading — a dry-run prints the same `File packed with root CID:` line as a real add, and that NEVER becomes a stage-one link (step 6). Otherwise:

```bash
filecoin-pin add <path> --egress-provider none --no-update-check
# owner-key mode only (user's explicit ask) — self-funding, capped:
filecoin-pin add <path> --auto-fund --max-balance <balance + 5> --egress-provider none --no-update-check
```

plus the step 4 metadata flag. Default (saved login): no funding flags — `--auto-fund` would be silently ignored anyway, and a shortfall is exactly step 3's funding round-trip (preflight exit 1, pre-filled link, no cap: the user approves the deposit in their own wallet). Owner-key mode: `--auto-fund` deposits from the wallet's USDFC whenever the Filecoin Pay balance or lockup would fall short; `--max-balance` is step 3's balance + 5, capping automatic top-up at 5 USDFC per share. If the add fails because funding needs exceed that cap — 🔴 CHECKPOINT: report the required amount and get the user's explicit permission before re-running with a higher cap, never raising it silently.

**FWSS storage only:** `--egress-provider none` on every add. The CLI's own default is already `none`, but the flag stays explicit so a stray `EGRESS_PROVIDER=beam` in the environment can never flip it. FilBeam CDN egress locks an extra 1 USDFC per new data set and is enabled ONLY when the user explicitly asks for CDN egress — same for any future add-on.

**Batch shares** (the user shares several artifacts at once): run one `add` per file IN PARALLEL — the CLI takes one path per add, but parallel runs collapse the wall-clock to roughly one add, and every file still gets its own link. One `balance` up front for the whole batch. A mid-batch funding shortfall fails only the adds that hit it — collect them, hand the user one funding link, re-run the failed adds after funding. In owner-key mode every add instead gets the same `--max-balance <that balance + 5>`, making the 5 USDFC top-up cap a shared ceiling for the batch (concurrent auto-funds cannot push past it) — a bigger need follows the funding-failure rule, explicit permission, never pooled silently. Report each stage-one link the moment its CID prints; each file gets its own ladder and ledger record.

Run the add in the background and poll its output — upload, on-chain confirmation, and the CLI's own IPNI wait take minutes, and nothing the user is waiting for depends on completion. The user gets their link from the two stages below while it runs.

### 6. Stage one: the propagating link

The moment `File packed with root CID: <cid>` prints during a REAL add (near upload start, minutes before completion), give the user `https://inbrowser.link/ipfs/<cid>` explicitly labeled **propagating, not yet verified** — the label is mandatory, and stage one is never the end. Never from a `--dry-run`: it prints the identical line for content that is never uploaded, and a link to it points at nothing. Presentation rule for EVERY link handed to the user (stage one, verified, funding, authorize): the link goes on its own line, plainly labeled — never inline mid-sentence where tool output and terminal noise can bury it.

### 7. Stage two: the verification ladder

Start the ladder as soon as stage one is reported, while the add still runs — retrievability comes from IPFS, never gate on `Add Complete`. Run rungs as quick probes between other work, never one long blocking poll.

**Rung 1 — IPNI publish status.** Minimum SP version: the piece-status signals require the storage provider to run **Curio ≥ v1.28.6** (the release that added `adCid`/`synced` to `GET /pdp/piece/<pieceCid>/status`). On an older provider (404, or a response without those fields) the only rung-1 signal is the CLI's own check (signal 3) — note the degraded verification in the report, and prefer providers on the version floor when targeting data sets explicitly.

Signals in order of authority; the first confirmed one passes the rung:

1. **Provider's own publish pipeline**: poll `curl -s https://<provider-host>/pdp/piece/<pieceCid>/status` (~15s; the Piece CID from the add's Copies section is correct here — this is the one place it belongs). `"synced": true` = the IPNI instance (cid.contact) confirmed it fully processed the advertisement — authoritative pass. `"synced": false` is INCONCLUSIVE, never failure: it's an in-memory, on-demand cache that clears on Curio restart and back-fills asynchronously — keep polling. `"advertised": true` with an `adCid` enables the client-side check below.
2. **Direct indexer confirmation**: `curl -s https://cid.contact/sync/status/ad/<adCid>` with the `adCid` from signal 1 — same authority, no provider middleman.
3. **The add's own `✓ IPNI provider records found.` line** — the CLI's internal check; still a valid pass.

Until this rung passes, no public gateway is touched — early polling seeds a negative cache that outlives indexing by ~20 minutes.

**Rung 2 — provider gateway 200.** Safe anytime, in parallel with rung 1 (only public gateways have the negative-cache problem): `curl -sIL -o /dev/null -w '%{http_code}' https://<provider-host>/ipfs/<root-cid>` → 200, host from the `Retrieval URL` in `Copies`, or — on the warm path where the add matched existing data sets — the provider hosts already in the local index. Warm-path providers typically serve within a couple of minutes, before external signals confirm anything. **Rung 1 + rung 2 = verified**: tell the user, never holding this behind the add finishing — and make the delivery unmissable: when the session has a browser surface (an embedded browser tab, or the OS open command for the user's own machine), OPEN the verified link in it, one tab per share — the page rendering is the delivery, chat lines get buried under tool output. Open only links the user just asked for, and only once verified — never an unverified stage-one link.

**The link never waits on the second copy.** One verified copy = a verified share link, handed to the user right away; the second copy is redundancy, not retrievability, and it always finishes in the background (delegate it to a subagent when the harness supports one). Nothing about copy 2 — slow commit, down provider, repair — ever delays the user's link.

**Rung 3 — public gateway, best-effort.** Only after rung 1: `curl -sIL -o /dev/null -w '%{http_code}' https://dweb.link/ipfs/<root-cid>` (follow redirects; the path URL 301s to a subdomain). dweb.link can 504 for 10–20 minutes after IPNI is populated. Report the dweb.link direct link (curl, hot-linking, embeds) when it passes; still 504 at report time → say the link is verified via IPNI + provider gateway and dweb.link is warming, and move on.

inbrowser.link is the canonical share URL (dweb.link and ipfs.io redirect browsers there anyway). If even the provider gateway serves nothing, the link stays labeled unverified until a later probe passes.

### 8. Background: on-chain confirmation

When the add finishes, read the `Add Complete` summary (no JSON output): Root CID under `Add Details` (`bafkrei…` small files, `bafyb…` larger — both valid), Data Set ID(s) under `Copies`. The Piece CID (`bafkzcib…`) names the stored CAR, not the content — never in a share link, and never hand the user a provider `/piece/…` URL either: it downloads the raw CAR container (users read it as "a zip"). User-facing links are exactly two: the share link and the Trace page.

**Whole add failed — provider down** (`Failed to create upload session` / 503): nothing was stored, the stage-one link is void — say so. Do NOT retry the metadata-filter add (it re-targets the same provider pair identically). Recover per step 4: pull state, probe liveness, one add per copy against existing healthy sets (`--copies 1 --data-set-id <id>`, usual flags), two distinct providers; existing sets can't cover both copies → create the redundancy set per the hard rules; no second distinct healthy provider at all → store one copy and mark `DEGRADED 1/2`.

**`Got 1/2 copies`** is degraded redundancy, not failure — copy 1 is stored and the link stands. Report it as: "redundancy degraded (1/2 copies) — adding the second copy in the background", and never describe a degraded share as "not stored" (that phrase belongs only to the failed-add case below). Then repair toward 2 copies NOW, in this session, in the background. Do NOT repair by re-running the metadata-filter add: it re-targets the same provider pair, and a broken commit path fails identically twice — while the provider often still serves the bytes, because redundancy is on-chain and retrievability is unaffected. The repair add is `--copies 1 --data-set-id <id>` where `<id>` is a live data set on a provider DISTINCT from the one holding copy 1 — never the set that already holds it; the point is landing the bytes somewhere else. A metadata-filter re-run is acceptable only for a transient-looking failure (timeout, not repeated `Commit failed`). Set `"note": "DEGRADED 1/2"` on the ledger record only if the repair has not landed by session end.

Report a short follow-up when the add completes: on-chain storage confirmed + data set ID(s) + the share link RESTATED — the final report always carries the canonical link on its own line, so the user never scrolls back for it. If the add fails after the link verified, say plainly: retrievable now, not yet stored — then Failures.

### 9. Record in the share ledger

The source of truth is `~/.filecoin-share/shares.json` — a JSON array, one record per share. It is strictly local and private: never store it on-chain, never upload it, never add it to a share — this skill only ever appends and edits records here.

The location is configurable by symlink: `~/.filecoin-share` may point anywhere; relocate with `mv ~/.filecoin-share <dest> && ln -s <dest> ~/.filecoin-share`. Always read and write through `~/.filecoin-share/`, never the resolved destination; a symlinked directory is normal. Asked to move it: do exactly that move-and-symlink, then confirm the ledger still resolves.

Append one record per share (create the file as `[]` if missing) — a bundle is ONE record, its contents listed inside (`files` = relative paths in the DAG, each reachable at `…/ipfs/<rootCid>/<path>`). Record what HAPPENED, not what was intended: every field comes from the actual `Add Complete` output, and `files` from listing the directory that was actually added. Writing `DELETED` into a note requires a chain receipt first — `data-set piece-status <id>` showing the piece pending removal or gone; rm command output alone is not a receipt.

```json
{"file":"NAME","date":"ISO-DATE","rootCid":"...","pieceCid":"bafkzcib...","datasets":[1548,1549],"network":"mainnet","note":""}
{"file":"EXAMPLE-DIR-NAME","shape":"bundle","fileCount":2,"files":["EXAMPLE-a.png","EXAMPLE-sub/EXAMPLE-b.ttf"],"date":"ISO-DATE","rootCid":"...","pieceCid":"...","datasets":[1548,1549],"network":"mainnet","note":""}
```

— base name (or directory name), UTC date (`date -u +%Y-%m-%d`), Root CID and Piece CID from the `Add Complete` summary, dataset IDs from `Copies`; for a bundle, build `files` with `find <dir> -type f` (relative paths) at share time. `note` carries state the user should see: `DEGRADED 1/2` (the repair queue), `DELETED <date>` after a removal, `superseded by <name>` — an empty note is the healthy case. That's the whole step; tell the user their share is recorded.

## Show, list, or check shares

Asked to show, list, or browse shares: read `~/.filecoin-share/shares.json` — a local JSON array, one record per share — and summarize it (file, date, the `https://inbrowser.link/ipfs/<rootCid>` link, note). Checking shares against Filecoin is out of this skill's scope; a user who asks to inspect on-chain state can be pointed at the CLI's own inspection commands (`data-set piece-status` and friends in `references/filecoin-pin-cli.md`). This skill's own scope ends at creating and repairing shares in the ledger.

## Failures

Explain every failure with the exact next action; the common ones (`No credentials found.`, expired/revoked session grants, insufficient USDFC in either auth mode, login grant-wait failures, lockup errors, IPNI timing) are in `references/filecoin-pin-cli.md` under Troubleshooting.
