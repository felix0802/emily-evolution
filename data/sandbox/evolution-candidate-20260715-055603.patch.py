# Auto-generated code snippet by Emily Self-Modify
# Based on: 双向视频扩散模型, 光流作为动作表示
# Generated: 2026-07-15T05:56:03.250759

```python
def integrate_video_diffusion():
    import torch, cv2, numpy as np
    from diffusers import AnimateDiffPipeline, MotionAdapter
    adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-v1-5-2")
    pipe = AnimateDiffPipeline.from_pretrained("emilianJR/epiCRealism", motion_adapter=adapter)
    pipe.enable_model_cpu_offload()
    frames = pipe("robot exploring environment", num_frames=16, guidance_scale=7.5).frames[0]
    flow = cv2.calcOpticalFlowFarneback(cv2.cvtColor(np.array(frames[0]), cv2.COLOR_RGB2GRAY),
                                        cv2.cvtColor(np.array(frames[1]), cv2.COLOR_RGB2GRAY), None, 0.5, 3, 15, 3, 5, 1.2, 0)
    return {"video_frames": frames, "optical_flow": flow.tolist()}
```