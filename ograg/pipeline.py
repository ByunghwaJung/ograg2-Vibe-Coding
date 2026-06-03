"""
End-to-end OG-RAG pipeline demo.

Run:
    cd c:\\AI\\ograg2-new
    python -m ograg.pipeline
"""

from __future__ import annotations
import os
import pickle
from pathlib import Path
import yaml
from openai import OpenAI

from .ontology_mapper import map_to_ontology
from .triple_extractor import extract_triples, triples_to_hypergraph
from .query_engine import OGRAGQueryEngine

# ---------------------------------------------------------------------------
# Sample data (agriculture domain — same domain as original OG-RAG paper)
# ---------------------------------------------------------------------------

SAMPLE_DOCUMENT = """
Wheat (Triticum aestivum) is a major cereal crop grown worldwide.
It is cultivated in temperate regions and requires well-drained loamy soil with pH 6.0-7.0.
Sowing is done from late October to mid-November.
The crop requires 450-650mm of rainfall during the growing season.
Recommended seed varieties include HD 2967, PBW 550, and GW 322.
Storage should be in cool, dry conditions at below 12% moisture content.
"""

SAMPLE_ONTOLOGY_SCHEMA = """
{
  "@context": {
    "crop": "http://example.org/crop#",
    "name": "crop:name",
    "scientific_name": "crop:scientificName",
    "soil_type": "crop:soilType",
    "soil_pH": "crop:soilPH",
    "sowing_period": "crop:sowingPeriod",
    "rainfall_mm": "crop:rainfallMM",
    "seed_varieties": {"@id": "crop:seedVarieties", "@container": "@list"},
    "storage_conditions": "crop:storageConditions"
  }
}
"""

CACHE_PATH = Path(__file__).parent.parent / "data" / "demo_graph.pkl"


def build_graph(client: OpenAI, use_cache: bool = True):
    if use_cache and CACHE_PATH.exists():
        print("[pipeline] Loading cached graph...")
        with open(CACHE_PATH, "rb") as f:
            return pickle.load(f)

    print("[pipeline] Step 1: Ontology mapping...")
    jsonld = map_to_ontology(SAMPLE_DOCUMENT, SAMPLE_ONTOLOGY_SCHEMA, client)
    print(f"  → {len(jsonld.get('@graph', []))} graph nodes")

    print("[pipeline] Step 2: Triple extraction...")
    triples = extract_triples(jsonld, client)
    print(f"  → {len(triples)} triples extracted")

    print("[pipeline] Step 3: Building HyperGraph...")
    graph = triples_to_hypergraph(triples)
    print(f"  → {len(graph)} hyperedges")

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(graph, f)
    print(f"  → Saved to {CACHE_PATH}")

    return graph


def _load_api_key() -> str:
    # 1) 환경변수 우선
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    # 2) 프로젝트 루트의 api_keys.yaml
    yaml_path = Path(__file__).parent.parent / "api_keys.yaml"
    if yaml_path.exists():
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        key = data.get("OPENAI_API_KEY", "")
        if key and key != "your-api-key-here":
            return key
    raise EnvironmentError("OPENAI_API_KEY not set. Edit api_keys.yaml or set the env var.")


def main():
    api_key = _load_api_key()

    client = OpenAI(api_key=api_key)
    graph = build_graph(client)

    print("[pipeline] Step 4+5: Building query engine (embedding nodes)...")
    engine = OGRAGQueryEngine(graph, client, top_k=10)

    questions = [
        "What are the recommended seed varieties for wheat?",
        "What soil conditions does wheat require?",
        "When should wheat be sown?",
    ]

    print("\n" + "=" * 60)
    for q in questions:
        print(f"\nQ: {q}")
        answer = engine.query(q)
        print(f"A: {answer}")
    print("=" * 60)


if __name__ == "__main__":
    main()
