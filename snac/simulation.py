"""
Main snac class for the Simulation object.

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

"""

import os
import time
import numpy as np
import xarray as xr
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
                 reload=False, save=True, load_profiles=False):
        """Object representing a 1D flash simulation
        parameters
        ----------
        model : str
            The name of the main model directory
        config : str
            Base name of config file to use, e.g. 'snec' for 'config/snec.ini'
        output_dir : str
            name of subdirectory containing model output files
        load_all : bool
            immediately load all model data (chk profiles, dat)
        reload : bool
            force reload model data from raw files (don't load from temp/)
        save : bool
            save extracted model data to temporary files (for faster loading)
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

        self.config = None               # model-specific configuration; see load_config()
        self.dat = None                  # integrated data from .dat; see load_dat()
        self.profiles = xr.Dataset()     # radial profile data for each timestep
        self.scalars = None              # scalar quantities: time of shock breakout, plateau duration...

        # self.get_scalars()
        self.load_config(config=config)

        if load_all:
            self.load_all(reload=reload, save=save, load_profiles=load_profiles)

        t1 = time.time()
        self.printv(f'Model load time: {t1-t0:.3f} s')

    # =======================================================
    #                      Setup/init
    # =======================================================
    def printv(self, string, verbose=None, **kwargs):
        """Verbose-aware print
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
        """Load config parameters from file
        parameters
        ----------
        config : str
        """
        self.config = load.load_config(name=config, verbose=self.verbose)

    def load_all(self, reload=False, save=True, load_profiles=False):
        """Load all model data
        parameters
        ----------
        reload : bool
        save : bool
        """
        self.load_dat(reload=reload, save=save)
        if load_profiles:
            self.load_all_profiles(reload=reload, save=save)




    # =======================================================
    #                   Loading Data
    # =======================================================
    def load_dat(self, reload=False, save=True):
        """Load .dat file
        parameters
        ----------
        reload : bool
        save : bool
        """
        self.dat = load.get_dat(
                        model=self.model,
                        cols_dict=self.config['dat_quantities']['fields'], reload=reload,
                        save=save, verbose=self.verbose)

    def load_all_profiles(self, reload=False, save=True):
            """Load profiles

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