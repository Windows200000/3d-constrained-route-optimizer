# Design Requirements

This document captures the design and behavioural requirements for the 3D Constrained Route Optimizer, as defined through development conversations.

---

## Goal

Find the **best possible route** visiting all systems, satisfying all chain constraints, within a **couple of seconds**.

The specific algorithm used is an implementation detail — what matters is the outcome:

1. All chain constraints are satisfied
2. The route is near-optimal (short total distance)
3. Computation completes in a few seconds for typical dataset sizes

---

## Chain Constraints

- A chain defines a **required subsequence** — the listed systems must appear in that order in the final route, with any other systems allowed in between
- A system can appear **multiple times** within a chain (e.g. `A → B → A → C`)
- **Multiple independent chains** are supported simultaneously
- **All chain combinations are valid** — there are no invalid chain configurations
- The solver must **always find a solution** satisfying all chains simultaneously
  - Example: chains `A → B → C` and `C → D → A` can coexist and will always be resolved

### Chain Examples

| Chain(s) | Meaning |
|----------|---------|
| `A → B → C` | A before B, B before C (anything can be between them) |
| `A → B → A` | A must appear twice, with B visited between the two occurrences |
| `A → B → C` + `C → D → A` | Both subsequences must be satisfied simultaneously — always possible |

---

## Routing

- **Fixed start & end points** must be supported, including **circular routes** (same start and end)
- The route must visit every system exactly once (except where chain repetition requires otherwise)

---

## Persistence

- All data — systems, chains, and settings — must be saved to **localStorage**
- Everything must be **automatically restored on page reload**
- Nothing should be lost between sessions

---

## UI / Technical

- **Browser-based**: no install, no dependencies — open `index.html` and go
- **3D interactive canvas**: drag to rotate, scroll to zoom
- **Drag-and-drop** interface for building and editing chains
- **Import Systems CSV** in `Name,X,Y,Z` format; paste directly or load a file; header row auto-detected
- **Import Chains CSV** in `Chain,Position,Name,X,Y,Z` format (same format as export); paste or load file; automatically adds any missing systems; replaces current chains
- **Export Chains CSV**: right panel `↓ CSV` button exports all chains to `chains.csv` with columns `Chain,Position,Name,X,Y,Z`
- **Export Route CSV**: header button exports the solved route as `route.csv` in `Name,X,Y,Z` format
- **Manual entry**: add systems one by one with coordinates
- **Legend removed** from right panel — chains panel fills full height
