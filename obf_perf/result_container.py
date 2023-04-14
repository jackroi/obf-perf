from dataclasses import dataclass, asdict
import statistics


@dataclass(frozen=True)
class Result:
    # class Builder:
    #     def __init__(self, name):
    #        pass

    name: str
    obfuscation_wall_time: float
    obfuscation_user_time: float
    obfuscation_system_time: float
    obfuscation_memory: int
    compile_wall_time: float
    compile_user_time: float
    compile_system_time: float
    source_code_size: int
    executable_size: int
    lines_of_code: int
    compression_metric: float
    execution_wall_time: float
    execution_user_time: float
    execution_system_time: float
    execution_memory: int
    execution_minor_page_faults: int
    execution_major_page_faults: int
    execution_total_page_faults: int
    executable_voluntary_context_switches: int
    executable_involuntary_context_switches: int
    executable_total_context_switches: int


class ResultContainer:
    def __init__(self):
        self._results = dict()

    # TODO: use snake_case instead of camel_case
    def addResult(self, result: Result):
        if result.name not in self._results:
            self._results[result.name] = []

        self._results[result.name].append(result)

    def getAverageResults(self):
        output_avg = dict()
        output_stdev = dict()

        for name in self._results:
            res_list = self._results[name]

            # list of dict
            res_list_asdict = [asdict(res) for res in res_list]
            # list of list (shape: metrics * runs)
            # for each metric, there is the list of runs
            metrics_runs = list(zip(*[d.values() for d in res_list_asdict]))

            averages = [name] + [ statistics.mean(runs) for runs in metrics_runs[1:] ]
            stdevs = [name] + [ statistics.stdev(runs) for runs in metrics_runs[1:] ]

            avg_result_params = { key: averages[i] for i, key in enumerate(Result.__dataclass_fields__.keys())  }
            stdev_result_params = { key: stdevs[i] for i, key in enumerate(Result.__dataclass_fields__.keys())  }

            output_avg[name] = Result(**avg_result_params)
            output_stdev[name] = Result(**stdev_result_params)

        return output_avg, output_stdev




            # TODO: trasform the list back to a Result object
            # TODO: check if easier way of transposing a dictionary




        # res = { name:  for name in range(3) }

        # return a dict with a result obj with averages



    # TODO: maybe serialize/deserialize


