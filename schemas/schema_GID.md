# Game Idea Document — Schema

---

## How to Use This Template
Fill in each section. The comments (<!-- like this -->) are guidance — delete them as you go. If a section doesn't apply to your game, write "N/A" and briefly say why. Don't leave sections blank — a deliberate "N/A" is more useful than an empty heading.

---

## Genre(s)
<!-- Primary genre / subgenre blend. Be specific — "puzzle" is not a genre, "puzzle-exploration" is. -->

## Reference Games & Inspirations
<!-- 3–5 titles. For each, state the ONE thing you're taking from it, not just the title. -->
- **[Title]** — [what specifically you're borrowing and why]

## Pillars
<!-- 3–5 design pillars. Each must be mechanically testable — if you can't build a prototype that proves or disproves it, it's a vibe, not a pillar. -->
<!-- For any pillar that involves a cost, constraint, or restriction on the player: state the specific mechanism. What is gained? What is lost? How is it enforced? -->
1. **[Pillar]** — [Mechanism: how this works in practice, not just what it aspires to]
2. **[Pillar]** — [Mechanism]
3. **[Pillar]** — [Mechanism]

## Scope Limitations
<!-- For each: name the genre expectation you're cutting, and why cutting it is a design choice, not a budget compromise. -->
- **No [feature]** — [What players expect and why you're not doing it. What does cutting this force you to do instead?]

## Core Loop
<!-- One sentence: the loop as a chain of verbs. Then expand. -->
**[Verb] → [Verb] → [Verb] → [Verb] → [Repeat]**

<!-- The core loop must visibly exercise EVERY pillar. If a pillar is not present in the loop, it is aspirational, not real. Flag this for yourself. -->

1. **Replayability mechanism:** [How does the player get value from a second session? If "they don't," say so — that's a valid answer for some designs.]
2. **Minimum content to ship:** [Quantify: number of levels, rooms, encounters, systems. No ranges — pick a number and defend it.]
3. **Procedural vs. authored:** [Is content procedural, hand-authored, or hybrid? If hand-authored, how do you prevent content drought? If procedural, how do you prevent incoherence?]

## Session Design
- **Target session length:** [X–Y minutes. What does one "unit" of play look like?]
- **Target total player engagement:** [X–Y hours first playthrough; X–Y for replay if applicable]
- **What makes the player stop AND want to come back?** [Stop trigger and return hook — be specific]
- **Why does this match monetization?** [Connect session design to how you're charging]

## Save System Philosophy
<!-- This is a design decision, not a technical one. -->
- **Can the player save manually?** [Yes/No. If yes, does this undermine any pillar?]
- **Is there autosave?** [When does it trigger? What state does it capture?]
- **Can the player save-scum?** [If yes, does this break any intended consequence or cost? If no, how is this communicated?]
- **What happens on ragequit?** [Player closes the app mid-session. What state do they return to?]

## Cognitive Load Strategy
<!-- If your game involves tracking state, remembering information, or managing complexity: how do you keep it manageable? -->
- **What is the player asked to hold in their head at any given time?** [Be honest — count the variables]
- **What aids exist?** [UI elements, environmental cues, journals, logs, visible state, audio cues — or nothing]
- **What is the maximum cognitive load at the hardest point in the game?** [Describe the worst case]
- **Design rule:** [State a concrete limit you will not exceed. e.g., "No puzzle requires tracking more than 3 unseen variables." If you don't have one, say so — but know that the adversarial review will flag it.]

---

## Elevator Pitch
<!-- 2–4 sentences. A stranger reads this and knows: what the game IS, what makes it DIFFERENT, and what the VISUAL HOOK is. -->

## The Big But
<!-- "My game is like [known title], but [the one key difference]." One sentence. -->

## Target Audience
<!-- Who specifically. Not "gamers." Reference comparable titles they already like. Age range. Psychographic: what do they enjoy about games? What do they dislike? -->

## Monetization Model
<!-- Premium, F2P, subscription, ad-supported, etc. Price point. Platform-specific pricing if different. IAP/DLC plans or explicit lack thereof. -->

---

## Platform Considerations
<!-- For each platform: -->
<!-- - Input method and why it works for your design -->
<!-- - Any constraints the platform imposes -->
<!-- - Is this platform primary or secondary? Be honest — "both are first-class" is almost always wrong. -->

## Assets
**What's needed:**
<!-- Categorized list: art, audio, UI, code systems, etc. -->

**Marketing-critical assets:**
<!-- Which assets MUST exist for the game to be marketable? (e.g., a gif-able moment, a trailer-ready sequence, a screenshot that communicates the hook) -->

**Most expensive category:** [What it is and how you're controlling cost]

**Where AI generation helps:** [Specific use cases, not "AI will help with everything"]

## Tools & Workflow
<!-- Engine, modeling tools, audio tools, version control, CI/CD if applicable. -->
<!-- Rule: no custom tooling unless you can name the specific problem it solves and the hour cost. -->

## First Playable Milestone
**What the player does:** [Describe the exact experience in one paragraph]

**What's missing:** [Everything NOT in the milestone]

**Does it prove fun?** [State what "success" looks like in concrete, observable terms. What does the playtester DO or SAY that tells you it's working? What tells you it's not?]

**Which pillars does this test?** [List them. If a pillar is NOT tested by the first playable, acknowledge this — it's a known gap.]

**Estimate:** [Hours, broken down by discipline]

## Phase Breakdown

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
<!-- 3–5 risks. For each: -->
<!-- - The risk (what goes wrong) -->
<!-- - Why it's plausible for THIS game specifically -->
<!-- - Mitigation (what you'll do about it) -->
<!-- - First cut if time runs short (what you sacrifice to solve it) -->

1. **[Risk]** — [Why plausible]. *Mitigation:* [action]. *First cut:* [sacrifice].

---

## Falsifiable Assumptions
<!-- 3–5 assumptions this design depends on. These are hypotheses, not facts. -->
<!-- Each must be testable: a playtest, a data point, or a market signal could disprove it. -->
<!-- If an assumption is disproved, what changes? -->

1. **[Assumption]** — [How you would test it. What changes if it's wrong.]
2. **[Assumption]** — [Test. Consequence if wrong.]

## Non-Negotiables
<!-- What cannot be cut, softened, or changed without killing the game's identity? -->
<!-- If any of these prove unworkable, the project needs fundamental rethinking, not scope adjustment. -->
<!-- Keep this list short (2–4 items). If everything is non-negotiable, nothing is. -->

1. **[Element]** — [Why this is identity-defining, not just preferred]

## Kill Criteria
<!-- At what point do you stop? State concrete, measurable thresholds. -->
<!-- These are commitments to yourself. If you can rationalize past them, they're too vague. -->

1. **[Milestone/trigger]** → [Decision: pivot, cut, or abandon]
2. **[Milestone/trigger]** → [Decision]
