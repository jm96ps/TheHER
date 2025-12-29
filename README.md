# TheHER
Bundle of scripts for playing with the hydrogen evolution reaction (HER)  in Python.

This repository contains some coding lines to fit the HER experimental curves and to work out the Tafel slopes for these curves.

Among the things it can work out are:

- Get the chemical rate constants for the Volmer-Heyrovsky mechanism
- Calculate the hydrogen coverage in each potential under the steady state approximation
- Calculate the Tafel slope for a determined potential window (such as calculating it at 10 mV) for establishing a criterion for the validation of the Tafel Slope analysis, regarding what is described in [1].

Considering the overall HER in alkaline media [2],


```math
\ce{H2O + 2e-->H2 + 2OH-}
```

Volmer step (adsorption),

$$
\ce{H2O + e- + M->MH_{ads} + OH-}
$$

 and the Heyrovsky step (desorption)

$$
\ce{H2O + MH_{ads} + e- ->H2 + OH- + M}
$$

the chemical rate constants, symmetry coefficients could also be estimated from the fitting of total dc current ($j=F\upsilon= \upsilon_1+\upsilon_2$) of experimental curves.

To calculate the hydrogen coverage in each potential, it was taken from the steady-state approximation ($\frac{d\theta_{H}}{dt}=0$), then

$$
\theta_{H}= \frac{\overrightarrow{k}_{1}+\overrightarrow{k}_{2}}{\overrightarrow{k}_{1}+\overleftarrow{k}_{-1}+\overrightarrow{k}_{2}+\overleftarrow{k}_{-2}}.
$$

1. Onno van der Heijden, Sunghak Park, Rafaël E. Vos, Jordy J. J. Eggebeen, and Marc T. M. Koper. “Tafel Slope Plot as a Tool to Analyze Electrocatalytic Reactions.” ACS Energy Letters, American Chemical Society, April 1, 2024, 1871–79. [10.1021/acsenergylett.4c00266](https://pubs.acs.org/doi/10.1021/acsenergylett.4c00266)

2. Lasia, Andrzej. “Mechanism and Kinetics of the Hydrogen Evolution Reaction.” International Journal of Hydrogen Energy 44, no. 36 (2019): 19484–518. [https://doi.org/10.1016/j.ijhydene.2019.05.183](https://doi.org/10.1016/j.ijhydene.2019.05.183).

