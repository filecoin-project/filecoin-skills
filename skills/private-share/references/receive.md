# Open a share you received

A share is two items: a Share link (`https://…#v1/<cid>&d=…`) and an Access key (`fak1_…`). Neither opens anything alone. Opening a share needs no wallet, login or Grant.

Commands and errors are in `filecoin-pin-cli.md` next to this file.

## 1. Check the CLI

Run the version check from `filecoin-pin-cli.md`. No `sharing-ok`: stop and tell the user.

## 2. Choose the output folder

Use the folder the user named. If they named none, ask. The CLI creates the folder if needed and never overwrites a file in it.

## 3. Open the share

Follow "The Access key" under `get --share` in `filecoin-pin-cli.md` to get the key to the CLI without it entering the chat, then open the share into the output folder:

```bash
filecoin-pin get --share '<link>' <output-dir>
```

Add `--network calibration` when the sender said the share is on calibration. Always single-quote the link: it contains `#` and `&`.

## 4. Report

Give the user the saved path on its own line.

What the check proves: `get --share` checked every block against the CID in the link, and the encryption envelope rejects any change to the content. So the saved content is exactly what the link names, unaltered. It does not prove who made it.

Errors are listed under `get --share` in `filecoin-pin-cli.md`.
