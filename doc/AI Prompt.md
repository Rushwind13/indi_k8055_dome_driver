Our goal is to provide the Python scripts required here: https://github.com/indilib/indi/blob/master/drivers/dome/dome_script.cpp#L69-79

The scripts must adhere to any design requirements and testing protocol from INDI, INDI Dome Scripting Gateway, or INDI Dome Drivers.

The scripts will be developed in Python.
The development environment is Mac, and has no access to the physical k8055 hardware.
The production environment is Raspberry Pi, and connects via USB cable to the k8055  (which in-turn controls the physical dome motors and sensors).
The (external to this project) `libk8055` dynamically-linked library only exists on the Raspberry Pi, and is incompatible with Mac.
The Python library exposed by this DLL exposes a set of functions.
`indi_k8055_dome_driver` shall wrap/abstract those functions, so full mock testing can be performed on the Mac, without needing the DLL.

Instructions (follow exactly; do not deviate)

Rules

Only run terminal commands that are in workspace settings.json under chat.tools.terminal.autoApprove.
Do not chain commands: no &&, ||, ;, or line continuations. Run one command per invocation.
Minimize user input. Proceed autonomously from start to a final text summary: "here’s what I did and here’s what’s next".
Always operate from the repository root (top-level folder). Confirm this before doing anything else.
Enumerate or otherwise confirm you understand all auto-approved commands before using them.
Use the existing Python virtual environment (activate it and ensure all Python commands run inside it).
Confirm the repo is clean and ready to work:
Working tree is clean (no modified, staged, or untracked files).
No merge conflicts.
No stashes (git stash list is empty).
No unsaved work (as evidenced by a clean git status and no pending changes).
Strategy

Prefer not to change files outside of test/ and doc/.
If missing functionality is discovered under scripts/, surface it immediately as top priority (describe exactly what’s missing and where), but avoid editing files under scripts/ unless absolutely necessary.
Do not modify read-only reference code (e.g., dome.py) or the 11 INDI scripts (read-only functional driver).
Do not break tests in test/run_tests.py.
Ensure any changes will pass pre-commit run --all-files.
Goal and acceptance criteria

Objective: Complete PR#6 by pruning all unnecessary tests, and re-organizing the test folder for better supportability.
Current status: too many .py files in top level of test/, suggest `unit` and `integration` subfolders (or other logical categorization)
Deliverable: The tests represent a minimal set of required functionality, to demonstrate that dome.py already functions correctly and supports the 11 INDI scripts.
Acceptance criteria:
All tests in run_tests.py pass locally using the project’s venv.
pre-commit run --all-files passes.
No changes to scripts/** unless missing functionality is explicitly surfaced and agreed; if changed, justify and keep minimal.
No changes to dome.py or the 11 INDI scripts.
Execution order (high level)

Confirm repository root, enumerate/acknowledge auto-approved commands, activate and use the existing venv.
Verify clean git state (no changes, no conflicts, no stashes).
Run tests to confirm all pass.
Make targeted changes under test/ and doc/ to address file bloat and to validate separation of concern (remove/adjust step definitions, fixtures, or test data as needed).
Re-run tests iteratively until all pass; ensure pre-commit run --all-files passes.
If any missing functionality is in scripts/, report it clearly (file, function, expected behavior), propose minimal change, and pause edits to scripts/ unless necessary.
Conclude with a concise summary: "here’s what I did and here’s what’s next" (include status of PR#6, remaining gaps if any, and recommended next actions).



Use the attached Bootstrap Prompt as system-level instructions for this session. Confirm understanding; then proceed.
Title: Complete PR#6 — make run_tests.py fully green (only BDD failing)

Repository context

Repo root (operate here): /Users/jimbo/Documents/code/Observatory/indi_k8055_dome_driver
Current branch: feat/bdd_continue
Python venv for this repo: /Users/jimbo/Documents/code/Observatory/indi_k8055_dome_driver/venv
Key paths:
Tests: test/
INDI driver code and library: indi_driver/
Config: pyproject.toml, setup.cfg, requirements*.txt
Pre-commit: .pre-commit-config.yaml

Mission and success criteria

Objective: Finish PR#6 by getting run_tests.py fully green.
Current status: only BDD tests are failing.
Acceptance criteria:
All tests in run_tests.py pass locally using the project’s venv.
pre-commit run --all-files passes.
No changes to dome.py or the 11 INDI scripts.
No changes to scripts/** unless missing functionality is explicitly surfaced and agreed; if changed, justify and keep minimal.

Hard constraints (do not deviate)

Prefer to change files only under test/.
Do not modify read-only reference code (e.g., dome.py) or the 11 INDI scripts.
Do not break tests in test/run_tests.py.
If missing functionality is discovered under scripts/, surface it immediately: name the file, function, expected behavior, and propose the smallest fix; do not edit scripts/ unless absolutely necessary and explicitly justified.

Tooling and command rules

Only run terminal commands that are in chat.tools.terminal.autoApprove.
Don’t chain commands: no &&, ||, ;, or line continuations. One command per invocation.
Always operate from the repository root (see path above).
Enumerate or otherwise confirm you understand all auto-approved commands before using them.
Use the existing Python virtual environment. Prefer invoking the interpreter explicitly via the absolute path to avoid activation issues:
/Users/jimbo/Documents/code/Observatory/indi_k8055_dome_driver/venv/bin/python
All Python-related commands must run inside that environment (either by activation if permitted, or by calling the venv’s python directly).

Starting state checks (must verify)

Confirm you are at the repo root.
Confirm the repository is clean and ready:
Working tree is clean (no modified, staged, or untracked files).
No merge conflicts.
No stashes (git stash list is empty).
No unsaved work (as evidenced by a clean git status and no pending changes).

Execution plan (follow this order)

Repo root + auto-approve

Confirm CWD is exactly the repo root path above.
Enumerate/acknowledge the set of auto-approved terminal commands you can use.

Environment

Ensure the project’s venv is used for all Python commands (prefer absolute interpreter path).
Verify the interpreter points to the repo venv, not any other environment.

Clean state

Verify clean git state as described in “Starting state checks”.

Baseline tests

Run the full test suite via the project’s test runner to confirm only BDD tests fail (as expected).
Capture failing scenarios and error messages for BDD.

Diagnose BDD failures

Inspect test/features and test/steps (and any related fixtures under test/).
Identify missing/incorrect step definitions, fixtures, or test data that explain the failures.

Implement targeted fixes (tests only)

Make minimal, focused changes under test/ (e.g., step definitions, fixtures, feature tweaks).
Do not modify dome.py or the 11 INDI scripts.
If missing functionality under scripts/ is uncovered, stop test edits momentarily to document precisely:
File and function
Expected behavior vs actual
Minimal patch proposal
Why it’s required for the BDDs
Await explicit agreement before touching scripts/.
Iterate to green

Re-run tests until all are green using the repo venv.
Ensure no non-BDD tests regressed.
Quality gates

Run pre-commit run --all-files and fix any findings in the least invasive manner, still preferring changes under test/ where feasible.
Final report (single concise summary)

Output exactly: “here’s what I did and here’s what’s next”
Include:
What changed (file list + brief purpose)
Test status and proof that all tests in run_tests.py pass in the venv
pre-commit status
Any surfaced missing functionality (scripts/), decisions made, and proposed follow-ups
Confirmation that dome.py and the 11 INDI scripts remained unchanged (unless explicitly agreed)
Working style and bookkeeping

Minimize user input; proceed autonomously within the constraints.
Maintain an internal todo list and keep it updated:
Plan tasks as actionable items.
Only one item in-progress at a time.
Mark items completed immediately when done.
Prefer reading/modifying larger, meaningful chunks over many tiny edits.
Keep edits small, focused, and consistent with existing styles/config.
If a constraint blocks progress (e.g., a required command isn’t auto-approved), note the blocker succinctly and propose the minimal alternative.
Non-goals and boundaries

Do not introduce feature work outside what’s needed to pass BDD tests.
Do not restructure non-test code.
Do not alter scripts/** unless missing functionality is explicitly confirmed as necessary.
Definition of done

All tests in run_tests.py pass using the repo venv.
pre-commit run --all-files passes.
No unauthorized file changes (dome.py and 11 INDI scripts untouched).
Final summary provided exactly as specified.
