# Save and share a session

Commands, credentials and errors are in `filecoin-pin-cli.md` next to this file.

Which flow:

- "save", "pin", "encrypt" this session: steps 1 to 5.
- "share this session with …", or "save this session and share it with …": steps 1 to 5, with `--get-share-link-restricted` in step 5, then reply as in step 7. If the ledger already has a save of this session and nothing has changed since, run step 6 with that CID instead.
- "share my last session": step 1, then step 6, with the newest ledger entry whose `project` is the current project, skipping entries with `derivedFrom` (handoff-only copies made for an earlier share). No entry for this project: show the newest entries and ask which one.

Every save holds the handoff. When the user asks to save the session ("save this session", "pin", "encrypt"), ask once, before step 3, whether to also include:

- artifacts: list the local files you will reference under `## Artifacts`, by path, so they can pick any to bundle;
- the transcript: the full session, which needs the warning and a yes in step 3.

Don't ask when the user asked for the handoff only ("save the handoff", "hand off this session"), or already said what to include ("include the report", "include the transcript", "without the transcript"). When saving and sharing in one request, ask this together with the share question below, in one message.

Before any share, ask what it contains, unless the user already said: the handoff and artifacts only, or the transcript too. When saving and sharing in one request, ask before step 3. Sharing the transcript needs its own confirmation, even when the user confirmed it for the save: the recipient can read all of it.

If the user wants the transcript in the save but not in the share, that takes two uploads: the save, then a handoff-only upload for the share (step 6). Say so and get a yes, or save without the transcript.

## 1. Check the CLI and credentials

Run the version check and the network check from `filecoin-pin-cli.md`. If the user chose the owner wallet (`PRIVATE_KEY`), skip the credentials check: it only looks at the saved login. Otherwise run it, and log in with `encrypt` if it fails.

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

Write `$dir/handoff.md` in exactly this shape. `origin` takes the values from "Origin values" in `SKILL.md`; leave out a field you don't have.

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

## 3. Bundle named artifacts and the transcript

Only files the user named or picked are bundled with the handoff. Copy each one:

```bash
mkdir -p "$dir/artifacts" && cp <named-file> "$dir/artifacts/"
```

Never copy a `.env` file, a key file, or anything the user didn't name. List each bundled file under `## Artifacts` as `artifacts/<name>`.

**The transcript, only when the user asks for it.** Find the tool's transcript by the session id from "Origin values" in `SKILL.md`:

```bash
ls ~/.claude/projects/*/<sessionId>.jsonl                                   # Claude Code
find ~/.codex/sessions -name "rollout-*-$CODEX_SESSION_ID.jsonl"            # Codex
```

No single file found: ask the user for the path. Copy it into the folder, never touching the original, and check its size:

```bash
cp "<transcript-path>" "$dir/transcript.jsonl" && chmod 600 "$dir/transcript.jsonl" && du -h "$dir/transcript.jsonl"
```

Never print or read the copy into the conversation. Then warn the user, and wait for an explicit yes:

- the transcript holds everything you saw in this session: command output, file contents, pasted text. It can contain secrets and sensitive information that no scan reliably finds;
- it is stored permanently, and the save is a paid upload of this size;
- if it is shared, the recipient can read all of it, and a share can't be revoked. That includes any Share link and Access key made earlier in this session: if the scan in step 4 finds `fak1_` values in the transcript, the recipient could open those earlier shares too;
- they should run their own redaction on the copy at `$dir/transcript.jsonl` (give the path) before saying yes.

No yes: delete the copy (`rm -f "$dir/transcript.jsonl"`) and save without it. On yes, list it under `## Artifacts`.

## 4. Check before saving

Format check. All six lines must print `ok`:

```bash
f="$dir/handoff.md"
head -1 "$f" | grep -qx -- '---' && grep -qx 'version: 1' "$f" && grep -qE '^createdAt: [0-9]{4}-' "$f" && grep -qE '^origin: \{ ?tool: [a-z]' "$f" && echo ok
for h in 'Context' 'Decisions' 'Constraints' 'Artifacts' 'Open threads'; do grep -qx "## $h" "$f" && echo ok; done
```

Secret scan. It prints the number of matches and the file name, never the matching text. CIDs are never flagged. A transaction hash has the same shape as a private key (64 hex characters), so it is skipped only where the text marks it as one: a `/tx/` link, or a label such as `tx`, `transaction`, or one ending in `hash` or `root` (`blockHash`, `stateRoot`). A bare 64-character hex value is still flagged. Access keys and Grants count only with a real key after the prefix, so placeholders like `fak1_…` in this skill's own text don't. `KEY=`, `SECRET=`, `TOKEN=` and `PASSWORD=` assignments with a value of six or more characters are flagged anywhere in a line, also inside JSON lines of a transcript.

```bash
node -e '
const fs = require("fs"), path = require("path"), dir = process.argv[1]
const hash = /(\/tx\/|\b(?:tx|transaction|\w*hash|\w*root)\b["\x27\s:=\\]*)0x[0-9a-f]{64}(?![0-9a-f])/gi
const secret = /fak1_[A-Za-z0-9_-]{16,}|fgr1_[A-Za-z0-9_-]{16,}|-----BEGIN [A-Z ]*PRIVATE KEY|(?<![0-9a-fA-F])(?:0x)?[0-9a-fA-F]{64}(?![0-9a-fA-F])|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9_-]{20,}|xox[abprs]-|(?<![A-Z0-9_])[A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*=["\x27]?[A-Za-z0-9_\-\/+.]{6,}/g
const files = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? files(path.join(d, e.name)) : [path.join(d, e.name)])
for (const f of files(dir)) {
  const n = (fs.readFileSync(f, "utf8").replace(hash, "$1<hash>").match(secret) ?? []).length
  if (n > 0) console.log(`${n}\t${path.relative(dir, f)}`)
}' "$dir"
```

- A match in `handoff.md`: find the line you wrote and remove the secret, or mark a transaction hash as one. Run the scan again.
- A match in a bundled file: stop. Tell the user which file matched and ask whether to drop it.
- Matches in `transcript.jsonl`: tell the user how many, and ask whether to redact it themselves, drop it, or keep it. They decide; don't open the file to look.

## 5. Save

```bash
filecoin-pin add "$dir" --encrypt --egress-provider none --no-update-check
```

To share in the same run, add `--get-share-link-restricted`: one command, and no second read of the header from the provider. With the owner wallet, run it with `--dry-run` first, show the user the cost, and run the real upload only after they say yes.

It takes one to a few minutes. Let it finish: a slow upload is not a failed one. Never stop it to start again. With the share flag, run it in the foreground with a long timeout (10 minutes): its output holds the Access key, and a background run saves the whole output to a file. Without it, you can run it in the background and poll. The root CID in the summary is the Encrypted root CID. Funding errors: see `filecoin-pin-cli.md`.

If `add` fails or exits `2`, never run it again to recover: follow Troubleshooting in `filecoin-pin-cli.md`. A second run makes a new CID and pays for a second upload. Record the ledger entry once the upload is stored, also when the commit is not confirmed yet: the CID stays the same. Tell the user if it is not confirmed.

Then add one entry to the ledger at `~/.filecoin-share/sessions.json`. The entry holds only these fields. Never a summary, a title or a key:

```json
{
  "cid": "<Encrypted root CID>",
  "pinnedAt": "<UTC time, date -u +%Y-%m-%dT%H:%M:%SZ>",
  "trigger": "manual",
  "project": "<git rev-parse --show-toplevel, or pwd>",
  "network": "mainnet",
  "origin": { "tool": "claude-code", "toolVersion": "2.1.3", "sessionId": "…", "transcriptPath": "…" },
  "transcript": true
}
```

`network` is `mainnet` or `calibration`, the network the upload went to. Add `"transcript": true` only when the upload includes the transcript.

`origin` follows "Origin values" in `SKILL.md`: `tool` always, other fields only when the tool exposes them. `transcriptPath` is a local path back to the session, filled only when the tool gives it to you. The transcript itself is uploaded only when the user confirmed it in step 3.

Append the entry and keep the file mode `0600`:

```bash
mkdir -p ~/.filecoin-share && ENTRY='<the entry as one line of JSON>' node -e '
const fs = require("fs"), f = process.env.HOME + "/.filecoin-share/sessions.json"
const list = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : []
list.push(JSON.parse(process.env.ENTRY))
fs.writeFileSync(f, JSON.stringify(list, null, 2) + "\n", { mode: 0o600 })
fs.chmodSync(f, 0o600)'
```

If this request also needs a handoff-only upload for the share (the two-uploads case above), make it now from the save folder, before cleaning up: copy the folder without `transcript.jsonl` to a new temp folder and follow step 6 from its sub-step 2.

Then delete the save folder: it holds the transcript in plain text when one was included. Use the `mktemp -d` parent of the path printed in step 2:

```bash
rm -rf "<the mktemp -d folder from step 2>"
```

Reply as in step 7. Then ask once: "Do you want a Share link for this session now? It makes a link and a separate Access key, and uploads nothing." On yes, run step 6. Don't ask when the user already asked to share.

## 6. Share

A link opens the whole upload, so check what the saved upload holds against what the user wants to share:

- They match (no transcript in the save, or the user confirmed sharing it): share the saved upload.

  ```bash
  filecoin-pin get-share-link <encrypted-root-cid> --restricted
  ```

  For an entry whose `network` is `calibration`, add `--network calibration` to every command in this step.

- The save includes the transcript (`"transcript": true` in the ledger) and the user wants the handoff and artifacts only: a share can't hold part of an upload, so it needs a handoff-only upload. It is one more paid upload: say so, and wait for a yes. Then:
  1. Restore the save into a temp folder. `get` prints the saved path:

     ```bash
     filecoin-pin get <encrypted-root-cid> "$(mktemp -d)"
     ```

  2. Delete `<saved-path>/transcript.jsonl`, and remove its line from `## Artifacts` in `<saved-path>/handoff.md`. If it was the only line there, write `None.` under the heading.
  3. Run the format check and the secret scan (step 4) on it, with `dir=<saved-path>` set at the start of each command.
  4. Upload it with the share flag, as in step 5:

     ```bash
     filecoin-pin add "<saved-path>" --encrypt --get-share-link-restricted --egress-provider none --no-update-check
     ```

  5. Record it in the ledger with the save's `origin` and `network`, no `"transcript"`, and `"derivedFrom": "<the save's CID>"`. Then delete the temp folder.
- The user wants the transcript, but the save doesn't have it: save again with it (step 1), and share that.

Then reply as in step 7.

## 7. Reply

Start the reply with this block, in this order. Leave out the link and the key when nothing was shared. Use "Session shared" when this run only shared an earlier save.

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
- who can read it: only the user (the owner wallet, or a session key with their Grant), plus, when shared, whoever holds both the link and the Access key. A share can't be revoked;
- when shared: the receiving agent restores it with this skill (`filecoin-pin get --share`). The Access key isn't saved anywhere, so send it now; another `get-share-link` makes a new link and key;
- not yet confirmed: the warning and the `piece-status` command from "Upload stored but not confirmed" in `filecoin-pin-cli.md`;
- fewer copies than requested: which providers hold it, as in "Only the second copy failed" in `filecoin-pin-cli.md`;
- calibration: the recipient passes `--network calibration` too.

**Sharing right after a save in this conversation** (the user said yes to the question in step 5): the save reply already gave the status, the CID and the bullets. Reply with only the Share link and the Access key block, then only the bullets that are new: who can read it now (whoever holds both; a share can't be revoked), how the recipient opens it (this skill, `filecoin-pin get --share`), and that the key isn't saved anywhere, so send it now. Don't repeat the status line, the CID, what the upload holds, the redundancy or the network note. Say only whether the share includes the transcript.

After this reply, never repeat the Access key, and never write it to the ledger, a file or a log.
