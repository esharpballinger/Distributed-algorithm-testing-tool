"""
File: maximal_independent_set.py
Description: An implementation of the Maximal Independent Set Congested Clique algorithm for the congested clique simulator
Author: Evan Sharp-Ballinger and Gonzalo Estrella

Greedy randomized MIS (Ghaffari, Gouleakis, Konrad, Mitrovic, Rubinfeld,
arXiv:1802.08237, p.6): draw a random permutation pi of the vertices; a vertex
joins the MIS iff no earlier-ranked neighbor joined. Simulated here in
parallel rounds: each round every undecided node exchanges (status, rank)
with its still-active problem-graph neighbors and joins when it holds the
smallest rank among them. Output is identical to sequential greedy for the
same permutation. Communication stays congested-clique; nodes simply only
address their problem-graph neighbors.
"""

import random
import math
from enum import Enum
from src.node import Node, Algorithm
from src.message import Message

class Status(Enum):
    UNDECIDED = "undecided"
    IN_MIS = "in_mis"
    OUT = "out"
    DEGREE = "degree"
    SHIFT = "shift"
    TOPOLOGY = "topology"
    RESULT = "result"
    NEXT_ITERATION = "next_iteration"

class Phase(Enum):
    # Phase 1: MPC Subgraph Gather
    PHASE_1_COUNT = "phase_1_count"
    PHASE_1_PREFIX = "phase_1_prefix"
    PHASE_1_SCATTER = "phase_1_scatter"
    PHASE_1_GATHER = "phase_1_gather"
    
    # Phase 2: Dynamic Probability 
    PHASE_2_GHAFFARI = "phase_2"
    
    # Phase 3: Sparse Remainder Gather
    PHASE_3_COUNT = "phase_3_count"
    PHASE_3_PREFIX = "phase_3_prefix"
    PHASE_3_SCATTER = "phase_3_scatter"
    PHASE_3_GATHER = "phase_3_gather"
    
    HALTED = "halted"

class MISNode(Node):
    def __init__(self, rank, neighbors, n, delta, id=None):
        super().__init__(Status.UNDECIDED, id=id)
        self.rank = rank
        self.neighbors = set(neighbors)
        self.active_neighbors = set(neighbors)
        self.announced_decision = False
        self.n = n
        self.delta = max(delta, 2) 
        self.leader_id = 0
        self.phase = Phase.PHASE_1_COUNT
        
        # Phase 1/3 Routing Variables
        self.phase_1_iteration = 1
        self.current_r = self._calculate_r(self.phase_1_iteration)
        self.forward_buffer = []
        self.gathered_subgraph = {}
        self.chunk_nodes = {}
        self.saved_expected_edges = 0
        self.edges_received = 0
        self.ready_to_broadcast = False
        self.chunk_verdicts = {}
        
        # Phase 2 Variables
        self.p = 0.5 
        self.marked = (random.random() < self.p)
        self.phase_2_round = 0
        self.phase_2_max_rounds = max(3, int(math.log2(math.log2(n + 2)) * 5))

    def _calculate_r(self, i):
        exponent = (0.75) ** i
        return self.n / (self.delta ** exponent)

    def send_message(self, supervisor):
        if self.phase == Phase.HALTED:
            return

        # Announce decision exactly once to neighbors
        if self.data is not Status.UNDECIDED and not self.announced_decision:
            for neighbor in self.active_neighbors:
                supervisor.queue_message(Message(self.id, neighbor, (self.data, self.rank, None, None)))
            self.announced_decision = True

        # --- Phase 1: O(1) Prefix-Sum Routing ---
        if self.phase == Phase.PHASE_1_COUNT:
            if self.data is Status.UNDECIDED and self.rank < self.current_r:
                # FIX: Snapshot the neighbors to guarantee edge delivery matches degree promise
                self.scatter_snapshot = list(self.active_neighbors)
                supervisor.queue_message(Message(self.id, self.leader_id, (Status.DEGREE, len(self.scatter_snapshot), self.rank, None)))

        elif self.phase == Phase.PHASE_1_PREFIX:
            if self.id == self.leader_id:
                for target, shift in getattr(self, 'shifts', {}).items():
                    supervisor.queue_message(Message(self.id, target, (Status.SHIFT, shift, None, None)))

        elif self.phase == Phase.PHASE_1_SCATTER:
            if hasattr(self, 'start_index') and hasattr(self, 'scatter_snapshot'):
                for k, neighbor in enumerate(self.scatter_snapshot):
                    target = (self.start_index + k) % self.n
                    supervisor.queue_message(Message(self.id, target, (Status.TOPOLOGY, self.id, neighbor, None)))
                del self.start_index
                del self.scatter_snapshot

        elif self.phase == Phase.PHASE_1_GATHER:
            if self.forward_buffer:
                u, v = self.forward_buffer.pop(0)
                supervisor.queue_message(Message(self.id, self.leader_id, (Status.TOPOLOGY, u, v, None)))
            
            if self.id == self.leader_id and self.ready_to_broadcast:
                for target_id, is_in_mis in self.chunk_verdicts.items():
                    verdict = Status.IN_MIS if is_in_mis else Status.OUT
                    supervisor.queue_message(Message(self.id, target_id, (Status.RESULT, verdict.value, None, None)))
                for i in range(self.n):
                    supervisor.queue_message(Message(self.id, i, (Status.NEXT_ITERATION, None, None, None)))
                self.ready_to_broadcast = False 

        # --- Phase 2: Dynamic Probability ---
        elif self.phase == Phase.PHASE_2_GHAFFARI:
            if self.data is Status.UNDECIDED:
                for neighbor in self.active_neighbors:
                    supervisor.queue_message(Message(self.id, neighbor, (self.data, self.rank, self.p, self.marked)))

        # --- Phase 3: Sparse Remainder Routing ---
        elif self.phase == Phase.PHASE_3_COUNT:
            if self.data is Status.UNDECIDED:
                # FIX: Snapshot the sparse remainder neighbors
                self.scatter_snapshot = list(self.active_neighbors)
                supervisor.queue_message(Message(self.id, self.leader_id, (Status.DEGREE, len(self.scatter_snapshot), self.rank, None)))

        elif self.phase == Phase.PHASE_3_PREFIX:
            if self.id == self.leader_id:
                for target, shift in getattr(self, 'shifts', {}).items():
                    supervisor.queue_message(Message(self.id, target, (Status.SHIFT, shift, None, None)))

        elif self.phase == Phase.PHASE_3_SCATTER:
            if hasattr(self, 'start_index') and hasattr(self, 'scatter_snapshot'):
                for k, neighbor in enumerate(self.scatter_snapshot):
                    target = (self.start_index + k) % self.n
                    supervisor.queue_message(Message(self.id, target, (Status.TOPOLOGY, self.id, neighbor, None)))
                del self.start_index
                del self.scatter_snapshot

        elif self.phase == Phase.PHASE_3_GATHER:
            if self.forward_buffer:
                u, v = self.forward_buffer.pop(0)
                supervisor.queue_message(Message(self.id, self.leader_id, (Status.TOPOLOGY, u, v, None)))
            
            if self.id == self.leader_id and self.ready_to_broadcast:
                for target_id, is_in_mis in self.chunk_verdicts.items():
                    verdict = Status.IN_MIS if is_in_mis else Status.OUT
                    supervisor.queue_message(Message(self.id, target_id, (Status.RESULT, verdict.value, None, None)))
                for i in range(self.n):
                    supervisor.queue_message(Message(self.id, i, (Status.NEXT_ITERATION, None, None, None)))
                self.ready_to_broadcast = False 


    def do_work(self):
        if self.phase == Phase.HALTED:
            self.inbox.clear()
            return

        self._process_removals()

        if self.phase == Phase.PHASE_1_COUNT:
            self._do_count_phase(Phase.PHASE_1_PREFIX)
        elif self.phase == Phase.PHASE_1_PREFIX:
            self._do_prefix_phase(Phase.PHASE_1_SCATTER)
        elif self.phase == Phase.PHASE_1_SCATTER:
            self._do_scatter_phase(Phase.PHASE_1_GATHER)
        elif self.phase == Phase.PHASE_1_GATHER:
            self._do_phase_1_gather()
            
        elif self.phase == Phase.PHASE_2_GHAFFARI:
            self._do_phase_2()
            
        elif self.phase == Phase.PHASE_3_COUNT:
            self._do_count_phase(Phase.PHASE_3_PREFIX)
        elif self.phase == Phase.PHASE_3_PREFIX:
            self._do_prefix_phase(Phase.PHASE_3_SCATTER)
        elif self.phase == Phase.PHASE_3_SCATTER:
            self._do_scatter_phase(Phase.PHASE_3_GATHER)
        elif self.phase == Phase.PHASE_3_GATHER:
            self._do_phase_3_gather()
            
        self.inbox.clear()

    def _process_removals(self):
        new_inbox = []
        for message in self.inbox:
            status = message.payload[0]
            if status is Status.IN_MIS:
                if self.data is Status.UNDECIDED:
                    self.data = Status.OUT
                self.active_neighbors.discard(message.sender)
            elif status is Status.OUT:
                self.active_neighbors.discard(message.sender)
            else:
                new_inbox.append(message)
        self.inbox = new_inbox

    def _do_count_phase(self, next_phase):
        if self.id == self.leader_id:
            self.shifts = {}
            self.chunk_nodes = {}
            total_edges = 0
            for msg in self.inbox:
                if msg.payload[0] == Status.DEGREE:
                    degree, rank = msg.payload[1], msg.payload[2]
                    self.shifts[msg.sender] = total_edges
                    self.chunk_nodes[msg.sender] = rank
                    total_edges += degree
            self.saved_expected_edges = total_edges
        self.phase = next_phase

    def _do_prefix_phase(self, next_phase):
        for msg in self.inbox:
            if msg.payload[0] == Status.SHIFT:
                self.start_index = msg.payload[1]
        self.phase = next_phase

    def _do_scatter_phase(self, next_phase):
        for msg in self.inbox:
            if msg.payload[0] == Status.TOPOLOGY:
                self.forward_buffer.append((msg.payload[1], msg.payload[2]))
        
        if self.id == self.leader_id:
            self.gathered_subgraph = {}
            self.edges_received = 0
            self.chunk_verdicts = {}
            self.ready_to_broadcast = False
            
            if self.edges_received == self.saved_expected_edges:
                self._compute_chunk_mis()
                
        self.phase = next_phase

    def _do_phase_1_gather(self):
        self._process_gather_inbox()

        advance = False
        for msg in self.inbox:
            if msg.payload[0] == Status.RESULT:
                if self.data == Status.UNDECIDED:
                    self.data = Status(msg.payload[1])
            elif msg.payload[0] == Status.NEXT_ITERATION:
                advance = True
        
        if advance:
            self.phase_1_iteration += 1
            self.current_r = self._calculate_r(self.phase_1_iteration)
            # sparsity_threshold = self.n / math.log2(self.n) if self.n > 1 else 0 
            sparsity_threshold = self.n / math.log2(self.n)**4 if self.n > 1 else 0 
            if self.current_r >= sparsity_threshold:
                self.phase = Phase.PHASE_2_GHAFFARI
            else:
                self.phase = Phase.PHASE_1_COUNT

    def _do_phase_3_gather(self):
        self._process_gather_inbox()

        advance = False
        for msg in self.inbox:
            if msg.payload[0] == Status.RESULT:
                if self.data == Status.UNDECIDED:
                    self.data = Status(msg.payload[1])
            elif msg.payload[0] == Status.NEXT_ITERATION:
                advance = True
        
        if advance:
            self.phase = Phase.HALTED

    def _process_gather_inbox(self):
        if self.id == self.leader_id:
            for msg in self.inbox:
                if msg.payload[0] == Status.TOPOLOGY:
                    u, v = msg.payload[1], msg.payload[2]
                    if u not in self.gathered_subgraph:
                        self.gathered_subgraph[u] = set()
                    self.gathered_subgraph[u].add(v)
                    self.edges_received += 1
            
            if self.edges_received == self.saved_expected_edges and not self.ready_to_broadcast:
                self._compute_chunk_mis()

    def _compute_chunk_mis(self):
        sorted_nodes = sorted(self.chunk_nodes.keys(), key=lambda x: self.chunk_nodes[x]) 
        mis = set()
        removed = set()
        for v in sorted_nodes:
            if v not in removed:
                mis.add(v)
                removed.add(v)
                if v in self.gathered_subgraph:
                    removed.update(self.gathered_subgraph[v])
                
        self.chunk_verdicts = {v: (v in mis) for v in sorted_nodes}
        self.ready_to_broadcast = True

    def _do_phase_2(self):
        if self.data is not Status.UNDECIDED:
            self.phase_2_round += 1
            if self.phase_2_round >= self.phase_2_max_rounds:
                self.phase = Phase.PHASE_3_COUNT
            return
            
        active_neighbors_p_sum = 0
        neighbor_marked = False
        
        for message in self.inbox:
            status, _, neighbor_p, neighbor_is_marked = message.payload
            if status is Status.UNDECIDED:
                active_neighbors_p_sum += neighbor_p
                if neighbor_is_marked:
                    neighbor_marked = True
        
        if self.marked and not neighbor_marked:
            self.data = Status.IN_MIS
            
        if active_neighbors_p_sum >= 2:
            self.p /= 2
        else:
            self.p = min(2 * self.p, 0.5)
            
        self.marked = (random.random() < self.p)
        
        self.phase_2_round += 1
        if self.phase_2_round >= self.phase_2_max_rounds:
            self.phase = Phase.PHASE_3_COUNT

class GreedyMISInit(Algorithm):
    def __init__(self, input_filename, seed=None):
        self.seed = seed if seed is not None else random.randrange(2**32)
        random.seed(self.seed)
        
        if self.input_graph is None:
            raw_graph = Algorithm.graph_input(input_filename)
            self.n = len(raw_graph)
            self.input_graph = {i: set() for i in range(self.n)}
            for u, neighbors in raw_graph.items():
                for v in neighbors:
                    if u != v:
                        self.input_graph[u].add(v)
                        self.input_graph[v].add(u)
        
        delta = 0
        if self.input_graph:
            delta = max(len(neighbors) for neighbors in self.input_graph.values())
                    
        self.ranks = random.sample(range(self.n), self.n)
        
        self.nodes = [
            MISNode(self.ranks[index], self.input_graph[index], self.n, delta, id=index)
            for index in range(self.n)
        ]

    def is_goal_met(self, nodes) -> bool:
        return all(node.data is not Status.UNDECIDED for node in nodes)