#!/usr/bin/env python3
"""
MASEE Results Analysis Script
Analyzes experiment results and generates reports
"""

import argparse
import json
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns


def load_experiment_results(results_dir: str) -> Dict[str, Any]:
    """Load all experiment results from a directory."""
    results = {}
    results_path = Path(results_dir)

    for log_file in results_path.glob("*.txt"):
        if "_log_" in log_file.name:
            # Parse filename to extract metadata
            parts = log_file.stem.split("_")
            if len(parts) >= 5:
                data_choice = parts[0]
                model = parts[2]
                experiment = parts[3]
                part = parts[4] if parts[4].isdigit() else "unknown"

                key = f"{data_choice}_{model}_{experiment}_{part}"
                results[key] = {
                    "file": str(log_file),
                    "data_choice": data_choice,
                    "model": model,
                    "experiment": experiment,
                    "part": part,
                    "size": log_file.stat().st_size
                }

    return results


def analyze_log_file(log_file: str) -> Dict[str, Any]:
    """Analyze a single log file for metrics."""
    metrics = {
        "total_lines": 0,
        "error_count": 0,
        "success_count": 0,
        "tool_calls": 0,
        "avg_response_time": 0,
        "completion_status": "unknown"
    }

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            metrics["total_lines"] = len(lines)

            for line in lines:
                line_lower = line.lower()
                if "error" in line_lower or "failed" in line_lower:
                    metrics["error_count"] += 1
                elif "success" in line_lower or "completed" in line_lower:
                    metrics["success_count"] += 1
                elif "tool" in line_lower and "call" in line_lower:
                    metrics["tool_calls"] += 1

            # Check if experiment completed
            last_lines = lines[-10:] if len(lines) > 10 else lines
            for line in last_lines:
                if "saved results" in line.lower() or "evaluation completed" in line.lower():
                    metrics["completion_status"] = "completed"
                    break
                elif "error" in line.lower() or "failed" in line.lower():
                    metrics["completion_status"] = "failed"
                    break

    except Exception as e:
        metrics["error_count"] = 1
        metrics["completion_status"] = "error"
        print(f"Error analyzing {log_file}: {e}")

    return metrics


def generate_summary_report(results: Dict[str, Any]) -> pd.DataFrame:
    """Generate a summary report of all experiments."""
    summary_data = []

    for key, result in results.items():
        metrics = analyze_log_file(result["file"])

        summary_data.append({
            "Experiment": key,
            "Data Choice": result["data_choice"],
            "Model": result["model"],
            "Experiment Type": result["experiment"],
            "Part": result["part"],
            "Status": metrics["completion_status"],
            "Total Lines": metrics["total_lines"],
            "Errors": metrics["error_count"],
            "Successes": metrics["success_count"],
            "Tool Calls": metrics["tool_calls"],
            "File Size (KB)": round(result["size"] / 1024, 2)
        })

    return pd.DataFrame(summary_data)


def create_visualizations(df: pd.DataFrame, output_dir: str):
    """Create visualizations of the results."""
    plt.style.use('default')
    sns.set_palette("husl")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # 1. Success rate by model
    fig, ax = plt.subplots(figsize=(12, 6))
    success_by_model = df.groupby('Model')['Status'].apply(
        lambda x: (x == 'completed').sum() / len(x) * 100
    ).sort_values(ascending=False)

    success_by_model.plot(kind='bar', ax=ax)
    ax.set_title('Success Rate by Model', fontsize=14, fontweight='bold')
    ax.set_xlabel('Model')
    ax.set_ylabel('Success Rate (%)')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/success_rate_by_model.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Error count by experiment type
    fig, ax = plt.subplots(figsize=(14, 6))
    error_by_exp = df.groupby('Experiment Type')['Errors'].mean().sort_values(ascending=False)

    error_by_exp.plot(kind='bar', ax=ax)
    ax.set_title('Average Error Count by Experiment Type', fontsize=14, fontweight='bold')
    ax.set_xlabel('Experiment Type')
    ax.set_ylabel('Average Errors')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/errors_by_experiment.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Status distribution
    fig, ax = plt.subplots(figsize=(8, 8))
    status_counts = df['Status'].value_counts()
    status_counts.plot(kind='pie', ax=ax, autopct='%1.1f%%')
    ax.set_title('Overall Experiment Status Distribution', fontsize=14, fontweight='bold')
    plt.savefig(f'{output_dir}/status_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Visualizations saved to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Analyze MASEE experiment results")
    parser.add_argument("--results-dir", default=".", help="Directory containing log files")
    parser.add_argument("--output-dir", default="analysis_results", help="Output directory for reports")
    parser.add_argument("--format", choices=["csv", "json", "html"], default="csv",
                       help="Output format for summary report")
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations")

    args = parser.parse_args()

    print("MASEE Results Analysis")
    print("=" * 30)

    # Load results
    print(f"Loading results from {args.results_dir}...")
    results = load_experiment_results(args.results_dir)
    print(f"Found {len(results)} experiment log files")

    if not results:
        print("No experiment log files found!")
        return

    # Generate summary
    print("Analyzing experiments...")
    summary_df = generate_summary_report(results)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Save summary report
    if args.format == "csv":
        output_file = f"{args.output_dir}/experiment_summary.csv"
        summary_df.to_csv(output_file, index=False)
    elif args.format == "json":
        output_file = f"{args.output_dir}/experiment_summary.json"
        summary_df.to_json(output_file, orient="records", indent=2)
    elif args.format == "html":
        output_file = f"{args.output_dir}/experiment_summary.html"
        summary_df.to_html(output_file, index=False, table_id="summary",
                          classes="table table-striped")

    print(f"Summary report saved to {output_file}")

    # Print key statistics
    print("\nKey Statistics:")
    print(f"Total experiments: {len(summary_df)}")
    print(f"Completed: {len(summary_df[summary_df['Status'] == 'completed'])}")
    print(f"Failed: {len(summary_df[summary_df['Status'] == 'failed'])}")
    print(f"Success rate: {len(summary_df[summary_df['Status'] == 'completed']) / len(summary_df) * 100:.1f}%")

    # Top models by success rate
    success_by_model = summary_df.groupby('Model')['Status'].apply(
        lambda x: (x == 'completed').sum() / len(x) * 100
    ).sort_values(ascending=False)

    print("\nTop models by success rate:")
    for model, rate in success_by_model.head().items():
        print(f"  {model}: {rate:.1f}%")

    # Generate visualizations
    if args.visualize:
        try:
            print("Generating visualizations...")
            create_visualizations(summary_df, f"{args.output_dir}/plots")
        except ImportError:
            print("Warning: matplotlib/seaborn not available. Skipping visualizations.")
            print("Install with: pip install matplotlib seaborn")

    print(f"\nAnalysis completed! Results saved to {args.output_dir}/")


if __name__ == "__main__":
    main()