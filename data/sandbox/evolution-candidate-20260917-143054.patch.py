# Auto-generated code snippet by Emily Self-Modify
# Based on: Byte-Pair Encoding (BPE), UnigramLM
# Generated: 2026-09-17T14:30:54.439262

def _bpe_unigram_enhance(texts, vocab_size=512, unk_token="<unk>"):
    from collections import Counter
    import math

    def _get_pairs(corpus):
        pairs = Counter()
        for word, freq in corpus.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs

    def _merge(corpus, pair):
        new_corpus = {}
        bigram = " ".join(pair)
        replacement = "".join(pair)
        for word, freq in corpus.items():
            new_word = word.replace(bigram, replacement)
            new_corpus[new_word] = freq
        return new_corpus

    corpus = Counter()
    for t in texts:
        for w in str(t).split():
            corpus[" ".join(list(w)) + " </w>"] += 1

    merges = []
    while len(merges) < vocab_size:
        pairs = _get_pairs(corpus)
        if not pairs:
            break
        best = max(pairs, key=pairs.get)
        corpus = _merge(corpus, best)
        merges.append(best)

    def _encode(word):
        symbols = list(word) + ["</w>"]
        while len(symbols) > 1:
            pairs = [(symbols[i], symbols[i + 1]) for i in range(len(symbols) - 1)]
            candidates = [p for p in pairs if p in merges]
            if not candidates:
                break
            pair = min(candidates, key=lambda p: merges.index(p))
            i = 0
            new_symbols = []
            while i < len(symbols):
                if i < len(symbols) - 1 and (symbols[i], symbols[i + 1]) == pair:
                    new_symbols.append(symbols[i] + symbols[i + 1])
                    i += 2
                else:
                    new_symbols.append(symbols[i])
                    i += 1
            symbols = new_symbols
        return symbols

    token_freq = Counter()
    encoded_texts = []
    for t in texts:
        tokens = []
        for w in str(t).split():
            tokens.extend(_encode(w))
        encoded_texts.append(tokens)
        token_freq.update(tokens)

    total = sum(token_freq.values()) or 1
    unigram_scores = {tok: math.log(freq / total) for tok, freq in token_freq.items()}
    unigram_scores[unk_token] = math.log(1e-9)

    return {
        "merges": merges,
        "vocab": list(token_freq.keys()),
        "unigram_scores": unigram_scores,
        "encoded": encoded_texts,
    }

_bpe_unigram_enhance([p.get("title", "") + " " + p.get("summary", "") for p in papers])