# Auto-generated code snippet by Emily Self-Modify
# Based on: 无编码器、无 VAE 的统一多模态架构, 空间一致 patch 重建, 基于扩散模型的 DEM 引导超分辨率, Vae
# Generated: 2026-09-11T12:24:23.382814

def enhance_multimodal_fusion(paper_metadata: dict, repo_state: dict) -> dict:
    import numpy as np
    from sklearn.decomposition import PCA

    def _spatial_consistent_patch(features: np.ndarray, patch_size: int = 8) -> np.ndarray:
        h, w = features.shape[:2]
        patches = []
        for i in range(0, h - patch_size + 1, patch_size):
            for j in range(0, w - patch_size + 1, patch_size):
                patch = features[i:i + patch_size, j:j + patch_size]
                patches.append(patch.flatten())
        patches = np.array(patches)
        if patches.size == 0:
            return features
        pca = PCA(n_components=min(16, patches.shape[1]))
        reduced = pca.fit_transform(patches)
        reconstructed = pca.inverse_transform(reduced)
        out = np.zeros_like(features)
        idx = 0
        for i in range(0, h - patch_size + 1, patch_size):
            for j in range(0, w - patch_size + 1, patch_size):
                out[i:i + patch_size, j:j + patch_size] = reconstructed[idx].reshape(patch_size, patch_size)
                idx += 1
        return out

    def _diffusion_dem_guided_sr(low_res: np.ndarray, dem_prior: np.ndarray, steps: int = 5) -> np.ndarray:
        up = np.kron(low_res, np.ones((2, 2)))
        if up.shape != dem_prior.shape:
            dem_prior = np.resize(dem_prior, up.shape)
        x = up.astype(np.float32)
        for t in range(steps):
            alpha = 1.0 - (t + 1) / (steps + 1)
            grad = np.gradient(x)
            guidance = 0.1 * (dem_prior - x)
            x = x + alpha * (grad[0] + grad[1]) + guidance
        return np.clip(x, 0, 1)

    def _unified_multimodal_encode(modalities: list) -> np.ndarray:
        encoded = []
        for m in modalities:
            arr = np.asarray(m, dtype=np.float32)
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            arr = (arr - arr.mean()) / (arr.std() + 1e-8)
            encoded.append(arr.flatten())
        max_len = max(len(e) for e in encoded)
        padded = [np.pad(e, (0, max_len - len(e))) for e in encoded]
        return np.mean(np.stack(padded, axis=0), axis=0)

    text_feat = np.array([hash(w) % 997 for w in paper_metadata.get("title", "").split()], dtype=np.float32)
    if text_feat.size == 0:
        text_feat = np.zeros(16, dtype=np.float32)
    grid = int(np.ceil(np.sqrt(text_feat.size)))
    img_feat = np.pad(text_feat, (0, grid * grid - text_feat.size)).reshape(grid, grid)
    patch_recon = _spatial_consistent_patch(img_feat)
    dem_prior = np.abs(np.gradient(patch_recon)[0])
    sr_feat = _diffusion_dem_guided_sr(patch_recon, dem_prior)
    fused = _unified_multimodal_encode([text_feat, patch_recon.flatten(), sr_feat.flatten()])
    repo_state["multimodal_fusion"] = fused.tolist()
    repo_state["fusion_dim"] = int(fused.shape[0])
    return repo_state