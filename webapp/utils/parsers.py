import os
import pandas as pd
import numpy as np

def detect_separator(path, sample_lines=5):
    # Try common separators by sampling the file
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = ''.join([next(f) for _ in range(sample_lines)])
    except Exception:
        return None

    candidates = [',', '\t', ';', ' ']
    best = None
    best_count = 0
    for c in candidates:
        count = sample.count(c)
        if count > best_count:
            best_count = count
            best = c
    return best


def parse_data_file(path, delimiter='auto', current_col=1, potential_col=2, skiprows=0):
    """Parse an uploaded data file and return (potential, current) as numpy arrays.

    Columns are 1-based by default (UI-friendly). Returns (potential, current).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    sep = None
    if isinstance(delimiter, str) and delimiter != 'auto' and delimiter != 'auto-detect':
        if delimiter == '\\t':
            sep = '\t'
        else:
            sep = delimiter
    elif delimiter == 'auto' or delimiter == 'auto-detect' or delimiter is None:
        sep = detect_separator(path) or None

    df = pd.read_csv(path, sep=sep, engine='python', comment='#', header=None, skiprows=skiprows)

    # Convert to numeric and pick columns
    try:
        c_idx = int(current_col) - 1
    except Exception:
        c_idx = 0
    try:
        p_idx = int(potential_col) - 1
    except Exception:
        p_idx = 1

    if df.shape[1] > max(c_idx, p_idx):
        sel = df.iloc[:, [c_idx, p_idx]]
    elif df.shape[1] >= 2:
        sel = df.iloc[:, :2]
    else:
        raise ValueError('File does not contain enough columns')

    sel = sel.apply(pd.to_numeric, errors='coerce')
    sel = sel.dropna(how='any')
    arr = sel.values
    if arr.shape[0] < 1:
        raise ValueError('No numeric rows found')

    current = np.asarray(arr[:, 0], dtype=float)
    potential = np.asarray(arr[:, 1], dtype=float)
    return potential, current
