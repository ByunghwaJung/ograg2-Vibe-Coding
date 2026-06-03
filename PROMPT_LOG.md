# AI 코딩 툴 활용 프롬프트 로그

- **논문 제목**: OG-RAG: Ontology-Grounded Retrieval Augmented Generation
- **사용 툴**: Claude Code (claude-sonnet-4-6)
- **작업 목표**: 논문의 핵심 알고리즘을 최소한의 코드로 재구현 (바이브 코딩)

---

## 프롬프트 1 — 구현 방향 결정

**입력 프롬프트**
```
논문 핵심 알고리즘만 깔끔하게 재현
```

**결과**
- 전체 파이프라인을 5단계로 정리
- 구현 방향: 핵심 알고리즘만, 외부 프레임워크 없이, 파일당 150줄 이하

---

## 프롬프트 2 — 씨드 프롬프트 (핵심 구현 명세)

**입력 프롬프트**
```
Implement the core algorithm from the OG-RAG paper (Ontology-Grounded Retrieval Augmented
Generation) as a clean, minimal Python implementation.

## Paper Core Algorithm

OG-RAG replaces flat vector search in RAG with ontology-grounded hypergraph retrieval.

### Pipeline:

**Step 1 — Ontology Mapping**
Given a domain ontology schema (JSON-LD context) and a document chunk, call an LLM to
produce a JSON-LD instance that maps the document data to the ontology structure.

Use this exact prompt template:
---
Here is a context definition for an ontology.
Context Definition:
{context_definition}
-----------------
Generate a JSON-LD using the following data and the above context definition for the given
ontology. Use '@graph' object namespace for the data in JSON-LD.
Be comprehensive and make sure to fill all of the data completely WITHOUT leaving the
sentence in "...".
Do not include any explanations or apologies in your response.
Do not add any other text other than the generated JSON-LD in your response.
Generate in Json format.
Data:
{data}
JSON-LD json:
---

**Step 2 — Triple Extraction**
Given the JSON-LD instance, call an LLM to extract (subject, predicate, object) triples.
Flatten all nested structures. Include parent node names in predicates.

Use this exact prompt template:
---
Using the @graph namespace in the following json-ld, generate a complete python list of
tuples of triples for knowledge graph in the format (subject, predicate, object).
Keep the property names exactly as it is in the Json-ld.
The 'subject', 'predicate', and 'object' can only be strings.
The triples cannot be nested, so please flatten them.
While constructing the predicate during flattening of nested fields, include the names of
all the parent subject nodes in predicate.
Generate all triples.
Do not add any other text in response other than the list of tuples of triples.
JSON-LD:
{data}
---

**Step 3 — HyperGraph Construction**
From triples, build:
- HyperNode: represents a (key, value) fact pair. e.g. ("crop name", "Wheat")
  Each node stores its text embedding (embed key+": "+value).
- HyperEdge: a set of HyperNodes that together represent one triple or fact cluster.
  Each edge stores all its nodes and the original fact dict.

**Step 4 — Query Retrieval (Greedy Set Cover)**
Given a query string:
1. Embed the query.
2. Score each HyperNode by cosine similarity to query embedding.
3. Select top-k nodes (k=10 by default).
4. Run Greedy Set Cover: pick the minimum number of HyperEdges that cover all top-k nodes.
5. Collect the fact dicts from selected HyperEdges as context.

**Step 5 — Answer Generation**
Call LLM with:
---
Given the context below, answer the following question.
Note that the context is provided as a list of valid facts in a dictionary format.
Context: {context}
Question: {query_str}
Answer:
---

## Implementation Requirements

- Language: Python 3.10+
- LLM: OpenAI API (gpt-4o-mini), use OPENAI_API_KEY env var
- Embeddings: OpenAI text-embedding-3-small
- Dependencies: openai, numpy, pickle (no heavy frameworks like LlamaIndex)
- Structure:
  ograg/
  ├── ontology_mapper.py    # Step 1: doc + schema → JSON-LD
  ├── triple_extractor.py   # Step 2: JSON-LD → triples
  ├── hypergraph.py         # Step 3: HyperNode, HyperEdge, HyperGraph classes
  ├── retriever.py          # Step 4: embed + greedy set cover
  ├── query_engine.py       # Step 5: assemble context + call LLM
  └── pipeline.py           # End-to-end: run all steps

- Keep each file under 150 lines. No unnecessary abstractions.
- Include a small demo in pipeline.py using a hardcoded sample document and ontology schema.

## What NOT to implement
- No web UI
- No RAPTOR, no SnippetRAG, no baseline comparisons
- No evaluation/scoring framework
- No CLI argument parsing

Start with hypergraph.py (the core data structure), then retriever.py, then the rest.
```

**결과**
- `ograg/` 패키지 전체 생성
  - `hypergraph.py` — HyperNode, HyperEdge, HyperGraph 데이터 구조
  - `ontology_mapper.py` — 문서 → JSON-LD 변환 (LLM 호출)
  - `triple_extractor.py` — JSON-LD → 트리플 추출 및 HyperGraph 변환
  - `retriever.py` — 임베딩 기반 노드 랭킹 + Greedy Set Cover
  - `query_engine.py` — 컨텍스트 조합 및 최종 답변 생성
  - `pipeline.py` — 농업 도메인 샘플 데이터로 전체 파이프라인 실행

---

## 프롬프트 3 — 설정 파일 구조 개선

**입력 프롬프트**
```
ograg2-new 쪽에 설정파일이 있어야 하지 않을까?
```

**결과**
- `api_keys.yaml` 을 새 프로젝트 루트에 생성
- `pipeline.py`의 키 로딩 로직을 프로젝트 독립적으로 수정

---

## 프롬프트 4 — git 교체

**입력 프롬프트**
```
git에 기존 파일은 모두 삭제하고 새롭게 생성한 폴더의 내용으로 교체해줘
```

**결과**
- 기존 파일 전체 삭제 (venv 제외)
- 새 구현 코드로 교체
- `.gitignore` 재작성 (api_keys.yaml, venv/, __pycache__ 제외)
- 커밋 및 푸시 완료

---

## 구현 결과물 구조

```
ograg/
├── __init__.py
├── hypergraph.py       # HyperNode · HyperEdge · HyperGraph
├── ontology_mapper.py  # 문서 청크 → JSON-LD (Prompt 1 포함)
├── triple_extractor.py # JSON-LD → (s, p, o) 트리플 → HyperGraph (Prompt 2 포함)
├── retriever.py        # 쿼리 임베딩 → Greedy Set Cover
├── query_engine.py     # 컨텍스트 + LLM 답변 생성 (Prompt 3 포함)
└── pipeline.py         # 전체 파이프라인 실행 진입점
```

## 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. api_keys.yaml에 OpenAI API 키 입력
# OPENAI_API_KEY: sk-...

# 3. 실행
python -m ograg.pipeline
```

---

## 논문 핵심 알고리즘 요약

| 단계 | 기존 RAG | OG-RAG |
|------|---------|--------|
| 지식 표현 | 평문 청크 | 온톨로지 기반 JSON-LD → (s, p, o) 트리플 |
| 검색 단위 | 청크 벡터 | HyperNode (key-value 팩트) |
| 검색 방법 | Top-k 코사인 유사도 | Greedy Set Cover (최소 HyperEdge 선택) |
| 컨텍스트 | 원문 청크 | 구조화된 팩트 딕셔너리 |
