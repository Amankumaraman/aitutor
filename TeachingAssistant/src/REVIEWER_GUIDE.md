# Teaching Assistant — Phase A (Steps 1–3) — Reviewer Guide

This document explains how to run and verify **Testing & Evaluation Phase A (End of Step 3)** locally.
All commands below are written for **Windows PowerShell** (the repo owner used PowerShell). If you use another shell, adapt paths/commands accordingly.

## Quick summary
Phase A implements:
- Gemini WebSocket client (mockable)
- Basic Teaching Assistant (startup/closing greetings, engagement monitor, prompt injection)
- Memory adapters (VectorStore mock + Knowledge Graph)
- Demo runner and unit tests

Everything can be run locally **without a real Gemini API key** (mock mode).

---

## Pre-requisites
- Python 3.8+ (the repo used Python 3.10)
- A virtual environment (recommended)
- Git (for checkout/branching & PR)

---

## Files you should have (important)
- `TeachingAssistant/src/gemini_stream/websocket_client.py`
- `TeachingAssistant/src/teaching_assistant/basic_ta.py`
- `TeachingAssistant/src/teaching_assistant/_demo.py`
- `TeachingAssistant/src/memory/vector_store_adapter.py`
- `TeachingAssistant/src/memory/knowledge_graph_adapter.py`
- `TeachingAssistant/src/conversation/transcription.py`
- `TeachingAssistant/src/tests/test_basic_ta.py`
- `TeachingAssistant/src/bulk_simulate.py`
- `TeachingAssistant/src/print_buffer.py`
- `TeachingAssistant/REVIEWER_GUIDE.md` (this file)
- Logs you should receive after running: `phaseA_demo.log`, `bulk_simulate_output.txt`, (optional) `phaseA_10min.log`.

---

## Environment setup (PowerShell)

From the repository root (folder that contains the `TeachingAssistant` folder):

1. Activate your venv:
```powershell
.\.venv\Scripts\Activate.ps1
````

2. Ensure Python imports resolve:

```powershell
$env:PYTHONPATH = "$env:PYTHONPATH;."
```

3. Enable mock modes and fix console encoding for Windows:

```powershell
$env:GEMINI_MOCK = "true"
$env:TRANSCRIBER_MOCK = "true"
chcp 65001
$env:PYTHONIOENCODING = "utf-8"
```

4. (Optional) Install test deps if you want to run pytest:

```powershell
python -m pip install networkx websockets pytest pytest-asyncio --default-timeout=120 --retries=5
```

> Note: `networkx` is required by the knowledge-graph adapter. `chromadb` and `sentence-transformers` are **not** required for Phase A; the vector store uses a lightweight mock embedding by default.

---

## Quick smoke test (demo — mock mode)

Run the demo which exercises Steps 1–3 in mock mode:

```powershell
python -m TeachingAssistant.src.teaching_assistant._demo > phaseA_demo.log 2>&1
Get-Content phaseA_demo.log -Tail 40
```

### Expected demo output (tail)

You should see something like:

```
[GeminiMock] connected (mock mode)
✓ Session started with greeting for DemoStudent
✓ Question recorded: q1 (correct)
✓ Question recorded: q2 (incorrect)
Vector DB search for 'question': {...}
KG flow: [...]
✓ Session ended with closing greeting for DemoStudent
```

**What this proves:**

* WebSocket client connected (mock).
* TA greeted at session start and session end.
* Questions were recorded and stored.
* Vector store returned entries.
* Knowledge graph contains conversation nodes.

---

## Memory proof: store 60+ utterances

Run the bulk simulation which writes 60 test utterances into vector store and KG:

```powershell
python TeachingAssistant\src\bulk_simulate.py > bulk_simulate_output.txt 2>&1
Get-Content bulk_simulate_output.txt
```

### Expected output:

```
[GeminiMock] connected (mock mode)
Stored utterances: 60
KG nodes: 60
```

**What this proves:** Memory systems can store and return >50 utterances.

---

## Unit tests

Run pytest (if installed):

```powershell
python -m pytest TeachingAssistant/src/tests -q
```

### Expected:

```
2 passed
```

Tests check:

* Greeting on start and end (start_session/end_session)
* Engagement monitor triggers check-in

---

## Long-run stability (optional)

To demonstrate WebSocket stability for 10+ minutes (mock mode):

1. Edit `_demo.py` to set `monitor_interval=60` in TA construction (or create a copy for this run).
2. Run and capture logs:

```powershell
python -m TeachingAssistant.src.teaching_assistant._demo > phaseA_10min.log 2>&1
# after ~10 minutes stop with Ctrl+C
Get-Content phaseA_10min.log -Tail 80
```

Look for:

* A single `[GeminiMock] connected (mock mode)` at the top and no reconnection churn.
* Check-ins at ~60s intervals if the session idles.

---

## How to inspect internal buffers

You can use `print_buffer.py` to check last messages added to the conversation buffer:

```powershell
python TeachingAssistant\src\print_buffer.py
```

---

## Enabling real Gemini WebSocket (for later; not required for Phase A)

If you have a Gemini Live API key and want to test against the real WS:

1. Install `websockets`:

```powershell
python -m pip install websockets
```

2. Set:

```powershell
$env:GEMINI_MOCK = "false"
$env:GEMINI_API_KEY = "<YOUR_KEY>"
python -m TeachingAssistant.src.teaching_assistant._demo
```

> Note: The real Gemini Live API may require different handshakes or payload fields beyond the current mock structure — that will be handled in Step 4.

---

## Troubleshooting

* **`ModuleNotFoundError: No module named 'TeachingAssistant'`** — run commands from the repository root (the folder that contains `TeachingAssistant`), not from inside `TeachingAssistant`.
* **Garbled characters like `Γ£ô` instead of `✓`** — run:

  ```powershell
  chcp 65001
  $env:PYTHONIOENCODING = "utf-8"
  ```

  or replace the checkmark character with `OK` in `basic_ta.py` if CI complains.
* **pip timeouts** — increase timeout or download wheels manually.

---

## Expected test matrix (what reviewer should tick off)

* [ ] Demo runs and shows `[GeminiMock] connected (mock mode)`
* [ ] Demo prints startup and closing greetings
* [ ] Demo prints question records and check-in prompt
* [ ] `bulk_simulate.py` prints `Stored utterances: 60` and `KG nodes: 60`
* [ ] `pytest` shows `2 passed`
* [ ] (Optional) `phaseA_10min.log` shows stable connection, no reconnect loops

---

## Files to attach to PR (suggested)

* `phaseA_demo.log`  — demo run output
* `bulk_simulate_output.txt` — bulk simulate output
* `phaseA_10min.log` — optional long-run log
* `pytest_output.txt` — optional test run output

---

## PR description (copy/paste)

```
Title: feat(teaching-assistant): implement Steps 1–3 (Phase A) — Basic TA + Gemini mock + memory adapters

Summary:
Implements Step 1–3 and Testing & Evaluation Phase A for the Teaching Assistant feature.

Notes for reviewers:
- All verification can be run locally in mock mode (no Gemini key).
- Repro steps are in TeachingAssistant/REVIEWER_GUIDE.md.

Included evidence:
- phaseA_demo.log
- bulk_simulate_output.txt
- (optional) phaseA_10min.log
```

---

If anything errors for you or the reviewer, paste the terminal output here and I’ll give a targeted fix. If you want I can also:

* Patch `basic_ta.py` to replace `✓` with `OK` to avoid encoding issues, and provide the exact `git` commit lines.
* Generate a small GitHub Actions YAML to run `pytest` on PRs.

---

**End of Reviewer Guide**

```

---

If you want, I’ll now:
- Provide the **exact `git` commit + PR message** you can paste in one go, or
- Patch `basic_ta.py` to replace the `✓` characters with `OK` and show the `git` commands to commit.

Which would you like next?
```
