<h1 align="center">obf-perf</h1>

<p align="center">
  <a href="" rel="noopener">
  <img height=200px src="https://i.imgur.com/td9cg4V.png" alt="obf-perf project logo"></a>
</p>

<div align="center">

  [![GitHub last commit](https://img.shields.io/github/last-commit/jackroi/obf-perf?style=for-the-badge)](https://github.com/jackroi/obf-perf/commits/master)
  [![GitHub issues](https://img.shields.io/github/issues/jackroi/obf-perf?style=for-the-badge)](https://github.com/jackroi/obf-perf/issues)
  [![GitHub](https://img.shields.io/github/license/jackroi/obf-perf?style=for-the-badge)](/LICENSE)

</div>

---

<p align="center">A tool to compare obfuscation methods.</p>

## 📝 Table of Contents
- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Built Using](#built_using)
- [Authors](#authors)

TODO: add an example output (table, json, plots)

## 🧐 About <a name = "about"></a>

The `obf-perf` tool is designed to compare different obfuscation
methods for software programs. In particular it aims to evaluate
and analyze the performance of the various obfuscation techniques.

With `obf-perf`, the original program is compared with several other
obfuscated versions of it, and a range of metrics are gathered, such as
time, memory, page faults, Halstead difficulty, and more. The results are
then presented in a graphical format to provide a clear and intuitive
comparison of the various obfuscation techniques used. Ultimately,
the goal of `obf-perf` is to provide software developers with valuable
insights into the effectiveness of different obfuscation techniques,
allowing them to make informed decisions on how best to protect their
code from malicious attacks.

This project was developed for the "Software Security" course of the
Computer Science master degree programme of Ca' Foscari University of Venice.

## 🏁 Getting Started <a name = "getting_started"></a>

### Prerequisites
The obf-perf project has a few dependencies that must be installed to
ensure its proper functioning. These dependencies include:
- [`Python` (3.8)](https://www.python.org/)
- [`tigress` (3.3.2)](https://tigress.wtf/)
- [`gcc`](https://gcc.gnu.org/)
- [`ctags`](https://github.com/universal-ctags/ctags)
- [`GNU time`](https://www.gnu.org/software/time/)

which are all essential components for running the tool.
Additionally, the project also requires some Python packages to be
installed, listed in the requirements.txt file.
Tigress is a critical dependency as it is used to generate the
obfuscated versions of the code under analysis.
Gcc is necessary for compiling the C code.
Ctags is used as a parser for the C code to compute some code metrics.
Finally, the GNU time program is used to measure the execution
peak memory usage of the program, that could not be measured
precisely using Python.

Therefore, ensuring that all the dependencies are installed correctly
is crucial for running `obf-perf` effectively.

### Installing
Download the project from GitHub and install the required Python packages
(a virtual environment is recommended)
using the following command (from the project root directory):

```bash
python3 -m pip install -r requirements.txt
```

To check if the installation was successful, run the following command:

```bash
python3 obf_perf.py -h
```


## 🎈 Usage <a name="usage"></a>
The `obf-perf` tool is designed to compare the effectiveness of different
obfuscation methods for a given C source code.
The tool takes as input the source code to obfuscate, as well as
a list of obfuscation configurations or a folder containing them.
It provides several optional arguments such as the output directory,
output format, number of runs, number of warmups, and optimization level.

For example, to compare three different obfuscation configurations
for a C program named "myprogram.c", you could run the following command:

```bash
obf-perf.py myprogram.c obf_config1.txt obf_config2.txt obf_config3.txt
```

To plot the results, use the `-p` option:

```bash
obf-perf.py myprogram.c obf_config1.txt obf_config2.txt obf_config3.txt -p
```

The tool supports different output formats, which can be specified using
the `-f` option. For example, to output the results in JSON format, use:

```bash
obf-perf.py myprogram.c obf_config1.txt obf_config2.txt obf_config3.txt -f json
```

The `-r` argument specifies the number of times the program is run to
gather performance metrics. By default, it is set to 1. For example,
to run the program 5 times, you can use the following command:

```bash
obf-perf.py myprogram.c obf_config1.txt obf_config2.txt obf_config3.txt -r 5
```

The `-w` argument specifies the number of times the program is run
before performing the actual analysis. This is useful for warming up
the program and ensuring that the results are not skewed by any initial
overhead. By default, it is set to 0. For example, to run the program
10 times for warming up before performing the actual analysis, you can
use the following command:

```bash
obf-perf.py myprogram.c obf_config1.txt obf_config2.txt obf_config3.txt -w 10
```

It is important to note that increasing the number of runs and warmups
can significantly increase the total runtime of the tool. Therefore,
it is recommended to use these options judiciously and consider the
trade-off between accuracy and runtime.

### Obfuscation configuration files
The obfuscation configurations utilized in `obf-perf` are formatted as
Tigress obfuscator commands, specifying desired transformations and
associated parameters. These configurations are stored in separate
text files, each representing a specific obfuscation setup. `obf-perf`
interprets these files and transfers the required parameters to Tigress
for the obfuscation process.

To create an obfuscation config for `obf-perf`, you can start by examining
an existing Tigress command script or shell script that performs the
desired obfuscation. Remove the `--out` and `source_code` parameters
from the Tigress command, as `obf-perf` handles these internally. You
can then take the remaining Tigress parameters and options and structure
them in a configuration file.

For example, let's say you have a Tigress command in a shell script named
`obfuscate.sh`:

```bash
tigress \
  --Environment=x86_64:Linux:Gcc:4.6 \
  --Transform=Virtualize \
    --Functions=sort \
    --VirtualizeDispatch=direct \
    --out=obf.c \
    myprogram.c
```

To convert this into an `obf-perf` obfuscation config, you can create
simply remove the last two lines, and you're left with a perfectly valid
`obf-perf` configuration file:

```bash
tigress \
  --Environment=x86_64:Linux:Gcc:4.6 \
  --Transform=Virtualize \
    --Functions=sort \
    --VirtualizeDispatch=direct
```

The line breaks (and indentation) are not required for `obf-perf` and
can be omitted, but are recommended for readability.
Backslashes are not required as well, but are useful if you
want to convert in a fast way configurations from and to shell scripts.

For more details about the available transformations and their parameters,
you can refer to the Tigress website or documentation. The Tigress website
provides comprehensive information about the transformations supported
by Tigress and their respective parameters, allowing you to explore and
experiment with various obfuscation techniques and configurations.


## ⛏️ Built Using <a name = "built_using"></a>
- [Python](https://www.python.org/) - Programming Language
- [`matplotlib`](https://matplotlib.org/) - Plotting Library
- [`prettytable`](https://github.com/jazzband/prettytable) - ASCII Tables Library

## ✍️ Authors <a name = "authors"></a>
- [@jackroi](https://github.com/jackroi) - Idea & Initial work

See also the list of
[contributors](https://github.com/jackroi/obf-perf/contributors) who
participated in this project.
