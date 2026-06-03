"""
Step 1 — Map a document chunk to an ontology schema via LLM → JSON-LD instance.
"""

from __future__ import annotations
import json
from openai import OpenAI

LLM_MODEL = "gpt-4o-mini"

ONTOLOGY_MAPPING_PROMPT = """\
Here is a context definition for an ontology.

Context Definition:

{context_definition}

-----------------

Generate a JSON-LD using the following data and the above context definition for the given ontology.
Use '@graph' object namespace for the data in JSON-LD.
Be comprehensive and make sure to fill all of the data completely WITHOUT leaving the sentence in "...".
If there are multiple subfields enumerated in a 'List' namespace then do not combine them in a single \
subfield, keep them as separate subfields to disambiguate.
Ensure that you populate all items in the 'List' namespace, do not leave any item.
Do not include any explanations or apologies in your response.
Do not add any other text other than the generated JSON-LD in your response
Generate in Json format.
----------------------
Data:

{data}
---------------------
JSON-LD json:\
"""


def map_to_ontology(doc_chunk: str, ontology_schema: str, client: OpenAI) -> dict:
    prompt = ONTOLOGY_MAPPING_PROMPT.format(
        context_definition=ontology_schema,
        data=doc_chunk,
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    raw = resp.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
