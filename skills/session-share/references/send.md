# Save and share a session

Commands, credentials and errors are in `filecoin-pin-cli.md` next to this file.

Which flow:

- "save", "pin", "encrypt" this session: steps 1 to 5.
- "share this session with …", "hand off this session to …", or "save this session and share it with …": steps 1 to 5, with `--get-share-link-restricted` in step 5 — but only after the share-content questions below are answered; a share that must not include the transcript while the save does goes through step 6's handoff-only upload instead. Then reply as in step 7. If the ledger already has a save of this session and nothing has changed since (check: `git status --short` clean in the project, and no work done in this conversation since that save), run step 6 with that CID instead.
- "share my last session": step 1, then step 6, with the newest entry in the ledger (`~/.filecoin-share/sessions.json`) whose `project` is the current project, skipping entries with `derivedFrom` (handoff-only copies made for an earlier share). No entry for this project: show the newest entries and ask which one.

Every save holds the handoff. When the user asks to save the session ("save this session", "pin", "encrypt"), ask once, before step 3, whether to also include:

- artifacts: list the local files you will reference under `## Artifacts`, by path, so they can pick any to bundle;
- the transcript: the full session, which needs the warning and a yes in step 3.

Don't ask when the user asked for the handoff only ("save the handoff"), or already said what to include ("include the report", "include the transcript", "without the transcript"). When saving and sharing in one request, ask this together with the share question below, in one message.

Before any share, ask what it contains, unless the user already said: the handoff and artifacts only, or the transcript too. When saving and sharing in one request, ask before step 3. 🔴 CHECKPOINT — sharing the transcript needs its own confirmation, even when the user confirmed it for the save: the recipient can read all of it.

If the user wants the transcript in the save but not in the share, that takes two uploads: the save, then a handoff-only upload for the share (step 6). Say so and get a yes, or save without the transcript.

## 1. Check the CLI and credentials

Run the version check:

```bash
command -v filecoin-pin || npm install -g filecoin-pin@latest   # needs Node 24+; always latest, so CLI improvements deploy
filecoin-pin get --help | grep -q -- '--share' && echo sharing-ok
```

No `sharing-ok`: follow "Install and version check" in `filecoin-pin-cli.md`. Then run the network check from the same file. If the user chose the owner wallet (`PRIVATE_KEY`), skip the credentials check: it only looks at the saved login. Otherwise run it, and log in with `encrypt` in `--scopes` if it fails (the login steps are under Credentials there).

## 2. Write the handoff

Write it in this turn from what you already know about the session. No extra model call.

Your memory of the session can be out of date, especially after a compaction. Before writing, check what can have changed since you last looked, with one cheap command each:

- every PR or issue you will mention as open, pending or "will merge": `gh pr view <n> --json state` or `gh issue view <n> --json state`;
- uncommitted work you will mention: `git status --short` in that repo.

Write what the checks show. If you can't check something (no `gh`, no network), write "as of <date>, not rechecked" next to it.

```bash
dir="$(mktemp -d)/session-$(date -u +%Y%m%dT%H%M%SZ)" && mkdir -p "$dir" && echo "$dir"
date -u +%Y-%m-%dT%H:%M:%SZ   # createdAt
```

Shell variables don't carry over between your commands. Wherever `$dir` appears below, write the path this printed, or set `dir=` again at the start of that command.

Write `$dir/handoff.md` in exactly this shape, with your values, never the example's: `createdAt` is the date printed above, and `origin` takes the values from "Origin values" in `SKILL.md`; leave out a field you don't have.

```markdown
---
version: 1
createdAt: 2026-10-29T14:02:11Z
origin: { tool: claude-code, toolVersion: 2.1.3 }
---

## Context

- What: the project or repo, and the task, in one line.
- Goal: the outcome the user wants.
- Where it stands: one line. Details go under Open threads.

## Decisions

- A choice that was made, and why. One bullet each. Status ("PR #12 was reviewed") is not a decision: put it under Open threads, or leave it out.

## Constraints

- Rules the next agent must follow: the user's requirements, limits and preferences. Not project decisions: those go under Decisions.

## Artifacts

- `src/report.ts` (path on the sender's machine): what it is.
- https://example.com/spec: what it is.
- `artifacts/report.pdf`: bundled, what it is.
- `transcript.jsonl`: the full session transcript, included at the user's request (only when it is).

## Open threads

- Unfinished work as of now, the next step, open questions. Only items that are still open; finished work goes under Decisions, or nowhere.
```

Context is at most three bullets, about 60 words: no history of what happened, no command output, and nothing that belongs under the other headings.

Write `None.` under a heading that has nothing. Write a summary, not the transcript. Name files and links; don't paste their contents.

Then reread it once: every open thread is still open, every state you mention matches the checks above, and each bullet sits under the right heading.

If the user stops the flow at any point after this — no save, changed their mind — delete the folder with the guarded cleanup command in step 5 before ending the turn: it can already hold a transcript copy.

## 3. Bundle named artifacts and the transcript

Only files the user named or picked are bundled with the handoff. Copy each one, with the source path quoted:

```bash
mkdir -p "$dir/artifacts" && cp '<named-file>' "$dir/artifacts/"
```

A name that itself contains a quote can't be substituted safely into any quoting: ask the user to rename the file first.

Never copy a `.env` file, a key file, or anything the user didn't name. List each bundled file under `## Artifacts` as `artifacts/<name>`.

**The transcript, only when the user asks for it.** Find the tool's transcript by the session id from "Origin values" in `SKILL.md`:

```bash
ls ~/.claude/projects/*/<sessionId>.jsonl                                   # Claude Code
find ~/.codex/sessions -name "rollout-*-$CODEX_SESSION_ID.jsonl"            # Codex
```

No single file found: ask the user for the path. Copy it into the folder, never touching the original, and check its size:

```bash
cp '<transcript-path>' "$dir/transcript.jsonl" && chmod 600 "$dir/transcript.jsonl" && du -h "$dir/transcript.jsonl"
```

A size cap applies to every upload; the CLI reads it from the installed release, and a large transcript is the one thing likely to reach it. If `add` later refuses with a size error, quote it and save without the transcript.

Never print or read the copy into the conversation. 🔴 CHECKPOINT — warn the user, and wait for an explicit yes:

- the transcript holds everything you saw in this session: command output, file contents, pasted text. It can contain secrets and sensitive information that no scan reliably finds;
- the save is a paid upload of this size, stored until the piece is removed;
- if it is shared, the recipient can read all of it, and a share can't be revoked. That includes any Share link and Access key made earlier in this session: if the scan in step 4 finds `fak1_` values in the transcript, the recipient could open those earlier shares too;
- they should run their own redaction on the copy at `$dir/transcript.jsonl` (give the path) before saying yes.

No yes: delete the copy (`rm -f "$dir/transcript.jsonl"`) and save without it. On yes, list it under `## Artifacts`.

## 4. Check before saving

Format check. All six lines must print, each starting `ok`; the missing one names the failure:

```bash
f="$dir/handoff.md"
head -1 "$f" | grep -qx -- '---' && grep -qx 'version: 1' "$f" && grep -qE '^createdAt: [0-9]{4}-' "$f" && grep -qE '^origin: \{ ?tool: [a-z]' "$f" && echo 'ok frontmatter'
for h in 'Context' 'Decisions' 'Constraints' 'Artifacts' 'Open threads'; do grep -qx "## $h" "$f" && echo "ok $h"; done
```

Fewer than six lines: fix `handoff.md` and run the check again (`ok frontmatter` checks the frontmatter in order: opening `---`, `version`, `createdAt`, `origin`). The file must use LF line endings and no byte-order mark; a CRLF file fails every line.

Secret scan. It is a backstop, not a guarantee: a clean scan doesn't make a file safe to share, it only catches known shapes. It prints the number of matches and the file name, never the matching text, and streams line by line, so a large transcript doesn't exhaust memory. It scans regular files only; anything else (a symlink, a pipe) prints `UNREADABLE`. CIDs are never flagged. A transaction hash has the same shape as a private key (64 hex characters), so it is skipped only where the text marks it as one — a `/tx/` link, or a label such as `tx`, `transaction`, or one ending in `hash` or `root` (`blockHash`, `stateRoot`) — and the value carries its `0x` prefix. A bare 64-character hex value is still flagged. Access keys and Grants count only with a real key after the prefix, so placeholders like `fak1_…` in this skill's own text don't. Assignments whose variable name contains `KEY`, `SECRET`, `TOKEN` or `PASSWORD` (`API_KEY=`, `MY_TOKEN=`, …) with a value of six or more characters are flagged anywhere in a line, also inside JSON lines of a transcript.

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

- A match in `handoff.md`: find the line you wrote and remove the secret, or mark a transaction hash as one (label plus `0x`). Run the scan again.
- 🔴 CHECKPOINT — a match in a bundled file: stop. Tell the user which file matched and ask whether to drop it.
- Matches in `transcript.jsonl`: tell the user how many, and ask whether to redact it themselves, drop it, or keep it. They decide; don't open the file to look.
- `UNREADABLE`: the file couldn't be scanned. Treat it as unscanned, not as clean — say so, and let the user decide whether it ships.

## 5. Save

```bash
filecoin-pin add "$dir" --encrypt --egress-provider none --no-update-check
```

To share in the same run, add `--get-share-link-restricted`: one command, and no second read of the header from the provider. With the owner wallet, run it with `--dry-run` first and show the user the cost. 🔴 CHECKPOINT — run the real upload only after they say yes.

It takes one to a few minutes. Let it finish: a slow upload is not a failed one. Never stop it to start again. With the share flag, run it in the foreground with a long timeout (10 minutes): its output holds the Access key, and a background run saves the whole output to a file. Without it, you can run it in the background and poll. The root CID in the summary is the Encrypted root CID. Funding errors: see `filecoin-pin-cli.md`.

If `add` fails or exits `2`, never run it again to recover: follow Troubleshooting in `filecoin-pin-cli.md`. A second run makes a new CID and pays for a second upload. Record the ledger entry once the upload is stored, also when the commit is not confirmed yet: the CID stays the same. Tell the user if it is not confirmed.

Then add one entry to the ledger at `~/.filecoin-share/sessions.json`. The entry holds only these fields, plus `"transcript": true` only when the upload includes the transcript. Never a summary, a title or a key:

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

`origin` follows "Origin values" in `SKILL.md`: `tool` always, other fields only when the tool exposes them. `transcriptPath` is a local path back to the session, filled only when the tool gives it to you. The transcript itself is uploaded only when the user confirmed it in step 3.

Append the entry and keep the file mode `0600`:

```bash
mkdir -p ~/.filecoin-share && ENTRY='<the entry as one line of JSON>' node -e '
const fs = require("fs"), f = process.env.HOME + "/.filecoin-share/sessions.json"
const list = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : []
if (!Array.isArray(list)) throw new Error("ledger is not a JSON array")
list.push(JSON.parse(process.env.ENTRY))
fs.writeFileSync(f, JSON.stringify(list, null, 2) + "\n", { mode: 0o600 })
fs.chmodSync(f, 0o600)'
```

A field value containing a single quote (an apostrophe in a project path) breaks the `ENTRY='…'` quoting: the command fails loudly with the ledger untouched. Pass the entry another way then, for example `ENTRY="$(cat entry.json)"` from a temp file you delete after.

If the append fails because the ledger isn't valid JSON or isn't an array (a crash or a hand edit), don't lose the entry: move the broken file aside (`mv ~/.filecoin-share/sessions.json ~/.filecoin-share/sessions.json.corrupt`), tell the user it was set aside with its contents recoverable by hand, and run the append again.

If this request also needs a handoff-only upload for the share (the two-uploads case above), make it now from the save folder, before cleaning up: follow step 6's handoff-only procedure.

Then delete the save folder: it holds the transcript in plain text when one was included. Set `d` to the `mktemp -d` parent of the path printed in step 2 — its `dirname`, never the system temp root itself — and run this guard (also the command for any other `mktemp -d` folder, passed as is, and whenever the user abandons the flow early). It deletes only a folder `mktemp -d` made, named `tmp.*` directly in the temp root, and refuses anything else, including the temp root and its parents:

```bash
d='<the temp folder to delete>'
case "$d" in
  *..*|*/tmp.*/*) echo "refusing to delete $d — not a mktemp -d folder itself" ;;
  /tmp/tmp.?*|/var/folders/*/*/T/tmp.?*|/private/var/folders/*/*/T/tmp.?*|"${TMPDIR%/}"/tmp.?*) rm -rf "$d" && echo cleaned ;;
  *) echo "refusing to delete $d — not a mktemp -d folder" ;;
esac
```

Reply as in step 7. Then ask once: "Do you want a Share link for this session now? It makes a link and a separate Access key, and uploads nothing." On yes, run step 6. Don't ask when the user already asked to share.

## 6. Share

The ledger is `~/.filecoin-share/sessions.json`. A link opens the whole upload, so check what the saved upload holds against what the user wants to share:

- They match (no transcript in the save, or the user confirmed sharing it): share the saved upload.

  ```bash
  filecoin-pin get-share-link <encrypted-root-cid> --restricted --no-update-check
  ```

  For an entry whose `network` is `calibration`, add `--network calibration` to every command in this step.

- The save includes the transcript (`"transcript": true` in the ledger) and the user wants the handoff and artifacts only: a share can't hold part of an upload, so it needs a handoff-only upload. 🔴 CHECKPOINT — it is one more paid upload: say so, and wait for a yes. Then:
  1. Restore the save into a captured temp folder, and copy it without the transcript into a second one. `get` prints the saved path inside `$o`:

     ```bash
     o="$(mktemp -d)" && echo "$o" && filecoin-pin get <encrypted-root-cid> "$o" --no-update-check
     t="$(mktemp -d)" && cp -R '<saved-path>/.' "$t/" && rm -f "$t/transcript.jsonl" && echo "$t"
     ```

  2. Remove the `transcript.jsonl` line from `## Artifacts` in `$t/handoff.md`. If it was the only line there, write `None.` under the heading.
  3. Run the format check and the secret scan (step 4) on it, with `dir=<the $t path>` set at the start of each command.
  4. Upload it with the share flag, as in step 5 (with the owner wallet: dry run, cost, yes), then:

     ```bash
     filecoin-pin add "<the $t path>" --encrypt --get-share-link-restricted --egress-provider none --no-update-check
     ```

     If this upload fails before it is stored, the save and its ledger entry still stand: the session is saved, just not shared. Nothing was uploaded, so running it again when the user asks is not the forbidden re-run — but it is still a new attempt the user pays for only once it succeeds.
  5. Record it in the ledger with the save's `origin` and `network`, no `"transcript"`, and `"derivedFrom": "<the save's CID>"`. Then delete both temp folders — the `$o` restore folder and the `$t` copy, each itself a `mktemp -d` path, passed to the guard as is, never their `dirname` — with step 5's guarded cleanup.
- The user wants the transcript, but the save doesn't have it: save again including the transcript (steps 2 to 5), and share that save.

Then reply as in step 7.

## 7. Reply

Start the reply with this block, in this order. Leave out the link and the key when nothing was shared. For an open link (only when the user asked for one, as in "Open links" in `filecoin-pin-cli.md`), leave out the Access key block, label the link "Share link (opens on its own: anyone who has it can read the content)", and repeat that section's warning. Use "Session shared" when this run only shared an earlier save.

```
<Session saved | Session shared> · <confirmed on chain | stored, not yet confirmed on chain> · <mainnet | calibration>

Encrypted root CID:
bafy…

Share link (send by one channel, e.g. email):
https://…#v1/…

Access key (send by a different channel, e.g. a chat message):
fak1_…
```

Then, in short bullets:

- what the upload holds: the handoff (a summary of context, decisions, constraints, artifacts and open threads; no keys), the bundled artifacts, and whether it includes the transcript;
- who can read it: only the user (the owner wallet, or a session key with their Grant), plus, when shared, whoever holds both the link and the Access key. A share can't be revoked, and this conversation's history now holds the Access key: anyone who can read this chat or its transcript can open the share;
- when shared: the receiving agent restores it with this skill (`filecoin-pin get --share`). A fresh upload is usually retrievable within minutes — "not found yet" on the recipient's side means indexing is still catching up; wait and retry. The Access key isn't saved anywhere, so send it now; another `get-share-link` makes a new link and key;
- not yet confirmed: the warning and the `piece-status` command from "Upload stored but not confirmed" in `filecoin-pin-cli.md`;
- fewer copies than requested: which providers hold it, as in "Only the second copy failed" in `filecoin-pin-cli.md`;
- calibration: the recipient passes `--network calibration` too.

**Sharing right after a save in this conversation** (the user said yes to the question in step 5): the save reply already gave the status, the CID and the bullets. Reply with only the Share link and the Access key block, then only the bullets that are new: who can read it now (whoever holds both; a share can't be revoked; this chat's history now holds the key), how the recipient opens it (this skill, `filecoin-pin get --share`), and that the key isn't saved anywhere, so send it now. Don't repeat the status line, the CID, what the upload holds, the redundancy or the network note. Say only whether the share includes the transcript.

After this reply, never repeat the Access key, and never write it to the ledger, a file or a log.
