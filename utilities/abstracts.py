from abc import ABC, abstractmethod
from typing import Optional, Protocol, List, Any
from z3 import Solver, ArithRef
from ortools.sat.python import cp_model
import gurobipy as gp

from utilities import SchedulingProblem
from utilities.typehints import SolverMetrics


class ISolver(ABC):
    """Abstract class for different solvers"""

    @abstractmethod
    def solve(self, problem: SchedulingProblem) -> tuple[Optional[list[dict]], SolverMetrics]:
        """Solve the scheduling problem and return solution with metrics"""
        pass

    @abstractmethod
    def get_solver_name(self) -> str:
        """Get the name of the solver"""
        pass


class IConstraint(Protocol):
    def apply_z3(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef], exam_room: List[ArithRef]) -> None:
        pass

    def apply_ortools(self, model: cp_model.CpModel, problem: SchedulingProblem, exam_time: dict, exam_room: dict) -> None:
        pass

    def apply_gurobi(self, model: gp.Model, problem: SchedulingProblem, exam_time: dict, exam_room: dict) -> None:
        pass


class BaseSolver(ABC):
    @abstractmethod
    def get_solver_name(self) -> str:
        pass

    @abstractmethod
    def solve(self) -> list[dict[str, int | Any]] | None:
        pass
