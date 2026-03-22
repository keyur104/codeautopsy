"""
Accuracy Tracking for CodeAutopsy
==================================
Logs every analysis with ground truth comparison for accuracy metrics.

In production, this would integrate with your incident management system
to track whether the AI's diagnosis matched the actual root cause.
"""

import json
import os
from datetime import datetime
from pathlib import Path

ACCURACY_LOG = Path(__file__).parent / "accuracy_log.jsonl"


def log_analysis(
    service_name: str,
    error_type: str,
    ai_root_cause: str,
    ai_confidence: float,
    ground_truth: str = None,
    correct: bool = None,
    time_to_diagnosis_seconds: float = None,
):
    """
    Log an analysis for accuracy tracking.
    
    Args:
        service_name: Service that had the incident
        error_type: Type of error
        ai_root_cause: What the AI diagnosed
        ai_confidence: AI's confidence score (0-100)
        ground_truth: Actual root cause (if known)
        correct: Whether AI was correct (True/False/None if unknown)
        time_to_diagnosis_seconds: How long the analysis took
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service_name": service_name,
        "error_type": error_type,
        "ai_root_cause": ai_root_cause,
        "ai_confidence_pct": ai_confidence,
        "ground_truth": ground_truth,
        "correct": correct,
        "time_to_diagnosis_seconds": time_to_diagnosis_seconds,
    }
    
    with open(ACCURACY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_accuracy_metrics():
    """
    Calculate accuracy metrics from logged analyses.
    
    Returns:
        dict with accuracy stats
    """
    if not ACCURACY_LOG.exists():
        return {
            "total_analyses": 0,
            "labeled_analyses": 0,
            "accuracy": None,
            "avg_confidence": None,
            "avg_time_seconds": None,
        }
    
    analyses = []
    with open(ACCURACY_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                analyses.append(json.loads(line))
    
    total = len(analyses)
    labeled = [a for a in analyses if a.get("correct") is not None]
    correct = [a for a in labeled if a["correct"] is True]
    
    confidences = [a["ai_confidence_pct"] for a in analyses if a.get("ai_confidence_pct")]
    times = [a["time_to_diagnosis_seconds"] for a in analyses if a.get("time_to_diagnosis_seconds")]
    
    return {
        "total_analyses": total,
        "labeled_analyses": len(labeled),
        "correct_diagnoses": len(correct),
        "accuracy": round(len(correct) / len(labeled) * 100, 1) if labeled else None,
        "avg_confidence": round(sum(confidences) / len(confidences), 1) if confidences else None,
        "avg_time_seconds": round(sum(times) / len(times), 1) if times else None,
        "confidence_when_correct": round(
            sum(a["ai_confidence_pct"] for a in correct) / len(correct), 1
        ) if correct else None,
        "confidence_when_wrong": round(
            sum(a["ai_confidence_pct"] for a in labeled if not a["correct"]) / 
            len([a for a in labeled if not a["correct"]]), 1
        ) if [a for a in labeled if not a["correct"]] else None,
    }


def seed_demo_data():
    """
    Seed the accuracy log with demo data for the hackathon.
    Shows what metrics would look like with real usage.
    """
    demo_analyses = [
        # Payment service - correct
        {
            "service_name": "payment-service",
            "error_type": "SocketTimeoutException",
            "ai_root_cause": "Timeout config reduced from 60s to 30s in recent deployment",
            "ai_confidence_pct": 96,
            "ground_truth": "Timeout config reduced from 60s to 30s in deploy d4f2a",
            "correct": True,
            "time_to_diagnosis_seconds": 47.3,
        },
        # Auth service - correct
        {
            "service_name": "auth-service",
            "error_type": "NullPointerException",
            "ai_root_cause": "Null check removed in JWT validation logic",
            "ai_confidence_pct": 92,
            "ground_truth": "Null check removed in UserService.validateToken",
            "correct": True,
            "time_to_diagnosis_seconds": 51.2,
        },
        # Order service - correct
        {
            "service_name": "order-service",
            "error_type": "DB connection pool exhaustion",
            "ai_root_cause": "Connection pool size not increased with traffic spike",
            "ai_confidence_pct": 88,
            "ground_truth": "Pool size (50) insufficient for 3x traffic increase",
            "correct": True,
            "time_to_diagnosis_seconds": 53.8,
        },
        # Notification service - correct
        {
            "service_name": "notification-service",
            "error_type": "Kafka consumer lag",
            "ai_root_cause": "Blocking HTTP call introduced in consumer thread",
            "ai_confidence_pct": 94,
            "ground_truth": "Blocking call to delivery-tracker-api in consumer",
            "correct": True,
            "time_to_diagnosis_seconds": 49.1,
        },
        # AWS DynamoDB - correct
        {
            "service_name": "dynamodb-service",
            "error_type": "DNS resolution failure",
            "ai_root_cause": "DNS race condition in automation system deleted all DynamoDB endpoint IPs",
            "ai_confidence_pct": 91,
            "ground_truth": "DNS planner/enactor race condition deleted endpoint IPs (AWS Oct 2025 real incident)",
            "correct": True,
            "time_to_diagnosis_seconds": 47.0,
        },
        # False positive example - AI was wrong
        {
            "service_name": "search-service",
            "error_type": "High latency",
            "ai_root_cause": "Elasticsearch index not optimized",
            "ai_confidence_pct": 73,
            "ground_truth": "Network partition between search-service and ES cluster",
            "correct": False,
            "time_to_diagnosis_seconds": 62.4,
        },
        # Another correct one
        {
            "service_name": "payment-service",
            "error_type": "SocketTimeoutException",
            "ai_root_cause": "Timeout config reduced in deployment",
            "ai_confidence_pct": 95,
            "ground_truth": "Timeout config reduced from 60s to 30s",
            "correct": True,
            "time_to_diagnosis_seconds": 48.9,
        },
    ]
    
    # Clear existing log
    if ACCURACY_LOG.exists():
        ACCURACY_LOG.unlink()
    
    for analysis in demo_analyses:
        analysis["timestamp"] = datetime.utcnow().isoformat() + "Z"
        with open(ACCURACY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(analysis) + "\n")
    
    print(f"✓ Seeded {len(demo_analyses)} demo analyses to {ACCURACY_LOG}")


if __name__ == "__main__":
    # Seed demo data
    seed_demo_data()
    
    # Show metrics
    metrics = get_accuracy_metrics()
    print("\n📊 Accuracy Metrics:")
    print(f"  Total analyses: {metrics['total_analyses']}")
    print(f"  Labeled (with ground truth): {metrics['labeled_analyses']}")
    print(f"  Correct diagnoses: {metrics['correct_diagnoses']}")
    print(f"  Accuracy: {metrics['accuracy']}%")
    print(f"  Avg confidence: {metrics['avg_confidence']}%")
    print(f"  Avg time to diagnosis: {metrics['avg_time_seconds']}s")
    print(f"  Confidence when correct: {metrics['confidence_when_correct']}%")
    print(f"  Confidence when wrong: {metrics['confidence_when_wrong']}%")
