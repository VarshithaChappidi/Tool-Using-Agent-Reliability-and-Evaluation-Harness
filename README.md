# Tool-Using Agent Reliability and Evaluation Harness

A deterministic support-workflow agent built with LangGraph, with a scenario harness for testing tool failures, bounded retries, ambiguous requests, prompt-injection-like inputs, and human approval requirements.

> **Implementation status:** This repository is a local research/demo harness. It uses synthetic ticket records and mock service APIs only. It drafts proposed follow-up actions; it does not connect to live customer systems or execute state-changing operations.

## Problem

An agent that can call tools must do more than produce a convincing response. It must validate inputs, handle transient failures predictably, avoid unsafe instruction overrides, and keep a human approval checkpoint before consequential actions.

## What is implemented

- A LangGraph workflow with classification, mock ticket retrieval, and action-drafting nodes.
- Pydantic models for structured requests and outcomes.
- Mock support API scenarios for successful responses, one-time timeouts, persistent timeouts, malformed responses, and missing tickets.
- Bounded retries for transient timeout failures.
- Clarification for ambiguous requests.
- Blocking behavior for prompt-injection-like instructions that attempt to bypass policy.
- An explicit `approval_required=True` outcome for proposed actions.
- A deterministic evaluation runner with scenario pass rate, recovery rate, tool-error count, and latency.
- Optional MLflow metric logging.
- Pytest coverage and GitHub Actions CI.

## Workflow

```text
User request
    |
    v
Classify / validate intent
    |---- ambiguous ------> request clarification
    |---- untrusted ------> block
    |
    v
Mock read-only ticket lookup
    |---- transient timeout --> bounded retry
    |---- malformed/error ----> controlled failure
    |
    v
Draft proposed follow-up
    |
    v
Human approval required (no automatic state change)
```

## Tech stack

- Python 3.11+
- LangGraph
- Pydantic
- Pytest
- MLflow (optional)
- Docker
- GitHub Actions

## Run locally

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m app.cli --scenario normal
```

Available scenarios: `normal`, `timeout_once`, `timeout_always`, `malformed`, `ambiguous`, and `prompt_injection`.

## Run the evaluation suite

```bash
python scripts/evaluate.py --output reports/evaluation.json
pytest -q
```

The default evaluator runs six deterministic synthetic scenarios. It checks whether each scenario reaches its expected terminal state and reports retry recovery and tool errors. These results are a functional smoke test of the policy paths, not an estimate of production agent quality or real-world API reliability.

To log aggregate metrics to MLflow:

```bash
python scripts/evaluate.py --mlflow
```

Set `MLFLOW_TRACKING_URI` to use a remote tracking server. Without it, MLflow uses its local default tracking behavior.

## Safety and reliability choices

- User-provided text is treated as untrusted input and cannot rewrite workflow policy.
- Retries are bounded; permanent or malformed failures are not retried.
- The demo tool only reads synthetic ticket data.
- A proposed update is drafted but never executed.
- Every outcome carries an approval-required flag so downstream orchestration can preserve a human checkpoint.

## Limitations and next steps

- The mock API is deterministic and does not model realistic network distributions.
- The approval gate is represented as a required outcome; a real deployment should add an authenticated approval node and durable audit record before invoking a write-capable tool.
- Add idempotency keys, per-tool timeout budgets, circuit breakers, structured traces, and sensitive-data redaction.
- Expand evaluation with adversarial paraphrases, multi-turn conversations, tool schema drift, and human-reviewed task-quality labels.
- Add deployment configuration, secrets management, tenant isolation, and integration tests against a sandbox service before connecting real systems.
