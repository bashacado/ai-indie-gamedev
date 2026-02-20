# Game Idea Document — Schema v3

> **When responding, remove these blockquoted instructions and return only the filled-in sections. If a section doesn't apply to your game, write "N/A" and briefly say why. Don't leave sections blank — a deliberate "N/A" is more useful than an empty heading.**

> **Hard constraints — these color every answer below:**
> - Solo dev budget: ~365 hours/year
> - Deploy on Windows (Steam) and/or iOS (iPhone/tablet). No consoles.
> - No photorealistic art. No side-scrollers. 3D preferred.
> - Multiplayer only if local (zero maintenance cost post-release).
> - Be blunt. I'd rather hear "this idea doesn't work because X" than a polished document for a doomed project.

> **Anti-padding rule:** If the seed document already contains a clear decision for a section, do not restate it at greater length. Write "Decided in seed: [one-line summary]" and move on. Your job is to stress-test, surface unknowns, and make decisions that haven't been made yet — not to elaborate on decisions that have. If you find yourself writing a paragraph that the seed author could have predicted word-for-word, stop and delete it.

---

## Decision Density Check (COMPLETE THIS BEFORE ANYTHING ELSE)

> Count the major design decisions that are still genuinely open — meaning the seed has NOT already committed to a specific answer. A decision is "open" if the seed either doesn't mention it, explicitly defers it, or presents multiple options without choosing.
>
> Major design decisions include: genre, core mechanic, core loop structure, level/world structure, monetization model, target audience, platform priority, input scheme, art style, progression system, session structure.
>
> **If 3 or fewer decisions are open:** This concept is stable. Skip to ABBREVIATED MODE below — fill in only the sections marked with ★. The remaining sections would produce elaboration, not insight. Use them only if the creator explicitly requests the full document.
>
> **If 4 or more decisions are open:** This concept is fluid. Fill in the FULL DOCUMENT — the schema can shape the trajectory.

**Open decisions identified:** [List them]
**Count:** [N]
**Mode:** [ABBREVIATED / FULL]

---

### ★ ABBREVIATED MODE (stable concepts only)

> Complete only these sections. Everything else is elaboration on settled decisions.

1. Pre-Mortem
2. Mechanical Depth Check (under Core Loop)
3. Falsifiable Assumptions
4. Non-Negotiables
5. Kill Criteria
6. Open Decisions
7. Honest Assessment

> After completing these, stop. Do not fill in the remaining sections unless the creator asks for the full document. A short, honest document that surfaces real unknowns is more valuable than a long, polished document that restates known decisions.

---

## Pre-Mortem (COMPLETE THIS FIRST — both modes)

> Before filling in ANY other section, write the pre-mortem. This forces you to confront the concept's weaknesses before you've invested effort defending it.
>
> Imagine it is one year from now. You spent 300+ hours on this game. It failed. Write 3 plausible reasons why, in order of likelihood. Be specific — not "it wasn't fun enough" but "the core loop had one verb (collect) with no variation, and playtesters stopped engaging after 8 minutes."
>
> Then: for each failure reason, state whether the current seed/design addresses it, partially addresses it, or ignores it entirely.
>
> If all three failure reasons are things the design ignores, this is a serious warning sign. Consider whether to proceed.

1. **[Most likely failure reason]** — [Specific and concrete]. *Addressed by current design?* [Yes / Partially / No — explain.]
2. **[Second failure reason]** — [Specific]. *Addressed?* [Yes / Partially / No.]
3. **[Third failure reason]** — [Specific]. *Addressed?* [Yes / Partially / No.]

---

## Genre(s)
> 1–2 genres. Be specific — "puzzle" is not a genre, "puzzle-exploration" is.

## Reference Games & Inspirations
> 3–5 games I'm drawing from. For each: the game name, and the ONE specific thing I'm stealing from it. No vague "it has good vibes."
- **[Title]** — [what specifically you're borrowing and why]

## Pillars
> 3–5 fundamental backbones. Short and ruthless.
> Each pillar must describe a player-facing behavior or system rule, not a feeling.
> I should be able to point at any feature and say which pillar it serves — or cut the feature.
> Bad: "Engaging combat." Good: "Every enemy has a telegraphed pattern the player can learn to parry."
> For any pillar that involves a cost, constraint, or restriction on the player: state the specific mechanism. What is gained? What is lost? How is it enforced?
1. **[Pillar]** — [Mechanism: how this works in practice, not just what it aspires to]
2. **[Pillar]** — [Mechanism]
3. **[Pillar]** — [Mechanism]

## Scope Limitations
> List 2–3 features your target audience would EXPECT this game to have, that you're choosing to cut anyway. For each, name what you gain from the cut (time, focus, simplicity). Cutting things nobody expected doesn't count.
> Frame each as a design choice, not a budget compromise. What does cutting this force you to do instead?
- **No [feature]** — [What players expect and why you're not doing it. What does cutting this force you to do instead?]

## Core Loop
> Primary loop in arrow format (e.g. Explore → Gather → Craft → Upgrade → Explore).
> The core loop must visibly exercise EVERY pillar. If a pillar is not present in the loop, it is aspirational, not real. Flag this for yourself.
**[Verb] → [Verb] → [Verb] → [Verb] → [Repeat]**

> Answer all three:
> 1. How does this loop generate replayability without large amounts of handcrafted content?
> 2. What is the MINIMUM content needed to ship this loop? (Be concrete — e.g. "8 enemy types, 1 biome, 20 items") No ranges — pick a number and defend it.
> 3. If procedural generation is used, list exactly which variables are being remixed and their value ranges. "Procedural" is not a plan. If hand-authored, how do you prevent content drought?

1. **Replayability mechanism:** [How does the player get value from a second session? If "they don't," say so — that's a valid answer for some designs.]
2. **Minimum content to ship:** [Quantify: number of levels, rooms, encounters, systems.]
3. **Procedural vs. authored:** [Is content procedural, hand-authored, or hybrid? State the strategy and its risks.]

### ★ Mechanical Depth Check
> Count the distinct verbs the player performs in the core loop. A "verb" is a discrete player action with its own input and feedback (e.g., "move," "collect," "aim," "build," "choose").
>
> - **1 verb:** The game is a single-mechanic experience. This can work (e.g., Flappy Bird, Desert Golfing) but it means ALL engagement comes from content variety, audiovisual polish, or escalating challenge. State which of these you're relying on.
> - **2 verbs:** Typical for casual/mobile. The interaction between the two verbs IS the game. State what that interaction is.
> - **3+ verbs:** Typical for mid-core+. Each verb must earn its place. If any verb could be removed without breaking the loop, cut it.
>
> If your verb count is 1 and your session target exceeds 5 minutes, this is a structural risk. Acknowledge it.

**Verb count:** [N]
**Player verbs:** [List them]
**If 1 verb:** [What sustains engagement? Content variety, escalating challenge, audiovisual spectacle, or something else?]

## Session Design
> Fill in all four:
- **Target session length:** [X–Y minutes. What does one "unit" of play look like?]
- **Target total player engagement:** [X–Y hours first playthrough; X–Y for replay if applicable]
- **What makes the player stop AND want to come back?** [Stop trigger and return hook — be specific]
- **Why does this match monetization?** [Connect session design to how you're charging]

## Save System Philosophy
> This is a design decision, not a technical one.
- **Can the player save manually?** [Yes/No. If yes, does this undermine any pillar?]
- **Is there autosave?** [When does it trigger? What state does it capture?]
- **Can the player save-scum?** [If yes, does this break any intended consequence or cost? If no, how is this communicated?]
- **What happens on ragequit?** [Player closes the app mid-session. What state do they return to?]

## Cognitive Load Strategy
> If your game involves tracking state, remembering information, or managing complexity: how do you keep it manageable?
- **What is the player asked to hold in their head at any given time?** [Be honest — count the variables]
- **What aids exist?** [UI elements, environmental cues, journals, logs, visible state, audio cues — or nothing]
- **What is the maximum cognitive load at the hardest point in the game?** [Describe the worst case]
- **Design rule:** [State a concrete limit you will not exceed. e.g., "No puzzle requires tracking more than 3 unseen variables." If you don't have one, say so — but know that the adversarial review will flag it.]

---

## Elevator Pitch
> 2–4 sentences. A stranger reads this and knows: what the game IS, what makes it DIFFERENT, and what the VISUAL HOOK is. If I post a screenshot or gif of this game, why would someone stop scrolling?

## The Big But
> "My game is like ___, but ___." One sentence.

## Target Audience
> Who is this for? Not "gamers." Reference comparable titles they already like. Age range. Psychographic: what do they enjoy about games? What do they dislike?

## Monetization Model
> Premium, F2P, subscription, ad-supported, etc. Price point. Platform-specific pricing if different. IAP/DLC plans or explicit lack thereof. This constrains design heavily, especially across Steam + iOS.

---

## Platform Considerations
> For each platform:
> - Input method and why it works for your design
> - Any constraints the platform imposes
> - Is this platform primary or secondary? Be honest — "both are first-class" is almost always wrong.
> If it doesn't work on both, say so.

## Assets
> What do I need to create or purchase? Be frugal, avoid hand-crafting.

**What's needed:**
> Categorized list: art, audio, UI, code systems, etc.

**Marketing-critical assets:**
> Which assets MUST exist for the game to be marketable? (e.g., a gif-able moment, a trailer-ready sequence, a screenshot that communicates the hook)

**Most expensive category:** [What it is and how you're controlling cost]

**Where AI generation helps:** [Specific use cases, not "AI will help with everything"]

## Tools & Workflow
> Engine, modeling tools, audio tools, version control, CI/CD if applicable.
> Rule: no custom tooling unless you can name the specific problem it solves and the hour cost.
> Unity/Blender compatibility matters if they aren't standalone.

## First Playable Milestone
> What is the minimum slice that proves the core loop is fun?
> Define it concretely — what does the player DO in this build, and what's missing that I'll add later?

**What the player does:** [Describe the exact experience in one paragraph]

**What's missing:** [Everything NOT in the milestone]

**Does it prove fun?** [State what "success" looks like in concrete, observable terms. What does the playtester DO or SAY that tells you it's working? What tells you it's not?]

**Which pillars does this test?** [List them. If a pillar is NOT tested by the first playable, acknowledge this — it's a known gap.]

**Estimate:** [Hours, broken down by discipline]

## Phase Breakdown
> Break the full project into phases. For each phase:
> - What it includes
> - T-shirt size estimate (S/M/L/XL where S≈20h, M≈50h, L≈100h, XL≈200h)
> - Flag which phase is most likely to balloon and why

| Phase | Content | Size | Balloon Risk |
|---|---|---|---|
| 0: Prototype | [scope] | [S/M/L/XL] ([hours]h) | [risk level + why] |
| 1: Core Build | [scope] | [size] ([hours]h) | [risk level + why] |
| 2: [name] | [scope] | [size] ([hours]h) | [risk level + why] |
| 3: [name] | [scope] | [size] ([hours]h) | [risk level + why] |
| 4: Ship | [scope] | [size] ([hours]h) | [risk level + why] |

**Total: ~[X]h.**
**If time compresses:** [What gets cut first, second, third. Be specific.]
**Minimum shippable game:** [Which phases, what total hours, what's lost]

## Risks & Mitigations
> 3–5 risks. For each:
> - The risk (what goes wrong)
> - Why it's plausible for THIS game specifically
> - Mitigation (what you'll do about it)
> - First cut if time runs short (what you sacrifice to solve it)
> No orphaned risks.

1. **[Risk]** — [Why plausible]. *Mitigation:* [action]. *First cut:* [sacrifice].

---

## ★ Falsifiable Assumptions
> 3–5 assumptions this design depends on. These are hypotheses, not facts.
> Each must be testable: a playtest, a data point, or a market signal could disprove it.
> If an assumption is disproved, what changes?

1. **[Assumption]** — [How you would test it. What changes if it's wrong.]
2. **[Assumption]** — [Test. Consequence if wrong.]

## ★ Non-Negotiables
> What cannot be cut, softened, or changed without killing the game's identity?
> If any of these prove unworkable, the project needs fundamental rethinking, not scope adjustment.
> Keep this list short (2–4 items). If everything is non-negotiable, nothing is.

1. **[Element]** — [Why this is identity-defining, not just preferred]

## ★ Kill Criteria
> At what point do you stop? State concrete, measurable thresholds.
> These are commitments to yourself. If you can rationalize past them, they're too vague.

1. **[Milestone/trigger]** → [Decision: pivot, cut, or abandon]
2. **[Milestone/trigger]** → [Decision]

---

## ★ Open Decisions

> List 2–5 design questions that this document does NOT answer — decisions that require prototyping, playtesting, or market research to resolve. For each, state what information you need and when in the phase plan you'll get it.
>
> If you cannot identify any open decisions, the document is either remarkably complete or the AI is not thinking hard enough. Recheck.

1. **[Decision]** — [What you need to know, and when/how you'll learn it]
2. **[Decision]** — [Info needed, timing]

## ★ Honest Assessment

> In 2–4 sentences, state your honest opinion of this game's commercial viability and creative merit. Do not hedge with "it depends on execution" — everything depends on execution. State whether you think this is a good use of 365 hours, and why or why not. If you think the concept should be abandoned or substantially rethought, say so here.
