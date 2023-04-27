import json
import statistics
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Union


@dataclass(frozen=True)
class Result:
    """Result of a single run of the benchmark."""

    name: str
    """Name of the obfuscation technique."""

    obfuscation_wall_time: float
    """Wall clock time of the obfuscation process."""

    obfuscation_user_time: float
    """User time of the obfuscation process."""

    obfuscation_system_time: float
    """System time of the obfuscation process."""

    obfuscation_memory: int
    """Maximum memory usage of the obfuscation process."""

    compile_wall_time: float
    """Wall clock time of the compilation process."""

    compile_user_time: float
    """User time of the compilation process."""

    compile_system_time: float
    """System time of the compilation process."""

    source_code_size: int
    """Size of the source code in bytes."""

    executable_size: int
    """Size of the executable in bytes."""

    lines_of_code: int
    """Number of lines of code."""

    norm_compression_distance: float
    """Normalized compression distance."""

    halstead_difficulty: float
    """Halstead difficulty metric."""

    execution_wall_time: float
    """Wall clock time of the execution process."""

    execution_user_time: float
    """User time of the execution process."""

    execution_system_time: float
    """System time of the execution process."""

    execution_memory: int
    """Maximum memory usage of the execution process."""

    execution_minor_page_faults: int
    """Number of minor page faults during the execution process."""

    execution_major_page_faults: int
    """Number of major page faults during the execution process."""

    execution_total_page_faults: int
    """Number of total page faults during the execution process."""

    execution_voluntary_context_switches: int
    """Number of voluntary context switches during the execution process."""

    execution_involuntary_context_switches: int
    """Number of involuntary context switches during the execution process."""

    execution_total_context_switches: int
    """Number of total context switches during the execution process."""


    def __getitem__(self, name: str):
        """Access the fields of the Result using the [] operator.

        Args:
            name: Name of the field to be accessed.

        Returns:
            The value of the field.
        """

        return getattr(self, name)


    @staticmethod
    def fields() -> List[str]:
        """Returns the names of the fields of the Result class.

        Returns:
            The list of names of the fields of the Result class.
        """

        return list(Result.__dataclass_fields__.keys())


class ResultContainer:
    """Container for the results of the benchmark."""

    def __init__(self):
        """Initializes the ResultContainer."""

        # dictionary that maps each obfuscation technique to a dictionary
        # containing the list of values of each metric
        # dict<name,dict<metric,list<value>>
        # example:
        # {
        #     "obf1": {
        #         "metric1": [1, 2, 3],
        #         "metric2": [4, 5, 6]
        #     },
        #     "obf2": {
        #         "metric1": [7, 8, 9],
        #         "metric2": [10, 11, 12]
        #     }
        # }
        self._results: Dict[str, Dict[str, List[Union[int, float]]]] = dict()


    def add_result(self, result: Result) -> None:
        """Adds a Result to the container.

        Args:
            result: The Result to be added.
        """

        # if the obfuscation technique has not been added yet,
        # create an empty dict for it
        if result.name not in self._results:
            # dict<metric,list<value>>
            self._results[result.name] = dict()

        # extract from the Result the list of all its key-value pairs
        # except the first one ("name")
        result_items = list(asdict(result).items())[1:]
        # for each metric-value pair, add the value to the list of values
        for metric_name, value in result_items:
            # if no list of values for the metric exists, create it (empty)
            if metric_name not in self._results[result.name]:
                self._results[result.name][metric_name] = []
            # add the value to the list of values for the metric
            self._results[result.name][metric_name].append(value)


    def metric_results(self,
                       metric_name: str) -> Dict[str, List[Union[int, float]]]:
        """Returns the results of a metric for each obfuscation technique.

        Args:
            metric_name: Name of the metric.

        Returns:
            A dictionary mapping each obfuscation technique to the list of
            values of the given metric.
        """

        # check if the metric exists
        if metric_name not in Result.fields():
            raise RuntimeError(f"Metric '{metric_name}' does not exist")

        # dictionary that maps each obfuscation technique to the list of
        # values of the given metric
        # dict<obf_name,list<value>>
        metric_results_by_obf: Dict[str, List[Union[int, float]]] = \
            { obf_name: self._results[obf_name][metric_name]
              for obf_name in self._results }

        return metric_results_by_obf


    def get_average_results(self) -> Tuple[Dict[str,
                                                Dict[str, Union[float, str]]],
                                           Dict[str,
                                                Dict[str, Union[float, str]]]]:
        """Returns the average results of the benchmark.

        Returns:
            A pair of dictionaries (avg_results, std_results) that map each
            obfuscation technique to a dictionary containing the average (and
            standard deviation) of each metric.
        """

        # dictionaries that map each obfuscation technique to a dictionary
        # containing the average (and standard deviation) of each metric
        avg_results: Dict[str, Dict[str, Union[float, str]]] = dict()
        std_results: Dict[str, Dict[str, Union[float, str]]] = dict()

        # for each obfuscation technique, compute the average and the stdev
        for obf_name, curr_results_dict in self._results.items():
            # dictionaries that map each metric to the average (and standard
            # deviation) of its values for the current obfuscation technique
            avg_result_params: Dict[str, Union[float, str]] = \
                    dict(name=obf_name)
            std_result_params: Dict[str, Union[float, str]] = \
                    dict(name=obf_name)

            # for each metric, compute the average and the standard deviation
            for metric_name, metric_result_list in curr_results_dict.items():
                if len(metric_result_list) > 1:
                    # more than one value

                    # compute the average and the standard deviation
                    avg_result_params[metric_name] = \
                            statistics.mean(metric_result_list)
                    std_result_params[metric_name] = \
                            statistics.stdev(metric_result_list)
                else:
                    # only one value

                    # the average is the value itself
                    avg_result_params[metric_name] = metric_result_list[0]
                    # the standard deviation is 0.0
                    std_result_params[metric_name] = 0.0

            # build the Result objects for the current obfuscation technique
            avg_results[obf_name] = avg_result_params
            std_results[obf_name] = std_result_params

        return avg_results, std_results


    def to_json(self):
        """Serializes the ResultContainer to JSON."""

        return json.dumps(self._results, indent=4)
