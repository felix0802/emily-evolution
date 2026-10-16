# Auto-generated code snippet by Emily Self-Modify
# Based on: Spatially aware audio-visual LLMs, Audio
# Generated: 2026-10-16T01:55:25.965368

def enhance_spatial_audiovisual_fusion(perception_output, llm_context):
    """
    Spatially aware audio-visual fusion enhancement.
    Aligns audio embeddings with spatial visual regions using cross-modal attention.
    """
    import numpy as np

    audio_emb = np.asarray(perception_output.get("audio_embedding", []), dtype=np.float32)
    visual_regions = perception_output.get("visual_regions", [])
    spatial_maps = perception_output.get("spatial_maps", [])

    if audio_emb.size == 0 or not visual_regions:
        return llm_context

    fused_regions = []
    for idx, region in enumerate(visual_regions):
        region_emb = np.asarray(region.get("embedding", []), dtype=np.float32)
        if region_emb.size == 0:
            continue
        spatial_weight = 1.0
        if idx < len(spatial_maps):
            smap = np.asarray(spatial_maps[idx], dtype=np.float32)
            if smap.size > 0:
                spatial_weight = float(np.clip(smap.mean(), 0.0, 1.0))
        sim = float(np.dot(audio_emb, region_emb) /
                    (np.linalg.norm(audio_emb) * np.linalg.norm(region_emb) + 1e-8))
        fused_regions.append({
            "region_id": region.get("id", idx),
            "audio_visual_score": sim * spatial_weight,
            "bbox": region.get("bbox"),
        })

    fused_regions.sort(key=lambda r: r["audio_visual_score"], reverse=True)
    top_k = fused_regions[:5]

    llm_context = dict(llm_context) if isinstance(llm_context, dict) else {"context": llm_context}
    llm_context["spatial_av_fusion"] = {
        "top_regions": top_k,
        "audio_energy": float(np.linalg.norm(audio_emb)),
        "modality": "spatially_aware_av",
    }
    return llm_context