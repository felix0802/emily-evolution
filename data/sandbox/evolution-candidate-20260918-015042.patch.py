# Auto-generated code snippet by Emily Self-Modify
# Based on: Sharded Data Parallelism (SDP), PROLOG for Legal Translation
# Generated: 2026-09-18T01:50:42.983329

def _sharded_prolog_legal_translate(self, papers: list) -> list:
    import hashlib
    from concurrent.futures import ThreadPoolExecutor

    def _shard_key(p):
        h = hashlib.sha256(p.get("id", "").encode()).hexdigest()
        return int(h[:8], 16) % self.num_shards

    shards = {i: [] for i in range(self.num_shards)}
    for p in papers:
        shards[_shard_key(p)].append(p)

    def _prolog_facts(batch):
        facts = []
        for p in batch:
            title = p.get("title", "").replace("'", "\\'")
            abstract = p.get("summary", "").replace("'", "\\'")[:400]
            facts.append(f"paper('{p.get('id','')}', '{title}', '{abstract}').")
        return facts

    def _translate_shard(idx):
        batch = shards[idx]
        if not batch:
            return []
        facts = _prolog_facts(batch)
        query = (
            "legal_translate(Title, Abstract, Clause) :- "
            "paper(_, Title, Abstract), "
            "clause_extract(Abstract, Clause)."
        )
        try:
            result = self.prolog_engine.query(facts, query)
            return result if isinstance(result, list) else [result]
        except Exception:
            return [{"shard": idx, "status": "fallback", "count": len(batch)}]

    with ThreadPoolExecutor(max_workers=self.num_shards) as ex:
        translated = list(ex.map(_translate_shard, range(self.num_shards)))

    flat = [item for sub in translated for item in sub]
    self._last_shard_stats = {
        "num_shards": self.num_shards,
        "per_shard": {i: len(shards[i]) for i in shards},
        "translated": len(flat),
    }
    return flat