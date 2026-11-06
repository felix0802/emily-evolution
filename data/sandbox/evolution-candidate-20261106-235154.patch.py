# Auto-generated code snippet by Emily Self-Modify
# Based on: 潜在智能体群体进化, 可运行研究世界构建
# Generated: 2026-11-06T23:51:54.173571

def evolve_population_agents(self, population_size=8, generations=3, mutation_rate=0.15):
    import random, copy, json
    def _score(agent):
        try:
            return float(agent.get("fitness", 0.0)) + random.uniform(0, 1e-6)
        except Exception:
            return 0.0
    def _mutate(agent):
        child = copy.deepcopy(agent)
        traits = child.setdefault("traits", {})
        for key in list(traits.keys()):
            if random.random() < mutation_rate:
                val = traits[key]
                if isinstance(val, (int, float)):
                    traits[key] = val * random.uniform(0.85, 1.15)
                elif isinstance(val, str):
                    traits[key] = val + random.choice(["_v2", "_alt", "_x"])
        child["fitness"] = 0.0
        child["generation"] = agent.get("generation", 0) + 1
        return child
    def _crossover(a, b):
        child = copy.deepcopy(a)
        for key, val in b.get("traits", {}).items():
            if random.random() < 0.5:
                child.setdefault("traits", {})[key] = copy.deepcopy(val)
        child["fitness"] = 0.0
        child["generation"] = max(a.get("generation", 0), b.get("generation", 0)) + 1
        return child
    population = self.state.setdefault("agent_population", [])
    while len(population) < population_size:
        population.append({"traits": {"exploration": random.random(), "exploitation": random.random(), "curiosity": random.random()}, "fitness": 0.0, "generation": 0})
    for gen in range(generations):
        population.sort(key=_score, reverse=True)
        survivors = population[: max(2, population_size // 2)]
        offspring = []
        while len(survivors) + len(offspring) < population_size:
            if random.random() < 0.5 and len(survivors) >= 2:
                a, b = random.sample(survivors, 2)
                offspring.append(_crossover(a, b))
            else:
                offspring.append(_mutate(random.choice(survivors)))
        population = survivors + offspring
        for agent in population:
            agent["fitness"] = self._evaluate_agent_fitness(agent) if hasattr(self, "_evaluate_agent_fitness") else random.random()
    population.sort(key=_score, reverse=True)
    self.state["agent_population"] = population
    self.state["best_agent"] = population[0] if population else {}
    try:
        self.logger.info("population evolved: best=%s", json.dumps(self.state["best_agent"].get("traits", {})))
    except Exception:
        pass
    return self.state["best_agent"]