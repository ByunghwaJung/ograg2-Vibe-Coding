# OG-RAG2 LLM Prompt 목록

OG-RAG2 시스템에서 LLM에 전달되는 모든 프롬프트 템플릿을 정리한 문서입니다.

---

## 목차

1. [온톨로지 매핑 프롬프트](#1-온톨로지-매핑-프롬프트)
2. [Knowledge Graph 트리플 생성 프롬프트](#2-knowledge-graph-트리플-생성-프롬프트)
3. [질의응답 프롬프트](#3-질의응답-프롬프트)
4. [스니펫 변환 프롬프트](#4-스니펫-변환-프롬프트)
5. [질문 생성 및 평가 프롬프트](#5-질문-생성-및-평가-프롬프트)

---

## 1. 온톨로지 매핑 프롬프트

**파일**: `ontology_mapping/ontology_mapping.py`  
**변수명**: `ONTOLOGY_JSONLD_DATA_CREATE_TMPL`  
**역할**: 입력 문서 청크를 온톨로지 스키마에 매핑하여 JSON-LD 구조로 변환  
**호출 시점**: `build_knowledge_graph.py` 실행 → 온톨로지 노드 생성 단계

```
Here is a context definition for an ontology.

Context Definition:

{context_definition}

-----------------

Generate a JSON-LD using the following data and the above context definition for the given ontology.
Use '@graph' object namespace for the data in JSON-LD.
Be comprehensive and make sure to fill all of the data completely WITHOUT leaving the sentence in "...".
If there are multiple subfields enumerated in a 'List' namespace then do not combine them in a single 
subfield, keep them as separate subfields to disambiguate.
Ensure that you populate all items in the 'List' namespace, do not leave any item.
Do not include any explanations or apologies in your response.
Do not add any other text other than the generated JSON-LD in your response
Generate in Json format. 
----------------------
Data:

{data}
---------------------
JSON-LD json:
```

**입력 변수**:
| 변수 | 설명 |
|------|------|
| `{context_definition}` | 온톨로지 JSON-LD 스키마 전체 내용 |
| `{data}` | 입력 문서에서 추출한 텍스트 청크 |

**출력**: JSON-LD 형식의 온톨로지 노드 (`ontology_node_N.jsonld`)

---

## 2. Knowledge Graph 트리플 생성 프롬프트

**파일**: `knowledge_graph/knowledge_graph.py`

### 2-1. 기본 트리플 추출 프롬프트

**변수명**: `DEFAULT_KG_TRIPLET_ONTOLOGY_EXTRACT_TMPL`  
**역할**: 온톨로지 JSON-LD를 파이썬 튜플 리스트 형태의 KG 트리플로 변환 (기본 버전)

```
Using the @graph namespace in the following json-ld, generate a complete python list of tuples 
of triples for knowledge graph in the format (subject, predicate, object).
Keep the property names exactly as it is in the Json-ld.
The 'subject', 'predicate', and 'object' can only be strings.
Subjects and objects should be in natural language.
Make sure that the predicate is structured so that it is a grammatically correct phrase.
The triples cannot be nested, so please flatten them. Also do not include triples keys of 
"subject", "object", "predicate", only the values.
For nested structure, within "@graph" object, such as "xy": {"k": "v"} flatten it by 
rearranging keys "xy", "k" to either "xyk", "xky", or "kxy" in a way that it grammatically 
makes sense.
Generate all triples.
Do not add any other text in response other than the list of tuples of triples.
------------------------------

JSON-LD:
{data}
```

### 2-2. 고급 트리플 추출 프롬프트 (Few-shot)

**변수명**: `KG_TRIPLET_ONTOLOGY_EXTRACT_TMPL`  
**역할**: 중첩 온톨로지 구조의 계층적 관계를 보존하며 트리플 생성 (실제 사용)  
**호출 시점**: `build_knowledge_graph.py` → `KGGenerator.generate_triples()` → LLM 호출

```
Using the @graph namespace in the following json-ld, generate a complete python list of tuples 
of triples for knowledge graph in the format (subject, predicate, object).
Keep the property names exactly as it is in the Json-ld, which is provided in the 'name' key 
for complex fields and directly as values for lists or strings.
The 'subject', 'predicate', and 'object' can only be strings.
The triples cannot be nested, so please flatten them. Also do not include triples keys of 
"subject", "object", "predicate", only the values.
While constructing the predicate during flattening of nested fields, include the names of all 
the parent subject nodes in predicate.

For example, an ontology snippet of nested fields and the generated Triplets are provided below:
--------------------------------------
Example of Ontology snippet:
"{"@graph": [
        {
            "@type": "Crop",
            "name": "Wheat",
            "has_types": [
                {
                    "@type": "CropType",
                    "name": "Triticum aestivum",
                    "used_for": "chapati and bakery products"
                }
            ]
            "has_growing_zones": {
                "@type": "cropCult:CropGrowingZones",
                "CropGrowingZone": [
                    {
                        "name": "North Western Plains Zone",
                        "has_seed_recommendations": {
                            "@type": "cropCult:SeedList",
                            "variety_name": ["KRL 19", "PBW 502"],
                            "has_early_sowing_time": {
                                "@type": "cropCult:SowingTime",
                                "start_date": "1st November",
                                "end_date": "20th November"
                            }
                        }
                    }
                ]
            }
        }
    ]
}"

Generated Triplets:
"[('Wheat', 'has type', 'Triticum aestivum'),
('North Western Plains Zone', 'Wheat has seed recommendation variety', 'KRL 19'),
('North Western Plains Zone', 'Wheat has seed recommendation variety', 'PBW 502'),
('KRL 19', 'Wheat North Western Plains Zone has early sowing time start date', '1st November'),
('KRL 19', 'Wheat North Western Plains Zone has early sowing time end date', '20th November'),
('PBW 502', 'Wheat North Western Plains Zone has early sowing time start date', '1st November'),
('PBW 502', 'Wheat North Western Plains Zone has early sowing time end date', '20th November')]"
--------------------------
Subjects and objects should be in natural language.
Generate all triples.
Do not add any other text in response other than the list of tuples of triples.
------------------------------

JSON-LD:
{data}
```

**입력 변수**:
| 변수 | 설명 |
|------|------|
| `{data}` | 온톨로지 노드 JSON-LD 파일 전체 내용 |

**출력**: Python 리스트 형태의 트리플 `[('subject', 'predicate', 'object'), ...]`

> **참고**: Windows 환경에서 LLM이 문자열 내 개행문자를 포함한 응답을 반환하는 버그가 있어,  
> `_clean_triples_str()` 전처리 및 `_extract_triples_regex()` 폴백 메서드를 추가하였음

---

## 3. 질의응답 프롬프트

### 3-1. OG-RAG 메인 질의응답 프롬프트

**파일**: `query_engine/ontograph_query_engine.py`  
**변수명**: `RAG_QUERY_PROMPT`  
**역할**: Greedy Set Cover로 검색된 Hyperedge 컨텍스트를 포함하여 LLM에 최종 답변 요청  
**호출 시점**: `query_llm.py` → `OntoHyperGraphQueryEngine.query()` → LLM 호출

```
Given the context below, answer the following question. 
Note that the context is provided as a list of valid facts in a dictionary format and an 
optional set of rules.

Context: {context}

Question: {query_str}

Answer:
```

**입력 변수**:
| 변수 | 설명 |
|------|------|
| `{context}` | Greedy Set Cover로 선택된 Hyperedge 팩트 목록 (딕셔너리 리스트) |
| `{query_str}` | 사용자 입력 질문 (한국어/영어 모두 가능) |

**실제 사용 예시**:
```
Context: [{'Soybean has storage condition temperature': 'cool and dry'},
          {'Soybean has storage condition max stack height': '1.5m'},
          {'Soybean has storage bags': '4-5 bags per stack'}]

Question: 대두 저장 조건을 설명해줘

Answer:
```

### 3-2. 순수 LLM 질의 프롬프트 (컨텍스트 없음)

**파일**: `query_engine/llm_query_engine.py`  
**변수명**: `QUERY_PROMPT`  
**역할**: KG 없이 LLM 단독으로 답변 (Baseline 비교용)

```
Answer the following question.
Question: {query_str}
---------------------
Answer: 
```

### 3-3. 규칙 기반 LLM 질의 프롬프트

**파일**: `query_engine/llm_query_engine.py`  
**변수명**: `QUERY_RULE_PROMPT`  
**역할**: 도메인 규칙을 컨텍스트로 제공하여 LLM 답변 생성

```
Given the context below, answer the following question.
---------------------
Context:
 {context}

---------------------
Question: {query_str}
---------------------
Answer: 
```

---

## 4. 스니펫 변환 프롬프트

**파일**: `query_engine/snippet_rag_query_engine.py`

### 4-1. 컨텍스트 기반 질의응답

**변수명**: `QUERY_PROMPT`

```
Given the context below, answer the following question.
---------------------
Context:
 {context}

---------------------
Question: {query_str}
---------------------
Answer: 
```

### 4-2. 온톨로지 정보 → 자연어 문장 변환

**변수명**: `CONVERT_PROMPT`  
**역할**: 딕셔너리 형태의 온톨로지 속성을 자연어 문장으로 변환

```
Convert the following information about an entity into an english sentence. 
The information is presented as a list of {key: value} where key is a property name and 
the value is its value.
Remove any redundant information but KEEP ALL the information that is important. 
DO NOT COMPRESS INFORMATION USING "and so on" or "etc" or "and others" etc.
---------------------
For example, 
Information: {'name': 'John Doe', 'age': '25', 'location': 'New York'}
Sentence: John Doe is 25 years old and lives in New York.

Information: {'@type': 'Crop', 'name': 'Soybean', 
              'seed_germination_test_requirements_are': 'Seed Germination Test Requirements'}
Sentence: The crop soybean has Seed Germination Test Requirements.
---------------------

Information: {information}
---------------------
Sentence: 
```

---

## 5. 질문 생성 및 평가 프롬프트

**파일**: `generate_questions.py`  
**용도**: 평가용 질문-답변 쌍 자동 생성 및 품질 평가

### 5-1. 규칙 기반 질문 생성

**변수명**: `RULE_QUESTION_TMPL`

```
Given the following data and a set of deductive rules, generate a hard question that require 
the application of the rules on the data to generate the answer. 

Data: {data}

Rules: {rules}

Question:
```

### 5-2. 규칙 기반 답변 생성

**변수명**: `RULE_ANSWER_TMPL`

```
Given the following data and a set of deductive rules, generate the answer to following 
question while applying of the rules on the data to generate the answer. 

Data: {data}

Rules: {rules}

Question: {question}

Answer: 
```

### 5-3. 질문 품질 평가

**변수명**: `CHECK_QUESTION_TMPL`  
**역할**: 생성된 질문이 규칙을 얼마나 잘 적용하는지 1~10점 척도로 평가

```
Given the following data and a set of deductive rules, check if the given question requires 
the application of the rules on the data to generate the given answer. 
Rate the question from 1-10, where 10 denotes a very good application of the rules and 
1 denotes a bad application of the rules.
Print the reasoning as "Reasoning: <>" followed by the rating as "Rating: <rating>", 
where <rating> is an integer from 1-10.

Data: {data}

Rules: {rules}

Question: {question}

Answer: {answer}

Reasoning: 
Rating:
```

---

## 프롬프트 흐름 요약

```
build_knowledge_graph.py 실행
        │
        ▼
[1] ONTOLOGY_JSONLD_DATA_CREATE_TMPL
    입력 문서 → JSON-LD 온톨로지 노드 생성
        │
        ▼
[2] KG_TRIPLET_ONTOLOGY_EXTRACT_TMPL
    JSON-LD → (subject, predicate, object) 트리플 리스트 생성
        │
        ▼
    data/kg/sample/ontology_triples.pkl 저장

query_llm.py 실행
        │
        ▼
[3] RAG_QUERY_PROMPT
    Hyperedge 컨텍스트 + 사용자 질문 → 최종 답변 생성
```

---

## 모델 설정 (config.yaml)

| 항목 | 값 |
|------|-----|
| LLM | `gpt-4o-mini` (OpenAI) |
| Embedding | `text-embedding-3-small` (OpenAI) |
| Max Tokens (KG 생성) | 10,000 |
| Max Tokens (질의응답) | 1,024 |
