"""
Audit Trail for CodeAutopsy
============================
Logs every AI recommendation with full context for accountability.

Addresses ethical concern: "If an engineer follows the AI's advice and it 
causes an outage, can you trace back what the AI said?"
"""

import json
from datetime import datetime
from pathlib import Path
import hashlib

AUDIT_LOG = Path(__file__).parent / "audit_trail.jsonl"


def log_recommendation(
    incident_id: str,
    alert_text: str,
    triage_data: dict,
    context_data: dict,
    history_data: dict,
    analysis_result: dict,
    elapsed_seconds: float,
    data_sources: list,
):
    """
    Log every AI recommendation with full context for audit trail.
    
    This creates an immutable record of:
    - What the AI was shown (inputs)
    - What the AI recommended (outputs)
    - When and how long it took
    - What data sources were used
    
    In production, this would be stored in a tamper-proof audit database.
    """
    # Generate unique incident ID if not provided
    if not incident_id:
        incident_id = hashlib.sha256(
            f"{alert_text}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]
    
    audit_entry = {
        "incident_id": incident_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0",
        "model": "claude-opus-4-6",
        
        # Inputs
        "inputs": {
            "alert_text": alert_text,
            "triage": triage_data,
            "context": {
                "logs_count": context_data.get("fetch_logs", {}).get("total_logs", 0),
                "deployments_count": len(context_data.get("get_recent_deployments", {}).get("deployments", [])),
                "trace_available": bool(context_data.get("fetch_distributed_trace")),
            },
            "history": {
                "runbooks_found": history_data.get("search_runbooks", {}).get("total_found", 0),
                "past_incidents_found": history_data.get("search_past_incidents", {}).get("total_found", 0),
            },
            "data_sources": data_sources,
        },
        
        # Outputs (AI recommendation)
        "recommendation": {
            "root_cause": analysis_result.get("root_cause"),
            "confidence_pct": analysis_result.get("confidence_pct"),
            "recommended_fix": analysis_result.get("recommended_fix"),
            "fix_code_snippet": analysis_result.get("fix_code_snippet"),
            "contributing_factors": analysis_result.get("contributing_factors", []),
            "escalation_needed": analysis_result.get("escalation_needed"),
            "escalation_reason": analysis_result.get("escalation_reason"),
            "time_to_resolve_estimate_minutes": analysis_result.get("time_to_resolve_estimate_minutes"),
        },
        
        # Metadata
        "elapsed_seconds": elapsed_seconds,
        "applied": None,  # Engineer marks this after applying fix
        "outcome": None,  # "resolved" | "made_worse" | "no_effect"
        "engineer_notes": None,
    }
    
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry) + "\n")
    
    return incident_id


def get_recommendation_by_id(incident_id: str):
    """Retrieve a specific recommendation from audit trail."""
    if not AUDIT_LOG.exists():
        return None
    
    with open(AUDIT_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                if entry["incident_id"] == incident_id:
                    return entry
    return None


def mark_recommendation_applied(incident_id: str, outcome: str, notes: str = ""):
    """
    Mark a recommendation as applied with outcome.
    
    Args:
        incident_id: The incident ID
        outcome: "resolved" | "made_worse" | "no_effect"
        notes: Engineer's notes on what happened
    """
    if not AUDIT_LOG.exists():
        return False
    
    entries = []
    updated = False
    
    with open(AUDIT_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                if entry["incident_id"] == incident_id:
                    entry["applied"] = datetime.utcnow().isoformat() + "Z"
                    entry["outcome"] = outcome
                    entry["engineer_notes"] = notes
                    updated = True
                entries.append(entry)
    
    if updated:
        with open(AUDIT_LOG, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
    
    return updated


def get_audit_stats():
    """Get statistics from audit trail."""
    if not AUDIT_LOG.exists():
        return {
            "total_recommendations": 0,
            "applied": 0,
            "resolved": 0,
            "made_worse": 0,
            "no_effect": 0,
        }
    
    entries = []
    with open(AUDIT_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    
    applied = [e for e in entries if e.get("applied")]
    
    return {
        "total_recommendations": len(entries),
        "applied": len(applied),
        "resolved": len([e for e in applied if e.get("outcome") == "resolved"]),
        "made_worse": len([e for e in applied if e.get("outcome") == "made_worse"]),
        "no_effect": len([e for e in applied if e.get("outcome") == "no_effect"]),
        "avg_confidence": round(
            sum(e["recommendation"]["confidence_pct"] for e in entries) / len(entries), 1
        ) if entries else 0,
    }


if __name__ == "__main__":
    # Demo: seed some audit entries
    print("Seeding demo audit trail...")
    
    demo_entries = [
        {
            "alert": "payment-service SocketTimeoutException",
            "root_cause": "Timeout config reduced from 60s to 30s",
            "confidence": 96,
            "outcome": "resolved",
        },
        {
            "alert": "auth-service NullPointerException",
            "root_cause": "Null check removed in JWT validation",
            "confidence": 92,
            "outcome": "resolved",
        },
        {
            "alert": "search-service high latency",
            "root_cause": "Elasticsearch index not optimized",
            "confidence": 73,
            "outcome": "made_worse",  # AI was wrong
        },
    ]
    
    for demo in demo_entries:
        incident_id = log_recommendation(
            incident_id="",
            alert_text=demo["alert"],
            triage_data={"service_name": demo["alert"].split()[0], "error_type": "unknown"},
            context_data={},
            history_data={},
            analysis_result={
                "root_cause": demo["root_cause"],
                "confidence_pct": demo["confidence"],
                "recommended_fix": "See analysis",
            },
            elapsed_seconds=50.0,
            data_sources=["logs", "deployments"],
        )
        mark_recommendation_applied(incident_id, demo["outcome"], "Demo entry")
    
    stats = get_audit_stats()
    print(f"\n✓ Audit trail seeded")
    print(f"  Total recommendations: {stats['total_recommendations']}")
    print(f"  Applied: {stats['applied']}")
    print(f"  Resolved: {stats['resolved']}")
    print(f"  Made worse: {stats['made_worse']}")
