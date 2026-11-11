# Save and share a session

Commands, credentials and errors are in `filecoin-pin-cli.md` next to this file.

## 0. Before you start

Pick the flow from the request:

| Request | Flow |
|---|---|
| "save this session", "pin", "encrypt" | Steps 1 to 7, then 9 |
| "save the handoff" | Steps 1 to 7, then 9, with no questions about what to include |
| "share this session with …", "hand off this session to …", "save this session and share it with …" | Steps 1 to 7 with a share flag in step 5, then 9. If the ledger already has a save of this session and nothing has changed since (`git status --short` clean in the project, no work done in this conversation since that save), run step 1, then step 8 with that save instead |
| "share my last session" | Step 1, then step 8 with the newest ledger entry whose `project` is the current project, skipping entries with `derivedFrom` (handoff-only copies made for an earlier share). No entry for this project: show the newest entries and ask which one |

Then ask what you need, all in one message:

- **What to include** (saves only). Every save holds the handoff. Ask whether to also include:
  - artifacts: list the local files you will reference under `## Artifacts`, by path, so the user can pick any to bundle;
  - the transcript: the full session, which needs the warning and a yes in step 3.
- **What the next agent should do** (saves only, optional). The answer becomes the first "Next" step under Open threads.
- **What the share contains** (shares only): the handoff and artifacts only, or the transcript too. 🔴 CHECKPOINT — sharing the transcript needs its own yes, even when the user confirmed it for the save: the recipient can read all of it.

Skip a question the user already answered ("include the report", "include the transcript", "without the transcript"). For "save the handoff", ask nothing.

If the user wants the transcript in the save but not in the share, that takes two uploads: the save, then a handoff-only copy for the share (step 8). Say so and get a yes, or save without the transcript.

## 1. Check the CLI and the login

```bash
command -v filecoin-pin || npm install -g filecoin-pin@latest   # needs Node 24+; always latest, so CLI improvements deploy
filecoin-pin get --help | grep -q -- '--share' && echo sharing-ok
```

No `sharing-ok`: follow "Install and version check" in `filecoin-pin-cli.md`. Then run the network check from the same file.

If the user chose the owner wallet (`PRIVATE_KEY`), skip the login check: it only looks at the saved login. Otherwise run it, and log in with `encrypt` in `--scopes` if it fails (Credentials in `filecoin-pin-cli.md`).

## 2. Write the handoff

Write it in this turn from what you already know about the session. No extra model call.

Your memory of the session can be out of date, especially after a compaction. Before writing, check what can have changed, with one cheap command each:

- every PR or issue you will mention as open, pending or "will merge": `gh pr view <n> --json state` or `gh issue view <n> --json state`;
- uncommitted work you will mention: `git status --short` in that repo.

Write what the checks show. If you can't check something (no `gh`, no network, not a git repo), write "as of <date>, not rechecked" next to it.

Make the save folder:

```bash
dir="$(mktemp -d)/session-$(date -u +%Y%m%dT%H%M%SZ)" && mkdir -p "$dir" && echo "$dir"
date -u +%Y-%m-%dT%H:%M:%SZ   # createdAt
```

Shell variables don't carry over between your commands. Wherever `$dir` appears below, write the path this printed, or set `dir=` again at the start of that command.

Write `$dir/handoff.md` in exactly this shape, with your values, never the example's. `createdAt` is the date printed above; `origin` takes the values from "Origin values" in `SKILL.md`, leaving out a field you don't have.

```markdown
---
version: 1
createdAt: 2026-10-29T14:02:11Z
origin: { tool: claude-code, toolVersion: 2.1.3 }
---

## Context

- What: the project or repo, and the task, in one line.
- Goal: the outcome the user wants, in their words when they gave one.
- Where it stands: one line. Details go under Open threads.

## Decisions

- A choice that was made, and why. One bullet each.

## Constraints

- Rules the next agent must follow: the user's requirements, limits, preferences and corrections.

## Artifacts

- `src/report.ts` (path on the sender's machine): what it is, and why it matters for the next step.
- https://example.com/spec: what it is, and why it matters.
- `artifacts/report.pdf`: bundled, what it is.
- `transcript.jsonl`: the full session transcript, included at the user's request (only when it is).

## Dead ends

- What was tried and didn't work, with the exact error or reason, so the next agent doesn't repeat it.

## Open threads

- Next: the one concrete step to take first.
- Then: other unfinished work and open questions, still open as of now.
```

Writing rules:

- Context is at most five bullets, about 100 words: no history, no command output, nothing that belongs under another heading.
- Status ("PR #12 was reviewed") is not a decision: it goes under Open threads, or nowhere. Project decisions go under Decisions, not Constraints.
- When the user said what the next agent should do, that is the "Next" step. Goal stays the overall outcome they want.
- Write `None.` under a heading that has nothing.
- Write a summary, not the transcript. Name files and links; don't paste their contents. Never write keys, tokens or `.env` values.
- Copy IDs, CIDs, commands and error messages exactly, never paraphrased.

Reread it once: every open thread is still open, every state you mention matches the checks above, and each bullet sits under the right heading.

If the user stops the flow at any point from here on, delete the save folder with the cleanup in step 7 before ending the turn: it can already hold a transcript copy.

## 3. Bundle artifacts and the transcript

**Artifacts.** Only files the user named or picked are bundled. Copy each one with the source path quoted, and list it under `## Artifacts` as `artifacts/<name>`:

```bash
mkdir -p "$dir/artifacts" && cp '<named-file>' "$dir/artifacts/"
```

A name that itself contains a quote can't be quoted safely: ask the user to rename the file first. Never copy a `.env` file, a key file, or anything the user didn't name.

**The transcript, only when the user asks for it.** Find the tool's transcript by the session id from "Origin values" in `SKILL.md`:

```bash
ls ~/.claude/projects/*/<sessionId>.jsonl                                   # Claude Code
find ~/.codex/sessions -name "rollout-*-$CODEX_SESSION_ID.jsonl"            # Codex
```

No single file found: ask the user for the path. Copy it into the folder, never touching the original, and check its size:

```bash
cp '<transcript-path>' "$dir/transcript.jsonl" && chmod 600 "$dir/transcript.jsonl" && du -h "$dir/transcript.jsonl"
```

Never print or read the copy into the conversation. 🔴 CHECKPOINT — warn the user, and wait for an explicit yes:

- the transcript holds everything you saw in this session: command output, file contents, pasted text. It can contain secrets and sensitive information that no scan reliably finds;
- the save is a paid upload of this size, stored until the piece is removed;
- if it is shared, the recipient can read all of it, and a share can't be revoked. That includes any Share link and Access key made earlier in this session: if the scan in step 4 finds `fak1_` values in the transcript, the recipient could open those earlier shares too;
- they should run their own redaction on the copy at `$dir/transcript.jsonl` (give the path) before saying yes.

No yes: delete the copy (`rm -f "$dir/transcript.jsonl"`) and save without it. On yes, list it under `## Artifacts`. Every upload has a size cap: if `add` later refuses with a size error, quote it and save without the transcript.

## 4. Check and review

**Format check.** All seven lines must print, each starting `ok`; a missing one names the failure:

```bash
f="$dir/handoff.md"
head -1 "$f" | grep -qx -- '---' && grep -qx 'version: 1' "$f" && grep -qE '^createdAt: [0-9]{4}-' "$f" && grep -qE '^origin: \{ ?tool: [a-z]' "$f" && echo 'ok frontmatter'
for h in 'Context' 'Decisions' 'Constraints' 'Artifacts' 'Dead ends' 'Open threads'; do grep -qx "## $h" "$f" && echo "ok $h"; done
```

Fewer than seven lines: fix `handoff.md` and run it again. `ok frontmatter` checks, in order, the opening `---`, `version`, `createdAt` and `origin`. The file must use LF line endings and no byte-order mark: a CRLF file fails every line.

**Secret scan.** A backstop, not a guarantee: it only catches known shapes. It prints the number of matches per file, never the matching text.

- CIDs are never flagged. A 64-character hex value is flagged unless the text marks it as a transaction hash: a `/tx/` link, or a label such as `tx`, `transaction`, or one ending in `hash` or `root`, with the `0x` prefix.
- `fak1_` and `fgr1_` count only with a real key after the prefix, so this skill's own placeholders don't.
- `…KEY=`, `…SECRET=`, `…TOKEN=` and `…PASSWORD=` assignments with a real value are flagged anywhere in a line, also inside a transcript's JSON lines.

```bash
node -e '
const fs = require("fs"), path = require("path"), readline = require("readline"), dir = process.argv[1]
const hash = /(\/tx\/|\b(?:tx|transaction|\w*hash|\w*root)\b["\x27\s:=\\]*)0x[0-9a-f]{64}(?![0-9a-f])/gi
const secret = /fak1_[A-Za-z0-9_-]{16,}|fgr1_[A-Za-z0-9_-]{16,}|-----BEGIN [A-Z ]*PRIVATE KEY|(?<![0-9a-fA-F])(?:0x)?[0-9a-fA-F]{64}(?![0-9a-fA-F])|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9_-]{20,}|xox[abprs]-|(?<![A-Z0-9_])[A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*=(?:\\?["\x27])?[A-Za-z0-9_\-\/+.]{6,}/g
const files = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? files(path.join(d, e.name)) : [path.join(d, e.name)])
;(async () => {
  for (const f of files(dir)) {
    let n = 0
    try {
      if (!fs.lstatSync(f).isFile()) { console.log(`UNREADABLE\t${path.relative(dir, f)}`); continue }
      const rl = readline.createInterface({ input: fs.createReadStream(f, "utf8"), crlfDelay: Infinity })
      for await (const line of rl) n += (line.replace(hash, "$1<hash>").match(secret) ?? []).length
    } catch (e) { console.log(`UNREADABLE\t${path.relative(dir, f)}`); continue }
    if (n > 0) console.log(`${n}\t${path.relative(dir, f)}`)
  }
})()' "$dir"
```

- A match in `handoff.md`: find the line you wrote and remove the secret, or mark a transaction hash as one (a label plus `0x`). Run the scan again.
- 🔴 CHECKPOINT — a match in a bundled file: stop. Tell the user which file matched and ask whether to drop it.
- Matches in `transcript.jsonl`: tell the user how many, and ask whether to redact it themselves, drop it, or keep it. Don't open the file to look.
- `UNREADABLE`: the file couldn't be scanned. Treat it as unscanned, not clean: say so, and let the user decide whether it ships.

**Review.** Show the user the handoff as it will be uploaded, with the bundled files, the transcript line and what the scan found, and offer one round of edits: it is what the next agent will act on. If their goal relies on something the checks in step 2 showed is out of date (a PR they want merged is already merged), say so. If they change the handoff, run the format check and the scan again. This is a quick review, not a gate: no answer means go on.

## 5. Upload

```bash
filecoin-pin add "$dir" --encrypt --egress-provider none --no-update-check
```

- To share in the same run, add `--get-share-link-restricted`, or `--get-share-link` for an open link the user asked for and confirmed ("Open links" in `filecoin-pin-cli.md`): one command, and no second read of the header from the provider.
- With the owner wallet, run it with `--dry-run` first and show the user the cost. 🔴 CHECKPOINT — run the real upload only after they say yes.
- It takes one to a few minutes. Let it finish: a slow upload is not a failed one, and you never stop it to start again. With a share flag, run it in the foreground with a 10-minute timeout: its output holds the Access key, and a background run saves the whole output to a file. Without one, you can run it in the background and poll.

Read the result with "Reading the `add` result" in `filecoin-pin-cli.md`. Never run `add` again to recover from a failure: a second run makes a new CID and pays for a second upload. The table there says what to do instead, including the funding stop, the one case where you run it again yourself.

The Encrypted root CID is the root CID in the output. Once the upload is stored, even when it isn't confirmed yet, go on to step 6: the CID stays the same.

## 6. Record it in the ledger

Add one entry to `~/.filecoin-share/sessions.json`. It holds only these fields, never a summary, a title or a key:

```json
{
  "cid": "<Encrypted root CID>",
  "savedAt": "<UTC time, date -u +%Y-%m-%dT%H:%M:%SZ>",
  "trigger": "manual",
  "project": "<git rev-parse --show-toplevel, or pwd>",
  "network": "<mainnet or calibration, the network the upload went to>",
  "origin": { "tool": "claude-code", "toolVersion": "2.1.3", "sessionId": "…", "transcriptPath": "…" }
}
```

- Add `"transcript": true` only when the upload includes the transcript.
- `origin` follows "Origin values" in `SKILL.md`: `tool` always, other fields only when the tool exposes them.
- `transcriptPath` is the local path of the original transcript, filled only when step 3 found it, through the lookup or the path the user gave. The transcript itself is uploaded only when the user confirmed it.

Append it, keeping the file mode `0600`:

```bash
mkdir -p ~/.filecoin-share && ENTRY='<the entry as one line of JSON>' node -e '
const fs = require("fs"), f = process.env.HOME + "/.filecoin-share/sessions.json"
const list = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : []
if (!Array.isArray(list)) throw new Error("ledger is not a JSON array")
list.push(JSON.parse(process.env.ENTRY))
fs.writeFileSync(f, JSON.stringify(list, null, 2) + "\n", { mode: 0o600 })
fs.chmodSync(f, 0o600)'
```

- A value with a single quote (an apostrophe in a project path) breaks the `ENTRY='…'` quoting, and the command fails with the ledger untouched. Pass the entry another way then, for example `ENTRY="$(cat entry.json)"` from a temp file you delete after.
- The ledger isn't valid JSON or isn't an array (a crash or a hand edit): don't lose the entry. Move the broken file aside (`mv ~/.filecoin-share/sessions.json ~/.filecoin-share/sessions.json.corrupt`), tell the user its contents can be recovered by hand, and run the append again.

If this request also needs a handoff-only copy for the share (the two-uploads case in step 0), make it now from the save folder, before cleaning up: step 8.

## 7. Clean up

Delete the save folder: it holds the transcript in plain text when one was included. Use this guard for every folder this skill makes with `mktemp -d`, including when the user stops the flow early and in `receive.md`. Pass the `mktemp -d` folder itself: for the save folder, that is the parent (`dirname`) of the path printed in step 2.

```bash
d='<the mktemp -d folder>'
case "$d" in
  *..*|*/tmp.*/*) echo "refusing to delete $d — not a mktemp -d folder itself" ;;
  /tmp/tmp.?*|/var/folders/*/*/T/tmp.?*|/private/var/folders/*/*/T/tmp.?*|"${TMPDIR%/}"/tmp.?*) rm -rf "$d" && echo cleaned ;;
  *) echo "refusing to delete $d — not a mktemp -d folder" ;;
esac
```

It deletes only a folder named `tmp.*` directly in the temp root, and refuses anything else, including the temp root and its parents.

## 8. Share

A link opens the whole upload, so compare what the saved upload holds with what the user wants to share. For an entry whose `network` is `calibration`, add `--network calibration` to every command here.

| Case | Do |
|---|---|
| They match: no transcript in the save, or the user confirmed sharing it | `filecoin-pin get-share-link <cid> --restricted --no-update-check` (no `--restricted` for an open link the user asked for) |
| The save has the transcript, the user wants the handoff only, and the ledger has an entry whose `derivedFrom` is this save's CID | That entry is the handoff-only copy: `get-share-link` on its CID, as above. Nothing is uploaded |
| The same, but there is no such entry | Make a handoff-only copy, below |
| The user wants the transcript, but the save doesn't have it | Save again including the transcript (steps 2 to 7), and share that save |

**Handoff-only copy.** 🔴 CHECKPOINT — it is one more paid upload: say so, and wait for a yes. Then:

1. Restore the save and copy its folder, keeping its `session-…` name, into a second temp folder without the transcript. `get` prints the saved path:

   ```bash
   o="$(mktemp -d)" && echo "$o" && filecoin-pin get <cid> "$o" --no-update-check
   t="$(mktemp -d)" && cp -R '<saved-path>' "$t/" && rm -f "$t/<session folder>/transcript.jsonl" && echo "$t/<session folder>"
   ```

2. Edit `$t/<session folder>/handoff.md` in place: remove the `transcript.jsonl` line from `## Artifacts`, writing `None.` if it was the only one.
3. Run the format check and the secret scan (step 4) on it, with `dir='<the $t/<session folder> path>'` at the start of each command.
4. Upload it with the share flag, as in step 5 (with the owner wallet: dry run, cost, yes):

   ```bash
   filecoin-pin add '<the $t/<session folder> path>' --encrypt --get-share-link-restricted --egress-provider none --no-update-check
   ```

   If this upload fails before anything is stored, the save and its ledger entry still stand: the session is saved, just not shared. Nothing was uploaded, so running it again when the user asks is not the forbidden re-run.
5. Record it in the ledger (step 6) with the save's `origin`, `network` and `project`, no `"transcript"`, and `"derivedFrom": "<the save's CID>"`.
6. Clean up `$o` and `$t`, each passed to the guard in step 7 as is.

## 9. Reply

Start the reply with this block:

```
<Session saved | Session shared> · <confirmed on chain | stored, not yet confirmed on chain> · <mainnet | calibration>

Encrypted root CID:
bafy…

Share link (send by one channel, e.g. email):
https://…#v1/…

Access key (send by a different channel, e.g. a chat message):
fak1_…
```

- **Confirmed or not:** as "Reading the `add` result" in `filecoin-pin-cli.md` says.
- **Nothing shared:** leave out the link and the key.
- **Shared an earlier save, no upload in this run:** "Session shared", with no confirmation part: it was reported when that save was made.
- **Open link:** leave out the Access key block, label the link "Share link (opens on its own: anyone who has it can read the content)", and repeat the warning from "Open links".

Then, in short bullets:

- what the upload holds: the handoff (a summary of context, decisions, constraints, artifacts, dead ends and open threads; no keys), the bundled artifacts, and whether it includes the transcript;
- who can read it: only the user (the owner wallet, or a session key with their Grant), plus, when shared, whoever holds the link and the Access key. A share can't be revoked, and this conversation's history now holds the Access key: anyone who can read this chat or its transcript can open the share;
- when shared: the receiving agent restores it with this skill (`filecoin-pin get --share`). A fresh upload is usually retrievable within minutes; "not found yet" means indexing is still catching up, so wait and retry. The Access key isn't saved anywhere, so send it now; another `get-share-link` makes a new link and key;
- not yet confirmed: the warning and the `piece-status` command from "Reading the `add` result";
- fewer copies than requested: which providers hold it;
- calibration: the recipient passes `--network calibration` too.

After a plain save, ask once: "Do you want a Share link for this session now? It makes a link and a separate Access key, and uploads nothing." On yes, run step 8, then reply with only the link and key block and the bullets that are new: who can read it now, how the recipient opens it, that the key isn't saved anywhere, and whether the share includes the transcript. Don't repeat the status line, the CID, what the upload holds, the redundancy or the network note.

After the reply, never repeat the Access key, and never write it to the ledger, a file or a log.
