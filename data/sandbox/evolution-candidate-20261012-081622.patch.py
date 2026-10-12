# Auto-generated code snippet by Emily Self-Modify
# Based on: Wikipedia Game, RATED 工具检索
# Generated: 2026-10-12T08:16:22.749276

def _wikipedia_game_retrieval(query: str, max_hops: int = 3) -> dict:
    import urllib.parse, urllib.request, json, re
    def _fetch(title):
        url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "extracts|links",
            "titles": title, "explaintext": 1, "pllimit": "20", "redirects": 1
        })
        req = urllib.request.Request(url, headers={"User-Agent": "evolution-station/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for _, p in pages.items():
            return p.get("extract", ""), [l.get("title", "") for l in p.get("links", [])]
        return "", []
    try:
        start = query.strip().replace(" ", "_")
        visited, frontier, path = set(), [start], []
        for _ in range(max_hops):
            if not frontier:
                break
            current = frontier.pop(0)
            if current in visited:
                continue
            visited.add(current)
            extract, links = _fetch(current)
            path.append({"title": current, "snippet": extract[:400]})
            scored = sorted(links, key=lambda t: -sum(
                1 for w in re.findall(r"\w+", query.lower()) if w in t.lower()))
            frontier.extend(scored[:3])
        return {"query": query, "path": path, "hops": len(path)}
    except Exception as e:
        return {"query": query, "error": str(e), "path": []}

def _rated_tool_retrieval(query: str, tools: list) -> list:
    import re
    q_tokens = set(re.findall(r"\w+", query.lower()))
    scored = []
    for t in tools:
        name = t.get("name", "") if isinstance(t, dict) else str(t)
        desc = t.get("description", "") if isinstance(t, dict) else ""
        t_tokens = set(re.findall(r"\w+", (name + " " + desc).lower()))
        overlap = len(q_tokens & t_tokens)
        relevance = overlap / (len(q_tokens) + 1e-6)
        reliability = float(t.get("reliability", 0.5)) if isinstance(t, dict) else 0.5
        cost = float(t.get("cost", 1.0)) if isinstance(t, dict) else 1.0
        rated = relevance * 0.6 + reliability * 0.3 - cost * 0.1
        scored.append((rated, t))
    scored.sort(key=lambda x: -x[0])
    return [t for _, t in scored[:5]]

def _enhanced_retrieval(query: str, available_tools: list) -> dict:
    wiki = _wikipedia_game_retrieval(query, max_hops=3)
    tools = _rated_tool_retrieval(query, available_tools)
    return {"wikipedia_path": wiki.get("path", []), "ranked_tools": tools,
            "context": " | ".join(p["snippet"] for p in wiki.get("path", [])[:2])}