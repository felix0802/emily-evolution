# Auto-generated code snippet by Emily Self-Modify
# Based on: 固定起始 token 线索, 循环模型固定点截断反向传播与终端 KV 共享
# Generated: 2026-10-06T17:30:29.767408

def _apply_fixed_point_kv_share(model, inputs, max_iters=8, tol=1e-4):
    import torch
    h = model.embed(inputs)
    kv_cache = None
    prev = None
    for step in range(max_iters):
        out, kv_cache = model.forward_with_kv(h, kv_cache=kv_cache, share_terminal_kv=True)
        if prev is not None and torch.max(torch.abs(out - prev)).item() < tol:
            break
        prev = out.detach()
        h = out
    return out, kv_cache


def _tbptt_fixed_point(model, inputs, targets, loss_fn, window=4, max_iters=8):
    import torch
    h = model.embed(inputs).detach()
    kv_cache = None
    for step in range(max_iters):
        h_in = h if step < max_iters - window else h.detach()
        out, kv_cache = model.forward_with_kv(h_in, kv_cache=kv_cache, share_terminal_kv=True)
        h = out
    loss = loss_fn(h, targets)
    loss.backward()
    return loss.item()


def _seed_token_clue(prompt, seed_tokens):
    if not seed_tokens:
        return prompt
    clue = " ".join(seed_tokens)
    return f"[SEED:{clue}] {prompt}"


def evolve_with_fixed_point(self, prompt, seed_tokens=None, targets=None):
    prompt = _seed_token_clue(prompt, seed_tokens)
    inputs = self.tokenize(prompt)
    if targets is not None and self.model is not None:
        loss = _tbptt_fixed_point(self.model, inputs, targets, self.loss_fn,
                                  window=4, max_iters=8)
        self.last_loss = loss
    out, kv = _apply_fixed_point_kv_share(self.model, inputs, max_iters=8)
    self.terminal_kv = kv
    return self.decode(out)