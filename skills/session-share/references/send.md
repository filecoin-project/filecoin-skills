# Save and share a session

Commands, credentials and errors are in `filecoin-pin-cli.md` next to this file.

Which flow:

- "save", "pin", "encrypt" this session: steps 1 to 5.
- "share this session with …": steps 1 to 6. If the ledger already has a save of this session and nothing has changed since, skip to step 6 with that CID.
- "share my last session": step 6 only, with the newest ledger entry whose `project` is the current project. No entry for this project: show the newest entries and ask which one.

## 1. Check the CLI and credentials

Run the version check, the credentials check and the network check from `filecoin-pin-cli.md`. Log in with `encrypt` if the credentials check fails.

## 2. Write the snapshot

Write it in this turn from what you already know about the session. No extra model call.

```bash
dir="$(mktemp -d)/session-$(date -u +%Y%m%dT%H%M%SZ)" && mkdir -p "$dir" && echo "$dir"
date -u +%Y-%m-%dT%H:%M:%SZ   # createdAt
```

Write `$dir/snapshot.md` in exactly this shape. `origin` takes the values from "Origin values" in `SKILL.md`; leave out a field you don't have.

```markdown
---
version: 1
createdAt: 2026-10-29T14:02:11Z
origin: { tool: claude-code, toolVersion: 2.1.3 }
---

## Decisions

- What was decided, and why. One bullet each.

## Constraints

- Requirements, limits and preferences the next agent must respect.

## Artifacts

- `src/report.ts` (path on the sender's machine): what it is.
- https://example.com/spec: what it is.
- `artifacts/report.pdf`: bundled, what it is.

## Open threads

- Unfinished work, the next step, open questions.
```

Write `None.` under a heading that has nothing. Write a summary, not the transcript. Name files and links; don't paste their contents.

## 3. Bundle named artifacts

Only files the user named ("include the report") go in the snapshot. Copy each one:

```bash
mkdir -p "$dir/artifacts" && cp <named-file> "$dir/artifacts/"
```

Never copy a `.env` file, a key file, or anything the user didn't name. List each bundled file under `## Artifacts` as `artifacts/<name>`.

## 4. Check before saving

Format check. All five lines must print `ok`:

```bash
f="$dir/snapshot.md"
head -1 "$f" | grep -qx -- '---' && grep -qx 'version: 1' "$f" && grep -qE '^createdAt: [0-9]{4}-' "$f" && grep -qE '^origin: \{ ?tool: [a-z]' "$f" && echo ok
for h in 'Decisions' 'Constraints' 'Artifacts' 'Open threads'; do grep -qx "## $h" "$f" && echo ok; done
```

Secret scan. It prints file names only, never the matching text:

```bash
grep -rlE 'fak1_|fgr1_|-----BEGIN [A-Z ]*PRIVATE KEY|(^|[^0-9a-fA-F])(0x)?[0-9a-fA-F]{64}([^0-9a-fA-F]|$)|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9_-]{20,}|xox[abprs]-|^[A-Z0-9_]*(KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*=' "$dir"
```

- A match in `snapshot.md`: find the line you wrote and remove the secret. A 64-character hex string can be a transaction hash, which is fine to keep. Run the scan again.
- A match in a bundled file: stop. Tell the user which file matched and ask whether to drop it.

## 5. Save

```bash
filecoin-pin add "$dir" --encrypt --egress-provider none --no-update-check
```

Run it in the background and poll; it takes one to a few minutes. The `Root CID:` line under `Add Details` is the Encrypted root CID. Funding errors: see `filecoin-pin-cli.md`.

If `add` fails or exits `2`, never run it again to recover: follow Troubleshooting in `filecoin-pin-cli.md`. A second run makes a new CID and pays for a second upload. Record the ledger entry only once the save is confirmed.

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

Tell the user the session is saved, with the Encrypted root CID on its own line. Only they (the owner wallet, or a session key with their Grant) can restore it until they share it.

## 6. Share

```bash
filecoin-pin get-share-link <encrypted-root-cid> --restricted
```

Show the two items once, labelled, each on its own line:

```
Share link (send by one channel, e.g. email):
https://…#v1/…

Access key (send by a different channel, e.g. a chat message):
fak1_…
```

Then tell the user:

- whoever holds both can read this snapshot, and the share can't be revoked;
- the receiving agent restores it with this skill (`filecoin-pin get --share`);
- the Access key is not saved anywhere, so they should send it now. Another `get-share-link` makes a new link and key.

After this reply, never repeat the Access key, and never write it to the ledger, a file or a log.
