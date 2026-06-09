import math
import csv
import time

# ─── CONFIG ───────────────────────────────────────────────────────────────────
STAR_LIST_CSV  = "test_star_list.csv"
CHAINS_CSV     = "test_chains.csv"
START          = "Sol"
END            = "Deneb"

# ─── LOAD SYSTEMS ─────────────────────────────────────────────────────────────
systems = {}  # name -> (x, y, z)
with open(STAR_LIST_CSV, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        systems[row["Name"]] = (float(row["X"]), float(row["Y"]), float(row["Z"]))

# ─── LOAD CHAINS ──────────────────────────────────────────────────────────────
# chains.csv format: Chain,Position,Name,X,Y,Z
# Each unique Chain number becomes one ordered chain list.
_raw_chains = {}  # chain_id -> [(position, name)]
with open(CHAINS_CSV, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        cid = int(row["Chain"])
        pos = int(row["Position"])
        name = row["Name"]
        _raw_chains.setdefault(cid, []).append((pos, name))

chains = [
    [name for _, name in sorted(entries)]
    for entries in sorted(_raw_chains.values(), key=lambda e: e[0][0] if e else 0)
]

# ─── BUILD DISTANCE MATRIX ────────────────────────────────────────────────────
names_list = list(systems.keys())
idx = {n: i for i, n in enumerate(names_list)}
N = len(names_list)
D = [[0.0] * N for _ in range(N)]
for i in range(N):
    ax, ay, az = systems[names_list[i]]
    for j in range(N):
        if i != j:
            bx, by, bz = systems[names_list[j]]
            D[i][j] = math.sqrt((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2)


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def route_dist_fast(route):
    return sum(D[idx[route[k]]][idx[route[k + 1]]] for k in range(len(route) - 1))


def init_progress():
    return [0] * len(chains)


def can_visit(name, progress):
    for ci, chain in enumerate(chains):
        p = progress[ci]
        for j in range(len(chain)):
            if chain[j] == name and j > p:
                return False
    return True


def advance(name, progress):
    np2 = progress[:]
    for ci, chain in enumerate(chains):
        if np2[ci] < len(chain) and chain[np2[ci]] == name:
            np2[ci] += 1
    return np2


def all_done(progress):
    return all(progress[ci] >= len(chains[ci]) for ci in range(len(chains)))


def fmt_time(seconds):
    if seconds < 0 or math.isinf(seconds):
        return "unknown"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    elif m > 0:
        return f"{m}m {s:02d}s"
    else:
        return f"{s}s"


# ─── GREEDY SEED ──────────────────────────────────────────────────────────────
def greedy_seed():
    """Nearest-neighbour greedy route respecting chain ordering (best-effort)."""
    visited = {START}
    route = [START]
    progress = advance(START, init_progress())
    remaining = [s for s in names_list if s != START and s != END]
    current = START
    while remaining:
        # find nearest unvisited that is allowed by constraints
        candidates = [s for s in remaining if can_visit(s, progress)]
        if not candidates:
            candidates = remaining  # fall back — may violate; just for seeding
        nxt = min(candidates, key=lambda s: D[idx[current]][idx[s]])
        route.append(nxt)
        visited.add(nxt)
        remaining.remove(nxt)
        progress = advance(nxt, progress)
        current = nxt
    route.append(END)
    return route


# ─── ETA / PROGRESS ───────────────────────────────────────────────────────────
middle_pool = [s for s in names_list if s != START and s != END] + [START]
TOTAL_TOP = len(middle_pool)

progress_tracker = {
    "top_done": 0,
    "branch_times": [],
}

approx_route = greedy_seed()

best = {
    "dist": route_dist_fast(approx_route),
    "route": approx_route[:],
}

checked = 0
pruned_dist = 0
pruned_constraint = 0
valid_found = [0]
start_time = time.time()
last_report = [start_time]


# ─── SEARCH ───────────────────────────────────────────────────────────────────
def branch_and_bound(partial_route, partial_dist, remaining, progress, depth):
    global checked, pruned_dist, pruned_constraint

    if not remaining:
        final_dist = partial_dist + D[idx[partial_route[-1]]][idx[END]]
        checked += 1
        final_progress = advance(END, progress)
        if not all_done(final_progress):
            pruned_constraint += 1
            return
        valid_found[0] += 1
        if final_dist < best["dist"]:
            best["dist"] = final_dist
            best["route"] = partial_route + [END]
            elapsed = time.time() - start_time
            print(f" ★ New best: {final_dist:.4f} ly | checked {checked:,} | "
                  f"valid {valid_found[0]:,} | elapsed {fmt_time(elapsed)}")
            print(f"   Route: {' -> '.join(best['route'])}")

        now = time.time()
        if now - last_report[0] > 15:
            last_report[0] = now
            _print_progress()
        return

    for i, name in enumerate(remaining):
        if not can_visit(name, progress):
            pruned_constraint += 1
            continue
        step_dist = D[idx[partial_route[-1]]][idx[name]]
        new_dist = partial_dist + step_dist
        if new_dist >= best["dist"]:
            pruned_dist += 1
            continue
        new_remaining = remaining[:i] + remaining[i + 1:]
        new_progress = advance(name, progress)
        branch_and_bound(
            partial_route + [name],
            new_dist,
            new_remaining,
            new_progress,
            depth + 1,
        )


def _print_progress():
    now = time.time()
    elapsed = now - start_time
    done = progress_tracker["top_done"]
    remaining_branches = TOTAL_TOP - done
    if done == 0 or not progress_tracker["branch_times"]:
        eta_str = "estimating..."
    else:
        avg = sum(progress_tracker["branch_times"]) / len(progress_tracker["branch_times"])
        eta_sec = avg * remaining_branches
        pct = 100.0 * done / TOTAL_TOP
        eta_str = f"~{fmt_time(eta_sec)} ({pct:.1f}% top-level done)"
    print(f" Progress | elapsed: {fmt_time(elapsed)} | ETA: {eta_str}")
    print(f" checked: {checked:,} | valid: {valid_found[0]:,} | best: {best['dist']:.4f} ly")
    print(f" pruned dist: {pruned_dist:,} | pruned constraint: {pruned_constraint:,}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
print(f"Systems  : {N}  ({', '.join(names_list)})")
print(f"Start    : {START} | End: {END}")
print(f"Chains   : {len(chains)}")
for ci, ch in enumerate(chains, 1):
    print(f"  Chain {ci}: {' -> '.join(ch)}")
print(f"Middle pool: {len(middle_pool)} elements")
print(f"Greedy seed: {best['dist']:.4f} ly  ({' -> '.join(approx_route)})")
print()
print("Starting exhaustive branch-and-bound...")
print("Progress reported every 15s. New bests printed immediately.")
print("=" * 65)

init_prog = advance(START, init_progress())

for top_i, first_sys in enumerate(middle_pool):
    if not can_visit(first_sys, init_prog):
        progress_tracker["top_done"] += 1
        continue
    step_dist = D[idx[START]][idx[first_sys]]
    if step_dist >= best["dist"]:
        progress_tracker["top_done"] += 1
        continue

    t0 = time.time()
    remaining_after_first = [s for j, s in enumerate(middle_pool) if j != top_i]
    new_prog = advance(first_sys, init_prog)
    branch_and_bound([START, first_sys], step_dist, remaining_after_first, new_prog, depth=1)

    branch_elapsed = time.time() - t0
    progress_tracker["top_done"] += 1
    progress_tracker["branch_times"].append(branch_elapsed)

    done = progress_tracker["top_done"]
    remaining_top = TOTAL_TOP - done
    avg = sum(progress_tracker["branch_times"]) / len(progress_tracker["branch_times"])
    eta_sec = avg * remaining_top
    pct = 100.0 * done / TOTAL_TOP
    total_elapsed = time.time() - start_time
    print(f" [Branch {done:2d}/{TOTAL_TOP}] first={first_sys:<20} "
          f"took {fmt_time(int(branch_elapsed))} | "
          f"ETA: {fmt_time(eta_sec)} ({pct:.1f}% done) | "
          f"total: {fmt_time(int(total_elapsed))}")

# ─── FINAL REPORT ─────────────────────────────────────────────────────────────
total_elapsed = time.time() - start_time
print()
print("=" * 65)
print("EXHAUSTIVE SEARCH COMPLETE")
print("=" * 65)
print(f"Total complete routes evaluated : {checked:,}")
print(f"Valid routes (all constraints)  : {valid_found[0]:,}")
print(f"Pruned (distance bound)         : {pruned_dist:,}")
print(f"Pruned (constraint violation)   : {pruned_constraint:,}")
print(f"Time elapsed                    : {fmt_time(int(total_elapsed))}")
print()
greedy_dist = route_dist_fast(approx_route)
gap = greedy_dist - best["dist"]
print(f"OPTIMAL distance : {best['dist']:.4f} ly")
print(f"Greedy seed dist : {greedy_dist:.4f} ly")
print(f"Gap              : {gap:.4f} ly ({100 * gap / best['dist']:.4f}%)")
print()
print("Optimal route:")
for i, s in enumerate(best["route"]):
    tag = " [START]" if i == 0 else (" [END]" if i == len(best["route"]) - 1 else "")
    seg = f" +{D[idx[best['route'][i - 1]]][idx[s]]:.2f} ly" if i > 0 else ""
    print(f"  {i + 1:2d}. {s}{seg}{tag}")
