# Auto-generated code snippet by Emily Self-Modify
# Based on: 结构化块跳过（Structured Block Skipping）, PPG基础模型统一基准（PPG-Bench）
# Generated: 2026-10-13T08:37:25.825341

def _structured_block_skip_and_benchmark(papers, repo_state):
    """
    结构化块跳过 + PPG-Bench 统一基准评估。
    插入到 evolve() 中调用: papers = _structured_block_skip_and_benchmark(papers, repo_state)
    """
    import re, json, hashlib
    from collections import defaultdict

    # 1) 结构化块跳过：按 section 标题切块，跳过已知低信息块
    SKIP_PATTERNS = re.compile(
        r'^(references|acknowledg|appendix|supplementary|related work|'
        r'ethics statement|broader impact|author contributions)\b',
        re.IGNORECASE
    )
    BLOCK_RE = re.compile(r'(?m)^(?:#{1,4}\s+|\d+\.\s+|\*\*)([A-Z][^\n]{2,80})$')

    def split_blocks(text):
        if not text:
            return []
        positions = [(m.start(), m.group(1).strip()) for m in BLOCK_RE.finditer(text)]
        if not positions:
            return [("body", text)]
        blocks, prev = [], 0
        for i, (pos, title) in enumerate(positions):
            if i > 0:
                blocks.append((positions[i-1][1], text[prev:pos]))
            prev = pos
        blocks.append((positions[-1][1], text[prev:]))
        return blocks

    def keep_block(title, body):
        if SKIP_PATTERNS.match(title):
            return False
        if len(body.strip()) < 120:
            return False
        return True

    filtered = []
    for p in papers:
        abstract = p.get("abstract") or p.get("summary") or ""
        blocks = split_blocks(abstract)
        kept = [b for t, b in blocks if keep_block(t, b)]
        if not kept:
            kept = [abstract]
        p["_blocks"] = kept
        p["_block_hash"] = hashlib.sha1(
            "||".join(kept).encode("utf-8", "ignore")
        ).hexdigest()[:16]
        filtered.append(p)

    # 2) PPG-Bench 统一基准：对每篇论文按统一维度打分
    BENCH_DIMS = {
        "novelty":       (r'\b(novel|new|first|unprecedented)\b', 1.0),
        "reproducibility": (r'\b(code|dataset|benchmark|open[- ]source|github)\b', 1.2),
        "methodology":   (r'\b(method|framework|architecture|algorithm)\b', 1.0),
        "evaluation":    (r'\b(evaluat|experiment|ablation|baseline|metric)\b', 1.1),
        "impact":        (r'\b(state[- ]of[- ]the[- ]art|sota|outperform|significant)\b', 1.3),
    }

    def ppg_score(text):
        t = text.lower()
        scores = {}
        for dim, (pat, w) in BENCH_DIMS.items():
            hits = len(re.findall(pat, t))
            scores[dim] = round(min(1.0, hits * 0.15) * w, 4)
        scores["_total"] = round(sum(scores.values()) / len(BENCH_DIMS), 4)
        return scores

    for p in filtered:
        text = " ".join(p.get("_blocks", [])) or p.get("abstract", "")
        p["ppg_bench"] = ppg_score(text)

    # 3) 去重 + 按 PPG 总分排序
    seen, deduped = set(), []
    for p in filtered:
        h = p.get("_block_hash")
        if h in seen:
            continue
        seen.add(h)
        deduped.append(p)
    deduped.sort(key=lambda x: x.get("ppg_bench", {}).get("_total", 0), reverse=True)

    # 4) 记录到 repo_state 以便后续验证层使用
    if isinstance(repo_state, dict):
        repo_state.setdefault("ppg_bench_history", []).append({
            "n_in": len(papers),
            "n_out": len(deduped),
            "top_score": deduped[0]["ppg_bench"]["_total"] if deduped else 0.0,
        })
        repo_state["ppg_bench_history"] = repo_state["ppg_bench_history"][-50:]

    return deduped