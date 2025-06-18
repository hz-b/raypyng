import itertools

class SimulationParams:
    def __init__(self, params: list[dict]):
        self.params = params
        self.ind_par = []   # Independent parameters (str)
        self.ind_val = []   # Lists of values for each independent param
        self.dep_map = []   # Maps independent value to dependent param dict

        self._process_params()

    def _process_params(self):
        for param_dict in self.params:
            keys = list(param_dict.keys())
            main_key = keys[0]
            self.ind_par.append(main_key)
            self.ind_val.append(param_dict[main_key])

            # If other keys exist, treat them as dependent
            if len(keys) > 1:
                dep_data = []
                for i, main_val in enumerate(param_dict[main_key]):
                    dep_entry = {k: param_dict[k][i] for k in keys[1:]}
                    dep_data.append((main_val, dep_entry))
                self.dep_map.append(dict(dep_data))
            else:
                self.dep_map.append(None)

    def simulation_parameters_generator(self):
        for combo in itertools.product(*self.ind_val):
            result = {}
            for i, val in enumerate(combo):
                ind_key = self.ind_par[i]
                result[ind_key] = val

                # If there are dependent parameters, add them
                if self.dep_map[i] is not None:
                    dep_values = self.dep_map[i].get(val, {})
                    result.update(dep_values)
            yield result

# ==== Example usage ====
if __name__ == "__main__":
    params = [
        {"energy": [500, 1000]},
        {"angle": [1, 2]},
        {"slope_error": [0, 1, 2], "focus": ["A", "B", "C"]},
    ]

    sp = SimulationParams(params)
    for i, sim in enumerate(sp.simulation_parameters_generator()):
        print(f"Simulation {i+1}: {sim.items()}")

