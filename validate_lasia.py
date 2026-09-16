import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from webapp.models.hydrogen import hydrogen_fitting

def test_lasia_example_1():
    print("Testing Lasia Example 1...")
    # Create dummy potential data
    potentials = np.linspace(0, -0.5, 100)
    currents = np.zeros_like(potentials)  # Dummy currents
    
    dummy_file = "dummy_lasia.csv"
    np.savetxt(dummy_file, np.column_stack((currents, potentials)), delimiter=",")
    
    # Set I: k1=1e-9, k-1=1e-11, k2=9e-12, k-2=9e-10
    fitter = hydrogen_fitting(
        file_path=dummy_file,
        area_electrode=1.0,
        delimiter=',',
        current_col=1,
        potential_col=2
    )
    
    # Mock result_model to evaluate functions without fitting
    class DummyResult:
        pass
    
    from lmfit import Parameters
    params = Parameters()
    params.add('k1', value=1e-9)
    params.add('k1r', value=1e-11)
    params.add('k2', value=9e-12)
    params.add('k2r', value=9e-10)
    params.add('bbv', value=0.5)
    params.add('bbh', value=0.5)
    
    fitter.result_model = DummyResult()
    fitter.result_model.params = params
    fitter.model_type = 'HER_simplified_fitting'
    
    # Check theta at eta = 0
    # From Lasia: theta_H is 0.9901 at eta = 0
    theta_H, _ = fitter.compute_theta(x=[0])
    print(f"Theta at eta=0 (Set I): {theta_H[0]:.4f} (Expected: ~0.9901)")
    
    # Calculate Tafel slope
    # Since we didn't fit, we need to generate currents from the model.
    # The model wrapper can be extracted or evaluated directly.
    decomp = fitter.compute_decomposition(x=potentials)
    fitter.current = decomp['total']
    
    x_tafel, slope_tafel = fitter.compute_tafel_slope(use_fitted=False)
    if len(slope_tafel) > 0:
        print(f"Tafel slope at high overpotential: {np.mean(slope_tafel[-10:]):.2f} mV/dec (Expected: ~118)")
        
    os.remove(dummy_file)
    print("Example 1 test complete.\n")

def test_lasia_example_2():
    print("Testing Lasia Example 2 (Set I)...")
    potentials = np.linspace(0, -0.5, 100)
    currents = np.zeros_like(potentials)
    dummy_file = "dummy_lasia_2.csv"
    np.savetxt(dummy_file, np.column_stack((currents, potentials)), delimiter=",")
    
    fitter = hydrogen_fitting(file_path=dummy_file, area_electrode=1.0, delimiter=',', current_col=1, potential_col=2)
    
    class DummyResult: pass
    from lmfit import Parameters
    params = Parameters()
    params.add('k1', value=1e-7)
    params.add('k1r', value=1e-10)
    params.add('k2', value=1e-12)
    params.add('k2r', value=1e-9)
    params.add('bbv', value=0.5)
    params.add('bbh', value=0.5)
    
    fitter.result_model = DummyResult()
    fitter.result_model.params = params
    fitter.model_type = 'HER_simplified_fitting'
    
    theta_H, _ = fitter.compute_theta(x=[0])
    print(f"Theta at eta=0 (Set I): {theta_H[0]:.4f} (Expected: close to 1)")
    
    decomp = fitter.compute_decomposition(x=potentials)
    fitter.current = decomp['total']
    
    x_tafel, slope_tafel = fitter.compute_tafel_slope(use_fitted=False)
    if len(slope_tafel) > 0:
        print(f"Tafel slope at high overpotential: {np.mean(slope_tafel[-10:]):.2f} mV/dec (Expected: ~118)")
        
    os.remove(dummy_file)
    print("Example 2 test complete.\n")

def test_lasia_example_4():
    print("Testing Lasia Example 4 (Set I)...")
    potentials = np.linspace(0, -0.5, 200)
    currents = np.zeros_like(potentials)
    dummy_file = "dummy_lasia_4.csv"
    np.savetxt(dummy_file, np.column_stack((currents, potentials)), delimiter=",")
    
    fitter = hydrogen_fitting(file_path=dummy_file, area_electrode=1.0, delimiter=',', current_col=1, potential_col=2)
    
    class DummyResult: pass
    from lmfit import Parameters
    params = Parameters()
    params.add('k1', value=1e-4)
    params.add('k1r', value=1e-1)
    params.add('k2', value=2e-11)
    params.add('k2r', value=2e-14)
    params.add('bbv', value=0.5)
    params.add('bbh', value=0.5)
    
    fitter.result_model = DummyResult()
    fitter.result_model.params = params
    fitter.model_type = 'HER_simplified_fitting'
    
    decomp = fitter.compute_decomposition(x=potentials)
    fitter.current = decomp['total']
    
    x_tafel, slope_tafel = fitter.compute_tafel_slope(use_fitted=False, window_size=5)
    if len(slope_tafel) > 0:
        print(f"Tafel slope at low overpotential: {np.mean(slope_tafel[5:15]):.2f} mV/dec (Expected: ~39)")
        print(f"Tafel slope at high overpotential: {np.mean(slope_tafel[-10:]):.2f} mV/dec (Expected: ~118)")
        
    os.remove(dummy_file)
    print("Example 4 test complete.\n")

if __name__ == '__main__':
    test_lasia_example_1()
    test_lasia_example_2()
    test_lasia_example_4()
