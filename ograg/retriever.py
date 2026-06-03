"""
Retriever — embed query, score HyperNodes, Greedy Set Cover over HyperEdges.
"""

from __future__ import annotations
import numpy as np
from openai import OpenAI
from .hypergraph import HyperGraph, HyperEdge, HyperNode

EMBED_MODEL = "text-embedding-3-small"


def get_embedding(text: str, client: OpenAI) -> np.ndarray:
    resp = client.embeddings.create(model=EMBED_MODEL, input=text)
    return np.array(resp.data[0].embedding, dtype=np.float32)


def embed_graph(graph: HyperGraph, client: OpenAI) -> None:
    """Embed all HyperNodes in-place (skip already embedded)."""
    for node in graph.all_nodes:
        if node.embedding is None:
            node.embedding = get_embedding(node.text, client)


def greedy_set_cover(
    target_nodes: list[HyperNode],
    graph: HyperGraph,
) -> list[HyperEdge]:
    """Return minimum HyperEdges that cover all target_nodes."""
    uncovered = set(id(n) for n in target_nodes)
    selected: list[HyperEdge] = []

    while uncovered:
        best_edge = max(
            graph.edges,
            key=lambda e: len(uncovered & {id(n) for n in e.nodes}),
        )
        covered_by_best = uncovered & {id(n) for n in best_edge.nodes}
        if not covered_by_best:
            break
        uncovered -= covered_by_best
        selected.append(best_edge)

    return selected


def retrieve(query: str, graph: HyperGraph, client: OpenAI, top_k: int = 10) -> list[dict]:
    """Return list of fact dicts as context for the query."""
    query_emb = get_embedding(query, client)

    # Score all nodes
    scored = sorted(
        graph.all_nodes,
        key=lambda n: n.similarity(query_emb),
        reverse=True,
    )
    top_nodes = scored[:top_k]

    # Greedy Set Cover
    selected_edges = greedy_set_cover(top_nodes, graph)

    return [edge.fact for edge in selected_edges]
