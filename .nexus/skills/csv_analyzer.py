"""NexusAgent Skill: Analyze CSV files and output statistical summaries."""

import csv
import io
from collections import Counter
from typing import Optional


def run(csv_content: str, delimiter: str = ",") -> dict:
    """Analyze CSV content and return summary statistics."""
    reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return {"error": "Empty CSV", "rows": 0}

    summary = {"rows": len(rows), "columns": list(rows[0].keys())}
    for col in rows[0].keys():
        values = [r[col] for r in rows if r[col]]
        numeric = []
        for v in values:
            try:
                numeric.append(float(v))
            except (ValueError, TypeError):
                pass
        if numeric:
            summary[col] = {
                "type": "numeric",
                "count": len(numeric),
                "mean": round(sum(numeric) / len(numeric), 4),
                "min": min(numeric),
                "max": max(numeric),
            }
        else:
            summary[col] = {"type": "categorical", "unique": len(set(values)), "top": Counter(values).most_common(3)}
    return summary
