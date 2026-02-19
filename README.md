# ai-indie-gamedev

Prompt templates for solo game developers who use AI as a design partner. These schemas are specifically worded to resist common LLM failure modes — vague optimism, emotional abstraction, scope fantasy, and self-reinforcing praise loops.

Built for use with Claude, GPT, or any capable LLM.

## Schemas

| Schema | Purpose |
|--------|---------|
| [GID.md](schemas/GID.md) | **Game Idea Document** — structured generation template that forces concrete mechanics, painful scope cuts, and real numbers instead of vibes. |
| [GID_ADVERSARIAL.md](schemas/GID_ADVERSARIAL.md) | **Adversarial Review** — run in a separate session after the GID. Catches contradictions, hidden risks, market blindspots, and comfortable lies. |
| [PROJECT_SNAPSHOT.md](schemas/PROJECT_SNAPSHOT.md) | **Project Snapshot** — canonical state document for maintaining continuity across AI chat sessions. Paste it at the start of a new thread to pick up where you left off. |

## Usage

1. **Generate:** Start a new AI session. Paste `GID.md` along with your game idea. Let the AI fill it in.
2. **Attack:** Start a *different* AI session. Paste the completed GID along with `GID_ADVERSARIAL.md`. Never let the same session grade its own work.
3. **Build:** Once you get a GREEN verdict (or fix a YELLOW), use `PROJECT_SNAPSHOT.md` to maintain state across development sessions.

## Design Principles

- **Force specifics.** "Name exactly" beats "describe." "SINGLE most expensive" beats "list some."
- **Cross-constrain.** Every section is checked against at least one other section. Pillars vs. loop. Session vs. monetization. Pitch vs. pillars.
- **Ban vibes.** Pillars must be system rules, not feelings. Procedural generation must list variables, not wave hands. Risks must pair with mitigations inline.
- **Separate generation from critique.** The adversarial pass runs in a fresh session so the AI can't protect its own output.

## Hard Constraints Assumed

These templates are tuned for a specific solo dev profile. Fork and adjust if yours differs:

- ~365 hours/year dev budget
- Windows (Steam) + iOS targets
- No photorealistic art
- 3D preferred
- Multiplayer only if local (zero post-release maintenance)
- Unity + Blender pipeline

## Contributing

Open an issue or PR if you find a phrasing that makes an LLM produce better output. The bar: does the new wording resist a specific, nameable failure mode?

## License

MIT
