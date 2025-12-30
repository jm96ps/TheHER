from matplotlib.pylab import rand
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import random
from scipy import stats
from statistics import mean
from lmfit import Model, Parameters, create_params
from matplotlib.ticker import FormatStrFormatter

path=r'/home/james/MEGA/Last_dance_Br/Mo2C_3/EF3_2/LSV_Mo2C_EF3_3(5).txt'

# Module-level constants
F = 96485.3  # Faraday constant (C/mol)
f1 = 38.92   # Default f1 value (will be updated if temperature/gas_constant provided)


class hydrogen_fitting:
    """
    A class for fitting hydrogen evolution reaction (HER) data using simplified or full models.
    
    Parameters:
    -----------
    file_path : str
        Path to the data file containing current and potential measurements
    area_electrode : float
        Area of the electrode in cm² (used to normalize current to current density)
    ohmic_drop : float
        Ohmic drop correction value in mV
    ref_correction : float, optional
        Reference correction value (default: 0.924)
    temperature : float, optional
        Temperature in Kelvin. If provided with gas_constant, f1 will be calculated
    gas_constant : float, optional
        Gas constant in J/(mol·K). If provided with temperature, f1 will be calculated
    bbv_initial : float, optional
        Initial value for bbv (Volmer transfer coefficient, default: 0.5)
    bbh_initial : float, optional
        Initial value for bbh (Heyrovsky transfer coefficient, default: 0.5)
    vary_bbv : bool, optional
        Whether to vary bbv during fitting (default: True)
    vary_bbh : bool, optional
        Whether to vary bbh during fitting (default: True)
    
    Methods:
    --------
    fit_data(model_type='simplified', fitting_method='powell')
        Fit the data using either 'simplified' or 'full' model
    get_results()
        Return the fitting results
    plot_results()
        Generate plots of the fitting results
    """
    
    def __init__(self, file_path, area_electrode, ohmic_drop, ref_correction=0.924, 
                 temperature=None, gas_constant=None, bbv_initial=0.5, bbh_initial=0.5,
                 vary_bbv=True, vary_bbh=True):
        """
        Initialize the hydrogen_fitting class.
        
        Parameters:
        -----------
        file_path : str
            Path to the data file
        area_electrode : float
            Electrode area in cm²
        ohmic_drop : float
            Ohmic drop correction
        ref_correction : float, optional
            Reference correction (default: 0.924)
        temperature : float, optional
            Temperature in Kelvin. If provided with gas_constant, f1 will be calculated
        gas_constant : float, optional
            Gas constant in J/(mol·K). If provided with temperature, f1 will be calculated
        bbv_initial : float, optional
            Initial value for bbv (default: 0.5)
        bbh_initial : float, optional
            Initial value for bbh (default: 0.5)
        vary_bbv : bool, optional
            Whether to vary bbv during fitting (default: True)
        vary_bbh : bool, optional
            Whether to vary bbh during fitting (default: True)
        """
        self.file_path = file_path
        self.area_electrode = area_electrode
        self.ohmic_drop = ohmic_drop
        self.ref_correction = ref_correction
        self.temperature = temperature
        self.gas_constant = gas_constant
        self.bbv_initial = bbv_initial
        self.bbh_initial = bbh_initial
        self.vary_bbv = vary_bbv
        self.vary_bbh = vary_bbh
        
        # Calculate f1 if temperature and gas_constant are provided
        self.f1 = self._calculate_f1()
        
        # Load and process data
        self._load_data()
        self._process_variables()
        
        # Results storage
        self.result_model = None
        self.model_type = None
    
    def _calculate_f1(self):
        """
        Calculate f1 from temperature and gas constant.
        f1 = F / (Temperature * Gas_constant)
        where F is Faraday constant (96485.3 C/mol)
        
        Returns:
        --------
        float
            f1 value (calculated or default 38.92)
        """
        global f1
        
        if self.temperature is not None and self.gas_constant is not None:
            f1_calc = F / (self.temperature * self.gas_constant)
            f1 = f1_calc  # Update global f1
            print(f"\nf1 calculated: F/({self.temperature}K × {self.gas_constant}J/mol·K) = {f1_calc:.6f}")
            return f1_calc
        else:
            f1 = 38.92  # Update global f1 with default
            print("\nUsing default f1 value: 38.92")
            return 38.92
        
    def _load_data(self):
        """Load data from file."""
        self.dframe = np.loadtxt(self.file_path, skiprows=1)
        
    def _process_variables(self):
        """Process raw data into current and potential."""
        current_raw = self.dframe[:, 0]
        
        # Normalize to current density if area provided
        if self.area_electrode is not None:
            self.current = current_raw / self.area_electrode
        else:
            self.current = current_raw
        
        # Calculate potential vs RHE
        self.potential = self.dframe[:, 1] - (current_raw * self.ohmic_drop) + self.ref_correction
        
    def fit_data(self, model_type='simplified', fitting_method='powell'):
        """
        Fit the data using specified model.
        
        Parameters:
        -----------
        model_type : str
            Type of model to use: 'simplified' or 'full'
        fitting_method : str
            Fitting method (default: 'powell')
            
        Returns:
        --------
        result_model : lmfit.ModelResult
            The fitting result object
        """
        # Create wrapper functions that capture self.f1 and F
        f1_val = self.f1
        
        def HER_simplified_wrapper(x, k1, k1r, k2, k2r, bbv, bbh):
            """Wrapper for simplified model with f1 captured"""
            vtotal = 2*(((k1*k2*(1 - np.e**(2*f1_val*x)))*np.e**(-bbh*x*f1_val))/(k1*np.e**((bbh - bbv)*f1_val*x) + k2 + np.e**(f1_val*x)*(k1r*np.e**((bbh - bbv)*f1_val*x) + k2r)))
            return -F*vtotal
        
        def Hydrogen_Full_wrapper(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh):
            """Wrapper for full model with f1 captured"""
            k2r_calc = (k1*k2)/k1r
            k3r_calc = (k3*k1**2)/k1r**2
            theta1 = Theta_Total_wrapper(x, k1, k1r, k2, k2r_calc, k3, k3r_calc, bbv, bbh)
            return -F*(k1*(1 - theta1))/np.e**(bbv*f1_val*x) - np.e**((1 - bbh)*f1_val*x)*k2r_calc*(1 - theta1) - np.e**((1 - bbv)*f1_val*x)*k1r*theta1 + (k2*theta1)/np.e**(bbh*f1_val*x)
        
        def Theta_Total_wrapper(x, k1, k1r, k2, k2r, k3, k3r, bbv, bbh):
            """Wrapper for Theta_Total with f1 captured"""
            A1 = -2*k3+2*k3r
            B1 = (-np.e**((-bbv)*f1_val*x))*k1 - np.e**((1 - bbv)*f1_val*x)*k1r - k2/np.e**(bbh*f1_val*x) - np.e**((1 - bbh)*f1_val*x)*k2r - 4*k3r
            C1 = k1/np.e**(bbv*f1_val*x) + np.e**((1 - bbh)*f1_val*x)*k2r + 2*k3r
            theta = (-B1-np.sqrt(B1**2-(4*A1*C1)))/2*A1
            return theta
        
        if model_type.lower() == 'simplified':
            self.model_type = 'HER_simplified_fitting'
            model_func = HER_simplified_wrapper
        elif model_type.lower() == 'full':
            self.model_type = 'Hydrogen_Full_Fitting'
            model_func = Hydrogen_Full_wrapper
        else:
            raise ValueError("model_type must be 'simplified' or 'full'")
        
        # Create model and parameters
        HER_model = Model(model_func, independent_vars=['x'])
        
        # Generate random initial parameters
        rand_params = np.array([rnd() for i in range(9)])
        
        if model_type.lower() == 'simplified':
            params = create_params(
                k1=dict(value=rand_params[0], max=1e-2, min=1e-20),
                k1r=dict(value=rand_params[1], max=1e-2, min=1e-20),
                k2=dict(value=rand_params[2], max=1e-2, min=1e-20),
                k2r=dict(value=rand_params[3], max=1e-2, min=1e-20),
                bbv=dict(value=self.bbv_initial, min=0, max=1, vary=self.vary_bbv),
                bbh=dict(value=self.bbh_initial, min=0, max=1, vary=self.vary_bbh)
            )
        else:  # full model
            params = create_params(
                k1=dict(value=rand_params[0], max=1e-2, min=1e-20),
                k1r=dict(value=rand_params[1], max=1e-2, min=1e-20),
                k2=dict(value=rand_params[2], max=1e-2, min=1e-20),
                k2r=dict(expr='(k1*k2)/k1r'),
                k3=dict(value=rand_params[3], max=1e-2, min=1e-20),
                k3r=dict(expr='(k3*k1**2)/k1r**2'),
                bbv=dict(value=self.bbv_initial, min=0, max=1, vary=self.vary_bbv),
                bbh=dict(value=self.bbh_initial, min=0, max=1, vary=self.vary_bbh)
            )
        
        # Set x values for ast evaluator
        params._asteval.symtable['x'] = self.potential
        
        # Perform fitting
        self.result_model = HER_model.fit(
            self.current,
            params,
            x=self.potential,
            method=fitting_method,
            nan_policy='omit'
        )
        
        print(self.result_model.fit_report())
        
        return self.result_model
    
    def get_results(self):
        """
        Get the fitting results.
        
        Returns:
        --------
        dict
            Dictionary containing results or None if not fitted yet
        """
        if self.result_model is None:
            print("No fitting results available. Run fit_data() first.")
            return None
        
        return {
            'result_model': self.result_model,
            'model_type': self.model_type,
            'parameters': self.result_model.params
        }
    
    def plot_results(self):
        """Generate and display plots of the fitting results."""
        if self.result_model is None:
            print("No results to plot. Run fit_data() first.")
            return
        
        plot_fitting(
            self.result_model,
            self.potential,
            self.current,
            self.model_type,
            self.area_electrode,
            self.f1
        )

def import_data(path):
    
    dframe = np.loadtxt(path, skiprows=1)
    #path="C:\\Users\\jamee\\MEGA\\Last_dance_Br\\Mo2C_3\\EF3_2\\LSV_Mo2C_EF3_3(5).txt"
    name="LSV_Mo2C_EF4_"
    # when1='before'
    when1='after'
    
    return dframe

def variables(dframe,ohmic_drop=6.43,ref_correction=0.924,area_electrode=None):
    
    if area_electrode != None:
        current = dframe[:, 0]/area_electrode   #Current density
    else:
        current = dframe[:, 0]   #Current density
    potential = dframe[:, 1]-(dframe[:, 0]*ohmic_drop)+ref_correction  # Potential vs RHE  
    
    return current,potential   

def Calculate_f(Temp,Gas_constant):
    
    F=96485.3
    
    f1=F/(Temp*Gas_constant)
    return f1



def rnd():

    exp1 = random.randint(-15, -4)
    significand = round(random.uniform(0.1, 9),2)
    return significand*10**exp1

def HER_simplified_fitting(x,k1,k1r,k2,k2r,bbv,bbh):
    
    vtotal = 2*(((k1*k2*(1 - np.e**(2*f1*x)))*np.e**(-bbh*x*f1))/(k1*np.e**((bbh - bbv)*f1*x) + k2 + np.e**(f1*x)*(k1r*np.e**((bbh - bbv)*f1*x) + k2r)))
    
    return -96485.3*vtotal
def Hydrogen_Full_Fitting(x, k1, k1r, k2,k2r, k3,k3r, bbv, bbh):

    k2r=(k1*k2)/k1r
    k3r=(k3*k1**2)/k1r**2

    theta1=Theta_Total(x, k1, k1r, k2,k2r, k3,k3r, bbv, bbh)

    return -96485.3*(k1*(1 - theta1))/np.e**(bbv*f1*x) - np.e**((1 - bbh)*f1*x)*k2r*(1 - theta1) - np.e**((1 - bbv)*f1*x)*k1r*theta1 + (k2*theta1)/np.e**(bbh*f1*x)

def Tafel(x, k1, k1r, k2,k2r, k3,k3r, bbv, bbh):

      theta = Theta_Total(x, k1, k1r, k2,k2r, k3,k3r, bbv, bbh)
      return -(k3r*(1 - theta)**2) + k3*theta**2

def Theta_VH(x, k1, k1r, k2,k2r, bbv, bbh, f1_val=38.92):
    
    theta=(k1/np.e**(bbv*f1_val*x) + np.e**((1 - bbh)*f1_val*x)*k2r)/(k1/np.e**(bbv*f1_val*x) + np.e**((1 - bbv)*f1_val*x)*k1r + k2/np.e**(bbh*f1_val*x) + np.e**((1 - bbh)*f1_val*x)*k2r)
    

    return theta,1-theta


def Theta_Total(x, k1, k1r, k2,k2r, k3, k3r, bbv, bbh, f1_val=38.92):

    k2r_calc=(k1*k2)/k1r
    k3r_calc=(k3*k1**2)/k1r**2
    A1=-2*k3+2*k3r_calc
    B1=(-np.e**((-bbv)*f1_val*x))*k1 - np.e**((1 - bbv)*f1_val*x)*k1r - k2/np.e**(bbh*f1_val*x) - np.e**((1 - bbh)*f1_val*x)*k2r_calc - 4*k3r_calc
    C1=k1/np.e**(bbv*f1_val*x) + np.e**((1 - bbh)*f1_val*x)*k2r_calc + 2*k3r_calc
    theta=(-B1-np.sqrt(B1**2-(4*A1*C1)))/2*A1

    return theta,1-theta

def fitting_models(model_name,potential,current,fitting_method='powell'):
    if model_name=='HER_simplified_fitting':
        HER_model= Model(model_name,independent_vars=['x'])

        params = create_params(k1=dict(value=rand[0], max=1e-2, min=1e-20),
                                k1r=dict(value=rand[1], max=1e-2, min=1e-20),
                                k2=dict(value=rand[2], max=1e-2, min=1e-20),
                                k2r=dict(value=rand[3], max=1e-2, min=1e-20),
                            #    k3=dict(value=rand[3], max=1e-2, min=1e-20),
                            #    k3r=dict(expr='(k3*k1**2)/k1r**2'),
                                bbv=dict(value=0.5, min=0, max=1, vary=True),
                                bbh=dict(value=0.5, min=0, max=1, vary=True)


                        )
        
    elif model_name=='Hydrogen_Full_Fitting':
        HER_model= Model(Hydrogen_Full_Fitting,independent_vars=['x'])

        params = create_params(k1=dict(value=rand[0], max=1e-2, min=1e-20),
                                k1r=dict(value=rand[1], max=1e-2, min=1e-20),
                                k2=dict(value=rand[2], max=1e-2, min=1e-20),
                                k2r=dict(expr='(k1*k2)/k1r'),
                                k3=dict(value=rand[3], max=1e-2, min=1e-20),
                                k3r=dict(expr='(k3*k1**2)/k1r**2'),
                                bbv=dict(value=0.5, min=0, max=1, vary=True),
                                bbh=dict(value=0.5, min=0, max=1, vary=True)


                        )
    params._asteval.symtable['x']= potential
    weight=(np.abs(current))
    # result_model1=HER_model.fit(current, params, x=potential, method='nelder',nan_policy='omit',weight=weight)
    result_model=HER_model.fit(current, params, x=potential, method=fitting_method,nan_policy='omit')
    print(result_model.fit_report())
    
    return result_model, model_name
    
def rows_generator(df1):
    
    i = 55   
    while (i+10) <= df1.shape[0]:
        yield df1.iloc[i:(i+10):1, :]
        i += 1



def Tafel_Slopes(p,c):
    v1=[]
    df=pd.DataFrame({'Pot':p,'Cur':c})
    j = 0
    
    for df in rows_generator(df):
        
        xz=0
        
        y=0
        xm=0
        res=0
        y=df['Pot']
        xz=np.log10(np.abs(df['Cur']))
        res=stats.linregress(xz,y)
        xm=y.mean()
        
        
        v1.append( [np.abs(res.slope), xm])
            
        j += 10
        print(xm,res.slope)
    v2=np.asarray(v1)
    
    return v2[:,1],v2[:,0]

def plot_fitting(result_model,potential,current,model_name,area_electrode=None, f1_val=38.92):
    
    if model_name=='HER_simplified_fitting':
        
        theta, theta_inv = Theta_VH(potential, result_model.params['k1'], result_model.params['k1r'], result_model.params['k2'],result_model.params['k2r'], result_model.params['bbv'], result_model.params['bbh'], f1_val)
    elif model_name=='Hydrogen_Full_Fitting':
        
        theta, theta_inv = Theta_Total(potential, result_model.params['k1'], result_model.params['k1r'], result_model.params['k2'],result_model.params['k2r'], result_model.params['k3'], result_model.params['k3r'], result_model.params['bbv'], result_model.params['bbh'], f1_val)
    
    pot1,Tafel_Experimental= Tafel_Slopes(potential,current)
    pot2,Tafel_theoretical=Tafel_Slopes(potential,result_model.eval(x=potential))
    
    
    # 1. Create a figure and a GridSpec layout
    fig = plt.figure(figsize=(8, 6))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1])

    # 2. Add the subplots using the GridSpec indices

    # Top-left and top-right plots in the first row
    # The 'sharex' argument links their x-axes
    ax1 = fig.add_subplot(gs[0, 0], sharex=None) # Start with no explicit sharing
    ax2 = fig.add_subplot(gs[0, 1], sharex=ax1) # Share ax1's x-axis

    # Bottom plot spanning both columns in the second row
    # This plot will have its own independent x-axis by default
    ax3 = fig.add_subplot(gs[1, :])

    ax1.set_xlabel('Potential vs RHE / V')
    ax1.yaxis.set_major_formatter(FormatStrFormatter('%2.1f'))
    if area_electrode != None:
        ax1.set_ylabel(r'Current/ mA $cm**{-2}$')
    else:
        ax1.set_ylabel(r'Current/ mA $')
        
    ax1.plot(potential, current*1000, 'o', label='Data')
    ax1.plot(potential, result_model.best_fit*1000, 'x', label='Fitting')
    ax1.legend()

    ax2.plot(potential, theta, '-', label=r'$\theta_H$')
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%.2e'))
    ax2.plot(potential, theta_inv, '-', label=r'$1 - \theta_H$')
    ax2.legend()

    ax3.set_xlabel('Mean potential vs RHE / V')
    ax3.set_ylabel(r'Tafel slope / mV dec$^{-1}$')
    ax3.plot(pot1,Tafel_Experimental,marker='s',label='Experimental')
    ax3.plot(pot2,Tafel_theoretical,marker='o',label='Theoretical')

     
