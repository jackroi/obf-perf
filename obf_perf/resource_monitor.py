"""Resource monitor for a process.

This module provides a class to run a process and monitor its resource usage.
It requires that `/usr/bin/time` is installed.

Typical usage example:
    import resource_monitor as rm

    # create a resource monitor for the command `ls -l`
    monitor = rm.ResourceMonitor(["ls", "-l"])

    # run the process and monitor its resource usage
    monitor.run()

    # get the stdout of the process
    stdout = monitor.stdout()

    # get the wall clock time of the process
    wall_time = monitor.wall_time()

    # get the maximum memory usage of the process
    max_memory = monitor.max_memory()
"""


import os
import time
import subprocess
from typing import List


class ResourceMonitor:
    """Runs a process and monitors its resource usage."""

    # attributes:
    # - _args (List[str]): the command to run
    # - _run (bool): whether the process has been run
    # - _resource_usage (resource.struct_rusage): the resource usage
    # - _wall_time (float): the wall clock time
    #   since resource.struct_rusage does not include it
    # - _max_memory (int): the maximum memory usage
    #   since resource.struct_rusage one is not precise due to
    #   how linux kernel process creation works (fork + exec)
    # - _stdout (str): the stdout of the process
    # - _stderr (str): the stderr of the process

    def __init__(self, args: List[str], check: bool = True):
        """Initializes the resource monitor.

        Args:
            args: The command to run.
            check: Whether to raise an error if the command exits with
                a non-zero exit status code.
        """

        # validate args
        if len(args) == 0:
            raise ValueError("Error: cannot monitor an empty command")

        # copy args
        self._args = args.copy()
        self._check = check
        # set as not run
        self._run = False


    def run(self) -> int:
        """Runs the process and monitors its resource usage.

        Requires that `/usr/bin/time` is installed.

        Returns:
            The exit status code of the process.

        Raises:
            CalledProcessError: If the process exits with a non-zero
                exit status code and `check` is `True`.
        """

        # extended args for precise memory usage monitoring
        # with `/usr/bin/time`
        # the one in the resource.struct_rusage is not precise
        # due to how linux kernel process creation works (fork + exec)
        # when forking, the memory usage is preserved, so the
        # memory usage of the child process is the same as the parent
        # if the child process does not allocate more memory

        # time -f "\n%M" <command> runs <command> and prints
        # the maximum memory usage to stderr on a new line
        args = ["/usr/bin/time", "-f", "\n%M"] + self._args

        # start timer for wall clock time
        start = time.perf_counter()
        # run the process, capturing both stdout and stderr
        p = subprocess.Popen(args,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        # read stdout and stderr
        stdout_data = p.stdout.read() # type: ignore
        stderr_data = p.stderr.read() # type: ignore

        # wait for process termination and
        # get exit status code and resource usage
        _, status, resource_usage = os.wait4(p.pid, 0)

        # stop timer for wall clock time
        end = time.perf_counter()

        # check exit status code and raise error if necessary
        if self._check and status != 0:
            raise subprocess.CalledProcessError(status,
                                                args,
                                                stdout_data,
                                                stderr_data)

        # store wall clock time
        self._wall_time = end - start

        # store resource usage
        self._resource_usage = resource_usage

        # decode and store stdout and stderr
        self._stdout = stdout_data.decode("utf-8")
        self._stderr = stderr_data.decode("utf-8")

        # get memory usage from stderr (`time` output)
        stderr_lines = self._stderr.splitlines()
        self._max_memory = int(stderr_lines[-1])
        # reconstruct the original stderr (without `time` output)
        self._stderr = "\n".join(stderr_lines[:-1]) + "\n"

        # set as run
        self._run = True

        return status


    def stdout(self) -> str:
        """Gets the stdout of the process.

        Returns:
            The stdout of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._stdout


    def stderr(self) -> str:
        """Gets the stderr of the process.

        Returns:
            The stderr of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._stderr


    def wall_time(self) -> float:
        """Gets the wall clock time of the process.

        Returns:
            The wall clock time of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._wall_time;


    def user_time(self) -> float:
        """Gets the user time of the process.

        Returns:
            The user time of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._resource_usage.ru_utime


    def system_time(self) -> float:
        """Gets the system time of the process.

        Returns:
            The system time of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._resource_usage.ru_stime


    def max_memory(self) -> int:
        """Gets the maximum memory usage of the process.

        Returns:
            The maximum memory usage of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._max_memory


    def minor_page_faults(self) -> int:
        """Gets the number of minor page faults of the process.

        Returns:
            The number of minor page faults of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._resource_usage.ru_minflt


    def major_page_faults(self) -> int:
        """Gets the number of major page faults of the process.

        Returns:
            The number of major page faults of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._resource_usage.ru_majflt


    def page_faults(self) -> int:
        """Gets the number of page faults of the process.

        Returns:
            The number of page faults of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self.minor_page_faults() + self.major_page_faults()


    def swaps(self) -> int:
        """Gets the number of swaps of the process.

        Returns:
            The number of swaps of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._resource_usage.ru_nswap


    def volountary_context_switches(self) -> int:
        """Gets the number of volountary context switches of the process.

        Returns:
            The number of volountary context switches of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._resource_usage.ru_nvcsw


    def involountary_context_switches(self) -> int:
        """Gets the number of involountary context switches of the process.

        Returns:
            The number of involountary context switches of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self._resource_usage.ru_nivcsw


    def context_switches(self) -> int:
        """Gets the number of context switches of the process.

        Returns:
            The number of context switches of the process.

        Raises:
            RuntimeError: If the process has not been run.
        """

        self._ensure_run()
        return self.volountary_context_switches() \
            + self.involountary_context_switches()


    def _ensure_run(self) -> None:
        """Ensures that the process has been run.

        Raises:
            RuntimeError: If the process has not been run.
        """

        # if not run, raise an error
        if not self._run:
            raise RuntimeError("Error: cannot get usage information"
                               " before `run()` is called")
