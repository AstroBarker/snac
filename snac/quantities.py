import numpy as np
from astropy import units as u
from astropy import constants as const

# snac
from . import tools

"""
Module for calculating physical quantities
"""

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

    # fractional ionization table
    fn = "./data/FeII_5169_eta.dat"
    rho, Temp, eta = np.loadtxt(fn, unpack=True)
    rho = np.flip(rho)
    Temp = np.flip(Temp)
    eta = np.flip(eta)

    # Iron mass fraction is nat tracked - assume it is the solar fraction of iron.
    # Should be valid in the outer parts of the star, where we will be looking later.
    X_Fe = 0.00177088 * X
    A_Fe = 56

    n_Fe = density * const.N_A.value * X_Fe / A_Fe

    # ==============================
    #    Compute ionization frac
    # ==============================

    eta_profile = np.zeros_like(density) # Initialize current eta profile as empty list
    
    for i in range( len( density ) ):
        # Eta table is for a finite range. Make sure our profiles stay within it,
        if( density[i] < np.min(rho) ):
            density[i] = np.min(rho)
        if( density[i] > np.max(rho) ):
            density[i] = np.max(rho) 
        if( temp[i] < np.min(Temp) ):
            eta_profile[i] = 0.0
            continue
        if( temp[i] > np.max(Temp) ):
            temp[i] = np.max(Temp)     
        ind_r = np.min(np.where( rho <= float(density[i]) )[0] ) 
        
        temps = Temp[ np.where( rho == rho[ind_r] ) ]
        
        ind_T = np.min(np.where( temps <= float(temp[i]) )[0] ) 
        
        eta_index = np.intersect1d( np.where(rho == rho[ind_r]), np.where(Temp == temps[ind_T]) )[0]
        eta_profile[i] = eta[eta_index]

    # ==============================
    #    Compute tau_sob
    # ==============================

    tau_sob = ( (np.pi * q_e**2)/(m_e * c) ) * n_Fe * f * t_exp * lambda_0 * eta_profile

    return tau_sob

def iron_velocity(vel, tau_sob):
    """
    Compute the velocity of the FeII 5169 line by finding where 
    the Sobolev optical depth = 1

    Parameters:
    -----------
    vel : np.array
    tau_sob : np.array
    """

    n = int(len(vel)/2) # Half the array, to just look in the outer part of the star
    tau_1_ind = np.argmin(abs( tau_sob[n:] - 1.0 ) ) + n    
        
    v_FeII = vel[tau_1_ind]/1e5
    if( vel[tau_1_ind]/1e5 < 1000):
        print(f"This velocity of {vel[tau_1_ind]/1e5} km/s is suspiciously low. \n")

    return v_FeII
        
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