"""TODO"""

import os
# import resource
import subprocess
import time
import re


class ResourceMonitor:
    def __init__(self, args):
        self._args = args.copy()
        #self._resource_usage = None
        self._run = False
        self._wall_time = 0.0


    def __str__(self):
        pass

    def run(self):
        # extended args for precise memory usage
        args = ["/usr/bin/time", "-f", "\n%M"] + self._args

        # start timer for wall clock time
        start = time.perf_counter()
        # run the process, capturing both stdout and stderr
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # assertion for pyright
        assert p.stdout is not None
        assert p.stderr is not None
        # read stdout and stderr
        stdout_data = p.stdout.read()
        stderr_data = p.stderr.read()

        # wait for process termination and
        # get exit status code and resource usage
        _, status, resource_usage = os.wait4(p.pid, 0)

        # stop timer for wall clock time
        end = time.perf_counter()

        # store wall clock time
        self._wall_time = end - start

        # store resource usage
        self._resource_usage = resource_usage

        # TODO: think if can do better (get already decoded or error handling)
        self._stdout = stdout_data.decode("utf-8")
        self._stderr = stderr_data.decode("utf-8")


        # TODO remove time output from stderr
        # TODO understand what to do if time gives an error
        # probably check status code + regex stderr and then clean stderr,
        # and maybe raise an error, or something like that

        # exit_code = p.returncode

        ERROR_REGEX = r'(\/usr\/bin\/time: cannot run).+(No such file or directory)'

        if status == 127 and re.match(ERROR_REGEX, self._stderr):
            self._stderr = ""
            raise RuntimeError(f"Error: no such executable file '{self._args[0]}'")

        # get memory usage from stderr (`time` output)
        stderr_lines = self._stderr.split("\n")
        self._max_memory = int(stderr_lines[-2])
        # reconstruct the original stderr (without `time` output)
        self._stderr = "\n".join(stderr_lines[:-2]) + "\n"

        # set as run
        self._run = True

        return status

    def stdout(self):
        return self._stdout

    def stderr(self):
        return self._stderr

    def wall_time(self):
        self._ensure_run()
        return self._wall_time;

    def user_time(self):
        self._ensure_run()
        return self._resource_usage.ru_utime

    def system_time(self):
        self._ensure_run()
        return self._resource_usage.ru_stime

    def max_memory(self):
        self._ensure_run()
        # return self._resource_usage.ru_maxrss
        return self._max_memory

    def minor_page_faults(self):
        self._ensure_run()
        return self._resource_usage.ru_minflt

    def major_page_faults(self):
        self._ensure_run()
        return self._resource_usage.ru_majflt

    def page_faults(self):
        self._ensure_run()
        return self.minor_page_faults() + self.major_page_faults()

    def swaps(self):
        self._ensure_run()
        return self._resource_usage.ru_nswap

    def volountary_context_switches(self):
        self._ensure_run()
        return self._resource_usage.ru_nvcsw

    def involountary_context_switches(self):
        self._ensure_run()
        return self._resource_usage.ru_nivcsw

    def context_switches(self):
        self._ensure_run()
        return self.volountary_context_switches() \
            + self.involountary_context_switches()

    def _ensure_run(self):
        if not self._run:
            raise RuntimeError("Error: cannot get usage information"
                               " before `run()` is called")
