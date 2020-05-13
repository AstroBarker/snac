# snac
Python tools for analyzing/plotting data from SuperNova Explosion Code ([SNEC](https://stellarcollapse.org/SNEC)). [1](http://adsabs.harvard.edu/abs/2015ApJ...814...63M)


# Setup

Set these shell environment variables:

* `SNAC_DIR` - path to this directory, e.g. export FLASHBANG=${HOME}/path/to/snac
* `SNEC_MODELS` - path to SNEC directory containing SNEC run directories. This can be tricky - 
each SNEC run gets its own directory (`DIR`) that houses the executable and within that is a data directory `Data`. We want to point to 
the directory conaining `DIR`

In order to import with ipython etc., append to your python path: `export PYTHONPATH=${FLASHBANG}:${PYTHONPATH}`

# Getting Started