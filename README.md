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

# Data Structures

The Simulation class contained four primary data structures: 
`Simulation.profiles`     : dict

`Simulation.solo_profile` : DataFrame

`Simulation.dat`          : DataFrame

`Simulation.scalars`      : DataFrame

`Simulation.profiles` contains the mass profiles loaded, as listed in `snec.ini`, for all output times. Organized by
`self.profiles['field'][timestamp][:,i]` where `i=0` is the mass profiles and `i=1` contains the field. Timestamps 
are keys and may be generally accessed by `[*self.profiles['rho]]` or your favorite method for generating a list of keys.
Example:
```python
times = [*self.profiles['rho']]
mass = self.profiles['rho'][times[0]][:,0]
density = self.profiles['rho'][times[0]][:,0]
```

`Simulation.solo_profile` is a DataFrame containing Lagrangian profiles at one time, constructed via 
`Simulation.get_profile_day(day=d)` where `day` is a time, in days, post shock breakout. Passing `-1` gives the 
initial profile. `solo_profile.time` returns the time of the profile.

`Simulation.dat` contains integrated quantities as a function of time that are written by SNEC to `.dat` files. 

`Simulation.scalars` contains a few scalar quantities such as time of shock breakout.