""" 
Functions for loading SNEC data 

Info:

"""

import os
import numpy as np
import pandas as pd
import pickle
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
def get_dat(model, cols, reload=False, save=True, verbose=True):
    """Get set of integrated quantities, as contained in .dat files
    Returns : pandas.DataFrame
    parameters
    ----------
    model : str
    cols : {}
        dictionary with column names and indexes (Note: 1-indexed)
    reload : bool
    save : bool
    verbose : bool
    """
    dat_table = None

    # attempt to load temp file
    if not reload:
        try:
            dat_table = load_dat_cache(model=model, verbose=verbose)
        except FileNotFoundError:
            tools.printv('dat cache not found, manually loading', verbose)

    # fall back on loading raw .dat
    if dat_table is None:
        dat_table = extract_dat(model, cols=cols, verbose=verbose)
        if save:
            save_dat_cache(dat_table, model=model, 
                           verbose=verbose)

    return dat_table

def extract_dat(model, cols, verbose=True):
    """Extract data from .dat file
    Returns : dataFrame of 1D quantities
    parameters
    ----------
    model : str
    cols : []
        list with column names
    run: str
    verbose : bool
    """
 
    df = pd.DataFrame()

    i = 0
    for key in cols:
        filepath = paths.dat_filepath(model=model, quantity=key)
        tools.printv(f'Extracting dat: {filepath}', verbose=verbose)

        if (key == 'conservation'):
            df_temp1 = pd.read_fwf(filepath, header=None, \
                names=['time', 'Egrav', 'Eint', 'Ekin', 'Etot', 'EtotmInt'])
            df_temp1 = df_temp1.drop(columns='EtotmInt')
            for col in df_temp1:
                df[col] = df_temp1[col]
        else:        
            df_temp = pd.read_fwf(filepath, header=None, names=['time', key])

            df[key] = df_temp[key]
        i += 1

    if ('conservation' in cols): # drop last row: no energy data written in last timestep.
        # df = df.drop(df.tail(1).index,inplace=True)
        return df[:-1]
    else:
        return df

def save_dat_cache(dat, model, verbose=True):
    """Save pre-extracted .dat quantities, for faster loading
    parameters
    ----------
    dat : pd.DataFrame
        data table as returned by extract_dat()
    model : str
    run : str
    verbose : bool
    """
    ensure_temp_dir_exists(model, verbose=False)
    filepath = paths.dat_temp_filepath(model=model)

    tools.printv(f'Saving dat cache: {filepath}', verbose)
    dat.to_pickle(filepath)


def load_dat_cache(model, verbose=True):
    """Load pre-extracted .dat quantities (see: save_dat_cache)
    parameters
    ----------
    model : str
    run : str
    verbose : bool
    """
    filepath = paths.dat_temp_filepath(model=model)
    tools.printv(f'Loading dat cache: {filepath}', verbose)
    return pd.read_pickle(filepath)    

# ===============================================================
#                      Profiles
# ===============================================================
def get_profiles(model, fields, reload=False, save=True, verbose=True):
    """Get set of integrated quantities, as contained in .dat files
    Returns : pandas.DataFrame
    parameters
    ----------
    model   : str
    fields  : []    
    reload  : bool
    save    : bool
    verbose : bool
    """
    dat_table = None

    # attempt to load temp file
    if not reload:
        try:
            dat_table = load_profile_cache(model=model, verbose=verbose)
        except FileNotFoundError:
            tools.printv('profile cache not found, manually loading', verbose)

    # fall back on loading raw .xg
    if dat_table is None:
        dat_table = extract_profile(model, fields=fields, verbose=verbose)
        if save:
            save_profile_cache(dat_table, model=model, 
                           verbose=verbose)

    return dat_table

def extract_profile(model, fields, verbose=True):
    """Extract data from .xg file
    Returns : dict of 1D quantities
    parameters
    ----------
    model : str
    fields : []
        dictionary with column names
    run: str
    verbose : bool
    """
 
    df = {}

    for key in fields:
        filepath = paths.profile_filepath(model=model, quantity=key)
        tools.printv(f'Extracting profile: {filepath}', verbose=verbose)

        df[key] = xg_to_dict(filepath)

    return df

def save_profile_cache(dat, model, verbose=True):
    """Save pre-extracted .xg quantities, for faster loading
    parameters
    ----------
    dat : dict
        data as returned by extract_profile()
    model : str
    run : str
    verbose : bool
    """
    ensure_temp_dir_exists(model, verbose=False)
    filepath = paths.profile_temp_filepath(model=model)

    tools.printv(f'Saving profile cache: {filepath}', verbose)

    pickle.dump( dat, open( filepath, "wb" ) )

def load_profile_cache(model, verbose=True):
    """Load pre-extracted .xg quantities (see: save_dat_cache)
    parameters
    ----------
    model : str
    run : str
    verbose : bool
    """
    filepath = paths.profile_temp_filepath(model=model)
    tools.printv(f'Loading profile cache: {filepath}', verbose)
    return pickle.load( open(filepath, 'rb') )

def xg_to_dict(fn):
    """
    Function to parse SNEC .xg files into dictionaries
    Slow.

    Parameters:
    -----------
    fn : str
    """
    dd = {}

    with open(fn, 'r') as rf:
        for line in rf:
            cols = line.split()
            # Beginning of time data - make key for this time                                                         
            if 'Time' in line:
                time = float(cols[-1])
                dd[time] = []
            # In time data -- build x,y arrays                                                                        
            elif len(cols)==2:
                dd[time].append(np.fromstring(line, sep=' '))
            # End of time data (blank line) -- make list into array                                                   
            else:
                dd[time] = np.array(dd[time])

    return dd

# =======================================================================
#                      Scalars
# =======================================================================

def get_scalars(model, var):
    """
    Get various SNEC scalar outputs. Needs work for scalability.

    Parameters:
    -----------
    model : str
    var : []
    """

    if ('M_preSN' in var or 't_sb' in var):
        m_preSN, tsb = get_info(model, var)
    if ('zams' in var or 'masscut' in var):
        zams, masscut = get_params(model, var)
     
    df = {}
    if 'masscut' in var: df['masscut'] = float(masscut)
    if 't_sb' in var: df['t_sb'] = float(tsb)
    if 'M_preSN' in var: df['M_preSN'] = float(m_preSN)
    if 'zams' in var: df['zams'] = float(zams) # Specific to a profile naming scheme. 

    return df

def get_params(model, var):
    """ Get information from SNEC parameters file. """
    # TODO: add options to config file to specify what to get here.

    fn = os.path.join(paths.output_path(model), 'parameters')
    with open(fn, "r") as f:
        for myline in f:
            # Find the line starting with mass_excised, split it at the '='
            if('masscut' in var and "mass_excised" in myline ):
                masscut = myline.split("= ")[1]

            # This is specific to how we name our profiles. s9.0_hydro.....
            if('zams' in var and myline[0:13] == ' profile_name' ):
                profile = myline.split("= ")[1]
                zams = (profile.split("_")[0]).split("s")[2]

            if ('zams' not in var): zams = '0.0'
            if ('masscut' not in var): masscut = '0.0'

    return zams.strip("\n"), masscut.strip("\n").split(" ")[0]

def get_info(model, var):
    """
    Extract information from info.dat
    """

    fn = os.path.join(paths.output_path(model), 'info.dat')

    with open(fn, "r") as f:
        for myline in f:
            if( myline[0:5] == ' Mass'):
                mass = myline.split("= ")[1]

            if( myline[0:17] == ' Time of breakout'):
                tsb = myline.split("= ")[1]
        tsb = tsb.split(" ")[3]
        mass = mass.split(" ")[3]

    return mass, tsb

# ===============================================================
#              Misc. file things
# ===============================================================
def try_mkdir(path, skip=False, verbose=True):
    """Try to make given directory
    parameters
    ----------
    path: str
    skip : bool
        do nothing if directory already exists
        if skip=false, will ask to overwrite an existing directory
    verbose : bool
    """
    tools.printv(f'Creating directory  {path}', verbose)
    if os.path.exists(path):
        if skip:
            tools.printv('Directory already exists - skipping', verbose)
        else:
            print('Directory exists')
            cont = input('Overwrite? (y/[n]): ')

            if cont == 'y' or cont == 'Y':
                subprocess.run(['rm', '-r', path])
                subprocess.run(['mkdir', path])
            elif cont == 'n' or cont == 'N':
                sys.exit()
    else:
        subprocess.run(['mkdir', '-p', path], check=True)


def ensure_temp_dir_exists(model, verbose=True):
    """Ensure temp directory exists (create if not)
    parameters
    ----------
    model : str
    verbose : bool
    """
    temp_path = paths.temp_path(model)
    try_mkdir(temp_path, skip=True, verbose=verbose)    