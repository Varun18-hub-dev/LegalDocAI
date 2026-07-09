import sys
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.context import QueryContext, Intent
from app.services.retriever import Retriever
from app.utils.logging import get_logger

log = get_logger("retrieval_benchmark")

# 1. Benchmark Ground Truth Dataset calibrated for KB v2.0
BENCHMARK_DATASET = [
    {
        "query": "consequences of breach of contract compensation",
        "expected_nodes": ["contract_Section_73_7", "contract_Section_74_8"],
        "expected_docs": ["contract"],
        "description": "Breach of Contract Section 73/74"
    },
    {
        "query": "freedom of speech and expression",
        # Part III of the Constitution groups Articles 12-35
        "expected_nodes": ["constitution_PART_III_117", "constitution_Article_19_124"],
        "expected_docs": ["constitution"],
        "description": "Article 19 / Part III of Constitution"
    },
    {
        "query": "right to equality before law",
        "expected_nodes": ["constitution_PART_III_117", "constitution_Article_14_110"],
        "expected_docs": ["constitution"],
        "description": "Article 14 / Part III of Constitution"
    },
    {
        "query": "punishment for theft",
        "expected_nodes": ["bns_Section_303_399", "bns_Section_304_400", "bns_Section_305_401"],
        "expected_docs": ["bns"],
        "description": "Theft provisions under BNS 2023"
    },
    {
        "query": "evidence given by witness in judicial proceeding relevance",
        "expected_nodes": ["bsa_Section_27_45"],
        "expected_docs": ["bsa"],
        "description": "Relevance of evidence in BSA Section 27"
    },
    {
        "query": "bail provisions for accused",
        "expected_nodes": ["bnss_Section_480_778"],
        "expected_docs": ["bnss"],
        "description": "Bail provisions under BNSS 2023"
    }
]

def is_node_match(expected: str, actual: str) -> bool:
    """Helper to verify if actual retrieved node ID matches the expected ground-truth ID."""
    if expected.lower() == actual.lower():
        return True
        
    exp_parts = expected.split("_")
    if len(exp_parts) < 2:
        return expected.lower() in actual.lower()
        
    doc = exp_parts[0]
    # Check document prefix
    if not actual.lower().startswith(doc.lower()):
        return False
        
    # Extract coordinate keyword/number (e.g. 73, 19, III, 27)
    num = exp_parts[-2] if exp_parts[-1].isdigit() else exp_parts[-1]
    
    # Normalize actual underscores/hyphens to spaces to use word boundaries
    actual_clean = actual.replace("_", " ").replace("-", " ")
    pattern = rf"\b{re.escape(str(num))}\b"
    return bool(re.search(pattern, actual_clean, re.IGNORECASE))

def run_benchmark(k_values: List[int] = [1, 3, 5, 8]):
    print("=" * 80)
    print("📊  LegalDocAI - Retrieval Pipeline Evaluation & Benchmarking")
    print("=" * 80)
    
    reports = []
    total_latency = 0.0
    queries_run = 0
    
    # Store aggregated metrics
    aggregated_metrics = {k: {"recall": 0.0, "precision": 0.0} for k in k_values}
    mrr_total = 0.0
    
    for case in BENCHMARK_DATASET:
        query = case["query"]
        expected_nodes = case["expected_nodes"]
        desc = case["description"]
        
        # 1. Initialize QueryContext state-carrier
        context = QueryContext(question=query)
        context.metadata["dev_mode"] = True
        
        # Classify intent for routing
        if any(w in query.lower() for w in ("article", "section", "provision")):
            context.intent = Intent.EXPLAIN_LAW
        else:
            context.intent = Intent.LEGAL_RESEARCH
            
        start_time = time.time()
        
        # 2. Execute Retrieval
        retrieved = Retriever.retrieve(context)
        
        latency = (time.time() - start_time) * 1000
        total_latency += latency
        queries_run += 1
        
        retrieved_ids = [node["id"] for node in retrieved]
        
        # 3. Compute Metrics for each K
        case_metrics = {}
        for k in k_values:
            top_k_retrieved = retrieved_ids[:k]
            
            # Count hits based on matching function
            hits = 0
            for exp in expected_nodes:
                for act in top_k_retrieved:
                    if is_node_match(exp, act):
                        hits += 1
                        break
            
            # Bound hits to expected count
            hits = min(hits, len(expected_nodes))
            
            recall = hits / len(expected_nodes) if expected_nodes else 0.0
            precision = hits / k
            
            case_metrics[f"recall@{k}"] = recall
            case_metrics[f"precision@{k}"] = precision
            
            aggregated_metrics[k]["recall"] += recall
            aggregated_metrics[k]["precision"] += precision
            
        # Compute MRR
        mrr = 0.0
        for rank, rid in enumerate(retrieved_ids, 1):
            is_match = False
            for exp in expected_nodes:
                if is_node_match(exp, rid):
                    is_match = True
                    break
            if is_match:
                mrr = 1.0 / rank
                break
        mrr_total += mrr
        
        reports.append({
            "description": desc,
            "query": query,
            "latency_ms": round(latency, 2),
            "expected": expected_nodes,
            "retrieved": retrieved_ids[:5],
            "metrics": case_metrics,
            "mrr": round(mrr, 4)
        })
        
    # Average Aggregates
    avg_latency = total_latency / queries_run if queries_run else 0.0
    avg_mrr = mrr_total / queries_run if queries_run else 0.0
    
    for k in k_values:
        aggregated_metrics[k]["recall"] = round(aggregated_metrics[k]["recall"] / queries_run, 4)
        aggregated_metrics[k]["precision"] = round(aggregated_metrics[k]["precision"] / queries_run, 4)
        
    # Print results report
    print("\n" + "=" * 80)
    print("📈  Evaluation Report Results Summary")
    print("=" * 80)
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"Mean Reciprocal Rank (MRR): {avg_mrr:.4f}")
    print("-" * 50)
    for k in k_values:
        print(f"Recall@{k}: {aggregated_metrics[k]['recall']:.4f} | Precision@{k}: {aggregated_metrics[k]['precision']:.4f}")
    print("=" * 80)
    
    # Save Report as Markdown
    report_path = Path(__file__).resolve().parent.parent / "data" / "benchmark_report.md"
    
    md_content = f"""# Retrieval Pipeline Evaluation Report
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Overall Summary
*   **Average Latency**: {avg_latency:.2f} ms
*   **Mean Reciprocal Rank (MRR)**: {avg_mrr:.4f}

| Metric | Score |
|---|---|
"""
    for k in k_values:
        md_content += f"| **Recall@{k}** | {aggregated_metrics[k]['recall']:.4f} |\n"
        md_content += f"| **Precision@{k}** | {aggregated_metrics[k]['precision']:.4f} |\n"
        
    md_content += """
## Per-Query Diagnostics

| Query Description | Latency (ms) | MRR | Expected IDs | Top Retrieved IDs |
|---|---|---|---|---|
"""
    for rep in reports:
        md_content += f"| {rep['description']} | {rep['latency_ms']} | {rep['mrr']} | `{rep['expected']}` | `{rep['retrieved']}` |\n"
        
    report_path.write_text(md_content, encoding="utf-8")
    print(f"📝  Saved detailed markdown evaluation report to: {report_path}")

if __name__ == "__main__":
    run_benchmark()
