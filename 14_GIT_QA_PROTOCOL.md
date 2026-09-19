# Git + QA Protocol

## Branching
During the speed build, keep main as latest passing milestone unless parallel changes genuinely require a branch.

## Builder loop
For each milestone:
1. implement
2. run milestone tests
3. run regression tests
4. fix failures
5. update PROGRESS.md
6. commit
7. push

Commit format:
MILESTONE-X: description

Never push a known-broken milestone as "complete".

## Laptop B
After each milestone push:
1. git pull
2. create fresh environment if needed
3. run tests
4. run manual acceptance checks
5. record QA_RESULTS.md

Report format:
MILESTONE:
COMMIT:
AUTOMATED:
MANUAL:
FAILURES:
REPRO STEPS:
SEVERITY:

After M6, Laptop B must perform a genuine stranger test:
1. move/remove its existing checkout;
2. clone the repository into a new folder;
3. do not copy `.venv`, caches, models, or untracked local files;
4. follow only README instructions;
5. launch only with `./run.sh`;
6. test Guided Demo with camera disabled;
7. test Live Camera;
8. replay Guided Demo three times;
9. record every needed verbal explanation as a defect.

Laptop A may receive the written failure report but must not coach Laptop B through setup.

## Stop-the-line failures
Builder must stop future feature work for:
- app doesn't start
- camera crash
- false high-confidence physiology during no-face
- low-confidence data triggers REASSESS
- fixture input broken
- dashboard cannot receive backend state
- demo cannot be rerun
- clean clone cannot launch with `./run.sh`
- guided demo requires a camera
- homepage does not explain the use case/safety boundary
- guided demo alert is directly scripted by frontend code

Cosmetic problems do not stop the line before core completion.
