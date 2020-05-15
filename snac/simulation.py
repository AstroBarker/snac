# -------------------------------
#   ____  _   _    _    ____ 
#  / ___|| \ | |  / \  / ___|
#  \___ \|  \| | / _ \| |    
#   ___) | |\  |/ ___ \ |___ 
#  |____/|_| \_/_/   \_\____|
# -------------------------------
"""
Main SNAC class for the Simulation object.

A Simulation instance represents a single set of SNEC run.
It can load model data files, manipulate/extract that data,
and plot.

Info
-------------------
    Setup arguments
    ---------------
    model: Name of the SNEC set (i.e. the directory name).

    Data structures
    ---------------
    dat: Integrated time-series quantities found in the `.dat` files.
    profile: Lagrangian profiles as extracted from `.xg` files.
    solo_profile: Lagrangian profile taken at a particular day
    scalars: Scalar quantities, e.g., time of shock breakout. Dictionary.

"""

# ------------------
# TODO:
# fallback, ejecta mass
# get_scalars needs work for scalability
# Add plotting functionality
# ------------------

import os
import time
import numpy as np
# import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# snac
# from . import analysis
from . import load
from . import paths
# from . import plot_tools
from . import tools
from . import quantities

# TODO: 

class Simulation:
    def __init__(self, model, config='snec',
                 output_dir='Data', verbose=True, load_all=True,
                 reload=False, save=True, load_profiles=True):
        """
        Object representing a 1D flash simulation
        parameters
        ----------
        model : str
            The name of the main model directory
        config : str
            Base name of config file to use, e.g. 'snec' for 'config/snec.ini'
        output_dir : str
            name of subdirectory containing model output files
        load_all : bool
            load all model data (profiles, dat)
        reload : bool
            load from raw data, not saved pickle files (slow)
        save : bool
            save extracted data to pickle files (for faster loading)
        verbose : bool
            print information to terminal
        load_profiles : bool
            do, or do not, load mass profiles
        """
        t0 = time.time()
        self.verbose = verbose
        self.model = model

        self.model_path = paths.model_path(model=model)
        self.output_path = os.path.join(self.model_path, output_dir)

        self.config = None               # model-specific configuration; see load_config(). Dicti
        self.dat = None                  # integrated data from .dat; see load_dat()
        self.profiles = None             # mass profile data for each timestep
        self.solo_profile = None         # profile at one timestep
        self.scalars = None              # scalar quantities: time of shock breakout..

        self.load_config(config=config)

        if load_all:
            self.load_all(reload=reload, save=save, load_profiles=load_profiles)

        t1 = time.time()
        self.printv(f'Model load time: {t1-t0:.3f} s')

    # =======================================================
    #                      Setup/init
    # =======================================================
    def printv(self, string, verbose=None, **kwargs):
        """
        Verbose-aware print
        parameters
        ----------
        string : str
            string to print if verbose=True
        verbose : bool
            override self.verbose setting
        **kwargs
            args for print()
        """
        if verbose is None:
            verbose = self.verbose
        if verbose:
            print(string, **kwargs)

    def load_config(self, config='snec'):
        """
        Load config parameters from file
        parameters
        ----------
        config : str
        """
        self.config = load.load_config(name=config, verbose=self.verbose)

    def load_all(self, reload=False, save=True, load_profiles=False):
        """
        Load all model data
        parameters
        ----------
        reload : bool
        save : bool
        """
        self.load_dat(reload=reload, save=save)
        self.get_scalars()
        self.dat['time'] -= self.scalars['t_sb'] # adjust to shock breakout. 
        if load_profiles:
            self.load_all_profiles(reload=reload, save=save)
            self.get_profile_day()  

    # =======================================================
    #                   Loading Data
    # =======================================================
    def load_dat(self, reload=False, save=True):
        """
        Load .dat file
        parameters
        ----------
        reload : bool
        save : bool
        """
        self.dat = load.get_dat(
                        model=self.model,
                        cols=self.config['dat_quantities']['fields'], reload=reload,
                        save=save, verbose=self.verbose)

    def load_all_profiles(self, reload=False, save=True):
            """
            Load profiles

            parameters
            ----------
            reload : bool
            save : bool
            """
            config = self.config['profiles']

            self.profiles = load.get_profiles(
                                    model=self.model,
                                    fields=config['fields'],
                                    reload=reload, save=save, verbose=self.verbose)
                            
    def get_scalars(self):
        """
        Compute all necessary SNEC scalar quantities
        """

        config = self.config['scalars']
        self.scalars = load.get_scalars(model=self.model, var=config['fields'])


    # =======================================================
    #                   Manipulation
    # =======================================================

    def get_dat_day(self, day=50.0):
        """
        Isolate dat quantities at a specific day post shock breakout, 50 by default

        Parameters:
        day : float
        """       
        
        time = self.dat['time'] 
        ind = np.max( np.where(time <= day * 86400.) )

        for col in self.dat:
            if col == 'time': continue

            label = col + '_50'
            self.scalars[label] = self.dat[col][ind]

    def get_profile_day(self, day=0.0):
        """
        Isolate mass profiles at a specific day, move from dict to DataFrame.

        Parameters:
        -----------
        day : float
            0 indicates shock breakout. Pass -1 for initial profile.
        """

        cols = self.config['profiles']['fields']

        times = np.array([*self.profiles['rho']]) #returns dictionary keys - the times.
        # This isolates the key for the data just before [day] days.

        if (day == 0.0): # If day = 0, add some padding so we're just through shock breakout.
            t = times[np.max( np.where( times - self.scalars['t_sb'] <= day*86400. ) ) + 2]
        elif (day > 0.0):
            t = times[np.max( np.where( times - self.scalars['t_sb'] <= day*86400. ) ) + 0]
        else:
            t = times[0]

        df = pd.DataFrame()
        # All profiles in the dict contain mass as first column. Just grab from one
        df['mass'] = self.profiles['rho'][t][:,0] 
        for col in cols:
            df[col] = self.profiles[col][t][:,1]

        df.time = t / 86400 # Actual timestamp, post shock breakout.
        df.day = day        # time looking for. 

        self.solo_profile = df

    # =======================================================
    #                   Quantities
    # =======================================================

    def vel_FeII(self, day=50.0):
        """
        Compute FeII 5169 line velocity from Sobolev optical depth = 1
        """
        if (self.solo_profile.day != day):
            self.get_profile_day(day=day)

        tau = quantities.tau_sob(density = self.solo_profile['rho'], 
                                temp=self.solo_profile['temp'], 
                                X=self.solo_profile['H_1'], 
                                t_exp = 50.0 + self.scalars['t_sb']/86400)
        
        self.scalars['v_Fe'] = quantities.iron_velocity(
                                    self.solo_profile['vel'], tau_sob=tau)

    def compute_total_energy(self, day=0.0):
        """
        Compute specific total energy profile.
        Recomputes and overwrites self.solo_profile

        Parameters:
        -----------
        day : float
        """
        if (self.solo_profile.day != day):
            self.get_profile_day(day=day)

        self.solo_profile['e_tot'] = quantities.total_energy(
                                        mass=self.solo_profile['mass'],
                                        radius=self.solo_profile['radius'], 
                                        vel=self.solo_profile['vel'], 
                                        rho=self.solo_profile['rho'], 
                                        eps=self.solo_profile['eps'])
                                

    def compute_bound_mass(self, day=0.0):
        """
        Compute bound mass. See quantities.bound_mass()

        Parameters:
        -----------
        day : float
        """

        if (self.solo_profile.day != day):
            self.get_profile_day(day=day)

        self.scalars['bound_mass'] = quantities.bound_mass(
                                    e_tot=self.solo_profile['e_tot'],
                                    mass=self.solo_profile['mass'])
        
    def compute_ejecta_mass(self, day=0.0):
        """
        Compute bound mass. See quantities.bound_mass()

        Parameters:
        -----------
        day : float
        """

        if (self.solo_profile.day != day):
            self.get_profile_day(day=day)

        self.scalars['M_ej'] = quantities.ejecta_mass(
                                    e_tot = self.solo_profile['e_tot'],
                                    mass = self.solo_profile['mass']
        )







