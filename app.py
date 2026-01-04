"""
Flask Web Application for Hydrogen Evolution Reaction (HER) Analysis
Deployable on Render.com
"""

from flask import Flask, render_template, request, jsonify, send_file, send_file
import numpy as np
import pandas as pd
from scipy import stats
import json
import os
import sys

# Load environment variables (optional for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars

# Add HER script to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'HER script'))

# Import HER modules
from utils import hydrogen_fitting, Tafel_Slopes, Theta_VH, Theta_Total
from her_model import HER_simplified_fitting, rnd

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Physical constants
F = 96485.3  # Faraday constant (C/mol)


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_data():
    """
    Handle data file upload and initial processing
    Returns: JSON with processed data and initial parameters
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get parameters from form
        area_electrode = float(request.form.get('area_electrode', 0.5))
        ohmic_drop = float(request.form.get('ohmic_drop', 6.43))
        pH = float(request.form.get('pH', 7))
        ref_electrode = float(request.form.get('ref_electrode', 0.098))
        ref_correction = pH * 0.059 + ref_electrode
        temperature = float(request.form.get('temperature', 298.15))
        gas_constant = float(request.form.get('gas_constant', 8.314))
        current_column = int(request.form.get('current_column', 0))
        potential_column = int(request.form.get('potential_column', 1))
        skip_rows = int(request.form.get('skip_rows', 1))
        
        # Calculate f1
        f1 = F / (temperature * gas_constant)
        
        # Read uploaded file
        # Save temporarily
        temp_path = '/tmp/temp_data.txt'
        file.save(temp_path)
        
        # Read first 10 lines for preview
        with open(temp_path, 'r') as f:
            first_10_lines = [f.readline().rstrip() for _ in range(10)]
        
        # Load data with flexible separator detection
        # Try to detect separator and read with pandas
        df = pd.read_csv(temp_path, sep=None, engine='python', skiprows=skip_rows, header=None)
        
        # Extract columns based on user selection
        current_raw = df.iloc[:, current_column].values
        potential_raw = df.iloc[:, potential_column].values
        
        # Process
        current = current_raw / area_electrode
        potential = potential_raw - (current_raw * ohmic_drop) + ref_correction
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'data': {
                'potential': potential.tolist(),
                'current': current.tolist(),
                'f1': f1,
                'num_points': len(potential),
                'preview': {
                    'first_5_current': current[:5].tolist(),
                    'first_5_potential': potential[:5].tolist()
                },
                'raw_lines': first_10_lines
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fit', methods=['POST'])
def fit_data():
    """
    Perform HER fitting
    Input: JSON with data and parameters
    Returns: Fitted parameters and model predictions
    """
    try:
        data = request.json
        
        potential = np.array(data['potential'])
        current = np.array(data['current'])
        model_type = data.get('model_type', 'simplified')
        f1 = data.get('f1', 38.92)
        
        # Initial parameter values
        bbv_initial = data.get('bbv_initial', 0.5)
        bbh_initial = data.get('bbh_initial', 0.5)
        vary_bbv = data.get('vary_bbv', True)
        vary_bbh = data.get('vary_bbh', True)
        
        # Generate random initial parameters
        from lmfit import Model, create_params
        
        if model_type == 'full':
            # Full model (3-step: Volmer-Heyrovsky-Tafel)
            def HER_full_wrapper(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh):
                k2r_calc = (k1*k2) / k1r
                k3r_calc = (k3*k1**2) / k1r**2
                A1 = -2*k3 + 2*k3r_calc
                B1 = (-np.e**((-bbv)*f1*x))*k1 - np.e**((1 - bbv)*f1*x)*k1r - \
                     k2/np.e**(bbh*f1*x) - np.e**((1 - bbh)*f1*x)*k2r_calc - 4*k3r_calc
                C1 = k1/np.e**(bbv*f1*x) + np.e**((1 - bbh)*f1*x)*k2r_calc + 2*k3r_calc
                theta = (-B1 - np.sqrt(B1**2 - (4*A1*C1))) / (2*A1)
                
                v1 = k1/np.e**(bbv*f1*x) - k1r*np.e**((1-bbv)*f1*x)*theta
                v2 = k2*theta/np.e**(bbh*f1*x) - k2r_calc*np.e**((1-bbh)*f1*x)
                v3 = k3*(theta**2) - k3r_calc
                vtotal = v1 + v2 + v3
                return -F * vtotal
            
            HER_model = Model(HER_full_wrapper, independent_vars=['x'])
            rand_params = [rnd() for _ in range(6)]
            
            params = create_params(
                k1=dict(value=rand_params[0], max=1e-2, min=1e-20),
                k1r=dict(value=rand_params[1], max=1e-2, min=1e-20),
                k2=dict(value=rand_params[2], max=1e-2, min=1e-20),
                k2r=dict(value=rand_params[3], max=1e-2, min=1e-20),
                k3=dict(value=rand_params[4], max=1e-2, min=1e-20),
                k3r=dict(value=rand_params[5], max=1e-2, min=1e-20),
                bbv=dict(value=bbv_initial, min=0, max=1, vary=vary_bbv),
                bbh=dict(value=bbh_initial, min=0, max=1, vary=vary_bbh)
            )
        else:
            # Simplified model (2-step: Volmer-Heyrovsky)
            def HER_simplified_wrapper(x, k1, k1r, k2, k2r, bbv, bbh):
                vtotal = 2 * (((k1*k2*(1 - np.e**(2*f1*x)))*np.e**(-bbh*x*f1)) / 
                              (k1*np.e**((bbh - bbv)*f1*x) + k2 + np.e**(f1*x)*
                              (k1r*np.e**((bbh - bbv)*f1*x) + k2r)))
                return -F * vtotal
            
            HER_model = Model(HER_simplified_wrapper, independent_vars=['x'])
            rand_params = [rnd() for _ in range(4)]
            
            params = create_params(
                k1=dict(value=rand_params[0], max=1e-2, min=1e-20),
                k1r=dict(value=rand_params[1], max=1e-2, min=1e-20),
                k2=dict(value=rand_params[2], max=1e-2, min=1e-20),
                k2r=dict(value=rand_params[3], max=1e-2, min=1e-20),
                bbv=dict(value=bbv_initial, min=0, max=1, vary=vary_bbv),
                bbh=dict(value=bbh_initial, min=0, max=1, vary=vary_bbh)
            )
        
        # Fit
        result = HER_model.fit(
            current,
            params,
            x=potential,
            method='powell',
            nan_policy='omit'
        )
        
        # Extract fitted parameters
        fitted_params = {
            'k1': float(result.params['k1'].value),
            'k1r': float(result.params['k1r'].value),
            'k2': float(result.params['k2'].value),
            'k2r': float(result.params['k2r'].value),
            'bbv': float(result.params['bbv'].value),
            'bbh': float(result.params['bbh'].value)
        }
        
        # Add k3 and k3r for full model
        if model_type == 'full':
            fitted_params['k3'] = float(result.params['k3'].value)
            fitted_params['k3r'] = float(result.params['k3r'].value)
        
        # Calculate predictions
        theoretical_current = result.best_fit
        
        # Calculate surface coverage
        if model_type == 'full':
            theta, theta_inv = Theta_Total(
                potential,
                result.params['k1'].value,
                result.params['k1r'].value,
                result.params['k2'].value,
                result.params['k2r'].value,
                result.params['k3'].value,
                result.params['k3r'].value,
                result.params['bbv'].value,
                result.params['bbh'].value,
                f1
            )
        else:
            theta, theta_inv = Theta_VH(
                potential,
                result.params['k1'].value,
                result.params['k1r'].value,
                result.params['k2'].value,
                result.params['k2r'].value,
                result.params['bbv'].value,
                result.params['bbh'].value,
                f1
            )
        
        # Calculate Tafel slopes
        pot_exp, tafel_exp = Tafel_Slopes(potential, current)
        pot_theo, tafel_theo = Tafel_Slopes(potential, theoretical_current)
        
        return jsonify({
            'success': True,
            'fitted_params': fitted_params,
            'predictions': {
                'potential': potential.tolist(),
                'current': theoretical_current.tolist(),
                'theta': theta.tolist(),
                'theta_inv': theta_inv.tolist(),
                'tafel_exp_pot': pot_exp.tolist(),
                'tafel_exp_slope': tafel_exp.tolist(),
                'tafel_theo_pot': pot_theo.tolist(),
                'tafel_theo_slope': tafel_theo.tolist()
            },
            'statistics': {
                'r_squared': float(result.rsquared) if hasattr(result, 'rsquared') else None,
                'chi_squared': float(result.chisqr),
                'reduced_chi_squared': float(result.redchi)
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/calculate', methods=['POST'])
def calculate_with_params():
    """
    Calculate predictions with user-specified parameters
    For interactive parameter adjustment
    """
    try:
        data = request.json
        
        potential = np.array(data['potential'])
        f1 = data.get('f1', 38.92)
        
        # Get parameters
        k1 = data['k1']
        k1r = data['k1r']
        k2 = data['k2']
        k2r = data['k2r']
        bbv = data['bbv']
        bbh = data['bbh']
        
        # Calculate predictions
        vtotal = 2 * (((k1*k2*(1 - np.e**(2*f1*potential)))*np.e**(-bbh*potential*f1)) / 
                      (k1*np.e**((bbh - bbv)*f1*potential) + k2 + np.e**(f1*potential)*
                      (k1r*np.e**((bbh - bbv)*f1*potential) + k2r)))
        theoretical_current = -F * vtotal
        
        # Calculate surface coverage
        theta, theta_inv = Theta_VH(potential, k1, k1r, k2, k2r, bbv, bbh, f1)
        
        # Calculate Tafel slopes
        pot_theo, tafel_theo = Tafel_Slopes(potential, theoretical_current)
        
        return jsonify({
            'success': True,
            'predictions': {
                'current': theoretical_current.tolist(),
                'theta': theta.tolist(),
                'theta_inv': theta_inv.tolist(),
                'tafel_theo_pot': pot_theo.tolist(),
                'tafel_theo_slope': tafel_theo.tolist()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
