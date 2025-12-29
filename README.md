# TheHER
Bundle of scripts for playing with the hydrogen evolution reaction (HER)  in Python.

This repository contains some coding lines to fit the HER experimental curves and to work out the Tafel slopes for these curves.

Among the things it can work out are:

- Get the chemical rate constants for the Volmer-Heyrovsky mechanism
- Calculate the hydrogen coverage in each potential under the steady state approximation
- Calculate the Tafel slope for a determined potential window (such as calculating it at 10 mV) for establishing a criterion for the validation of the Tafel Slope analysis, regarding what is described in [10.1021/acsenergylett.4c00266](https://pubs.acs.org/doi/10.1021/acsenergylett.4c00266)
