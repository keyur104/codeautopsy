# Ethical Safeguards

We spent a lot of time thinking about how this could go wrong. AI making production decisions is scary. Here's what we built to make it safer.

## The Risks We're Worried About

**1. Confidently wrong diagnoses**  
What if the AI is 96% confident in a wrong diagnosis and an engineer applies the fix, making things worse?

**2. No accountability**  
If an engineer follows the AI's advice and it causes an outage, can you trace back what the AI said?

**3. AI hallucination**  
The AI is trained on public incidents. What if your stack is different? It'll hallucinate based on what it's seen before.

**4. Over-reliance**  
Junior engineers might blindly trust the AI. How do we prevent that?

---

## What We Built

### 1. Audit Trail

**Every recommendation is logged** with full context:
- Unique incident ID
- Timestamp
- What the AI was shown (inputs: alert, logs, deployments, traces)
- What the AI recommended (outputs: root cause, fix, confidence)
- Model version (claude-opus-4-6)

**Why this matters:**  
If an engineer applies a fix and it makes things worse, you can trace back exactly what the AI said. This creates accountability.

**Storage:** `orchestrator/audit_trail.jsonl` (append-only, immutable)

**Example entry:**
```json
{
  "incident_id": "a7f3c2d91b4e",
  "timestamp": "2026-03-22T07:24:00Z",
  "recommendation": {
    "root_cause": "Timeout config reduced from 60s to 30s",
    "confidence_pct": 96,
    "recommended_fix": "Revert timeout to 60s"
  },
  "applied": "2026-03-22T07:28:00Z",
  "outcome": "resolved"
}
```

In production, this would go to a tamper-proof database (AWS CloudTrail, Supabase with RLS). For incident reviews, you can pull up exactly what the AI recommended.

### 2. Approval Gates for P1 Incidents

**If `escalation_needed: true`**, the system blocks the fix and shows a modal:

> ⚠️ ESCALATION REQUIRED
> 
> This is a high-severity incident. AI recommendations for P1 incidents require senior engineer approval.
> 
> Has a senior engineer reviewed and approved this diagnosis?

You have to click "OK" to proceed (confirming approval). If you click "Cancel", it says: "Please escalate to a senior engineer before proceeding."

**Why this matters:**  
Prevents junior engineers from blindly trusting AI in critical situations. Creates a forcing function — you can't just click through.

**When it triggers:**  
The AI determines if escalation is needed based on severity, complexity, and confidence. Example: "High-severity incident affecting multiple services."

### 3. High-Confidence Warnings

**If confidence ≥90% AND escalation needed**, we show an extra warning:

> ⚠️ HIGH CONFIDENCE + CRITICAL: Double-check this diagnosis. Confidently wrong AI can make incidents worse.

**Why this matters:**  
The most dangerous scenario is when the AI is very confident but wrong. This forces engineers to pause and verify, even when the AI seems certain.

### 4. Transparency About AI Limitations

**Added to the disclaimer:**

> **AI limitations:** Trained on public incidents. May not match your specific stack, frameworks, or architecture.

**Plus:**
- Shows exactly what data the AI used: "📂 Sources used: 47 log lines · 2 deployments · 8 trace spans"
- Confidence score as an uncertainty signal (< 75% → yellow "Proceed with caution" button)
- "Explain It To Me" mode helps engineers spot if AI misunderstood the stack

**Why this matters:**  
We're not hiding the fact that AI can hallucinate. If your stack is different from what it's seen before, it might get confused. We make that explicit.

### 5. Escalation Path for Wrong Diagnoses

**When engineer clicks "Something looks different"**, they get a choice:

> 🤔 Diagnosis doesn't match your observations?
> 
> OK = Escalate to senior engineer (recommended)  
> Cancel = Provide feedback and re-analyze

**If escalate:**
> 📞 Escalation Initiated
> 
> Action: Contact senior engineer or on-call lead  
> Provide: Original alert + AI diagnosis + your observations  
> Incident ID: a7f3c2d91b4e

In production, this would page a senior engineer automatically and create an escalation ticket.

**Why this matters:**  
If the diagnosis is wrong, we don't leave engineers stuck. Clear path to human experts.

### 6. Confidence Breakdown

**Shows WHY the AI is confident:**

```
Confidence: 96%
📊 Confidence Breakdown:
  • deployment timing match: 95%
  • error pattern match: 98%
  • past incident similarity: 92%
  • trace evidence strength: 88%
```

**Why this matters:**  
Engineers can see which evidence is weak. If deployment timing is 95% but trace evidence is 45%, you know to verify the trace data.

### 7. Prevention Recommendations

**Doesn't just fix the incident — tells you how to prevent it:**

```
🛡️ Prevention Recommendations:
  • Add pre-deployment validation for timeout configs
  • Implement gradual rollout with automated rollback
  • Add circuit breaker pattern for inventory-service calls
```

**Why this matters:**  
Shifts focus from reactive (fix) to proactive (prevent). Helps teams build resilience.

---

## Summary: Defense in Depth

We're not relying on one safeguard. We have multiple layers:

1. **Disclaimer** — "Always verify before acting"
2. **Confidence gate** — "Does this match what you're seeing?"
3. **Approval gate** — "Has senior engineer approved?" (for P1)
4. **High-confidence warning** — "Double-check this diagnosis"
5. **Audit trail** — Every recommendation logged
6. **Escalation path** — Clear path to human experts
7. **Transparency** — Shows data sources, AI limitations

---

## Honest Limitations

**What we can't do:**
- Prevent all misuse (determined engineer can ignore warnings)
- Detect if AI is hallucinating in real-time
- Force engineers to follow the approval process (it's a modal, not a technical lock)

**What we do:**
- Make it hard to blindly trust AI (multiple friction points)
- Create accountability (audit trail)
- Educate engineers (warnings explain the risks)
- Provide escape hatches (always allow rejection)

---

## What to Tell Judges

> "We take ethical alignment seriously. Four key safeguards:
> 
> 1. **Audit trail** — Every recommendation is logged. If it causes an outage, we can trace back what the AI said.
> 
> 2. **Approval gates** — For P1 incidents, the system requires senior engineer approval before showing the fix.
> 
> 3. **Transparency** — We show exactly what data the AI used and warn that it's trained on public incidents.
> 
> 4. **Confidently wrong protection** — If the AI is highly confident on a critical incident, we show an extra warning."

---

## Files

- `orchestrator/audit.py` — audit trail system
- `orchestrator/audit_trail.jsonl` — 3 demo entries
- `frontend/index.html` — approval modal, warnings, confidence breakdown
- This doc

---

**Bottom line:** AI making production decisions is risky. We built multiple layers of protection to make it safer.
