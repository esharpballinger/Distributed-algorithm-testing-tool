"""
File: test_mis.py
Description: tests for the greedy randomized maximal independent set algorithm
Author: Evan Sharp-Ballinger and Gonzalo Estrella
"""

import random
from pathlib import Path

import pytest

from src.node import Algorithm
from src.supervisor import Supervisor
from src.maximal_independent_set import GreedyMISInit, Status

GOOBER = str(Path(__file__).resolve().parent.parent / "src" / "goober.txt")


def run_mis(filename, seed):
    algorithm = GreedyMISInit(filename, seed=seed)
    supervisor = Supervisor(algorithm.nodes, algorithm)
    supervisor.run_simulation()
    return algorithm, supervisor


def mis_of(nodes):
    return {node.id for node in nodes if node.data is Status.IN_MIS}


def assert_valid_mis(algorithm):
    nodes = algorithm.nodes
    in_set = mis_of(nodes)
    # every node has decided
    assert all(node.data is not Status.UNDECIDED for node in nodes)
    # independence: no two adjacent nodes are both in the set
    for v in in_set:
        assert not (algorithm.graph[v] & in_set), f"node {v} has a neighbor in the MIS"
    # maximality: every excluded node has a neighbor in the set
    for node in nodes:
        if node.id not in in_set:
            assert algorithm.graph[node.id] & in_set, f"node {node.id} could join"
    # matches the sequential greedy result for the same permutation
    assert in_set == algorithm.expected_mis


def write_graph_file(tmp_path, n, edges):
    neighbors = {i: [] for i in range(n)}
    for u, v in edges:
        neighbors[u].append(v)
    content = f"{n}\n" + "\n".join(
        " ".join(str(v) for v in neighbors[i]) for i in range(n)
    ) + "\n"
    path = tmp_path / "graph.txt"
    path.write_text(content)
    return str(path)


def test_graph_input_parses_neighbor_ids_as_ints():
    graph = Algorithm.graph_input(GOOBER)
    assert graph == {0: [1, 2, 3], 1: [0, 4], 2: [0], 3: [1], 4: [4]}


def test_init_symmetrizes_adjacency_and_drops_self_loops():
    algorithm = GreedyMISInit(GOOBER, seed=0)
    assert algorithm.graph == {
        0: {1, 2, 3},
        1: {0, 3, 4},
        2: {0},
        3: {0, 1},
        4: {1},
    }


@pytest.mark.parametrize("seed", [0, 1, 7, 12345])
def test_goober_graph_end_to_end(seed):
    algorithm, _ = run_mis(GOOBER, seed)
    assert_valid_mis(algorithm)


def test_same_seed_reproduces_same_mis():
    first, _ = run_mis(GOOBER, 42)
    second, _ = run_mis(GOOBER, 42)
    assert mis_of(first.nodes) == mis_of(second.nodes)


@pytest.mark.parametrize("seed", [3, 11, 2024])
def test_random_graphs_end_to_end(tmp_path, seed):
    rng = random.Random(seed)
    n = 30
    edges = [
        (u, v)
        for u in range(n)
        for v in range(u + 1, n)
        if rng.random() < 0.15
    ]
    filename = write_graph_file(tmp_path, n, edges)
    algorithm, _ = run_mis(filename, seed)
    assert_valid_mis(algorithm)


def test_single_node_joins(tmp_path):
    filename = write_graph_file(tmp_path, 1, [])
    algorithm, _ = run_mis(filename, seed=5)
    assert mis_of(algorithm.nodes) == {0}


def test_edgeless_graph_everyone_joins(tmp_path):
    filename = write_graph_file(tmp_path, 4, [])
    algorithm, _ = run_mis(filename, seed=5)
    assert mis_of(algorithm.nodes) == {0, 1, 2, 3}


def test_complete_graph_exactly_one_joins(tmp_path):
    n = 6
    edges = [(u, v) for u in range(n) for v in range(u + 1, n)]
    filename = write_graph_file(tmp_path, n, edges)
    algorithm, _ = run_mis(filename, seed=9)
    in_set = mis_of(algorithm.nodes)
    assert len(in_set) == 1
    assert_valid_mis(algorithm)
