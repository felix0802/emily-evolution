# Auto-generated code snippet by Emily Self-Modify
# Based on: Tetris3D, Long-WAM
# Generated: 2026-10-08T08:06:05.388930

def _tetris3d_long_wam_enhance(paper_meta: dict, repo_state: dict) -> dict:
    import hashlib, math, time
    from collections import deque

    def _tetris3d_pack(items, depth=3):
        grid = {}
        for idx, item in enumerate(items):
            key = hashlib.sha1(str(item).encode()).hexdigest()[:8]
            x = idx % 4
            y = (idx // 4) % 4
            z = (idx // 16) % depth
            grid[(x, y, z)] = {"id": key, "payload": item, "ts": time.time()}
        return grid

    def _long_wam_score(grid, horizon=8):
        if not grid:
            return 0.0
        coords = list(grid.keys())
        centroid = tuple(sum(c[i] for c in coords) / len(coords) for i in range(3))
        spread = sum(math.dist(c, centroid) for c in coords) / len(coords)
        recency = sum(1.0 / (1.0 + time.time() - v["ts"]) for v in grid.values())
        window = deque(maxlen=horizon)
        for v in grid.values():
            window.append(len(v["payload"]) if hasattr(v["payload"], "__len__") else 1)
        wam = sum(window) / max(1, len(window))
        return (spread * 0.4) + (recency * 0.3) + (wam * 0.3)

    candidates = []
    for key in ("title", "abstract", "authors", "categories", "summary"):
        if key in paper_meta:
            candidates.append({key: paper_meta[key]})
    for key in ("stars", "forks", "issues", "commits", "language"):
        if key in repo_state:
            candidates.append({key: repo_state[key]})

    grid = _tetris3d_pack(candidates, depth=3)
    score = _long_wam_score(grid, horizon=8)

    return {
        "tetris3d_grid": grid,
        "long_wam_score": round(score, 4),
        "enhancement": "tetris3d+long_wam",
        "candidate_count": len(candidates),
    }

_enhancement = _tetris3d_long_wam_enhance(paper_meta, repo_state)