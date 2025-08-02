from pathlib import Path
from z3 import *
import time
import argparse
import z3_batchsolver.input_output.reader as reader
import z3_batchsolver.input_output.writer as writer

# NOTE: Inspired by code and instructions from the following sources:
# NOTE: https://ericpony.github.io/z3py-tutorial/guide-examples.htm
# NOTE: https://z3prover.github.io/papers/programmingz3.html
class Z3Solver:
    def __init__(self, time_limit, solver_name="cvc5", tests_dir=None):
        if tests_dir is None:
            # Set root directory using existing file structure
            # Z3-BatchSolver -> src -> z3_batchsolver -> z3_solver.py
            self.ROOT = Path(__file__).resolve().parents[2]
            self.TESTS = self.ROOT / "tests"
        else:
            # Use provided tests directory to set root directory
            self.TESTS = Path(tests_dir)
            self.ROOT = self.TESTS.parents[0]

        # Results are in a sibling directory to the tests directory
        self.RESULTS = self.ROOT / "results"

        self.time_limit = time_limit
        self.solver_name = solver_name
        self.writer = writer.Writer(self.RESULTS, self.solver_name)
        
    def reinit(self):
        # Create solver
        self.solver = Solver()
        
        # Set solver options
        self.solver.set(unsat_core=True)
        self.solver.set(timeout=int(self.time_limit))

        self.start_time = time.time()
        self.sat_model = [] # if SAT, stores satisfying values

    def get_solver_name(self):
        return self.solver_name

    def execute(self):
        for file in reader.get_sorted_files(self.TESTS):
            if file.is_file():
                # Reinitialize data for new file
                self.reinit()
                print(f"Reading file: {file}")

                #with file.open("r") as input:
                    #input_code = input.read()

                self.solver.from_file(str(file)) # from_file expects string, not Path

                # Check satisfiability
                result = self.solver.check()
                if result == sat:
                    model = self.solver.model()
                    # Get all declared variable names and terms
                    for decl in model.decls():
                        name = decl.name() # constant name
                        value = model[decl] # constant value
                        self.sat_model.append([name, value])
                elif result == unsat:
                    self.sat_model.append(["UNSAT"])
                elif result == unknown:
                    self.sat_model.append(["UNKNOWN (TIMEOUT)"])

                print()
                self.writer.store_result(file, self.start_time, self.sat_model)
        self.writer.write()

# CLI entry point
def main():
    parser = argparse.ArgumentParser(description="Run the Z3 solver on a directory of SMT2 files.")
    parser.add_argument("--time_limit", required=True, type=int, 
        help="Time limit for each check-sat (in ms).")
    parser.add_argument("--solver_name", default="Z3",
        help="Name for the solver run (used in output results).")
    parser.add_argument("--tests_dir", default=None, 
        help="Path to directory containing test SMT2 files.")
    args = parser.parse_args()

    solver = Z3Solver(
        time_limit=str(args.time_limit),
        solver_name=args.solver_name,
        tests_dir=args.tests_dir
    )
    solver.execute()

if __name__ == "__main__":
    main()
