from collections import Counter
from dataclasses import dataclass


@dataclass
class YearAggregate:
    year: int
    incident_count: int
    total_stremmata_burned: float
    top_prefectures: list[tuple[str, int]]


def aggregate_year(year: int, rows: list[dict]) -> YearAggregate:
    total_stremmata = 0.0
    prefecture_counts: Counter = Counter()

    for row in rows:
        total_stremmata += row["stremmata_burned"]
        prefecture = row["prefecture"].strip()
        if prefecture:
            prefecture_counts[prefecture] += 1

    return YearAggregate(
        year=year,
        incident_count=len(rows),
        total_stremmata_burned=total_stremmata,
        top_prefectures=prefecture_counts.most_common(3),
    )
