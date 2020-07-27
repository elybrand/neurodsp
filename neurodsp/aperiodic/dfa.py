"""Fluctuation analyses to measure fractal properties of time series."""

import numpy as np
import scipy as sp

from neurodsp.utils.data import split_signal

###################################################################################################
###################################################################################################

def compute_fluctuations(sig, fs, n_scales=10, min_scale=0.01, max_scale=1.0, deg=1, method='dfa'):
    """Compute a fluctuation analysis on a signal.

    Parameters
    ----------
    sig : 1d array
        Time series.
    fs : float, Hz
        Sampling rate, in Hz.
    n_scales : int, optional, default=10
        Number of scales to estimate fluctuations over.
    min_scale : float, optional, default=0.01
        Shortest scale to compute over, in seconds.
    max_scale : float, optional, default=1.0
        Longest scale to compute over, in seconds.
    deg : int, optional, default=1
        Polynomial degree for detrending. Only used for DFA.

        - 1 for regular DFA
        - 2 or higher for generalized DFA
    method : {'dfa', 'rs'}
        Method to use to compute fluctuations:

        - 'dfa' : detrended fluctuation
        - 'rs' : rescaled range

    Returns
    -------
    t_scales : 1d array
        Time-scales over which fluctuation measures were computed.
    fluctuations : 1d array
        Average fluctuation at each scale.
    exp : float
        Slope of line in loglog when plotting time scales against fluctuations.
        This is the alpha value for DFA, or the Hurst exponent for rescaled range.

    Notes
    -----
    These analyses compute fractal properties by analyzing fluctuations across windows.

    Overall, these approaches involve dividing the time-series into non-overlapping
    windows at log-spaced scales and computing a fluctuation measure across windows.
    The relationship of this fluctuation measure across window sizes provides
    information on the fractal properties of a signal.

    Measures available are:

    - DFA: detrended fluctuation analysis
        - computes ordinary least squares fits across signal windows
    - RS: rescaled range
        - computes the range of signal windows, divided by the standard deviation
    """

    # Get log10 equi-spaced scales and translate that into window lengths
    t_scales = np.logspace(np.log10(min_scale), np.log10(max_scale), n_scales)
    win_lens = np.round(t_scales * fs).astype('int')

    # Step through each scale and measure fluctuations
    fluctuations = np.zeros_like(t_scales)
    for idx, win_len in enumerate(win_lens):

        if method == 'dfa':
            fluctuations[idx] = compute_detrended_fluctuation(sig, win_len=win_len, deg=deg)
        elif method == 'rs':
            fluctuations[idx] = compute_rescaled_range(sig, win_len=win_len)
        else:
            raise ValueError('Fluctuation method not understood.')

    # Calculate the relationship between between fluctuations & time scales
    exp = np.polyfit(np.log10(t_scales), np.log10(fluctuations), deg=1)[0]

    return t_scales, fluctuations, exp


def compute_rescaled_range(sig, win_len):
    """Compute rescaled range of a given time series at a given scale.

    Parameters
    ----------
    sig : 1d array
        Time series.
    win_len : int
        Window length for each rescaled range computation, in samples.

    Returns
    -------
    rs : float
        Average rescaled range over windows.
    """

    # Demean signal
    sig = sig - np.mean(sig)

    # Calculate cumulative sum of the signal & split the signal into segments
    segments = split_signal(sp.cumsum(sig), win_len).T

    # Calculate rescaled range as range divided by standard deviation (of non-cumulative signal)
    rs_win = np.ptp(segments, axis=0) / np.std(split_signal(sig, win_len).T, axis=0)

    # Take the mean across windows
    rs = np.mean(rs_win)

    return rs


def compute_detrended_fluctuation(sig, win_len, deg=1):
    """Compute detrended fluctuation of a time series at the given window length.

    Parameters
    ----------
    sig : 1d array
        Time series.
    win_len : int
        Window length for each detrended fluctuation fit, in samples.
    deg : int, optional, default=1
        Polynomial degree for detrending.

    Returns
    -------
    det_fluc : float
        Measured detrended fluctuation, as the average error fits of the window.
    """

    # Calculate cumulative sum of the signal & split the signal into segments
    segments = split_signal(sp.cumsum(sig - np.mean(sig)), win_len).T

    # Calculate local trend, as the line of best fit within the time window
    _, fluc, _, _, _ = np.polyfit(np.arange(win_len), segments, deg=deg, full=True)

    # Convert to root-mean squared error, from squared error
    det_fluc = np.mean((fluc / win_len))**0.5

    return det_fluc
