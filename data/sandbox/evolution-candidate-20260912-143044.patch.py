# Auto-generated code snippet by Emily Self-Modify
# Based on: 静态数据流编译与CUDA图重放, 分布偏移的通用量化, Cuda
# Generated: 2026-09-12T14:30:44.854404

def _apply_static_dataflow_cudagraph_replay(self, model, sample_inputs, num_replays=3):
    import torch
    import torch.cuda as cuda
    from torch.cuda import graph_pool_handle

    if not torch.cuda.is_available():
        return model

    device = torch.device("cuda")
    model = model.to(device).eval()

    static_inputs = [torch.as_tensor(x, device=device).clone() for x in sample_inputs]
    static_outputs = None

    warmup_stream = cuda.Stream()
    warmup_stream.wait_stream(cuda.current_stream())
    with cuda.stream(warmup_stream):
        for _ in range(3):
            static_outputs = model(*static_inputs)
    cuda.current_stream().wait_stream(warmup_stream)

    g = cuda.CUDAGraph()
    pool = graph_pool_handle()
    with cuda.graph(g, pool=pool):
        static_outputs = model(*static_inputs)

    replay_outputs = []
    for _ in range(num_replays):
        g.replay()
        replay_outputs.append(static_outputs.detach().clone())

    drift = torch.stack([o.float() for o in replay_outputs]).std(dim=0).mean().item()
    self._quantization_scale = max(drift, 1e-6)

    def _replay_forward(*inputs):
        for si, x in zip(static_inputs, inputs):
            si.copy_(torch.as_tensor(x, device=device))
        g.replay()
        return static_outputs

    model.replay_forward = _replay_forward
    model.quant_scale = self._quantization_scale
    return model