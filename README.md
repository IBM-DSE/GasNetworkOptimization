# Optimizing the topology of a gas transmission network #

### Table of Contents ###
- [Introduction](#intro)
- [Implementation](#impl)

## Introduction ##
<a id=intro ></a>

This project implements a mathematical formulations of gas network topology optimization, which is solved
by using 
[IBM&reg; Decision Optimization (DO)](https://content-dsxlocal.mybluemix.net/docs/content/DODS/DODS_home.html) 
for [Data Science Experience (DSX) Local](https://content-dsxlocal.mybluemix.net/).

The project is composed by the following assets:
- Notebooks:
  - [`Gas_Network_Optimization`](#gas-opt)
- DO Model:
  - [`Gas_Network_Optimization`](#domod)
- Datasets:
  - A collection of CSV files representing the data of the gas network (derived from [gaslib.zib.de](http://gaslib.zib.de)),
  plus two different transportation scenarios that specify certain gas quantities
  
  
## Implementation ##
<a id=impl ></a>

The implementation is based on Jupyter notebooks with Python 2.7, and DO Models for DSX. The main project assets 
are described in the following.

### Notebook `Gas_Network_Optimization` ###
<a id=gas-opt ></a>

This notebook implements a mathematical model for the gas network topology optimization problem. 
A simplification is used which leads to a mixed-integer linear program that is modeled and solved with 
[IBM&reg; DO CPLEX&reg; Modeling for Python](https://developer.ibm.com/docloud/documentation/optimization-modeling/modeling-for-python/): 
[`docplex`](https://pypi.org/project/docplex/). The addressed formulation is described and discussed within the notebook.

### DO Model `Gas_Network_Optimization` ###
<a id=domod ></a>

This DO Model handles the optimization approach implemented in the notebook `Gas_Network_Optimization`. 
In particular, several DO Scenarios are created and the optimization is performed for each scenario. This 
DO Model contains also a dashboard that reports a summary chart comparing cost KPIs and an overview 
of new pipelines which have been selected by the optimization model.
