---
name: engram-share
description: Use when the user wants a shareable or durable browser link for something an agent made, or says "share this file", "share these files", "share this folder", "share as a bundle", "one link for all of these", "pin this", "publish this report", "send someone this file", "make this public", "ipfs link". Single .html, .htm, .md, .mp4 files (each under 1000 MiB), or a directory shared as one bundle link (any contents, under 1000 MiB total). Asked to show, list, or check existing shares — use engram-library instead; this skill only creates and repairs them.
---

# engram-share

One command from a local file to a durable, verified browser link: store the file on Filecoin mainnet through the `filecoin-pin` CLI, hand back `https://inbrowser.link/ipfs/<root-cid>`, and record the share in the local index. The CLI is the single seam — drive it directly, no wrapper scripts. Flags, output formats, and troubleshooting live in `references/filecoin-pin-cli.md`; read that, never the web.

The skill shares; the CLI pins. "Pin" appears only in CLI commands and quoted user phrases, never in your own reports.

## Red lines

Hard rules; each owning section carries the full rule. Skim before every share.

- Mainnet only; calibration is never an option (Network).
- Share exactly the paths the user named — one add per requested share, and nothing else is ever pinned (Scope gate).
- Secrets files are write-only; key material never enters conversation, output, or logs (Keys).
- `--provider-id` never as a reuse mechanism — it always creates a new data set and stacks billing floors; deliberate redundancy-set creation is its only use (step 4).
- Never create a new data set to upgrade off a legacy one without the user's explicit permission — it's a real new billing floor, same gate as raising the auto-fund cap (step 4).
- A compact-pair upgrade is forward-only: past shares and the legacy pair are never touched, moved, or re-added — only new shares target the new pair (step 4).
- Never plan a 1-copy share; two copies on two distinct providers, degraded only temporarily (step 4).
- Never run `payments deposit` manually (step 3).
- In session mode, never attempt any payments operation — a session key cannot move money; funding is the owner's, via the user (step 2).
- Never raise the 5 USDFC auto-fund cap without the user's explicit permission (step 5).
- Every add passes `--egress-provider none` unless the user explicitly names the add-on (step 5).
- Never report an unverified link without its "propagating" label, and never stop at stage one (step 6).
- Never poll a public gateway before the IPNI rung passes — it seeds a negative cache (step 7).
- Never put a Piece CID in a share link (step 8).
- Never store the share ledger on-chain; only files the user explicitly asked to share are ever stored (step 9). The rendered library (`engram-library`'s job) stays local too.

## Scope gate

Two shapes of share:

- **Single file** with a `.html`, `.htm`, `.md`, or `.mp4` extension — the self-contained artifacts agents produce. Other single files (images, archives, arbitrary data): decline, suggest converting to self-contained HTML, bundling into a directory share, or using the filecoin-pin CLI directly. Markdown is stored as-is; tell the user gateways serve it as plain text, so HTML renders better.
- **Bundle** — a directory shared as ONE link: `filecoin-pin add <dir>` packs it into a single DAG, and the link renders as a browsable folder listing with every file inside reachable at `…/ipfs/<root-cid>/<filename>`. Pass the directory ITSELF to `add` — an archive (zip/tar) made first pins as one opaque file: no folder view, no per-file links, and the user gets a download instead of a browsable bundle. Any file types are fine inside a bundle (the bundle is the artifact); dotfiles are skipped unless `--include-hidden`. Warn before bundling anything that looks unintended (build junk, secrets-shaped files, `node_modules`) — the whole tree becomes public.

Size gate, every share: check before sharing — single file `stat -f %z` (macOS) / `stat -c %s` (Linux), bundle `du -sk <dir>` for the total. At or over 1,048,576,000 bytes (1000 MiB — the skill's hard cap, matching typical provider per-upload limits; a bundle is one piece, so the whole tree counts), decline with the size and the limit — there is no "just this once". Oversized MP4 → suggest trimming or re-encoding; oversized HTML → slim embedded media; oversized bundle → split it or drop the heavy files. Under the limit, MP4 links play in the browser (gateways stream with byte-range support); mention that large files can buffer on best-effort gateways.

Filename privacy: the base name is published on-chain as piece metadata where anyone can read it — and in a bundle, every file and folder name inside the tree is public as part of the DAG. If any name reveals something sensitive, warn and suggest a neutral rename before sharing. Contents are public anyway; this check is about the names.

## Network: mainnet only

This skill operates exclusively on Filecoin mainnet: never offer, configure, or fall back to a calibration/testnet endpoint, and never source an env file that points the CLI at one. If the configured RPC or key targets calibration, stop and tell the user.

## Keys: write-only secrets

Never expose a private key or env-var value into the session, chat, logs, or any file the user did not ask for: never ask the user to paste a key, never `echo`/`env`/`printenv` or interpolate key material into output. Load keys only inside the shell that runs the CLI. Mask wallet addresses you display; call the key "the configured key" when debugging.

Secrets files (`~/.engram.env`, `~/.filecoin-pin.env`, `~/.filecoin.env`, any user-designated key file) are write-only from your perspective: inspect them ONLY with boolean or count checks (`test -f`, `grep -qE '^(export )?PRIVATE_KEY=' file`, `wc -l < file`) and branch on exit codes — a byte-emitting read (`cat`, `sed`, `head`, unqualified `grep`) plus one wrong format assumption leaks a whole bare-hex key. Unknown format = every byte is secret. Bare-key files (single hex line) are valid: load with `PRIVATE_KEY="$(cat file)"` prefixed to the CLI command, never echoed.

## Workflow

### 1. Preflight

`command -v filecoin-pin`; missing → `npm install -g filecoin-pin` (needs Node 24+; engine/syntax errors → `node --version`, tell the user to upgrade). `references/filecoin-pin-cli.md` is what step 7 onward reads and is tracked in git so it's visible on install, but it can drift from whatever CLI version is actually installed: compare `filecoin-pin --version` against the "verified against vX.Y.Z" line at the top of the reference file, and if they differ (or the file is missing), regenerate it now, once, before continuing — run `filecoin-pin --help` and each subcommand's `--help` (`add`, `import`, `payments`, `data-set`, `provider`, `rm`, `session` — including their sub-subcommands, e.g. `payments status`, `session create`, `provider ping`), condense into one section per command plus a Troubleshooting section (funding shortfalls, lockup errors, IPNI timing), and update the version line at the top. Done when the binary resolves and the reference file's version line matches the installed CLI.

### 2. Authenticate

Two credential modes: **owner** (a wallet private key — full access, including payments) and **session** (a scoped key authorized on-chain by an owner — data operations only). Resolve the first source that exists. When BOTH a session key and an owner key are present in the environment, prefer the session key — the narrower credential — but say so, and do not assume the CLI resolves it the same way: v2.0.1 documents both under one env-var tier without stating a winner, so pass the choice explicitly with `--session-key`/`--wallet-address` rather than relying on implicit precedence:

1. `SESSION_KEY` + `WALLET_ADDRESS` in the environment — session mode;
2. `PRIVATE_KEY` in the environment — owner mode;
3. `~/.engram.env`; 4. `~/.filecoin-pin.env`; 5. `~/.filecoin.env`;
6. a user-designated key file, often bare-hex — verify shape by count/boolean checks only, load per Keys.

For files (3–6), pass the path to the CLI with `--credentials-file <path>` rather than sourcing it: the CLI loads a dotenv-style file before resolving other options and never overrides variables already set, so the key never enters your shell or your environment. Ensure `chmod 600`. A file may carry either `PRIVATE_KEY` or `SESSION_KEY`+`WALLET_ADDRESS` — decide which by boolean grep only (`grep -qE '^(export )?SESSION_KEY=' file`), never by reading it, per Keys. A bare-hex file has no variable names and is therefore always an owner key.

Step 2 is done when a source is resolved AND you have told the user which mode is in play. Never resolve silently between the two: they differ in what the rest of this workflow is permitted to do.

**Session mode: data operations only.** A session key can create data sets and add pieces; it cannot move money. The authorizable scopes are exactly `createDataSet`, `addPieces`, `schedulePieceRemovals` and `terminateService` — there is no payments scope — so `payments setup`, `payments fund`, `payments deposit` and `add --auto-fund` all need the owner wallet. In session mode: step 3 runs `payments status` read-only and never `payments setup --auto`; step 5 omits `--auto-fund` and `--max-balance`; and a funding shortfall is not yours to fix — stop, report the shortfall, and tell the user to fund from the owner wallet (the Filecoin Pay console is the easiest route), then re-run. Verify this against the installed CLI the first time you hit it: the payments commands accept session flags, and v2 gates scopes per command, so a clear refusal is expected rather than silent success.

Asked to set up a session key: instruct, never act. Creating one requires the owner key (`filecoin-pin session create --scopes createDataSet,addPieces` — the default grants ALL scopes, needlessly including piece removal and service termination), so it is the user's command to run, not yours, exactly as with the key file below. Two-party alternative when the user will not expose the owner key to this machine at all: they run `filecoin-pin session generate` here, hand you only the session ADDRESS, and authorize it elsewhere with `session authorize <address> --scopes createDataSet,addPieces`. **Never run `session generate` yourself** — verified against v2.0.1, it prints the session private key on stdout, so running it inside the session writes key material straight into the transcript and logs, exactly what Keys forbids. It is the user's command in their own shell; ask them for the address only.

**First run (nothing configured):** stop and instruct the user to create `~/.filecoin-pin.env` themselves containing `PRIVATE_KEY=0x...` for a funded wallet (FIL for gas, USDFC for storage), then `chmod 600` it. Never offer to write the key file, and never ask for the key in the conversation. A session key is the better first-run answer when the user already has a funded owner wallet elsewhere — point them at the session-mode rules above. (No browser-pairing flow exists in the released CLI — `session create --console` and `session import` are not in v2.0.1. One is being built as `filecoin-pin login`, not as a `--console` flag: it pairs with the console's session-keys page and will be a better first-run answer than a hand-written key file. It is still draft (filecoin-pin#699→#703), so check `filecoin-pin login --help` before ever instructing the user to run it, and fall back to this section when it is absent.)

### 3. Payment setup

`filecoin-pin payments status`. Gate: `Network: Filecoin - Mainnet`, or stop per Network. **In session mode, status is all you may run here** — read the balance, and if funds or allowances are missing, stop per step 2's session rules instead of trying to fix it. In owner mode, if the account is unconfigured or has no Filecoin Pay balance, run `filecoin-pin payments setup --auto` once — it approves the storage service and seeds a deposit so the first upload does not fail cryptically; skip it when funds and allowances already show. Shortfalls during a share are `--auto-fund`'s job on the add, never a manual `payments deposit`. Step 3 is done when status shows mainnet with funds in place, with the balance noted (step 5 uses it).

**Wallet has no FIL or no USDFC at all** (setup or `--auto-fund` fails on wallet balance, not Filecoin Pay balance — the CLI reports the shortfall but not where to get funds): stop and tell the user plainly what the wallet needs and where to get it. Easiest: the Filecoin Pay console at `https://pay.filecoin.cloud/console` swaps to USDFC and deposits in one guided flow. Alternatives: mint USDFC against FIL at `https://app.usdfc.net` (Secured Finance, redeemable anytime) or swap FIL→USDFC on SushiSwap; the FIL itself (gas — well under 1 FIL covers many shares) comes from any major exchange. A few USDFC covers many shares; re-run `payments status` when they say it's done.

### 4. Target the skill's data sets

Every add passes `--data-set-metadata source=engram-share`. Treat the tag value as an opaque constant that MUST never change — it is the on-chain key to every data set this skill has ever created, and a different value orphans them all. The CLI find-or-creates: matches existing skill data sets (`Matched existing data sets … via metadata filter`) or creates one per storage copy, each on a different provider. The priority order is fixed: reuse existing data sets first (they cost nothing extra until their billed floor is exhausted), create a new one only when reuse cannot deliver both copies — redundancy outranks the creation cost, so a new set on a fresh provider beats going degraded.

**Compact vs. legacy** (synapse-sdk#925): mainnet data sets with ID `1559` or higher use the newer, more efficient `PieceV2` storage layout ("compact" — see CONTEXT.md); below `1559` is "legacy," still fully retrievable, just less efficient. This never affects a user with no existing skill data set — a freshly created set is always compact, no action needed. It matters in two cases:
1. **Choosing among multiple matching sets**: when the metadata filter matches more than one live data set on a needed provider, prefer a compact one (`id >= 1559`) over a legacy one — same reuse-is-free economics, just the more efficient set first.
2. **The skill's own working pair predates the cutover**: check the pair's IDs against `1559` before targeting them. If they're legacy and the wallet has comfortably more than one share's worth of funds beyond the current balance, offer a one-time upgrade — explain the ongoing cost delta (a new pair adds its own floor, ~0.04 USDFC/month) and that the old pair keeps working untouched either way. Create the new pair only on explicit yes; from then on it's the preferred target for new shares (existing shares' records and the old pair are left exactly as they are — this is a going-forward preference, never a migration of past shares).

**Filter matches more than the pair** (skill data sets accumulate over time; the CLI refuses non-interactively: `Add failed: --data-set-metadata matched N data sets … but expected 2`): fall back to explicit targeting — pick two live sets on two distinct providers (liveness probe below), one add per copy with `--copies 1 --data-set-id <id>`, run in parallel.

Two hard rules, happy path and repair alike:

1. **Two copies on two distinct providers, always.** Never plan a 1-copy share to save cost. When the usual pair can't host both copies (a provider down), fall through in order: another EXISTING skill data set on a distinct healthy provider first (reuse is free); a NEW data set on a healthy provider only when no existing set can take the copy — the extra floor is the price of the redundancy promise. Only when no second distinct healthy provider is reachable at all does the share go out degraded: report it and set `"note": "DEGRADED 1/2"` on the share's ledger record — the note is the repair queue — never hold the session open waiting for a provider to recover.
2. **Reuse goes through `--data-set-id`, never `--provider-id`.** An existing data set is always reused by naming it: `--data-set-id <id>`, one add per copy (one `--data-set-id` restricts the add to that set's provider). `--provider-id` can NOT reuse — it always mints a brand-new data set even when that provider already holds skill data, so reaching for it "to reuse provider N's set" silently stacks a billing floor instead. Its only legitimate use is the last resort of rule 1: deliberately creating a redundancy set at a healthy provider that holds no skill data set, the new floor accepted knowingly.

**Picking a set** (repair, substitution, or the multi-match fallback): candidate IDs come from `~/.engram/shares.json` and recent add output; `data-set show <id>` tells you each set's provider. Among live candidates on a needed provider, prefer a compact one (`id >= 1559`) per the rule above. Probe the provider once with `filecoin-pin provider ping <provider-id>` — the CLI's supported liveness check, which queries the provider's PDP service directly. A successful ping = up; a failure or timeout = down, no retries — and take any live set on a provider you need. (`provider ping` has been available since at least v1.2.0, so no version fallback is needed.) (`data-set ls` can lag and omit live sets; use it only for extra candidates.)

### 5. Share

Cost preview on request: `filecoin-pin add <path> --dry-run`, report without uploading. Otherwise:

```bash
filecoin-pin add <path> --auto-fund --max-balance <balance + 5> --egress-provider none
```

plus the step 4 metadata flag. `--auto-fund` deposits from the wallet's USDFC whenever the Filecoin Pay balance or lockup would fall short; `--max-balance` is step 3's balance + 5, capping automatic top-up at 5 USDFC per share. If the add fails because funding needs exceed that cap, report the required amount and get the user's explicit permission before re-running with a higher cap — never raise it silently.

**Session mode:** drop `--auto-fund` and `--max-balance` entirely — the add is `filecoin-pin add <path> --egress-provider none` plus the step 4 metadata flag. A shortfall then surfaces as a plain add failure: handle it per step 2's session rules (report it, hand funding back to the user), never by retrying with funding flags a session key cannot use.

**FWSS storage only:** `--egress-provider none` on every add. As of CLI v2.0.0 `none` is already the default, so passing it is belt-and-braces — keep it explicit so the behaviour is pinned regardless of which CLI version is installed. FilBeam CDN egress (`beam`) draws egress from the owner lockup and locks an extra 1 USDFC per new data set; enable it ONLY when the user explicitly asks for CDN egress — same for any future add-on.

**Batch shares** (the user shares several artifacts at once): run one `add` per file IN PARALLEL — the CLI takes one path per add, but parallel runs collapse the wall-clock to roughly one add, and every file still gets its own link. One `payments status` up front for the whole batch; every add gets the same `--max-balance <that balance + 5>`, which makes the 5 USDFC top-up cap a shared ceiling for the batch (concurrent auto-funds cannot push past it) — a bigger need follows the funding-failure rule, explicit permission, never pooled silently. Report each stage-one link the moment its CID prints; each file gets its own ladder and ledger record.

Keep the default 2 copies. Run the add in the background and poll its output — upload, on-chain confirmation, and the CLI's own IPNI wait take minutes, and nothing the user is waiting for depends on completion. The user gets their link from the two stages below while it runs.

### 6. Stage one: the propagating link

The moment `File packed with root CID: <cid>` prints (near upload start, minutes before completion), give the user `https://inbrowser.link/ipfs/<cid>` explicitly labeled **propagating, not yet verified** — the label is mandatory, and stage one is never the end.

### 7. Stage two: the verification ladder

Start the ladder as soon as stage one is reported, while the add still runs — retrievability comes from IPFS, never gate on `Add Complete`. Run rungs as quick probes between other work, never one long blocking poll.

**Rung 1 — IPNI publish status.** As of CLI v2.0.0 the add confirms indexing through the provider's Curio piece-status endpoint itself (filecoin-pin#689), so the CLI's own signal is authoritative and costs nothing — read it first, and hand-probe only when it is absent or inconclusive.

Signals in order of authority; the first confirmed one passes the rung:

1. **The add's own confirmation** — the `✓ IPNI provider records found.` line in the add output. On v2.0.0+ this is the CLI's Curio piece-status check: an authoritative pass. An `IPNI provider records not found` warning does NOT fail the add and is INCONCLUSIVE, never failure — fall through to the signals below rather than reporting a problem.
2. **Provider's own publish pipeline**: poll `curl -s https://<provider-host>/pdp/piece/<pieceCid>/status` (~15s; the Piece CID from the add's Copies section is correct here — this is the one place it belongs). `"synced": true` = the IPNI instance (cid.contact) confirmed it fully processed the advertisement — authoritative pass. `"synced": false` is INCONCLUSIVE, never failure: it's an in-memory, on-demand cache that clears on Curio restart and back-fills asynchronously — keep polling. `"advertised": true` with an `adCid` enables the client-side check below.
3. **Direct indexer confirmation**: `curl -s https://cid.contact/sync/status/ad/<adCid>` with the `adCid` from signal 2 — same authority, no provider middleman.

Minimum SP version for the hand-probed signals (2 and 3): they require the storage provider to run **Curio ≥ v1.28.6** (the release that added `adCid`/`synced` to `GET /pdp/piece/<pieceCid>/status`). On an older provider (404, or a response without those fields) signal 1 is the only rung-1 signal available — note the degraded verification in the report, and prefer providers on the version floor when targeting data sets explicitly.

Until this rung passes, no public gateway is touched — early polling seeds a negative cache that outlives indexing by ~20 minutes.

**Rung 2 — provider gateway 200.** Safe anytime, in parallel with rung 1 (only public gateways have the negative-cache problem): `curl -sIL -o /dev/null -w '%{http_code}' https://<provider-host>/ipfs/<root-cid>` → 200, host from the `Retrieval URL` in `Copies`, or — on the warm path where the add matched existing data sets — the provider hosts already in the local index. Warm-path providers typically serve within a couple of minutes, before external signals confirm anything. **Rung 1 + rung 2 = verified**: tell the user, never holding this behind the add finishing.

**The link never waits on the second copy.** One verified copy = a verified share link, handed to the user right away; the second copy is redundancy, not retrievability, and it always finishes in the background (delegate it to a subagent when the harness supports one). Nothing about copy 2 — slow commit, down provider, repair — ever delays the user's link.

**Rung 3 — public gateway, best-effort.** Only after rung 1: `curl -sIL -o /dev/null -w '%{http_code}' https://dweb.link/ipfs/<root-cid>` (follow redirects; the path URL 301s to a subdomain). dweb.link can 504 for 10–20 minutes after IPNI is populated. Report the dweb.link direct link (curl, hot-linking, embeds) when it passes; still 504 at report time → say the link is verified via IPNI + provider gateway and dweb.link is warming, and move on.

inbrowser.link is the canonical share URL (dweb.link and ipfs.io redirect browsers there anyway). If even the provider gateway serves nothing, the link stays labeled unverified until a later probe passes.

### 8. Background: on-chain confirmation

When the add finishes, read the `Add Complete` summary (no JSON output): Root CID under `Add Details` (`bafkrei…` small files, `bafyb…` larger — both valid), Data Set ID(s) under `Copies`. The Piece CID (`bafkzcib…`) names the stored CAR, not the content — never in a share link, and never hand the user a provider `/piece/…` URL either: it downloads the raw CAR container (users read it as "a zip"). User-facing links are exactly two: the share link and the Trace page.

**Whole add failed — provider down** (`Failed to create upload session` / 503): nothing was stored, the stage-one link is void — say so. Do NOT retry the metadata-filter add (it re-targets the same provider pair identically). Recover per step 4: pull state, probe liveness, one add per copy against existing healthy sets (`--copies 1 --data-set-id <id>`, usual flags), two distinct providers; existing sets can't cover both copies → create the redundancy set per the hard rules; no second distinct healthy provider at all → store one copy and mark `DEGRADED 1/2`.

**`Got 1/2 copies`** is degraded redundancy, not failure — copy 1 is stored and the link stands. Report it as: "redundancy degraded (1/2 copies) — adding the second copy in the background", and never describe a degraded share as "not stored" (that phrase belongs only to the failed-add case below). Then repair toward 2 copies NOW, in this session, in the background. Do NOT repair by re-running the metadata-filter add: it re-targets the same provider pair, and a broken commit path fails identically twice — while the provider often still serves the bytes, because redundancy is on-chain and retrievability is unaffected. The repair add is `--copies 1 --data-set-id <id>` where `<id>` is a live data set on a provider DISTINCT from the one holding copy 1 — never the set that already holds it; the point is landing the bytes somewhere else. A metadata-filter re-run is acceptable only for a transient-looking failure (timeout, not repeated `Commit failed`). Set `"note": "DEGRADED 1/2"` on the ledger record only if the repair has not landed by session end.

Report a short follow-up when the add completes: on-chain storage confirmed + data set ID(s). If the add fails after the link verified, say plainly: retrievable now, not yet stored — then Failures.

### 9. Record in the share ledger

The source of truth is `~/.engram/shares.json` — a JSON array, one record per share. It is strictly local and private: never store it on-chain, never upload it, never add it to a share. Browsing, checking, and rendering the ledger into a viewable page are `engram-library`'s job, not this skill's — this skill only ever appends and edits records here.

The location is configurable by symlink: `~/.engram` may point anywhere; relocate with `mv ~/.engram <dest> && ln -s <dest> ~/.engram`. Always read and write through `~/.engram/`, never the resolved destination; a symlinked directory is normal. Asked to move it: do exactly that move-and-symlink, then confirm the ledger still resolves.

Append one record per share (create the file as `[]` if missing) — a bundle is ONE record, its contents listed inside (`files` = relative paths in the DAG, each reachable at `…/ipfs/<rootCid>/<path>`). Record what HAPPENED, not what was intended: every field comes from the actual `Add Complete` output, and `files` from listing the directory that was actually added. Writing `DELETED` into a note requires a chain receipt first — `data-set piece-status <id>` showing the piece pending removal or gone; rm command output alone is not a receipt.

```json
{"file":"NAME","date":"ISO-DATE","rootCid":"...","pieceCid":"bafkzcib...","datasets":[1548,1549],"network":"mainnet","note":""}
{"file":"EXAMPLE-DIR-NAME","shape":"bundle","fileCount":2,"files":["EXAMPLE-a.png","EXAMPLE-sub/EXAMPLE-b.ttf"],"date":"ISO-DATE","rootCid":"...","pieceCid":"...","datasets":[1548,1549],"network":"mainnet","note":""}
```

— base name (or directory name), UTC date (`date -u +%Y-%m-%d`), Root CID and Piece CID from the `Add Complete` summary, dataset IDs from `Copies`; for a bundle, build `files` with `find <dir> -type f` (relative paths) at share time. `note` carries state the user should see: `DEGRADED 1/2` (the repair queue), `DELETED <date>` after a removal, `superseded by <name>` — an empty note is the healthy case. That's the whole step; tell the user their share is recorded and, if they want to see it alongside their other shares, that engram-library renders the browsable view.

## Show, list, or check shares

Asked to show, list, browse, or check shares against Filecoin: that's `engram-library`, not this skill — hand off to it. This skill's own scope ends at creating and repairing shares in the ledger.

## Failures

Explain every failure with the exact next action; the common ones (insufficient USDFC, `--auto-fund`, lockup errors, IPNI timing) are in `references/filecoin-pin-cli.md` under Troubleshooting.
