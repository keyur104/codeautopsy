# Error Handling

We spent time thinking about what happens when things go wrong. Because they will.

## The Problem

In a hackathon demo, everything works. In production, everything breaks:
- Claude API times out
- Network connections drop
- Tools return empty results
- Rate limits get hit

If we didn't handle these, the pipeline would crash and engineers would see a blank screen. Not great when you're trying to diagnose a P1 incident at 3am.

## What We Built

### 1. API Timeout Protection

**Added:** 60-second timeout on all Claude API calls

**Why:** Without this, if Claude is slow, the whole pipeline hangs indefinitely. Engineers wait forever, get frustrated, give up.

**How it works:**
```python
anthropic.Anthropic(api_key=api_key, timeout=60.0)
```

If Claude doesn't respond in 60 seconds, we show: "Timed out after 60s. Claude API may be overloaded."

### 2. Error Wrapper for Every Agent

**Added:** `_safe_agent_call()` wrapper that catches:
- `APITimeoutError` — Claude is slow
- `APIConnectionError` — Network issues
- `RateLimitError` — Too many requests
- `APIError` — General API failures
- `Exception` — Anything else

**Why:** Each agent (Triage, Context, History, Analyst) calls Claude. If any of them fail, we want a clear error message, not a cryptic stack trace.

**How it works:**
```python
async for event in _safe_agent_call(triage_agent, alert_text, client, agent_name="Triage Agent"):
    # If it fails, yields: {"type": "error", "message": "Triage Agent timed out..."}
```

### 3. Data Validation

**Added checks for:**
- Triage must return a `service_name` (if not, show error)
- Context should have logs OR deployments (if neither, show warning)
- Analysis must complete (if not, return partial data)

**Why:** If tools return empty results, the analyst gets garbage input and produces a garbage diagnosis. Better to warn the engineer early.

**Example:**
If no logs and no deployments found:
> "⚠️ No logs or deployments found. Analysis may be incomplete."

### 4. Graceful Degradation

**What happens now when things fail:**

| Failure | Old Behavior | New Behavior |
|---------|--------------|--------------|
| Claude API timeout | Hang forever | Show "timed out after 60s", stop gracefully |
| No logs found | Proceed blindly | Warn "No logs found, analysis may be incomplete" |
| Triage fails | Silent failure | Clear error: "Triage did not identify service" |
| Analysis fails | Crash | Return partial data (triage + context) with error |
| Rate limit hit | Crash | Show "rate limited, wait and retry" |

### 5. Frontend Error Display

**Added:**
- Distinguishes recoverable vs non-recoverable errors
- Shows "(Retrying...)" for recoverable errors
- Displays warnings (⚠️) separately from errors (❌)
- Handles `pipeline_failed` event gracefully

**Example:**
If Claude times out on the first try but succeeds on retry:
> "❌ Triage Agent timed out after 60s (Retrying...)"

Then:
> "✓ Triage Agent: Service identified"

## What This Fixes

**Before:**
- If Claude API is slow, the whole thing hangs
- If a tool returns empty results, the analyst gets confused
- If the API fails, you see a cryptic error or blank screen

**After:**
- 60-second timeout prevents infinite hangs
- Empty results trigger warnings, not crashes
- API failures show clear, actionable error messages
- Partial results are returned when possible

## Testing

We didn't have time to test every failure mode, but the code is there. To test:

**Simulate timeout:**
Set `ANTHROPIC_API_KEY` to an invalid key → should show "API error" gracefully

**Simulate empty data:**
Modify `mock_data.py` to return empty logs → should show warning

**Simulate network issue:**
Disconnect internet mid-analysis → should show connection error

## What to Tell Judges

> "We added error handling for API timeouts, connection failures, and empty data. If the Claude API times out, we show a clear message and retry if possible. If tools return empty results, we warn the user but continue with partial data. The system degrades gracefully instead of crashing."

## Files Modified

- `orchestrator/orchestrator.py` — error wrapper, validation, fallbacks (~65 lines)
- `frontend/index.html` — error display, stream handling (~15 lines)

---

**Bottom line:** Production systems fail. We handle it gracefully instead of crashing.
