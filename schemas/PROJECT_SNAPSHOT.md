# Project Snapshot

> Paste this at the start of a new AI session to restore full project context. The AI should treat it as canonical system memory and architecture law. Work statelessly from it. Preserve its architecture contracts and invariants. Assume no prior context. Ignore prior assistant assumptions. Pick up from Next Steps unless told otherwise.

---

```
=== PROJECT SNAPSHOT ===

## Meta
- Generated: <date>
- Thread Summary: <1–2 sentences>

## Goals
- Primary Objective: <what we're building>
- Current Milestone: <what we're working on now>

## Architecture Contracts (MUST NOT BREAK)
<Hard invariants, ownership rules, structural boundaries.
 Do not suggest changes unless I say "revisit contracts".>

## System Diagram
<Mermaid or brief structural overview>

## Data Contracts
<Key schemas, interfaces, type definitions that define system shape>

## Lifecycle
<Step flow of major operations>

## Key Decisions & Context
<Design decisions with rationale, as bullets.
 Cap at ~15 bullets. When exceeding cap, archive older decisions
 to a DECISIONS_LOG file and keep only active/recent decisions here.>

## State
- Completed: <what's done>
- In Progress: <what's partial, with status>
- Known Issues: <bugs, blockers, open questions>

## Next Steps
<Ordered immediate TODOs>

## Code Reference (optional)
<Only critical small snippets a new thread cannot infer from files.
 For large files: filename + one-line description.>

=== END PROJECT SNAPSHOT ===
```

---

## Keywords

| Command | Action |
|---------|--------|
| `snapshot` | Generate a full snapshot from current session state |
| `snapshot diff` | Only what changed since last snapshot |
| `revisit contracts` | Unlock Architecture Contracts for modification |

## Rules

- Prioritize decisions and rationale over code listings.
- Keep compact — a new thread with zero context must be able to continue from this document alone.
- Never re-question Architecture Contracts unless explicitly unlocked with `revisit contracts`.
