"""
Herein lies a total of 1 suggested solver, with another 4 alternative solvers,
TOTALING to 5 solvers to perform the solution.
"""

from .zthree import ZThreeSolver
from .gurobi import GurobiSolver
from .ortools import ORToolsSolver
from .cbc import CBCSolver
from .scip import SCIPSolver
from .deap import DEAPSolver
from .localsearch import LocalSearchSolver
from .tabusearch import TabuSearchSolver
