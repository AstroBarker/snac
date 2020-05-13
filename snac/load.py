""" Functions for loading SNEC data 

Info:

"""

import os
import numpy as np
import pandas as pd
import configparser
import ast
import subprocess
import sys
import time

# snac
from . import paths
# from . import quantities
# from . import analysis
from . import tools

# TODO:

# =======================================================================
#                      Config files
# =======================================================================
def load_config(name=None, verbose=True):
    """Load .ini config file and return as dict
    parameters
    ----------
    name: str
        label of config file to load
    verbose : bool
    """
    filepath = paths.config_filepath(name=name)
    tools.printv(f'Loading config: {filepath}', verbose)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f'Config file not found: {filepath}')

    ini = configparser.ConfigParser()
    ini.read(filepath)

    config = {}
    for section in ini.sections():
        config[section] = {}
        for option in ini.options(section):
            config[section][option] = ast.literal_eval(ini.get(section, option))

    return config


# =======================================================================
#                      Dat files
# =======================================================================
def get_dat(model, cols_dict, reload=False, save=True, verbose=True):
    """Get set of integrated quantities, as contained in .dat files
    Returns : pandas.DataFrame
    parameters
    ----------
    model : str
    cols_dict : {}
        dictionary with column names and indexes (Note: 1-indexed)
    reload : bool
    save : bool
    verbose : bool
    """
    dat_table = None

    # attempt to load temp file
    if reload:
        try:
            dat_table = load_dat_cache(model=model, verbose=verbose)
        except FileNotFoundError:
            printv('dat cache not found, reloading', verbose)

    # fall back on loading raw .dat
    if dat_table is None:
        dat_table = extract_dat(model, cols_dict=cols_dict, verbose=verbose)
        if save:
            save_dat_cache(dat_table, model=model, 
                           verbose=verbose)

    return dat_table

def extract_dat(model, cols_dict, run='run', verbose=True):
    """Extract and reduce data from .dat file
    Returns : dict of 1D quantities
    parameters
    ----------
    model : str
    cols_dict : {}
        dictionary with column names and indexes (Note: 1-indexed)
    run: str
    verbose : bool
    """
    filepath = paths.dat_filepath(model=model, run=run)
    printv(f'Extracting dat: {filepath}', verbose=verbose)
    # TODO: NEED to loop over cols_dict, load all of the quantities, and form on DataFrame object
    idxs = []
    keys = []

    for key, idx_1 in cols_dict.items():
        idxs += [idx_1 - 1]  # change to zero-indexed
        keys += [key]

    return pd.read_fwf(filepath, header=None, names=['time', quantity])