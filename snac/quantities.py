import numpy as np
from astropy import units as u
from astropy import constants as const
import os

# snac
from . import tools
from . import paths

"""
Module for calculating physical quantities
"""

msun = const.M_sun.cgs.value

def tau_sob(density, temp, X, t_exp):
    """
    Compute Sobolev optical depth profile for FeII 5169. See README for some details.
    
    Parameters:
    -----------
    density : np.array
    temperature : np.array
    X : np.array
        Hydrogen mass fraction
        All are profiles at a specific time, from SNEC output.
    t_exp : float
        time since explosion. Time of profiles + t_sb. Days.
    """

    m_e = const.m_e.cgs.value
    c = const.c.cgs.value
    q_e = const.e.gauss.value
    f = 0.023
    lambda_0 = (5169 * u.Angstrom).to('cm').value
    t_exp *= 86400
    A_Fe = 56

    # fractional ionization table
    fn = os.path.join(paths.data_path(), 'FeII_5169_eta.dat')
    rho, Temp, eta = np.loadtxt(fn, unpack=True)
    rho = np.flip(rho)
    Temp = np.flip(Temp)
    eta = np.flip(eta)

    # Iron mass fraction is nat tracked - assume it is the solar fraction of iron.
    # Should be valid in the outer parts of the star, where we will be looking later.
    X_Fe = 0.0016912 * X

    n_Fe = density * const.N_A.value * X_Fe / A_Fe

    # ==============================
    #    Compute ionization frac
    # ==============================

    eta_profile = np.zeros_like(density) # Initialize current eta profile as zeros
    
    for i in range( len( density ) ):
        # Eta table is for a finite range. Make sure our profiles stay within it,
        if( density[i] < np.min(rho) ):
            eta_profile[i] = 0.0
            continue
        if( density[i] > np.max(rho) ):
            # density[i] = np.max(rho) 
            eta_profile[i] = 0.0
            continue
        if( temp[i] < np.min(Temp) ):
            eta_profile[i] = 0.0
            continue
        if( temp[i] > np.max(Temp) ):
            # temp[i] = np.max(Temp)  
            eta_profile[i] = 0.0
            continue   
        if( temp[i] == np.max(Temp) and density[i] == np.max(rho) ):
            eta_profile[i] = 0 #8.68775e-05
            continue
        #ind_r = np.where( rho <= float(density[i]) )
        # This selects all indices with rho_table = rho_snec
        # Not necessarily finding "closest" density value
        diff = np.abs( rho - float(density[i]) )
        ind_min = diff.argmin()
        # ind_r = np.where( rho == rho[np.min(np.where( rho <= float(density[i]) ))] )
        ind_r = np.where( rho == rho[ind_min] )
        
        temps = Temp[ ind_r ] 
        
        ind_T = np.min(np.where( temps <= float(temp[i]) ) ) + ind_r[0][0]
        # ind_T = np.where( Temp <= float(temp[i]))
        # print(density[i], temp[i], eta[ind_T])
        
        # eta_index = np.intersect1d( np.where(rho == rho[ind_r]), np.where(Temp == Temp[ind_T]) )#[0]
        # print(eta_index)
        eta_profile[i] = eta[ind_T]

    # ==============================
    #    Compute tau_sob
    # ==============================

    tau_sob = ( (np.pi * q_e**2)/(m_e * c) ) * n_Fe * f * t_exp * lambda_0 * eta_profile

    return tau_sob

def iron_velocity(vel, tau_sob):
    """
    Compute the velocity of the FeII 5169 line by finding where 
    the Sobolev optical depth = 1

    If tau_sob !> 0 anywhere (likely because it is 0 zerowhere -- see above) 
    then it is returned as -1 and vel_Fe is set to 0. This is the case where 
    our rho, temp was not on the provided eta table.

    Parameters:
    -----------
    vel     : np.array
    tau_sob : np.array
    """

    n = int(len(vel)/4) # Half the array, to just look in the outer part of the star
    
    try:    
        tau_1_ind = np.max( np.where( tau_sob > 1.0 ) )
    except:
        tau_1_ind = -1

    if tau_1_ind > 0:

        v_FeII = vel[tau_1_ind]/1e5
        if( vel[tau_1_ind]/1e5 < 1000):
            print(f"This velocity of {vel[tau_1_ind]/1e5} km/s is suspiciously low. \n")

        return v_FeII

    else:
        return 0.0
        
def total_energy(mass, radius, vel, rho, eps):
    """
    Compute the total energy profile at a given time.
    rho * (vel**2 + eps - grav); grav = G * mass / radius

    Parameters:
    -----------
    mass   : DataFrame
    radius : DataFrame
    vel    : DataFrame
    rho    : DataFrame
    eps    : DataFrame
    """

    grav = const.G.cgs.value * mass / radius

    return rho * ( vel**2 + eps - grav ) 

def get_energy_boundary(e_tot):
    """
    Return the index where the total energy profile from total_energy()
    swaps from negative to positive in the core.

    Notice: may return garbage if solo_profile is before shock breakout as the 
    envelope is not yet unbound.

    Parameters:
    -----------
    e_tot : pd.DataFrame
        self.solo_profile['e_tot']

    Return:
    -------
    indx: corresponds to the first cell that is unbound.
    """

    try:
        return int( np.max( np.where( e_tot < 0.0 ) ) + 1 )
    except:
        return None

def bound_mass(e_tot, mass):
    """
    Compute the amount of mass in the core still gravitationally 
    bound at a given solo_profile. In solar masses.

    Parameters:
    -----------
    e_tot : pd.DataFrame
    mass  : pd.DataFrame
        e.g., self.solo_profile['e_tot']
    """

    indx = get_energy_boundary(e_tot)

    if indx is None:
        return 0.0
    else:
        return mass[indx-1] / msun

def ejecta_mass(e_tot, mass):
    """
    Compute the mass of the ejecta for a given solo_profile.
    In solar masses.

    Parameters:
    -----------
    e_tot : pd.DataFrame
    mass  : pd.DataFrame
        e.g., self.solo_profile['e_tot']
    """

    indx = get_energy_boundary(e_tot)
    n = len(mass) - 1

    return (mass[n] - mass[indx]) / msun
