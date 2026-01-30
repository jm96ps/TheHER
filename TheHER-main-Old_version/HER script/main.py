"""
Main script to demonstrate the hydrogen_fitting class usage
"""

from utils import hydrogen_fitting
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

def main():
    """
    Main function to run hydrogen fitting analysis
    """
    
    print("="*60)
    print("Hydrogen Evolution Reaction (HER) Fitting Analysis")
    print("="*60)
    
    # Get experimental parameters from user
    print("\n" + "="*60)
    print("Experimental Parameters:")
    print("="*60)
    
    # File path
    default_path = r'/home/james/MEGA/Last_dance_Br/Mo2C_3/EF3_2/LSV_Mo2C_EF3_3(5).txt'
    file_path = input(f"Enter data file path (default: {default_path}): ").strip()
    if not file_path:
        file_path = default_path
    
    # Electrode area
    try:
        area_electrode = float(input("Enter electrode area in cm² (default 0.5): ") or "0.5")
    except ValueError:
        print("Invalid input! Using default value 0.5")
        area_electrode = 0.5
    
    # Ohmic drop
    try:
        ohmic_drop = float(input("Enter ohmic drop in ohm·cm² (default 6.43): ") or "6.43")
    except ValueError:
        print("Invalid input! Using default value 6.43")
        ohmic_drop = 6.43
    
    # pH value
    try:
        pH = float(input("Enter pH value (default 14 for 1M NaOH): ") or "14")
    except ValueError:
        print("Invalid input! Using default value 14")
        pH = 14
    
    # Reference electrode potential
    print("\nCommon reference electrodes at 25°C:")
    print("  Hg/HgO (1M NaOH): 0.098 V vs SHE")
    print("  SCE: 0.241 V vs SHE")
    print("  Ag/AgCl (sat. KCl): 0.197 V vs SHE")
    print("  Ag/AgCl (3M KCl): 0.210 V vs SHE")
    
    try:
        ref_electrode = float(input("Enter reference electrode potential vs SHE in V (default 0.098): ") or "0.098")
    except ValueError:
        print("Invalid input! Using default value 0.098")
        ref_electrode = 0.098
    
    # Calculate reference correction
    ref_correction = pH * 0.059 + ref_electrode
    print(f"\nCalculated potential correction: {ref_correction:.3f} V")
    print(f"  (Formula: pH × 0.059 + E_ref = {pH} × 0.059 + {ref_electrode} = {ref_correction:.3f} V)")
    
    # Optional: Temperature and Gas constant (if not provided, default f1=38.92 is used)
    temperature = 298.15  # Kelvin (room temperature, ~25°C)
    gas_constant = 8.314  # J/(mol·K)
    
    # Get user input for bbv and bbh parameters
    print("\n" + "="*60)
    print("Transfer Coefficient Parameters (bbv and bbh):")
    print("="*60)
    
    try:
        bbv_initial = float(input("Enter initial bbv value (default 0.5): ") or "0.5")
        bbh_initial = float(input("Enter initial bbh value (default 0.5): ") or "0.5")
    except ValueError:
        print("Invalid input! Using default values (0.5, 0.5)")
        bbv_initial = 0.5
        bbh_initial = 0.5
    
    # Ask if user wants to vary bbv and bbh
    vary_bbv_str = input("Allow bbv to vary during fitting? (yes/no, default yes): ").strip().lower()
    vary_bbv = vary_bbv_str != 'no'
    
    vary_bbh_str = input("Allow bbh to vary during fitting? (yes/no, default yes): ").strip().lower()
    vary_bbh = vary_bbh_str != 'no'
    
    print(f"\nParameters set:")
    print(f"  bbv_initial = {bbv_initial}, vary = {vary_bbv}")
    print(f"  bbh_initial = {bbh_initial}, vary = {vary_bbh}")
    
    print("="*60)
    print("Hydrogen Evolution Reaction (HER) Fitting Analysis")
    print("="*60)
    
    # Initialize the hydrogen fitting object
    print(f"\nLoading data from: {file_path}")
    fitter = hydrogen_fitting(
        file_path=file_path,
        area_electrode=area_electrode,
        ohmic_drop=ohmic_drop,
        ref_correction=ref_correction,
        temperature=temperature,
        gas_constant=gas_constant,
        bbv_initial=bbv_initial,
        bbh_initial=bbh_initial,
        vary_bbv=vary_bbv,
        vary_bbh=vary_bbh
    )
    print("Data loaded successfully!")
    
    # Choose model type: 'simplified' or 'full'
    print("\n" + "="*60)
    print("Available models:")
    print("  1. 'simplified' - Simplified HER model")
    print("  2. 'full'       - Full HER model with Tafel step")
    print("="*60)
    
    model_choice = input("\nSelect model (simplified/full): ").strip().lower()
    if model_choice not in ['simplified', 'full']:
        print("Invalid choice! Using 'simplified' model.")
        model_choice = 'simplified'
    
    # Fit the data
    print(f"\nFitting data using {model_choice} model...")
    result = fitter.fit_data(model_type=model_choice, fitting_method='powell')
    
    # Get results
    print("\n" + "="*60)
    print("Fitting Results:")
    print("="*60)
    results = fitter.get_results()
    
    if results:
        print(f"Model type: {results['model_type']}")
        print("\nOptimized Parameters:")
        for param_name, param in results['parameters'].items():
            print(f"  {param_name}: {param.value:.4e}")
    
    # Plot results
    print("\n" + "="*60)
    print("Generating plots...")
    print("="*60)
    fitter.plot_results()
    plt.tight_layout()
    plt.show()
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
    if model_choice not in ['simplified', 'full']:
        print("Invalid choice! Using 'simplified' model.")
        model_choice = 'simplified'
    
    # Fit the data
    print(f"\nFitting data using {model_choice} model...")
    result = fitter.fit_data(model_type=model_choice, fitting_method='powell')
    
    # Get results
    print("\n" + "="*60)
    print("Fitting Results:")
    print("="*60)
    results = fitter.get_results()
    
    if results:
        print(f"Model type: {results['model_type']}")
        print("\nOptimized Parameters:")
        for param_name, param in results['parameters'].items():
            print(f"  {param_name}: {param.value:.4e}")
    
    # Plot results
    print("\n" + "="*60)
    print("Generating plots...")
    print("="*60)
    fitter.plot_results()
    plt.tight_layout()
    plt.show()
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
