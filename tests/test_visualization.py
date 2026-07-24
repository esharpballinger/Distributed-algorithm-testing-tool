"""
File: test_visualization.py
Description: tests for the MIS round-by-round HTML visualization
Author: Evan Sharp-Ballinger and Gonzalo Estrella
"""

import json
import re
from pathlib import Path

from src.maximal_independent_set import GreedyMISInit, Status
from src.mis_visualization import run_with_history, render_html, write_html

GOOBER = str(Path(__file__).resolve().parent.parent / "src" / "goober.txt")


def test_run_with_history_records_every_round():
    algorithm = GreedyMISInit(GOOBER, seed=42)
    supervisor, history = run_with_history(algorithm)

    # one snapshot before the first round plus one per round
    assert len(history) == supervisor.round + 1
    # everyone starts undecided and ends decided
    assert all(status == "undecided" for status in history[0])
    assert all(status != "undecided" for status in history[-1])
    # each snapshot covers every node
    assert all(len(snapshot) == algorithm.n for snapshot in history)


def test_render_html_embeds_run_data():
    algorithm = GreedyMISInit(GOOBER, seed=42)
    _, history = run_with_history(algorithm)
    html = render_html(algorithm, history)

    assert "<svg" in html
    data = json.loads(re.search(r"const RUN = (\{.*?\});", html, re.S).group(1))
    assert data["n"] == algorithm.n
    assert data["seed"] == 42
    assert data["rounds"] == len(history)
    assert data["statuses"] == history
    assert data["ranks"] == algorithm.ranks
    assert sorted(data["mis"]) == sorted(algorithm.expected_mis)
    assert data["checks"] == {"independent": True, "maximal": True, "matches_greedy": True}
    # every undirected edge appears exactly once
    edges = {tuple(sorted(e)) for e in data["edges"]}
    expected = {tuple(sorted((u, v))) for u in algorithm.graph for v in algorithm.graph[u]}
    assert edges == expected and len(data["edges"]) == len(expected)


def test_write_html_creates_file(tmp_path):
    algorithm = GreedyMISInit(GOOBER, seed=7)
    _, history = run_with_history(algorithm)
    out = tmp_path / "mis_run.html"
    write_html(algorithm, history, str(out))
    assert out.exists()
    assert "<svg" in out.read_text()
