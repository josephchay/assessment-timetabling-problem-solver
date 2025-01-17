# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0]

### Added
- Four default constraints whereby all sat instances are sat and unsat instances are unsat, each all accurate, valid, and correct.
- Feature - Added fifth constraint while still maintaining the initial constraints accuracy and preciseness.
- Feature - Added well-rounded and structured developed GUI for users of all levels of expertise, including developers, debuggers, and normal daily end-users.
- Feature - Added table manager with scroll of results, and better GUI designs.
- Documentation - Added development, installation, and usage guide for our developed custom GUI interface.
- Feature - Added statistics visualizations graph for timetabling analysis
- Feature - Added statistics visualization button for each satisfiable instance.
- Feature - Added 3 new alternative solvers for the system.
- Feature - Added SCIPSolver for alternative solution.
- Feature - Added Local Search and Tabu Search solvers for alternative solution.
- Feature - Added DEAPSolver for alternative solution.
- Feature - Added foundation functionality for results comparison between multiple solvers.
- Feature - Added 8 more unique extraordinary constraints for the system.
- Feature - Added full-fledge evaluation metrics for all the original and additional constraints.
- Feature - Added full-fledge login and registration methods for user and invigilator with privilege management.
- Feature - Added invigilator privilege of creating student accounts, whereby students are not granted such privileges.
- Feature - Added Constraints selection for processing under selected solver(s) for users to choose - providing a more dynamic methodology of solutions.
- Feature - Made Display Tables for mutli-solvers to be extremely versatile reflecting results, metrics, performance displayed according to the user's selected constraints.
- Feature - Made Display Tables for single solvers to be extremely versatile reflecting results, metrics, performance displayed according to the user's selected constraints.

### Changed
- Made space between statistics buttons and visualization options more.
- Renewed the solution timers to be more user friendly by including both milliseconds and the combination of minutes and seconds.
- Refactored the GUIManager into multiple clean class codes.

### Refactoring
- Updated code structure to be more clean through Separation of Concerns.
- Updated code structure for preparations for alternative solutions.
- Updated with minor changes in code structure.
- Refactored to make Ortools solver analyzes the constraints better.
- Refactored Table GUI for visualizing results to be more user-friendly.
- Added comments and docblocks to the code for better understanding and readability.

### Improved
- Updated statistics visualization buttons and their information display options.
- Updated the functionality of CBC Solver to make it more effective in comprehending all the constraints.
- Updated the table results display for better details of statistics comparison between multiple solvers' solutions.
- Improved the performance and metrics legend guide for multi-solvers' solution panelling logic and interface.
- Beautified and made statistics visualization buttons more beautiful.
- Beautified and perfected the UI design for the GUI results table for display.
- Convert visualization options into a dropdown menu - saving space and a much cleaner GUI.
