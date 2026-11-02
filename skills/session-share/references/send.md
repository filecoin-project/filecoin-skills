# Save and share a session

Commands, credentials and errors are in `filecoin-pin-cli.md` next to this file.

Which flow:

- "save", "pin", "encrypt" this session: steps 1 to 5.
- "share this session with …", or "save this session and share it with …": steps 1 to 5, with `--get-share-link-restricted` in step 5, then reply as in step 7. If the ledger already has a save of this session and nothing has changed since, run step 6 with that CID instead.
- "share my last session": step 6 only, with the newest ledger entry whose `project` is the current project. No entry for this project: show the newest entries and ask which one.

## 1. Check the CLI and credentials

Run the version check, the credentials check and the network check from `filecoin-pin-cli.md`. Log in with `encrypt` if the credentials check fails.

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

Write `$dir/handoff.md` in exactly this shape. `origin` takes the values from "Origin values" in `SKILL.md`; leave out a field you don't have.

```markdown
---
version: 1
createdAt: 2026-10-29T14:02:11Z
origin: { tool: claude-code, toolVersion: 2.1.3 }
---

## Decisions

- A choice that was made, and why. One bullet each. Status ("PR #12 was reviewed") is not a decision: put it under Open threads, or leave it out.

## Constraints

- Rules the next agent must follow: the user's requirements, limits and preferences. Not project decisions: those go under Decisions.

## Artifacts

- `src/report.ts` (path on the sender's machine): what it is.
- https://example.com/spec: what it is.
- `artifacts/report.pdf`: bundled, what it is.

## Open threads

- Unfinished work as of now, the next step, open questions. Only items that are still open; finished work goes under Decisions, or nowhere.
```

Write `None.` under a heading that has nothing. Write a summary, not the transcript. Name files and links; don't paste their contents.

Then reread it once: every open thread is still open, every state you mention matches the checks above, and each bullet sits under the right heading.

## 3. Bundle named artifacts

Only files the user named ("include the report") are bundled with the handoff. Copy each one:

```bash
mkdir -p "$dir/artifacts" && cp <named-file> "$dir/artifacts/"
```

Never copy a `.env` file, a key file, or anything the user didn't name. List each bundled file under `## Artifacts` as `artifacts/<name>`.

## 4. Check before saving

Format check. All five lines must print `ok`:

```bash
f="$dir/handoff.md"
head -1 "$f" | grep -qx -- '---' && grep -qx 'version: 1' "$f" && grep -qE '^createdAt: [0-9]{4}-' "$f" && grep -qE '^origin: \{ ?tool: [a-z]' "$f" && echo ok
for h in 'Decisions' 'Constraints' 'Artifacts' 'Open threads'; do grep -qx "## $h" "$f" && echo ok; done
```

Secret scan. It prints file names only, never the matching text:

```bash
grep -rlE 'fak1_|fgr1_|-----BEGIN [A-Z ]*PRIVATE KEY|(^|[^0-9a-fA-F])(0x)?[0-9a-fA-F]{64}([^0-9a-fA-F]|$)|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9_-]{20,}|xox[abprs]-|^[A-Z0-9_]*(KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*=' "$dir"
```

- A match in `handoff.md`: find the line you wrote and remove the secret. A 64-character hex string can be a transaction hash, which is fine to keep. Run the scan again.
- A match in a bundled file: stop. Tell the user which file matched and ask whether to drop it.

## 5. Save

```bash
filecoin-pin add "$dir" --encrypt --egress-provider none --no-update-check
```

To share in the same run, add `--get-share-link-restricted`: one command, and no second read of the header from the provider. With the owner wallet, run it with `--dry-run` first and show the user the cost.

Run it in the background and poll; it takes one to a few minutes. Let it finish: a slow upload is not a failed one. Never stop it to start again. The root CID in the summary is the Encrypted root CID. Funding errors: see `filecoin-pin-cli.md`.

If `add` fails or exits `2`, never run it again to recover: follow Troubleshooting in `filecoin-pin-cli.md`. A second run makes a new CID and pays for a second upload. Record the ledger entry once the upload is stored, also when the commit is not confirmed yet: the CID stays the same. Tell the user if it is not confirmed.

Then add one entry to the ledger at `~/.filecoin-share/sessions.json`. The entry holds only these fields. Never a summary, a title or a key:

```json
{
  "cid": "<Encrypted root CID>",
  "pinnedAt": "<UTC time, date -u +%Y-%m-%dT%H:%M:%SZ>",
  "trigger": "manual",
  "project": "<git rev-parse --show-toplevel, or pwd>",
  "origin": { "tool": "claude-code", "toolVersion": "2.1.3", "sessionId": "…" }
}
```

`origin` follows "Origin values" in `SKILL.md`: `tool` always, other fields only when the tool exposes them. `transcriptPath` is a local path back to the session, filled only when the tool gives it to you; the transcript itself is never uploaded.

Append the entry and keep the file mode `0600`:

```bash
mkdir -p ~/.filecoin-share && ENTRY='<the entry as one line of JSON>' node -e '
const fs = require("fs"), f = process.env.HOME + "/.filecoin-share/sessions.json"
const list = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : []
list.push(JSON.parse(process.env.ENTRY))
fs.writeFileSync(f, JSON.stringify(list, null, 2) + "\n", { mode: 0o600 })
fs.chmodSync(f, 0o600)'
```

Reply as in step 7. Then ask once: "Do you want a Share link for this session now? It makes a link and a separate Access key, and uploads nothing." On yes, run step 6. Don't ask when the user already asked to share.

## 6. Share

```bash
filecoin-pin get-share-link <encrypted-root-cid> --restricted
```

Then reply as in step 7.

## 7. Reply

Start the reply with this block, in this order. Leave out the link and the key when nothing was shared.

```
Session saved · <confirmed on chain | stored, not yet confirmed on chain> · <mainnet | calibration>

Encrypted root CID:
bafy…

Share link (send by one channel, e.g. email):
https://…#v1/…

Access key (send by a different channel, e.g. a chat message):
fak1_…
```

Then, in short bullets:

- what the handoff holds: a summary of decisions, constraints, artifacts and open threads; no transcript, no keys;
- who can read it: only the user (the owner wallet, or a session key with their Grant), plus, when shared, whoever holds both the link and the Access key. A share can't be revoked;
- when shared: the receiving agent restores it with this skill (`filecoin-pin get --share`). The Access key isn't saved anywhere, so send it now; another `get-share-link` makes a new link and key;
- not yet confirmed: the warning and the `piece-status` command from "Upload stored but not confirmed" in `filecoin-pin-cli.md`;
- calibration: the recipient passes `--network calibration` too.

**Sharing right after a save in this conversation** (the user said yes to the question in step 5): the save reply already gave the status, the CID and the bullets. Reply with only the Share link and the Access key block, then only the bullets that are new: who can read it now (whoever holds both; a share can't be revoked), how the recipient opens it (this skill, `filecoin-pin get --share`), and that the key isn't saved anywhere, so send it now. Don't repeat the status line, the CID, what the handoff holds, the redundancy or the network note.

After this reply, never repeat the Access key, and never write it to the ledger, a file or a log.
