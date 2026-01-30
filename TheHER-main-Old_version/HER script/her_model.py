"""
Hydrogen Evolution Reaction (HER) Fitting Model Module

This module provides functions for fitting and analyzing HER electrochemical data
using simplified and full model approaches with surface coverage calculations.

Author: Your Name
License: MIT
"""

import numpy as np
import pandas as pd
from scipy import stats


# Physical Constants
FARADAY_CONSTANT = 96485.3  # C/mol


def rnd():
    """
    Generate random initial parameter in scientific notation.
    
    Returns:
        float: Random value between 1e-15 and 1e-4
    """
    import random
    exp1 = random.randint(-15, -4)
    significand = round(random.uniform(0.1, 9), 2)
    return significand * 10 ** exp1


def HER_simplified_fitting(x, k1, k1r, k2, k2r, bbv, bbh, f1_val):
    """
    Calculate current using simplified HER model (2-step mechanism).
    
    Model: H+ + e- ⇌ H_ads (step 1)
           H_ads + H+ + e- → H2 (step 2)
    
    Parameters
    ----------
    x : array_like
        Potential values (V)
    k1 : float
        Forward rate constant for step 1 (A/cm²)
    k1r : float
        Reverse rate constant for step 1 (A/cm²)
    k2 : float
        Forward rate constant for step 2 (A/cm²)
    k2r : float
        Reverse rate constant for step 2 (A/cm²)
    bbv : float
        Symmetry factor for step 1 (0-1)
    bbh : float
        Symmetry factor for step 2 (0-1)
    f1_val : float
        Normalized Faraday constant (F/RT)
    
    Returns
    -------
    array_like
        Calculated current density (A/cm²)
    """
    vtotal = 2 * (((k1*k2*(1 - np.e**(2*f1_val*x)))*np.e**(-bbh*x*f1_val)) / 
                   (k1*np.e**((bbh - bbv)*f1_val*x) + k2 + np.e**(f1_val*x)*
                   (k1r*np.e**((bbh - bbv)*f1_val*x) + k2r)))
    return -FARADAY_CONSTANT * vtotal


def Theta_VH(x, k1, k1r, k2, k2r, bbv, bbh, f1_val=38.92):
    """
    Calculate surface coverage (H_ads) for simplified HER model.
    
    Parameters
    ----------
    x : array_like
        Potential values (V)
    k1, k1r, k2, k2r : float
        Rate constants (A/cm²)
    bbv, bbh : float
        Symmetry factors (0-1)
    f1_val : float, optional
        Normalized Faraday constant (default: 38.92 at 298.15 K)
    
    Returns
    -------
    tuple
        (theta, 1-theta) - coverage of H_ads and empty sites
    """
    theta = (k1/np.e**(bbv*f1_val*x) + np.e**((1 - bbh)*f1_val*x)*k2r) / \
            (k1/np.e**(bbv*f1_val*x) + np.e**((1 - bbv)*f1_val*x)*k1r + 
             k2/np.e**(bbh*f1_val*x) + np.e**((1 - bbh)*f1_val*x)*k2r)
    return theta, 1 - theta


def Theta_Total(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh, f1_val=38.92):
    """
    Calculate surface coverage for full HER model (3-step mechanism).
    
    Parameters
    ----------
    x : array_like
        Potential values (V)
    k1, k1r, k2, k2r, k3, k3r : float
        Rate constants (A/cm²)
    bbv, bbh : float
        Symmetry factors (0-1)
    f1_val : float, optional
        Normalized Faraday constant (default: 38.92 at 298.15 K)
    
    Returns
    -------
    tuple
        (theta, 1-theta) - coverage of H_ads and empty sites
    """
        # safe computations: avoid negative discriminant and division by near-zero A1
        k2r_calc = (k1 * k2) / k1r if k1r != 0 else 0.0
        k3r_calc = (k3 * k1**2) / (k1r**2) if k1r != 0 else 0.0
        A1 = -2 * k3 + 2 * k3r_calc
        B1 = (-np.e**((-bbv) * f1_val * x)) * k1 - np.e**((1 - bbv) * f1_val * x) * k1r - \
             k2/np.e**(bbh * f1_val * x) - np.e**((1 - bbh) * f1_val * x) * k2r_calc - 4 * k3r_calc
        C1 = k1/np.e**(bbv * f1_val * x) + np.e**((1 - bbh) * f1_val * x) * k2r_calc + 2 * k3r_calc

        # discriminant (guard negative values introduced by numerical noise)
        disc = B1**2 - (4 * A1 * C1)
        disc = np.where(disc < 0, 0.0, disc)

        denom = 2 * A1
        # avoid division by zero: where denom is ~0, set theta to nan (upstream code should handle)
        with np.errstate(divide='ignore', invalid='ignore'):
            theta = np.where(np.abs(denom) < 1e-30, np.nan, (-B1 - np.sqrt(disc)) / denom)

        # clip to physically-meaningful coverage range [0,1]
        theta = np.clip(theta, 0.0, 1.0)
        return theta, 1 - theta


def rows_generator(df, start_idx=55, window_size=10):
    """
    Generate rolling windows for Tafel slope calculation.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'Pot' and 'Cur' columns
    start_idx : int, optional
        Starting index (default: 55)
    window_size : int, optional
        Window size for rolling calculation (default: 10)
    
    Yields
    ------
    pd.DataFrame
        Windowed slices of data
    """
    i = start_idx
    while (i + window_size) <= df.shape[0]:
        yield df.iloc[i:(i+window_size):1, :]
        i += 1


def Tafel_Slopes(potential, current, start_idx=55, window_size=10):
    """
    Calculate Tafel slopes from potential and current data.
    
    Tafel equation: η = a + b*log10(i)
    where b is the Tafel slope (mV/dec)
    
    Parameters
    ----------
    potential : array_like
        Potential values (V)
    current : array_like
        Current density values (A/cm²)
    start_idx : int, optional
        Starting index for rolling window (default: 55)
    window_size : int, optional
        Window size for calculation (default: 10)
    
    Returns
    -------
    tuple
        (pot_mean, tafel_slopes) - mean potentials and slopes for each window
    """
    v1 = []
    df = pd.DataFrame({'Pot': potential, 'Cur': current})
    for df_window in rows_generator(df, start_idx, window_size):
        y = df_window['Pot'].values
        xz = np.log10(np.abs(df_window['Cur'].values))
        res = stats.linregress(xz, y)
        xm = y.mean()
        v1.append([np.abs(res.slope), xm])
    v2 = np.asarray(v1)
    return v2[:, 1], v2[:, 0]


def process_electrochemical_data(current_raw, potential_raw, area_electrode, 
                                  ohmic_drop, ref_correction):
    """
    Process raw electrochemical data with normalization and corrections.
    
    Parameters
    ----------
    current_raw : array_like
        Raw current (mA)
    potential_raw : array_like
        Raw potential (V)
    area_electrode : float
        Electrode area (cm²)
    ohmic_drop : float
        Ohmic drop correction (mV)
    ref_correction : float
        Reference correction (V)
    
    Returns
    -------
    tuple
        (current_density, corrected_potential) - processed data
    """
    if area_electrode is None:
        raise ValueError('Electrode area is required to compute current density')
    try:
        area = float(area_electrode)
        if area == 0:
            raise ValueError('Electrode area must be non-zero')
    except Exception:
        raise ValueError('Electrode area must be numeric')

    current_density = current_raw / area  # Normalize to current density (A/cm²)
    # Apply ohmic drop and reference correction to potential
    potential = potential_raw - (current_raw * ohmic_drop) + ref_correction
    return current, potential
