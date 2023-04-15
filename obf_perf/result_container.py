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
    execution_voluntary_context_switches: int
    execution_involuntary_context_switches: int
    execution_total_context_switches: int

    def __getitem__(self, name):
        return getattr(self, name)

    @staticmethod
    def fields():
        return list(Result.__dataclass_fields__.keys())


class ResultContainer:
    def __init__(self):
        # dict<name,dict<metric,list<value>>
        self._results = dict()

    # TODO: use snake_case instead of camel_case
    def addResult(self, result: Result):
        if result.name not in self._results:
            self._results[result.name] = dict()

        # extract a list containing all the key-value pairs except the first ("name")
        result_items = list(asdict(result).items())[1:]
        for metric, value in result_items:
            if metric not in self._results[result.name]:
                self._results[result.name][metric] = []
            self._results[result.name][metric].append(value)

    def metric_results(self, metric_name: str):
        if metric_name not in Result.fields():
            raise RuntimeError("TODO")

        metric_results_by_obf = { obf_name: self._results[obf_name][metric_name]
                                  for obf_name in self._results }

        return metric_results_by_obf



    # def getAllResults(self):
        # TODO

    #     for name in self._results:
    #         res_list = self._results[name]

    #         # list of dict
    #         res_list_asdict = [asdict(res) for res in res_list]
    #         # list of list (shape: metrics * runs)
    #         # for each metric, there is the list of runs
    #         metrics_runs = list(zip(*[d.values() for d in res_list_asdict]))

    #         avg_result_params = { key: averages[i] for i, key in enumerate(Result.__dataclass_fields__.keys())  }
    #         stdev_result_params = { key: stdevs[i] for i, key in enumerate(Result.__dataclass_fields__.keys())  }

    #         output_avg[name] = Result(**avg_result_params)
    #         output_stdev[name] = Result(**stdev_result_params)


    def getAverageResults(self):
        avg_results = dict()
        std_results = dict()

        for obf_name, curr_results_dict in self._results.items():
            avg_result_params = dict(name=obf_name)
            std_result_params = dict(name=obf_name)

            for metric_name, metric_result_list in curr_results_dict.items():
                if len(metric_result_list) > 1:
                    avg_result_params[metric_name] = \
                            statistics.mean(metric_result_list)
                    std_result_params[metric_name] = \
                            statistics.stdev(metric_result_list)
                else:
                    avg_result_params[metric_name] = metric_result_list[0]
                    std_result_params[metric_name] = 0.0
            avg_results[obf_name] = Result(**avg_result_params)
            std_results[obf_name] = Result(**std_result_params)

        return avg_results, std_results


    # TODO: maybe serialize/deserialize


