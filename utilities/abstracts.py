# Import the ABC (Abstract Base Class) and abstractmethod decorator from the abc module
# These are fundamental Python tools for creating abstract classes and methods
# ABC provides the base class functionality for abstract classes
# abstractmethod is a decorator that marks methods as abstract, requiring implementation in subclasses
from abc import ABC, abstractmethod

# Import typing utilities for better type hints and code documentation
# Optional allows specification of values that might be None
# Protocol is used for defining interfaces in Python
# List and Any are for specifying collection types and generic types respectively
from typing import Optional, Protocol, List, Any

# Import the Solver class from z3 library for constraint solving
# ArithRef is used for arithmetic expressions in z3
# These are essential components for implementing constraint satisfaction problems
from z3 import Solver, ArithRef

# Import cp_model from Google's OR-Tools for constraint programming
# This provides another approach to solving constraint satisfaction problems
# OR-Tools is a powerful optimization engine for operations research
from ortools.sat.python import cp_model

# Import gurobipy for mathematical optimization
# Gurobi is a commercial optimization solver
# Used for solving complex linear and quadratic programming problems
import gurobipy as gp

# Import the SchedulingProblem class from utilities module
# This class represents the core problem structure for exam scheduling
# Contains all the necessary data and constraints for the scheduling problem
from utilities import SchedulingProblem

# Import type hints specific to the scheduling system
# SolverMetrics contains metrics about solver performance
# Used for tracking and analyzing solver behavior
from utilities.typehints import SolverMetrics


# Define an abstract base class for solvers
# This class serves as a template for all solver implementations
# Ensures consistent interface across different solver types
# Forces implementation of key methods in child classes
class ISolver(ABC):
    """Abstract class for different solvers"""

    # Abstract method for solving the scheduling problem
    # Must be implemented by all concrete solver classes
    # Takes a SchedulingProblem as input and returns a solution with metrics
    # The @abstractmethod decorator enforces implementation in subclasses
    @abstractmethod
    def solve(self, problem: SchedulingProblem) -> tuple[Optional[list[dict]], SolverMetrics]:
        """Solve the scheduling problem and return solution with metrics"""
        pass

    # Abstract method to get the solver's name
    # Must be implemented by all concrete solver classes
    # Used for identification and logging purposes
    # The @abstractmethod decorator enforces implementation in subclasses
    @abstractmethod
    def get_solver_name(self) -> str:
        """Get the name of the solver"""
        pass


# Define a Protocol for constraints
# Protocols define interfaces in Python's type system
# This ensures consistent constraint implementation across different solvers
# Acts as a contract for constraint classes
class IConstraint(Protocol):
    # Method for applying constraints in Z3 solver
    # Takes solver instance, problem, and variable mappings as input
    # Modifies the solver's state by adding constraints
    # Must be implemented by all constraint classes
    def apply_z3(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef], exam_room: List[ArithRef]) -> None:
        pass

    # Method for applying constraints in OR-Tools solver
    # Takes model instance, problem, and variable mappings as input
    # Adds constraints to the OR-Tools model
    # Must be implemented by all constraint classes
    def apply_ortools(self, model: cp_model.CpModel, problem: SchedulingProblem, exam_time: dict, exam_room: dict) -> None:
        pass

    # Method for applying constraints in Gurobi solver
    # Takes model instance, problem, and variable mappings as input
    # Adds constraints to the Gurobi model
    # Must be implemented by all constraint classes
    def apply_gurobi(self, model: gp.Model, problem: SchedulingProblem, exam_time: dict, exam_room: dict) -> None:
        pass


# Define an abstract base class for basic solver functionality
# Provides common structure for all concrete solver implementations
# Ensures consistent interface across different solver types
# Acts as a foundation for specific solver implementations
class BaseSolver(ABC):
    # Abstract method to get solver name
    # Must be implemented by concrete solver classes
    # Used for identification and logging
    # The @abstractmethod decorator enforces implementation in subclasses
    @abstractmethod
    def get_solver_name(self) -> str:
        pass

    # Abstract method for solving the scheduling problem
    # Must be implemented by concrete solver classes
    # Returns either a solution or None if no solution is found
    # The @abstractmethod decorator enforces implementation in subclasses
    @abstractmethod
    def solve(self) -> list[dict[str, int | Any]] | None:
        pass
