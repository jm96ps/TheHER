
from matplotlib.ticker import FormatStrFormatter
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import random
from lmfit.model import Model, save_model
import pybroom as br
import warnings
from lmfit import create_params, minimize
warnings.simplefilter(action='ignore', category=FutureWarning)
from scipy import stats
from statistics import mean
# from sympy import symbols, diff
# import sympy

# Data import

path="C:\\Users\\jamee\\MEGA\\Last_dance_Br\\Mo2C_3\\EF4\\LSV_Mo2C_EF4_3(5).txt"
name="LSV_Mo2C_EF4_"
# when1='before'
when1='after'
dframe = np.loadtxt(path, skiprows=1)
dframe
current = dframe[:, 0]   #Current density
potential = dframe[:, 1]-(dframe[:, 0]*6.05)+0.924  # Potential vs RHE
# k=print(np.size(potential,0))

# Functions to randomizing parameters

def Export_LSV(path,when1):
    
    with open('Theta_'+path+when1+'.txt', 'a', newline='\n') as fh:
        fh.write(theta_degree.to_string(index=False))
        fh.write('\n')

    with open('Fit_'+path+when1+'.txt', 'a') as fh:
         fh.write(result_model.fit_report())
         fh.write('\n')

    # %%
    with open('Tafel_'+path+when1+'.txt', 'a') as fh:

         fh.write(Tafel_slope.to_string(index=False))
         fh.write('\n')
    return

def rnd():

    exp1 = random.randint(-15, -4)
    significand = round(random.uniform(0.1, 9),2)
    return significand*10**exp1


rand = []
rand = np.array([rnd() for i in range(9)])

F=96485.3
f1=38.92

def HER_simple(x,k1,k1r,k2,k2r,bbv,bbh):
    
    vtotal = 2*(((k1*k2*(1 - np.e**(2*f1*x)))*np.e**(-bbh*x*f1))/(k1*np.e**((bbh - bbv)*f1*x) + k2 + np.e**(f1*x)*(k1r*np.e**((bbh - bbv)*f1*x) + k2r)))
    
    return -F*vtotal
# def Hydrogen_Full_Fitting(x, k1, k1r, k2,k2r, k3,k3r, bbv, bbh):

#     k2r=(k1*k2)/k1r
#     k3r=(k3*k1**2)/k1r**2

#     theta1=Theta_full_model(x, k1, k1r, k2,k2r, k3,k3r, bbv, bbh)

#     return -96485.3*(k1*(1 - theta1))/np.e**(bbv*38.92*x) - np.e**((1 - bbh)*38.92*x)*k2r*(1 - theta1) - np.e**((1 - bbv)*38.92*x)*k1r*theta1 + (k2*theta1)/np.e**(bbh*38.92*x)

def Volmer(x, k1, k1r, k2,k2r, bbv, bbh):

    theta,theta2 = Theta_k(x, k1, k1r, k2,k2r, bbv, bbh)
    return (k1*(theta2))/np.e**(38.92203*bbv*x) - np.e**(38.92203*(1 - bbv)*x)*k1r*theta


def Heyrovsky(x, k1, k1r, k2,k2r,  bbv, bbh):

    theta1,theta2 = Theta_k(x, k1, k1r, k2,k2r, bbv, bbh)
    return -((np.e**((1 - bbh)*39.92*x))*k2r*(theta2)) + (k2*theta1)/np.e**(bbh*38.92*x)


# def Tafel(x, k1, k1r, k2,k2r, k3,k3r, bbv, bbh):

#     theta = Theta_k(x, k1, k1r, k2,k2r, k3,k3r, bbv, bbh)
#     return -(k3r*(1 - theta)**2) + k3*theta**2


def Theta_k(x, k1, k1r, k2,k2r, bbv, bbh):
    
    theta=(k1/np.e**(bbv*f1*x) + np.e**((1 - bbh)*f1*x)*k2r)/(k1/np.e**(bbv*f1*x) + np.e**((1 - bbv)*f1*x)*k1r + k2/np.e**(bbh*f1*x) + np.e**((1 - bbh)*f1*x)*k2r)
    
    
    
    # k2r=(k1*k2)/k1r
    # k3r=(k3*k1**2)/k1r**2
    # A1=-2*k3+2*k3r
    # B1=(-np.e**((-bbv)*38.92*x))*k1 - np.e**((1 - bbv)*38.92*x)*k1r - k2/np.e**(bbh*38.92*x) - np.e**((1 - bbh)*38.92*x)*k2r - 4*k3r
    # C1=k1/np.e**(bbv*38.92*x) + np.e**((1 - bbh)*38.92*x)*k2r + 2*k3r
    # theta=(-B1-np.sqrt(B1**2-(4*A1*C1)))/2*A1

    return theta,1-theta

def Theta_full_model(x, k1, k1r, k2,k2r,k3,k3r, bbv, bbh):
    
    k2r=(k1*k2)/k1r
    k3r=(k3*k1**2)/k1r**2
    A1=-2*k3+2*k3r
    B1=(-np.e**((-bbv)*38.92*x))*k1 - np.e**((1 - bbv)*38.92*x)*k1r - k2/np.e**(bbh*38.92*x) - np.e**((1 - bbh)*38.92*x)*k2r - 4*k3r
    C1=k1/np.e**(bbv*38.92*x) + np.e**((1 - bbh)*38.92*x)*k2r + 2*k3r
    theta=(-B1-np.sqrt(B1**2-(4*A1*C1)))/2*A1
    theta2=1-theta
    return theta,theta2



HER_model= Model(HER_simple,independent_vars=['x'])

params = create_params(k1=dict(value=rand[0], max=1e-2, min=1e-20),
                        k1r=dict(value=rand[1], max=1e-2, min=1e-20),
                        k2=dict(value=rand[2], max=1e-2, min=1e-20),
                        k2r=dict(value=rand[3], max=1e-2, min=1e-20),
                    #    k3=dict(value=rand[3], max=1e-2, min=1e-20),
                    #    k3r=dict(expr='(k3*k1**2)/k1r**2'),
                        bbv=dict(value=0.5, min=0, max=1, vary=False),
                        bbh=dict(value=0.5, min=0, max=1, vary=False)


                       )
params._asteval.symtable['x']= potential





def rows_generator(df1):
    
    i = 55   
    while (i+10) <= df1.shape[0]:
        yield df1.iloc[i:(i+10):1, :]
        i += 1



def Tafel(p,c):
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
            
        j += 1
        
    v2=np.asarray(v1)
    
    return v2[:,1],v2[:,0]
  


""" def jac(x, k1,k1r,k2,k3,bbv,bbh):

    x, k1,k1r,k2,k3,bbv,bbh= symbols('x k1 k1r k2 k3 bbv bbh', real=True)


    j=Theta_k(x, k1,k1r,k2,k3,bbv,bbh)




    jac1=diff(j, k1)
    jac2=diff(j, k1r)
    jac3=diff(j, k2)
    jac4=diff(j, k3)
    jac5=diff(j,bbv)
    jac6=diff(j,bbh)

    jac_list=sympy.Array((jac1,jac2,jac3,jac4,jac5,jac6))
    model_lf=sympy.lambdify(list(jac_list.free_symbols),jac_list)
    mac=model_lf(x, k1,k1r,k2,k3,bbv,bbh)
    return mac """

weight=(np.abs(current))
# result_model1=HER_model.fit(current, params, x=potential, method='nelder',nan_policy='omit',weight=weight)
result_model=HER_model.fit(current, params, x=potential, method='powell',nan_policy='omit')



print(result_model.fit_report())


# dt_tot = br.tidy(result_model.result, var_names=['loss', 'dataset'])


theta_plot,theta_plot2 = Theta_k(potential, result_model.params['k1'], result_model.params['k1r'], result_model.params['k2'],result_model.params['k2r'], result_model.params['bbv'], result_model.params['bbh'])

volmer_plot =  Volmer(potential, result_model.params['k1'], result_model.params['k1r'], result_model.params['k2'],result_model.params['k2r'], result_model.params['bbv'], result_model.params['bbh'])

heyrovsky_plot =  Heyrovsky(potential, result_model.params['k1'], result_model.params['k1r'], result_model.params['k2'],result_model.params['k2r'], result_model.params['bbv'], result_model.params['bbh'])

total =heyrovsky_plot+volmer_plot



Tafel_x2,Tafel_s2=Tafel(potential,result_model.best_fit)
Tafel_x3,Tafel_s3=Tafel(potential,current)

theta_degree = pd.DataFrame({'Potential': potential, 'Theta': theta_plot})
Tafel_slope=pd.DataFrame({'Potential':Tafel_x2, 'Slope_cur': Tafel_s3,'Slope_fit': Tafel_s2})


fig, (ax, ax2, ax3) = plt.subplots(3, sharex=False)
fig.suptitle('HER microkinetics')

fig.set_label('Potential vs RHE / V')
plt.xlabel('Potential vs RHE /V')
ax.yaxis.set_major_formatter(FormatStrFormatter('%2.1f'))

ax.set_ylabel(r'Current/ mA $cm**{-2}$')
ax.plot(potential, current*1000, 'o', label='Data')
ax.plot(potential, result_model.best_fit*1000, 'x', label='Fitting')
ax.legend()

# ax2.plot(potential, theta_plot, '-', label=r'$\theta_1{H}$')
ax2.yaxis.set_major_formatter(FormatStrFormatter('%.2e'))
ax2.plot(potential, theta_plot, '-', label=r'$\theta{H}$')
ax2.plot(potential, theta_plot2, '-', label=r'$\theta_2{H}$')
ax2.legend()


ax3.scatter(Tafel_x3,Tafel_s3,marker='s')

ax3.scatter(Tafel_x2,Tafel_s2,marker='o')


plt.legend()
plt.show()

Export_LSV(name, when1)
