<p align="center"><img src="./assets/engram-header.png" alt="engram — memories that can't be rewritten" width="820"></p>

# engram

A suite of Filecoin tools for agents.

An engram is the physical trace a memory leaves in a brain. This suite is that, for the things agents make, remembered by Filecoin. 


## Skills

| Skill | What it does |
|---|---|
| [`engram-share`](./skills/engram-share/) | Share what your agent just made: one prompt from a local HTML, Markdown, or MP4 file to a content-addressed, verified, stored browser link. |
| [`engram-library`](./skills/engram-library/) *(beta)* | Browse what you've shared, and check it against Filecoin itself: renders the local catalog into a browsable library, verifies it against the storage providers holding it, and discovers pieces the catalog lost track of. |


## Install

```bash
npx skills add filecoin-project/engram --skill engram-share
npx skills add filecoin-project/engram --skill engram-library
```

Each skill's own README covers its prerequisites and first-time setup.

## License

Dual-licensed under [MIT](./LICENSE-MIT) and [Apache 2.0](./LICENSE-APACHE).
