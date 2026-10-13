# Filecoin PDP Agent

Let your AI agent help you earn on Filecoin using your spare hardware and storage capacity. Install [filecoin-pdp-agent](SKILL.md) to have it deploy and operate a Curio PDP provider that can earn storage payments on your behalf. Start with a fresh machine or an existing provider on Linux, macOS or another compatible host.

**This skill is designed for full agent control, including access to the private keys and credentials Curio uses.** The agent can read and use the provider's signing key, sign transactions, and spend funds controlled by that key. Use a provider environment and funded wallet you intend to place under agent control. Secret-handling instructions keep keys out of chat, logs and issue reports; the agent still has access to them. See the [full control model and setup guide](https://github.com/filecoin-project/curio/blob/main/documentation/en/filecoin-pdp-agent.md).

## Install

Choose one method. The distribution repository is [filecoin-project/filecoin-skills](https://github.com/filecoin-project/filecoin-skills). GitHub installation requires the skill directory to be published on its default branch.

### Skills CLI

With Node.js/npm available, run:

```sh
npx skills add filecoin-project/filecoin-skills --skill filecoin-pdp-agent --global
```

Select the agent you use when prompted. `--global` makes the skill available across working directories, so you can start without a Curio checkout. The [Skills CLI](https://github.com/vercel-labs/skills#install-a-skill) supports Claude Code, Codex, Cursor, OpenClaw and other agents. To select an agent directly, append its documented identifier, such as `--agent codex` or `--agent claude-code`.

### Codex's built-in installer

Ask Codex:

```text
Use $skill-installer to install https://github.com/filecoin-project/filecoin-skills/tree/main/skills/filecoin-pdp-agent
```

Codex's [skill installer](https://learn.chatgpt.com/docs/build-skills#install-curated-skills-for-local-use) accepts skills from other repositories. If the installed skill does not appear, restart Codex.

## Start the provider

Run your agent with access to the target machine, locally or through an available remote connection. After installation, ask:

```text
Use filecoin-pdp-agent to set up and run a Filecoin PDP provider on this machine. I authorize full agent control of this provider, including access to the private keys Curio uses and the funds I allocate. Handle installation and ongoing operation. Ask me for any missing storage, funding or access decisions.
```

The agent inspects the host, resolves missing resource decisions, installs supported prerequisites, clones Curio when the selected deployment guide requires it, and deploys the required services. It then configures storage, the dedicated provider wallet and public endpoint, completes registration, verifies readiness, and schedules periodic health and earnings checks. An existing provider is adopted in place. Curio runs continuously on its own; the agent checks in periodically and follows up more closely when an issue needs attention.

Provide the host access, storage allocation and operating funds the agent requests. The agent handles routine deployment, recovery and maintenance within your delegation, asking for human action when necessary access or a decision is missing. Ongoing checks require a working scheduler; the agent verifies and reports whether one is active. Installation alone adds the skill; the request above starts provider setup and operation.
