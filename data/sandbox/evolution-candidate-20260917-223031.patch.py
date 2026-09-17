# Auto-generated code snippet by Emily Self-Modify
# Based on: BPE 与 UnigramLM 的解耦比较, 零阶偏好对齐
# Generated: 2026-09-17T22:30:31.758917

def _decoupled_tokenizer_preference_alignment(papers, repo_state, top_k=5):
    import re, math, json
    from collections import Counter

    def _bpe_merge_counts(text, max_merges=64):
        tokens = list(text)
        merges = Counter()
        for _ in range(max_merges):
            pairs = Counter(zip(tokens[:-1], tokens[1:]))
            if not pairs:
                break
            (a, b), _c = pairs.most_common(1)[0]
            merges[(a, b)] += 1
            new_tokens, i = [], 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == a and tokens[i + 1] == b:
                    new_tokens.append(a + b)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens
        return merges

    def _unigram_lm_scores(text, vocab):
        if not vocab:
            return {}
        total = sum(vocab.values()) or 1
        logp = {t: math.log(c / total) for t, c in vocab.items()}
        scores = {}
        for t in vocab:
            scores[t] = logp.get(t, -20.0)
        return scores

    def _zero_order_preference(candidates, ref_scores, beta=0.7):
        ranked = []
        for c in candidates:
            s = ref_scores.get(c, -20.0)
            ranked.append((c, s))
        ranked.sort(key=lambda x: -x[1])
        return [c for c, _ in ranked[:top_k]]

    corpus = " ".join(p.get("title", "") + " " + p.get("abstract", "") for p in papers)
    corpus = re.sub(r"[^a-zA-Z0-9\s]", " ", corpus).lower()
    bpe_merges = _bpe_merge_counts(corpus)
    unigram_vocab = Counter(corpus.split())
    unigram_scores = _unigram_lm_scores(corpus, unigram_vocab)

    bpe_tokens = [a + b for (a, b) in bpe_merges.keys()]
    bpe_scores = {t: unigram_scores.get(t, -20.0) for t in bpe_tokens}

    candidates = list(set(list(unigram_scores.keys()) + bpe_tokens))
    preferred = _zero_order_preference(candidates, {**unigram_scores, **bpe_scores}, beta=0.7)

    repo_state["tokenizer_preference"] = {
        "bpe_merges": len(bpe_merges),
        "unigram_vocab": len(unigram_vocab),
        "preferred_tokens": preferred,
        "alignment": "zero_order_preference",
    }
    return repo_state