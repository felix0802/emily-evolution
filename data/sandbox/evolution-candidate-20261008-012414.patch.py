# Auto-generated code snippet by Emily Self-Modify
# Based on: Flow Matching, Flow Matching
# Generated: 2026-10-08T01:24:14.529152

def flow_matching_enhance(perception_data, understanding_data, decision_data):
    import numpy as np
    from scipy.integrate import solve_ivp

    def _flow_velocity(x, t, target):
        return (target - x) / max(1e-6, 1.0 - t)

    def _flow_match_sample(source, target, steps=16):
        x = np.asarray(source, dtype=float).copy()
        target = np.asarray(target, dtype=float)
        dt = 1.0 / steps
        for i in range(steps):
            t = i * dt
            v = _flow_velocity(x, t, target)
            x = x + v * dt
        return x

    def _flow_match_integrate(source, target):
        source = np.asarray(source, dtype=float)
        target = np.asarray(target, dtype=float)
        dim = source.shape[0]

        def ode(t, x):
            return _flow_velocity(x, t, target)

        sol = solve_ivp(ode, [0.0, 1.0], source, t_eval=np.linspace(0, 1, 8), rtol=1e-5)
        return sol.y[:, -1]

    def _align_vectors(a, b):
        a = np.asarray(a, dtype=float).ravel()
        b = np.asarray(b, dtype=float).ravel()
        n = min(a.size, b.size)
        if n == 0:
            return a, b
        a, b = a[:n], b[:n]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na > 1e-9:
            a = a / na
        if nb > 1e-9:
            b = b / nb
        return a, b

    def _extract_vector(obj):
        if isinstance(obj, dict):
            for key in ("embedding", "vector", "features", "score", "value"):
                if key in obj:
                    return _extract_vector(obj[key])
            vals = []
            for v in obj.values():
                if isinstance(v, (int, float)):
                    vals.append(float(v))
            return np.array(vals) if vals else np.array([0.0])
        if isinstance(obj, (list, tuple)):
            flat = []
            for v in obj:
                if isinstance(v, (int, float)):
                    flat.append(float(v))
                elif isinstance(v, (list, tuple, dict)):
                    flat.extend(_extract_vector(v).tolist())
            return np.array(flat) if flat else np.array([0.0])
        if isinstance(obj, (int, float)):
            return np.array([float(obj)])
        return np.array([0.0])

    p_vec = _extract_vector(perception_data)
    u_vec = _extract_vector(understanding_data)
    d_vec = _extract_vector(decision_data)

    p_vec, u_vec = _align_vectors(p_vec, u_vec)
    u_vec, d_vec = _align_vectors(u_vec, d_vec)

    blended = _flow_match_sample(p_vec, u_vec, steps=16)
    refined = _flow_match_integrate(blended, d_vec)

    confidence = float(np.clip(1.0 - np.linalg.norm(refined - d_vec) / (np.linalg.norm(d_vec) + 1e-6), 0.0, 1.0))

    return {
        "flow_matched_vector": refined.tolist(),
        "flow_confidence": confidence,
        "flow_source_dim": int(p_vec.size),
        "flow_target_dim": int(d_vec.size),
    }