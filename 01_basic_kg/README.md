# 📘 Version 1: Basic Knowledge Graph (Core Foundation)

Welcome to **Version 1** of the Knowledge Graph Explainer project! 

This version focuses strictly on the **fundamental building blocks** of Knowledge Graphs without any visualization complexity. It teaches you how raw natural text is transformed into structured knowledge that computers (and conversational agents) can understand and query.

---

## 🎯 What You Will Learn in Version 1

1. **Information Extraction**: How NLP Dependency Parsing breaks down English sentences into `(Subject, Predicate, Object)` triplets.
2. **Semantic Web & RDF**: Why plain strings are converted into Universal Resource Identifiers (**URIs**) and typed **Literals**.
3. **Graph Storage**: How the **Turtle (`.ttl`)** format serializes knowledge.
4. **SPARQL Querying**: How to query a Knowledge Graph using standard graph queries.
5. **Conversational Question-Answering**: How to build an interactive AI chat agent that queries the graph to give factual answers.

---

## 📂 Files in this Version

| File | Purpose |
| :--- | :--- |
| [`extractor.py`](file:///Users/shashibetadur/Desktop/Agent_007/KG_Ex/01_basic_kg/extractor.py) | Reads text, tokenizes, and extracts (S, P, O) triplets using spaCy. |
| [`rdf_store.py`](file:///Users/shashibetadur/Desktop/Agent_007/KG_Ex/01_basic_kg/rdf_store.py) | Ingests triplets into an RDF graph using `rdflib`, runs SPARQL queries, and saves Turtle (`.ttl`). |
| [`conversational_agent.py`](file:///Users/shashibetadur/Desktop/Agent_007/KG_Ex/01_basic_kg/conversational_agent.py) | Graph-QA chat agent that translates user questions into SPARQL and answers them. |
| [`run_basic.py`](file:///Users/shashibetadur/Desktop/Agent_007/KG_Ex/01_basic_kg/run_basic.py) | One-click master script running the entire pipeline step-by-step. |

---

## 🚀 How to Run Version 1

### 1. Run the Entire Basic Pipeline
```bash
python 01_basic_kg/run_basic.py
```
This runs the extractor, builds the RDF graph, tests SPARQL, and runs sample questions.

### 2. Run Only the Triplet Extractor
```bash
python 01_basic_kg/extractor.py --file sample_text.txt
```

### 3. Chat Interactively with the Conversational Agent
```bash
python 01_basic_kg/conversational_agent.py
```
*Ask questions like:*
- `Who won the nobel prize for chemistry?`
- `What did Marie Curie discover?`
- `Who created Python?`
- `Tell me about Apple`
- `exit` to quit

### 4. Ask a Single Question from the Terminal
```bash
python 01_basic_kg/conversational_agent.py --ask "Who won the nobel prize for chemistry?"
```
Add `--verbose` to see the generated SPARQL query!
