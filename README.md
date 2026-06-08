# 3D Constrained Route Optimizer

A browser-based tool for solving the **Travelling Salesman Problem (TSP)** in 3D space with **chain ordering constraints**. No install, no dependencies — open `index.html` and go.

Originally built for **Elite Dangerous** route planning, but works for any dataset with 3D coordinates (X, Y, Z).

> **Note:** This project is 100% AI-generated, built entirely through a conversation with [Perplexity AI](https://www.perplexity.ai).

---

## Features

- **3D interactive canvas** — drag to rotate, scroll to zoom
- **Fixed start & end points** — including circular routes (same start and end)
- **Chain ordering constraints** — drag systems into chains to enforce visit order
  - Chains are subsequence-based: other systems can appear anywhere between chain elements
  - A system can appear multiple times within a chain (e.g. `A → B → A → C`)
  - Multiple independent chains supported simultaneously
- **Near-optimal routing** — greedy nearest-neighbour → 2-opt hill climbing → perturbation restarts
- **CSV import/export** — `Name,X,Y,Z` format; paste directly or load a file
- **Manual entry** — add systems one by one with coordinates
- **localStorage persistence** — systems, chains, and settings survive page refresh

---

## Usage

1. Open `index.html` in any modern browser
2. Import a CSV (`Name,X,Y,Z`) or add systems manually
3. Set a **Start** and **End** system
4. *(Optional)* Click **+ New Chain** and drag systems into ordering chains
5. Click **▶ CALCULATE ROUTE**
6. Export the result as CSV

---

## CSV Format

```csv
Name,X,Y,Z
Sol,0,0,0
Alpha Centauri,1.3,-0.5,2.1
Sirius,-8.5,2.3,6.2
```

Header row is auto-detected and optional.

---

## Chain Constraints

A chain defines a **required subsequence** — the listed systems must appear in that order somewhere in the final route, but any other systems can appear in between.

| Chain | Meaning |
|-------|---------|
| `A → B → C` | A before B, B before C (anything can be between them) |
| `A → B → A` | A must appear twice, with B visited between the two occurrences |

---

## Algorithm

1. **Greedy nearest-neighbour** — builds initial valid route respecting all chain constraints
2. **2-opt** — iteratively reverses route segments to reduce distance while re-validating constraints
3. **Perturbation restarts** — random swaps to escape local minima, followed by another 2-opt pass
4. Up to 80 iterations, converges in milliseconds for ≤20 systems

---

## License

MIT — see [LICENSE](./LICENSE)
