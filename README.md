# OpsControl

OpsControl is a human-in-the-loop exception desk for operations teams. It turns a surge of unstructured status updates into a prioritized queue, impact assessments, draft stakeholder communications, and an explicit review queue.

## Status

Scaffold only. Product requirements and seed-data contracts are defined before implementation.

## Repository layout

- `docs/PRD.md` - product requirements and acceptance criteria
- `docs/seed-data-spec.md` - deterministic demo dataset contract
- `data/` - future scenario fixtures
- `src/opscontrol/` - application package
- `tests/` - automated tests

## Planned MVP

1. Ingest email, webhook, and EDI-style operational updates.
2. Deduplicate repeated events and classify each exception.
3. Run a bounded impact investigation with stored trace data.
4. Draft stakeholder communication and route uncertain cases to a human.
5. Provide a replayable incident scenario for product and regression testing.

## Local setup

Implementation has not started. Once the first service is added, local setup and test commands will be documented here.

## Design principles

- Human approval remains required for outbound communication.
- Ambiguity routes to review; it is never silently guessed.
- Every automated decision is traceable.
- The demo must be deterministic and safe to replay.