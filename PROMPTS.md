# AI 코딩 툴 활용 프롬프트 로그

- **논문 제목**: OG-RAG: Ontology-Grounded Retrieval Augmented Generation  
- **사용 툴**: Claude Code (claude-sonnet-4-6)  
- **GitHub**: https://github.com/ByunghwaJung/ograg2-Vibe-Coding  

---

## 1단계 — 과제 이해 및 구현 방향 결정

**프롬프트**
```
타겟논문을 AI 코딩 툴을 이용하여 구현해보고자 한다
뭐부터 시작할까
```

**Claude Code 응답 요약**
- 구현 방향 3가지 제시: (1) 기존 백엔드에 웹 UI 추가, (2) RAG 파이프라인 처음부터 재구현, (3) 논문 핵심 알고리즘만 재현
- 바이브 코딩의 핵심은 **씨드 프롬프트** 작성이라고 안내

**선택**
```
논문 핵심 알고리즘만 깔끔하게 재현
```

---

## 2단계 — 논문 분석 및 씨드 프롬프트 작성

**프롬프트**
```
별도 폴더를 생성해서 하자. 
```

**Claude Code가 작성한 씨드 프롬프트 (핵심 구현 명세)**

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
- LLM: OpenAI API (gpt-4o-mini)
- Embeddings: OpenAI text-embedding-3-small
- Dependencies: openai, numpy, pyyaml (no heavy frameworks like LlamaIndex)
- Structure:
  ograg/
  ├── ontology_mapper.py
  ├── triple_extractor.py
  ├── hypergraph.py
  ├── retriever.py
  ├── query_engine.py
  └── pipeline.py
- Keep each file under 150 lines. No unnecessary abstractions.

## What NOT to implement
- No web UI
- No RAPTOR, no SnippetRAG, no baseline comparisons
- No evaluation/scoring framework
```

**결과**  
`c:\AI\ograg2\ograg\` 아래 6개 파일 생성 완료

---

## 3단계 — 설정 파일 구조 개선

**프롬프트**
```
설정파일도 생성
```

**Claude Code 응답 요약**
- `api_keys.yaml`을 새 프로젝트 루트에 생성
- `pipeline.py`의 키 로딩 로직을 환경변수 → 프로젝트 내 yaml 순으로 탐색하도록 수정

**생성된 파일**
```
c:\AI\ograg2\
├── api_keys.yaml       ← 신규 추가
├── requirements.txt
└── ograg\
    └── ...
```

---

## 4단계 — 실행 테스트

**프롬프트**
```
네  (실행 확인)
```

**실행 결과**
```
[pipeline] Step 1: Ontology mapping...
  → 1 graph nodes
[pipeline] Step 2: Triple extraction...
  → 10 triples extracted
[pipeline] Step 3: Building HyperGraph...
  → 10 hyperedges
  → Saved to data/demo_graph.pkl
[pipeline] Step 4+5: Building query engine (embedding nodes)...

============================================================

Q: What are the recommended seed varieties for wheat?
A: The recommended seed varieties for wheat are HD 2967, PBW 550, and GW 322.

Q: What soil conditions does wheat require?
A: Wheat requires well-drained loamy soil with a soil pH of 6.0-7.0.

Q: When should wheat be sown?
A: Wheat should be sown from late October to mid-November.
============================================================
```

- 전체 5단계 파이프라인 정상 동작 확인
- 농업 도메인(밀) 샘플 문서에 대해 질의응답 성공

---

## 5단계 — git 기존 내용 교체

**프롬프트**
```
git에 기존 파일은 모두 삭제하고 새롭게 생성한 폴더의 내용으로 교체해줘
```

**Claude Code 수행 내용**
1. 기존 `api_keys.yaml`(실제 키 포함)을 새 프로젝트로 복사 보존
2. `.git`을 제외한 기존 파일 전체 삭제
3. `ograg2-new` 내용을 `ograg2`로 복사
4. 새 `.gitignore` 작성 (`api_keys.yaml`, `venv/`, `__pycache__/` 제외)
5. `git add -A` → 커밋 → 푸시

**커밋 메시지**
```
Replace full OG-RAG2 implementation with clean minimal re-implementation
```

---

## 최종 구현 결과

### 파일 구조

```
ograg/
├── __init__.py
├── hypergraph.py       # HyperNode · HyperEdge · HyperGraph 자료구조
├── ontology_mapper.py  # 문서 청크 → JSON-LD (Step 1)
├── triple_extractor.py # JSON-LD → (s, p, o) 트리플 → HyperGraph (Step 2, 3)
├── retriever.py        # 쿼리 임베딩 + Greedy Set Cover (Step 4)
├── query_engine.py     # 컨텍스트 조합 + LLM 답변 생성 (Step 5)
└── pipeline.py         # 전체 파이프라인 실행 진입점
```

### 실행 방법

```bash
pip install -r requirements.txt
# api_keys.yaml에 OPENAI_API_KEY 입력
python -m ograg.pipeline
```

### 논문 핵심 알고리즘 비교

| 항목 | 기존 RAG | OG-RAG (구현) |
|------|---------|--------------|
| 지식 표현 | 평문 청크 | 온톨로지 JSON-LD → (s, p, o) 트리플 |
| 검색 단위 | 청크 벡터 | HyperNode (key-value 팩트 쌍) |
| 검색 방법 | Top-k 코사인 유사도 | Greedy Set Cover |
| 컨텍스트 | 원문 청크 | 구조화된 팩트 딕셔너리 |

---

## 구현 후 질의응답

테스트 도메인: 밀(Wheat) 재배 정보 / 모델: gpt-4o-mini

```
Q: What is the scientific name of wheat?
A: The scientific name of wheat is Triticum aestivum.

Q: How much rainfall does wheat need?
A: Wheat needs 450-650 mm of rainfall.

Q: What are the storage conditions for wheat?
A: The storage conditions for wheat are cool, dry conditions at below 12% moisture content.

Q: 밀 재배에 적합한 토양 조건은?
A: 밀 재배에 적합한 토양 조건은 잘 배수되는 양토(롬)입니다.

Q: 밀 씨앗 보관 방법을 알려줘
A: 밀 씨앗은 12% 미만의 수분 함량을 유지하며 시원하고 건조한 환경에서 보관해야 합니다.

Q: 밀 파종 시기는 언제인가요?
A: 밀의 파종 시기는 10월 하순부터 11월 중순까지입니다.
```

→ 영어·한국어 질문 모두 정상 답변 생성 확인
