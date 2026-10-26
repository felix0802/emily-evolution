# Auto-generated code snippet by Emily Self-Modify
# Based on: 语言引导的室内场景生成, 统一动作条件世界模型
# Generated: 2026-10-26T02:01:48.389656

def _enhance_scene_world_model(perception, llm, decision, action, verify):
    import json, math, random
    from collections import defaultdict

    def _lang_guided_scene(desc, constraints):
        tokens = [t for t in desc.lower().split() if len(t) > 2]
        rooms = defaultdict(lambda: {"objects": [], "affordances": set()})
        for tok in tokens:
            if tok in ("kitchen", "bedroom", "living", "bathroom", "office"):
                rooms[tok]["objects"].append("anchor")
            elif tok in ("table", "chair", "sofa", "bed", "shelf", "lamp"):
                rooms["living"]["objects"].append(tok)
                rooms["living"]["affordances"].add(f"use_{tok}")
        for c in constraints:
            if "avoid" in c and "clutter" in c:
                for r in rooms.values():
                    r["objects"] = list(dict.fromkeys(r["objects"]))[:8]
        return {k: {"objects": v["objects"], "affordances": sorted(v["affordances"])}
                for k, v in rooms.items()}

    def _unified_action_world(state, action_vec, horizon=3):
        traj = []
        s = dict(state)
        for t in range(horizon):
            a = action_vec[t] if t < len(action_vec) else action_vec[-1]
            s["x"] = s.get("x", 0.0) + a.get("dx", 0.0)
            s["y"] = s.get("y", 0.0) + a.get("dy", 0.0)
            s["energy"] = max(0.0, s.get("energy", 1.0) - abs(a.get("dx", 0)) * 0.05)
            s["t"] = t
            traj.append(dict(s))
        return traj

    try:
        scene_desc = perception.get("scene_description", "") if isinstance(perception, dict) else ""
        constraints = perception.get("constraints", []) if isinstance(perception, dict) else []
        scene_graph = _lang_guided_scene(scene_desc, constraints)

        action_vec = decision.get("action_vector", []) if isinstance(decision, dict) else []
        if not action_vec:
            action_vec = [{"dx": random.uniform(-0.2, 0.2), "dy": random.uniform(-0.2, 0.2)}]
        world_traj = _unified_action_world(decision.get("state", {}), action_vec)

        plan = {
            "scene_graph": scene_graph,
            "world_trajectory": world_traj,
            "feasible": all(p.get("energy", 1.0) >= 0 for p in world_traj),
        }
        if isinstance(decision, dict):
            decision["enhanced_plan"] = plan
        if isinstance(action, dict):
            action["scene_graph"] = scene_graph
            action["world_trajectory"] = world_traj
        if isinstance(verify, dict):
            verify["scene_world_consistency"] = plan["feasible"]
        return plan
    except Exception as e:
        return {"error": str(e), "feasible": False}

_enhance_scene_world_model(perception, llm, decision, action, verify)