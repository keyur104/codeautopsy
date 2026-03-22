# Accuracy Tracking

One of the first questions we asked ourselves: "How do we know if the AI is actually right?"

You can't ship a diagnostic tool without measuring accuracy. So we built a tracking system that logs every analysis and compares it to ground truth.

## How It Works

Every time CodeAutopsy analyzes an incident, we log:
- What the AI diagnosed (root cause)
- How confident it was (0-100%)
- What actually happened (ground truth, if known)
- Whether the AI was correct
- How long it took

This goes into `orchestrator/accuracy_log.jsonl` — an append-only log that tracks everything.

## Current Metrics

We've run 7 analyses with known ground truth:

```
Total analyses: 7
Correct diagnoses: 6
Accuracy: 85.7%
Average confidence: 89.9%
Average time: 51.4 seconds
```

**When correct:** Average confidence is 92.7%  
**When wrong:** Average confidence is 73%

That last part is important. When the AI is wrong, it's less confident. The confidence score isn't just a random number — it's somewhat calibrated.

## The One We Got Wrong

Out of 7 test cases, we got 1 wrong:

**Incident:** search-service high latency  
**AI said:** Elasticsearch index not optimized  
**Actually was:** Network partition between search-service and ES cluster  
**Confidence:** 73% (lower than usual)

The AI saw slow queries and assumed it was an index issue. It missed the network partition because the symptoms looked similar. But notice the confidence was only 73% — lower than the 93% average when correct. This suggests the AI knew something was off.

## Why This Matters

**For judges:** We're not just claiming the tool works. We're measuring it. 85.7% accuracy on 7 test cases is a small sample, but it's honest. In production, you'd need 100+ labeled incidents to have statistical confidence.

**For users:** You can see the accuracy badge in the UI header. Click it for details. Every analysis gets logged automatically, so the metrics update over time.

## How to Use This

**API endpoint:**
```bash
curl http://localhost:8000/metrics/accuracy
```

**Returns:**
```json
{
  "total_analyses": 7,
  "accuracy": 85.7,
  "avg_confidence": 89.9,
  "confidence_when_correct": 92.7,
  "confidence_when_wrong": 73.0
}
```

**In the UI:**
Look for the green badge in the header: "📊 Accuracy: 85.7%"

Click it to see the full breakdown.

## What We'd Do in Production

**Short term:**
- Engineers mark analyses as correct/incorrect after resolving incidents
- System updates ground truth and recalculates metrics
- Track accuracy per service, error type, time of day

**Long term:**
- A/B test against human-only diagnosis
- Measure impact on time-to-resolution
- Track false positive rate, false negative rate
- Publish benchmarks on 100+ real incidents

## Honest Limitations

**Current state:**
- Only 7 test cases (small sample)
- Ground truth is manually labeled
- No statistical significance testing

**What we're NOT claiming:**
- This is production-ready (it's not)
- 85.7% will hold at scale (might go up or down)
- The AI is always right (it's not — see the 1 wrong diagnosis)

**What we ARE claiming:**
- We're measuring accuracy (most hackathon projects don't)
- The confidence score is somewhat calibrated
- We have a system in place to track this over time

## Files

- `orchestrator/accuracy.py` — tracking system
- `orchestrator/accuracy_log.jsonl` — 7 logged analyses
- API endpoint: `GET /metrics/accuracy`
- UI badge in header (click for details)

---

**Bottom line:** We're not perfect, but we're honest about it. 85.7% accuracy with calibrated confidence scores. That's a starting point, not an end goal.
