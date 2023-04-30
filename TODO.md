# TODO

- Probably remove psutil from requirements.txt
- Maybe split table if too big (and thus also transposing it)
- Find a way to write the unit of measurement (probably in the name column)
- Sort results in a nice way
- Execute non obfuscated version
- Compute some code metrics using tigress SoftwareMetrics transformation

- Probably unify sorting function across several files with a single name `sort`
 (so can target just that with obfuscation)

- Maybe a flag to use the gcc -O3 optimization

- Catch Keyboard interrupt (CTRL-C)
- snake_case
- Maybe logging ???
- Try on macos ???

- Comments
- Readme
- Some prepared example output
- Typings

- doc strings: use third person

- Maybe try `perf` for cache hit/miss
- Probably catch some exception from clin (main) (eg: OSError)

- Probably transform bytes (B) in KB
- Probably legend on the left


Dependencies
- requirements.txt
- tigress
- gcc
- ctags
- time
