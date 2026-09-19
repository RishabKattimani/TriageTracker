# Pre-Hackathon Checklist

Allowed prep should remain non-code if event rules require all code during the build window.

## Prepare beforehand
- all specification files
- architecture diagram
- dashboard mockups
- presentation
- 60-90 second submission-video outline
- 2-5 minute Loom recording outline required by the event
- demo script
- judge Q&A
- public papers/docs
- algorithm notes/pseudocode
- threshold plan
- test-case definitions
- fixture metadata format
- volunteer recording plan
- GitHub repo if rules allow empty/scaffold-free repo creation
- Cursor settings and GitHub authentication
- Python installed
- Homebrew installed
- browser tested
- webcam permissions understood
- confirm event rules permit prerecorded fixtures/assets
- prepare repository description and submission copy draft

## Volunteer recordings
If pre-event data/assets are permitted:
- stable seated videos
- talking
- mild motion
- occlusion
- dark lighting
- controlled physiological change after safe ordinary activity

Because there is no reference wearable:
- do not label exact HR ground truth unless manually measured with a reliable reference method
- use recordings mainly for repeatability, motion rejection, baseline/change behavior
- use live manual pulse count only as a rough sanity check, not scientific ground truth

## On both Macs
Before event:
- confirm Cursor installed
- confirm Git configured
- confirm GitHub authentication
- confirm Python available
- confirm webcam permission path
- confirm ability to run shell commands
- do NOT run/build project code before start if prohibited

## At start
1. Put all 17 specs and permitted fixtures in the empty repository; do not include prewritten application code.
2. On Laptop A, open the repository root in Cursor Agent mode.
3. Start with: `Read 16_MASTER_CURSOR_PROMPT.md completely and execute it. Read every referenced specification before writing application code. Begin M0.`
4. Builder executes milestones and pushes only passing gates.
5. Laptop B pulls after each passing milestone and records independent results in `QA_RESULTS.md`.
6. After M6, Laptop B performs a brand-new clone and follows only README + `./run.sh`; Laptop A gives no verbal setup help.
7. Fix all BLOCKER/HIGH clean-install or guided-demo failures.
8. Freeze feature development at least 30 minutes before submissions close.
9. Record demo video, capture screenshots, verify repository access, complete submission fields, and submit early.

## Cursor start message

Paste only this into a new Cursor Agent conversation from the repository root:

```text
Read 16_MASTER_CURSOR_PROMPT.md completely and execute it.
Before writing application code, read every specification file it references in numeric order.
You are operating inside the project repository. Begin with M0.
Do not ask me to make decisions already resolved by the specifications.
Do not proceed past a failed milestone gate.
```

## Laptop B QA start message

After Laptop A pushes the first milestone, open a separate Cursor Agent conversation on Laptop B and paste:

```text
Read 15_QA_AGENT_PROMPT.md completely and act as the independent QA engineer.
Read the specification files it references.
For each milestone pushed to main, pull the exact commit, run milestone and regression tests, perform the required manual checks, and update QA_RESULTS.md.
Do not modify core implementation unless Laptop A explicitly asks for a minimal test-driven repair.
Never approve hardcoded demo state, fabricated physiology, or a milestone that only passes its own self-authored tests.
```

## Required Loom recording checklist

- Loom screen recorder installed and signed in
- presenter camera bubble enabled
- MacBook webcam used for live physiological proof
- dashboard and console text readable
- controlled-change fixture ready
- team introductions under 30 seconds
- elevator pitch under 30 seconds
- live camera shows ROIs, measurements, EVM, abstention, and recovery
- controlled-change video produces the reassessment alert through the backend
- technical stack and engineering challenge explained briefly
- ending answers who benefits, why it matters, and what comes next
- total duration between 2 and 5 minutes; target 3-3.5 minutes
- no dependency on iPhone streaming or stock hospital footage
