from pyscipopt import Model, quicksum

from typing import Any, List, Dict
from utilities import BaseSolver, SchedulingProblem


class SCIPSolver(BaseSolver):
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.model = Model("SCIPScheduler")

    @staticmethod
    def get_solver_name() -> str:
        return 'SCIP Solver'

    def solve(self) -> List[Dict[str, int]] | None:
        try:
            # Create variables
            assignments = {}
            for e in range(self.problem.number_of_exams):
                for r in range(self.problem.number_of_rooms):
                    for t in range(self.problem.number_of_slots):
                        assignments[(e, r, t)] = self.model.addVar(
                            vtype="B",
                            name=f"exam_{e}_room_{r}_time_{t}"
                        )

            # Single assignment constraint
            for e in range(self.problem.number_of_exams):
                self.model.addCons(
                    quicksum(assignments[(e, r, t)]
                             for r in range(self.problem.number_of_rooms)
                             for t in range(self.problem.number_of_slots)) == 1
                )

            # Room capacity constraints
            for r in range(self.problem.number_of_rooms):
                for t in range(self.problem.number_of_slots):
                    self.model.addCons(
                        quicksum(assignments[(e, r, t)] * self.problem.exams[e].get_student_count()
                                 for e in range(self.problem.number_of_exams))
                        <= self.problem.rooms[r].capacity
                    )

            # Student conflict constraints
            for student in range(self.problem.total_students):
                student_exams = [e for e in range(self.problem.number_of_exams)
                                 if student in self.problem.exams[e].students]

                for t in range(self.problem.number_of_slots):
                    self.model.addCons(
                        quicksum(assignments[(e, r, t)]
                                 for e in student_exams
                                 for r in range(self.problem.number_of_rooms)) <= 1
                    )

            # Solve
            self.model.setParam('display/verblevel', 0)
            self.model.optimize()

            if self.model.getStatus() == "optimal":
                solution = []
                for e in range(self.problem.number_of_exams):
                    for r in range(self.problem.number_of_rooms):
                        for t in range(self.problem.number_of_slots):
                            if self.model.getVal(assignments[(e, r, t)]) > 0.5:
                                solution.append({
                                    'examId': e,
                                    'room': r,
                                    'timeSlot': t
                                })
                return solution if len(solution) == self.problem.number_of_exams else None
            return None

        except Exception as e:
            print(f"SCIP Solver error: {str(e)}")
            return None
