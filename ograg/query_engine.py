"""
Step 5 — Assemble retrieved context and call LLM for final answer.
"""

from __future__ import annotations
from openai import OpenAI
from .hypergraph import HyperGraph
from .retriever import retrieve, embed_graph

LLM_MODEL = "gpt-4o-mini"

RAG_QUERY_PROMPT = """\
Given the context below, answer the following question.
Note that the context is provided as a list of valid facts in a dictionary format.

Context: {context}

Question: {query_str}

Answer:\
"""


class OGRAGQueryEngine:
    def __init__(self, graph: HyperGraph, client: OpenAI, top_k: int = 10) -> None:
        self.graph = graph
        self.client = client
        self.top_k = top_k
        embed_graph(graph, client)

    def query(self, question: str) -> str:
        facts = retrieve(question, self.graph, self.client, top_k=self.top_k)
        prompt = RAG_QUERY_PROMPT.format(context=facts, query_str=question)
        resp = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return resp.choices[0].message.content.strip()
