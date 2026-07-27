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

class Phase(Enum):
    PHASE_1_CHUNK_SEND = "phase_1_chunk_send"
    PHASE_1_CHUNK_BROADCAST = "phase_1_chunk_broadcast"
    PHASE_2_GHAFFARI = "phase_2"
    PHASE_3_ROUTE_SEND = "phase_3_route_send"
    PHASE_3_ROUTE_FORWARD = "phase_3_route_forward"
    PHASE_3_BROADCAST_RESULTS = "phase_3_broadcast_results"
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
        self.phase = Phase.PHASE_1_CHUNK_SEND
        
        # Phase 1 (MPC Subgraph Gathering) Variables
        self.phase_1_iteration = 1
        self.phase_1_threshold = n / (math.log(n)**10) if n > 1 else 0
        self.current_r = self._calculate_r(self.phase_1_iteration)
        self.chunk_verdicts = {}
        
        # Phase 2 (Ghaffari) Variables
        self.p = 0.5 
        self.marked = (random.random() < self.p)
        self.phase_2_round = 0
        self.phase_2_max_rounds = max(3, int(math.log2(math.log2(n + 2)) * 5))
        
        # Buffer for routing
        self.forward_buffer = []
        self.final_mis_verdicts = {}

    def _calculate_r(self, i):
        """Calculates the rank threshold r_i = n / \Delta^{(3/4)^i}"""
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

        if self.phase == Phase.PHASE_1_CHUNK_SEND:
            if self.data is Status.UNDECIDED and self.rank < self.current_r:
                supervisor.queue_message(Message(self.id, self.leader_id, (Status.TOPOLOGY, self.rank, list(self.active_neighbors), self.id)))

        elif self.phase == Phase.PHASE_1_CHUNK_BROADCAST:
            if self.id == self.leader_id:
                for target_id, is_in_mis in self.chunk_verdicts.items():
                    verdict = Status.IN_MIS if is_in_mis else Status.OUT
                    supervisor.queue_message(Message(self.id, target_id, (Status.RESULT, verdict.value, None, None)))

        elif self.phase == Phase.PHASE_2_GHAFFARI:
            if self.data is Status.UNDECIDED:
                for neighbor in self.active_neighbors:
                    supervisor.queue_message(Message(self.id, neighbor, (self.data, self.rank, self.p, self.marked)))

        elif self.phase == Phase.PHASE_3_ROUTE_SEND:
            if self.data is Status.UNDECIDED:
                intermediate = (self.id + 1) % self.n
                supervisor.queue_message(Message(self.id, intermediate, (Status.TOPOLOGY, self.rank, list(self.active_neighbors), self.id)))

        elif self.phase == Phase.PHASE_3_ROUTE_FORWARD:
            for payload in self.forward_buffer:
                supervisor.queue_message(Message(self.id, self.leader_id, payload))

        elif self.phase == Phase.PHASE_3_BROADCAST_RESULTS:
            if self.id == self.leader_id:
                for target_id, is_in_mis in self.final_mis_verdicts.items():
                    if target_id != self.id:
                        verdict = Status.IN_MIS if is_in_mis else Status.OUT
                        supervisor.queue_message(Message(self.id, target_id, (Status.RESULT, verdict.value, None, None)))

    def do_work(self):
        if self.phase == Phase.HALTED:
            self.inbox.clear()
            return

        self._process_removals()

        if self.phase == Phase.PHASE_1_CHUNK_SEND:
            self._do_phase_1_chunk_send()
        elif self.phase == Phase.PHASE_1_CHUNK_BROADCAST:
            self._do_phase_1_chunk_broadcast()
        elif self.phase == Phase.PHASE_2_GHAFFARI:
            self._do_phase_2()
        elif self.phase == Phase.PHASE_3_ROUTE_SEND:
            self._do_phase_3_route_send()
        elif self.phase == Phase.PHASE_3_ROUTE_FORWARD:
            self._do_phase_3_route_forward()
        elif self.phase == Phase.PHASE_3_BROADCAST_RESULTS:
            self._do_phase_3_broadcast_results()
            
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

    def _do_phase_1_chunk_send(self):
        self.chunk_verdicts = {}
        if self.id == self.leader_id:
            subgraph = {}
            ranks = {}
            
            if self.data is Status.UNDECIDED and self.rank < self.current_r:
                subgraph[self.id] = self.active_neighbors
                ranks[self.id] = self.rank
                
            for message in self.inbox:
                status, rank, neighbors, orig_sender = message.payload
                if status == Status.TOPOLOGY:
                    subgraph[orig_sender] = set(neighbors)
                    ranks[orig_sender] = rank
                    
            sorted_nodes = sorted(subgraph.keys(), key=lambda x: ranks[x]) 
            mis = set()
            removed = set()
            for v in sorted_nodes:
                if v not in removed:
                    mis.add(v)
                    removed.update(subgraph[v].intersection(subgraph.keys()))
                    
            if self.id in mis:
                self.data = Status.IN_MIS
            elif self.id in subgraph:
                self.data = Status.OUT
                
            self.chunk_verdicts = {v: (v in mis) for v in sorted_nodes}
            
        self.phase = Phase.PHASE_1_CHUNK_BROADCAST

    def _do_phase_1_chunk_broadcast(self):
        for message in self.inbox:
            status, verdict, _, _ = message.payload
            if status == Status.RESULT:
                self.data = Status(verdict)
                
        self.phase_1_iteration += 1
        self.current_r = self._calculate_r(self.phase_1_iteration)
        
        if self.current_r >= self.phase_1_threshold or self.current_r >= self.n:
            self.phase = Phase.PHASE_2_GHAFFARI
        else:
            self.phase = Phase.PHASE_1_CHUNK_SEND

    def _do_phase_2(self):
        if self.data is not Status.UNDECIDED:
            self.phase_2_round += 1
            if self.phase_2_round >= self.phase_2_max_rounds:
                self.phase = Phase.PHASE_3_ROUTE_SEND
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
            self.phase = Phase.PHASE_3_ROUTE_SEND

    def _do_phase_3_route_send(self):
        self.forward_buffer.clear()
        for msg in self.inbox:
            if msg.payload[0] == Status.TOPOLOGY:
                self.forward_buffer.append(msg.payload)
        self.phase = Phase.PHASE_3_ROUTE_FORWARD

    def _do_phase_3_route_forward(self):
        if self.id == self.leader_id:
            subgraph = {}
            ranks = {}
            
            if self.data is Status.UNDECIDED:
                subgraph[self.id] = self.active_neighbors
                ranks[self.id] = self.rank
                
            for message in self.inbox:
                status, rank, neighbors, orig_sender = message.payload
                if status == Status.TOPOLOGY:
                    subgraph[orig_sender] = set(neighbors)
                    ranks[orig_sender] = rank
                    
            sorted_nodes = sorted(subgraph.keys(), key=lambda x: ranks[x]) 
            mis = set()
            removed = set()
            for v in sorted_nodes:
                if v not in removed:
                    mis.add(v)
                    removed.update(subgraph[v])
                    
            if self.id in mis:
                self.data = Status.IN_MIS
            elif self.id in subgraph:
                self.data = Status.OUT
                
            self.final_mis_verdicts = {v: (v in mis) for v in sorted_nodes}
            
        self.phase = Phase.PHASE_3_BROADCAST_RESULTS

    def _do_phase_3_broadcast_results(self):
        for message in self.inbox:
            status, verdict, _, _ = message.payload
            if status == Status.RESULT:
                self.data = Status(verdict)
        self.phase = Phase.HALTED


class GreedyMISInit(Algorithm):
    def __init__(self, input_filename, seed=None):
        self.seed = seed if seed is not None else random.randrange(2**32)
        random.seed(self.seed)
        
        # Only read from the file if the graph hasn't been cached yet
        if self.input_graph is None:
            raw_graph = Algorithm.graph_input(input_filename)
            self.n = len(raw_graph)
            self.input_graph = {i: set() for i in range(self.n)}
            for u, neighbors in raw_graph.items():
                for v in neighbors:
                    if u != v:
                        self.input_graph[u].add(v)
                        self.input_graph[v].add(u)
        
        # Calculate delta unconditionally using the cached graph
        delta = 0
        if self.input_graph:
            delta = max(len(neighbors) for neighbors in self.input_graph.values())
                    
        self.ranks = random.sample(range(self.n), self.n)
        
        self.nodes = [
            MISNode(self.ranks[index], self.input_graph[index], self.n, delta, id=index)
            for index in range(self.n)
        ]
        self.expected_mis = self._sequential_greedy_mis()

    def _sequential_greedy_mis(self):
        mis = set()
        removed = set()
        for v in sorted(range(self.n), key=lambda v: self.ranks[v]):
            if v not in removed:
                mis.add(v)
                removed.update(self.input_graph[v])
        return mis

    def is_goal_met(self, nodes) -> bool:
        return all(node.data is not Status.UNDECIDED for node in nodes)