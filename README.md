# snac
Python tools for analyzing/plotting data from SuperNova Explosion Code ([SNEC](https://stellarcollapse.org/SNEC)). [1](http://adsabs.harvard.edu/abs/2015ApJ...814...63M)


# Setup

Set these shell environment variables:

* `SNAC_DIR` - path to this directory, e.g. export FLASHBANG=${HOME}/path/to/snac
* `SNEC_MODELS` - path to SNEC directory containing SNEC run directories. This can be tricky - 
each SNEC run gets its own directory (`DIR`) that houses the executable and within that is a data directory `Data`. We want to point to 
the directory conaining `DIR`

In order to import with ipython etc., append to your python path: `export PYTHONPATH=${SNAC_DIR}:${PYTHONPATH}`

# Getting Started
The Simulation class contains tools to mediate the loading/manipulation of data. Each class represents a single SNEC run.
`snac` assumes that the output is organized as follow, from `$SNEC_MODELS`:
```
$SNEC_MODELS
├── mass1
│   ├── Data
│       ├── C_init_frac.dat
│       ├── E_shell.xg
│       ├── H_1.xg
│            ...
├── mass2
│   ├── Data
│   │   ├── C_init_frac.dat
│   │   ├── E_shell.xg
│   │   ├── H_1.xg
│   │   ├── H_2.xg
│   │   ├── H_init_frac.dat
│   │   ├── He_1.xg
```

You can construct the Simulation object in using:
```
import snac

data = snac.simulation.Simulation(model='mass1', 
                                      output_dir='Data')
```
Where `model` is the name of the SNEC run directory, and `output` is the name of the output directory containing the data.

Note: Loading mass profiles for a large number of SNEC runs is quite slow in the current implementation, particularly 
for the first time, before pickle'd copies have been made.