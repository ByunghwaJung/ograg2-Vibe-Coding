"""
HyperNode, HyperEdge, HyperGraph — OG-RAG core data structures.

HyperNode : a (key, value) fact with its embedding
HyperEdge : a set of HyperNodes representing one ontology fact cluster
HyperGraph: collection of edges, supports node lookup
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class HyperNode:
    key: str
    value: str
    embedding: Optional[np.ndarray] = field(default=None, repr=False)

    @property
    def text(self) -> str:
        return f"{self.key}: {self.value}"

    def similarity(self, query_embedding: np.ndarray) -> float:
        if self.embedding is None:
            return 0.0
        a, b = self.embedding, query_embedding
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


@dataclass
class HyperEdge:
    nodes: list[HyperNode]
    fact: dict  # original fact dict for context

    def covers(self, node: HyperNode) -> bool:
        return node in self.nodes


class HyperGraph:
    def __init__(self) -> None:
        self.edges: list[HyperEdge] = []

    def add_edge(self, edge: HyperEdge) -> None:
        self.edges.append(edge)

    @property
    def all_nodes(self) -> list[HyperNode]:
        seen, result = set(), []
        for edge in self.edges:
            for node in edge.nodes:
                if id(node) not in seen:
                    seen.add(id(node))
                    result.append(node)
        return result

    def edges_covering(self, node: HyperNode) -> list[HyperEdge]:
        return [e for e in self.edges if e.covers(node)]

    def __len__(self) -> int:
        return len(self.edges)
