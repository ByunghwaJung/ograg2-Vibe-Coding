"""
Step 2 — Extract (subject, predicate, object) triples from a JSON-LD instance via LLM.
Step 3 — Convert triples into HyperNodes + HyperEdges.
"""

from __future__ import annotations
import ast
import re
import json
from openai import OpenAI
from .hypergraph import HyperNode, HyperEdge, HyperGraph

LLM_MODEL = "gpt-4o-mini"

TRIPLE_EXTRACT_PROMPT = """\
Using the @graph namespace in the following json-ld, generate a complete python list of tuples \
of triples for knowledge graph in the format (subject, predicate, object).
Keep the property names exactly as it is in the Json-ld, which is provided in the 'name' key \
for complex fields and directly as values for lists or strings.
The 'subject', 'predicate', and 'object' can only be strings.
The triples cannot be nested, so please flatten them. Also do not include triples keys of \
"subject", "object", "predicate", only the values.
While constructing the predicate during flattening of nested fields, include the names of all \
the parent subject nodes in predicate.
Generate all triples.
Do not add any other text in response other than the list of tuples of triples.
------------------------------

JSON-LD:
{data}\
"""


def extract_triples(jsonld: dict, client: OpenAI) -> list[tuple[str, str, str]]:
    prompt = TRIPLE_EXTRACT_PROMPT.format(data=json.dumps(jsonld, indent=2))
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    raw = resp.choices[0].message.content.strip()
    return _parse_triples(raw)


def _parse_triples(raw: str) -> list[tuple[str, str, str]]:
    # Remove markdown fences
    raw = re.sub(r"```[a-z]*", "", raw).strip().rstrip("`")
    # Normalize newlines inside strings that break ast.literal_eval
    raw = re.sub(r"\n\s*", " ", raw)
    try:
        result = ast.literal_eval(raw)
        return [(str(s), str(p), str(o)) for s, p, o in result]
    except Exception:
        # Fallback: regex extraction
        matches = re.findall(r'\(\s*["\'](.+?)["\']\s*,\s*["\'](.+?)["\']\s*,\s*["\'](.+?)["\']\s*\)', raw)
        return [(s, p, o) for s, p, o in matches]


def triples_to_hypergraph(triples: list[tuple[str, str, str]]) -> HyperGraph:
    graph = HyperGraph()
    for subject, predicate, obj in triples:
        subject_node = HyperNode(key="subject", value=subject)
        predicate_node = HyperNode(key="predicate", value=predicate)
        object_node = HyperNode(key="object", value=obj)
        fact = {"subject": subject, "predicate": predicate, "object": obj}
        edge = HyperEdge(nodes=[subject_node, predicate_node, object_node], fact=fact)
        graph.add_edge(edge)
    return graph
