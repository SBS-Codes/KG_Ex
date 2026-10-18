# 🧠 Knowledge Graph Explainer: From Raw Text to SPARQL & Conversational AI

A hands-on, beginner-friendly educational project that demonstrates how to build, query, visualize, and chat with a **Knowledge Graph (KG)** from scratch using Python.

---

## 📖 Table of Contents
1. [What is a Knowledge Graph? (A Beginner's Guide)](#-what-is-a-knowledge-graph-a-beginners-guide)
2. [Project Architecture & The Two Versions](#-project-architecture--the-two-versions)
3. [The Step-by-Step Process Explained Simply](#-the-step-by-step-process-explained-simply)
4. [Practice Questions Tailored to the Text](#-practice-questions-tailored-to-the-text)
5. [How to Use the Programs (Step-by-Step Commands)](#-how-to-use-the-programs-step-by-step-commands)
6. [Repository Structure](#-repository-structure)

---

## 🌟 What is a Knowledge Graph? (A Beginner's Guide)

Think about how humans remember facts. When you read:
> *"Marie Curie won the Nobel Prize in Chemistry in 1911."*

You don't just store a string of 50 letters in your brain. Instead, your mind connects three distinct concepts:
1. **The Person**: Marie Curie
2. **The Relationship**: won
3. **The Award & Date**: Nobel Prize in Chemistry (in 1911)

A **Knowledge Graph** organizes computer data in the exact same way. Instead of dumping text into isolated rows of a spreadsheet or a flat document, information is stored as **nodes (entities)** connected by **edges (relationships)**.

### The Core Building Block: The SPO Triplet
Every fact in a Knowledge Graph is represented as a **Triplet**:
$$\text{(Subject)} \xrightarrow{\text{[Predicate]}} \text{(Object)}$$

| Element | Description | Example |
| :--- | :--- | :--- |
| **Subject** | The actor or primary entity | `Marie Curie` |
| **Predicate** | The relationship, action, or state | `discovered` |
| **Object** | The receiving entity, concept, or date | `radium` |

---

## 🏗️ Project Architecture & The Two Versions

To make learning easy, this project is split into **two clean, modular versions**:

```
                                      [ Raw Text File (sample_text.txt) ]
                                                      │
                                                      ▼
                                       Phase 1: NLP Dependency Parsing
                                       (Identifies Subjects, Verbs, Objects)
                                                      │
                                                      ▼
                                       Phase 2: Extract SPO Triplets
                                                      │
                        ┌─────────────────────────────┴─────────────────────────────┐
                        ▼                                                           ▼
       ┌─────────────────────────────────┐                         ┌─────────────────────────────────┐
       │   VERSION 1: BASIC KG VARIANT   │                         │   VERSION 2: VISUAL KG VARIANT  │
       │         (01_basic_kg/)          │                         │         (02_visual_kg/)         │
       ├─────────────────────────────────┤                         ├─────────────────────────────────┤
       │ • RDFLib Store (URIs & Literals)│                         │ • Everything in Version 1       │
       │ • Turtle (.ttl) Serialization   │                         │ • Static PNG Graph (NetworkX)   │
       │ • SPARQL Query Engine           │                         │ • Interactive Web App (Vis.js)  │
       │ • Conversational Q&A Agent      │                         │   (drag, zoom, click inspect)   │
       └─────────────────────────────────┘                         └─────────────────────────────────┘
```

### Which Version Should You Start With?
* **Start with [Version 1 (`01_basic_kg/`)](01_basic_kg/)**: If you want to understand the foundational data structures, RDF, Turtle serialization, SPARQL queries, and conversational Q&A without any visual overhead.
* **Explore [Version 2 (`02_visual_kg/`)](02_visual_kg/)**: Once you understand the basics, this version renders the graph as a high-resolution PNG image and an interactive web explorer.

---

## 🧩 The Step-by-Step Process Explained Simply

### Step 1: Reading Text & NLP Dependency Parsing
Computers cannot understand English grammar automatically. We use **spaCy**'s syntactic dependency parser to break down sentences into grammatical parts:
- **`nsubj` (Nominal Subject)**: Identifies who or what is performing the action (e.g. `Alan Turing`).
- **`ROOT` / `VERB`**: Identifies the core action (e.g. `designed`).
- **`dobj` (Direct Object)**: Identifies the target receiving the action (e.g. `ACE computer`).
- **Compound Noun Expansion**: Ensures multi-word names stay together (e.g. `Marie` + `Curie` $\rightarrow$ `Marie Curie`, `Nobel Prize` + `in Chemistry` $\rightarrow$ `Nobel Prize in Chemistry`).
- **Passive Voice Handling**: Converts passive structures like *"Python was created by Guido van Rossum"* into `(Python -> was created by -> Guido van Rossum)`.

### Step 2: The RDF Semantic Web Standard
In natural language, the word *"Apple"* could mean a fruit or a tech company. The **W3C Semantic Web** standard solves this ambiguity using:
- **URIs (Uniform Resource Identifiers)**: Gives every entity a unique global address:
  - `http://example.org/kg/Apple`
  - `http://example.org/kg/Marie_Curie`
- **Literals**: Used for raw values like numbers or years:
  - `"1991"^^xsd:gYear`
- **Turtle (`.ttl`)**: A clean, human-readable format for storing triples:
  ```turtle
  @prefix ex: <http://example.org/kg/> .
  @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
  @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

  ex:Marie_Curie rdfs:label "Marie Curie" ;
      ex:discovered ex:polonium, ex:radium ;
      ex:won ex:Nobel_Prize_in_Chemistry ;
      ex:wonIn "1911"^^xsd:gYear .
  ```

### Step 3: Querying with SPARQL
**SPARQL** is the query language of Knowledge Graphs (similar to SQL for relational databases). To ask *"What did Marie Curie discover?"*, we write:
```sparql
PREFIX ex: <http://example.org/kg/>
SELECT ?item WHERE {
    ex:Marie_Curie ex:discovered ?item .
}
```

### Step 4: The Conversational Agent (Graph-QA)
Large Language Models sometimes hallucinate facts. By connecting a conversational agent to a Knowledge Graph:
1. The agent identifies the entity mentioned in your question (e.g., *"chemistry"* $\rightarrow$ `ex:Nobel_Prize_in_Chemistry`).
2. It generates a targeted SPARQL query.
3. It constructs an answer strictly from the graph:
   > **Question**: *"Who won the nobel prize for chemistry?"*  
   > **Answer**: *"Marie Curie won the Nobel Prize in Chemistry in 1911."*

### Step 5: Graph Layout & Physics Visualization
In Version 2, mathematical graph layout algorithms (**Force-Directed / Spring Layout**) calculate physical forces:
- Connected nodes are drawn together like springs.
- Unconnected nodes repel each other like magnets.
This produces an organic, beautiful visual network where clusters and relationships become obvious immediately.

---

## ❓ Practice Questions Tailored to the Text

The sample corpus ([`sample_text.txt`](sample_text.txt)) covers historical breakthroughs in science and technology. Here are practice questions you can test with the Conversational Agent:

| # | Question | Expected Factual Answer |
| :---: | :--- | :--- |
| **1** | *"Who won the nobel prize for chemistry?"* | `Marie Curie won the Nobel Prize in Chemistry in 1911.` |
| **2** | *"Who won the nobel prize in physics?"* | `Marie Curie won the Nobel Prize in Physics.` |
| **3** | *"What did Marie Curie discover?"* | `Marie Curie discovered polonium and radium.` |
| **4** | *"Who created Python?"* | `Python was created by Guido van Rossum in 1991.` |
| **5** | *"When was Python created?"* | `Python was created in 1991.` |
| **6** | *"Who designed the ACE computer?"* | `ACE computer was designed by Alan Turing in 1945.` |
| **7** | *"When was the ACE computer designed?"* | `ACE computer was designed in 1945.` |
| **8** | *"Who co-founded Apple?"* | `Apple was co-founded by Steve Jobs.` |
| **9** | *"What did Apple release?"* | `Apple released iPhone in 2007.` |
| **10** | *"When was the iPhone released?"* | `iPhone was released in 2007.` |
| **11** | *"What did Google develop?"* | `Google developed TensorFlow.` |
| **12** | *"What did Albert Einstein publish?"* | `Albert Einstein published theory of general relativity.` |
| **13** | *"Tell me about Apple"* | `Lists all outgoing and incoming relations for Apple.` |
| **14** | *"What topics do you know about?"* | `Lists all indexed entities in the knowledge graph.` |

*(See [`sample_questions.txt`](sample_questions.txt) for the categorized list).*

---

## 💻 How to Use the Programs (Step-by-Step Commands)

### 1. Prerequisites & Setup
Make sure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/your-username/KG_Ex.git
cd KG_Ex

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # On macOS/Linux
# .venv\Scripts\activate        # On Windows

# Install dependencies
pip install -r requirements.txt

# Download the spaCy English NLP model
python -m spacy download en_core_web_sm
```

---

### 2. Using Version 1 (Basic Knowledge Graph)

#### A. Run the Complete Step-by-Step Pipeline
```bash
python 01_basic_kg/run_basic.py
```
*What happens:* It reads `sample_text.txt`, extracts triplets, displays a formatted table, saves `knowledge_graph.ttl`, and tests sample questions.

#### B. Run Just the Triplet Extractor on Any Text File
```bash
python 01_basic_kg/extractor.py --file sample_text.txt --json-out triplets.json
```

#### C. Start an Interactive Chat with the Knowledge Graph
```bash
python 01_basic_kg/conversational_agent.py
```
*Example session:*
```text
You: Who won the nobel prize for chemistry?
Agent: Marie Curie won the Nobel Prize in Chemistry in 1911.

You: What did Marie Curie discover?
Agent: Marie Curie discovered polonium and radium.

You: Who created Python?
Agent: Python was created by Guido van Rossum in 1991.

You: exit
Agent: Goodbye! Keep learning Knowledge Graphs!
```

#### D. Ask a Single Question Directly from the Terminal
```bash
python 01_basic_kg/conversational_agent.py --ask "Who won the nobel prize for chemistry?"
```

#### E. View the Generated SPARQL Query Behind the Scenes
```bash
python 01_basic_kg/conversational_agent.py --ask "Who won the nobel prize for chemistry?" --verbose
```

#### F. Run the Full Automated Benchmark QA Suite
```bash
python 01_basic_kg/conversational_agent.py --demo
```

---

### 3. Using Version 2 (Visual Knowledge Graph)

#### A. Generate Static PNG and Interactive HTML Graphs
```bash
python 02_visual_kg/run_visual.py
```
This outputs:
- `knowledge_graph.png`: Static high-resolution graph diagram.
- `knowledge_graph.html`: Interactive web application.

#### B. Open the Interactive Web Graph in Your Browser
```bash
# macOS
open knowledge_graph.html

# Linux
xdg-open knowledge_graph.html

# Windows
start knowledge_graph.html
```

#### C. Interacting with the Web Graph:
- **Drag nodes**: Move entities around to watch the physics simulation adjust.
- **Scroll**: Zoom in and out.
- **Click**: Click any node or relation arrow to view its connections and source sentence.
- **Search bar**: Type any name (e.g. `Curie` or `Apple`) to automatically pan and zoom to it.

---

### 4. LLM-Assisted Triplet Extraction Options

This repository includes **two specialized scripts** for using LLMs to extract knowledge graph triplets:

| Script | Key Capabilities | Best Used When... |
| :--- | :--- | :--- |
| [**`llm_bridge.py`**](llm_bridge.py) *(Enhanced)* | • Local inference via **Ollama** (`--ollama`)<br>• Local inference via **LM Studio** (`--lmstudio`)<br>• Direct `.gguf` / MLX model loading (`--local-path`)<br>• Cloud APIs (OpenAI, Gemini, Anthropic)<br>• Interactive copy-paste fallback | You want automated local extraction using your local GPU (e.g. Llama 3.2 on M1 Mac) or cloud APIs. |
| [**`llm_bridge_copypaste.py`**](llm_bridge_copypaste.py) *(Original)* | • Pure prompt generator & terminal JSON parser<br>• Zero local model installation required<br>• Works with any free browser chat window | You don't have local LLM software installed and just want to copy/paste into ChatGPT, Claude, or Gemini. |

---

#### A. Using `llm_bridge.py` (Local Models & Automated Inference)

1. **Run with your local Ollama model (e.g. Llama 3.2 on M1 Mac)**:
   ```bash
   python llm_bridge.py --ollama --model llama3.2-local
   ```

2. **Run with LM Studio local server**:
   Start the local server in LM Studio on port 1234, then run:
   ```bash
   python llm_bridge.py --lmstudio
   ```

3. **Run directly from a local `.gguf` file**:
   ```bash
   python llm_bridge.py --local-path "/path/to/your/model.gguf"
   ```

4. **Run in interactive copy-paste mode (fallback)**:
   ```bash
   python llm_bridge.py
   ```

---

#### B. Using `llm_bridge_copypaste.py` (Lightweight Browser Copy-Paste)

This script is 100% lightweight and requires zero local LLM tools:

1. **Start the script**:
   ```bash
   python llm_bridge_copypaste.py
   ```
2. **Copy** the prompt printed in your terminal.
3. **Paste** it into [ChatGPT](https://chatgpt.com), [Claude](https://claude.ai), or [Gemini](https://gemini.google.com).
4. **Copy** the JSON response from your browser, paste it back into the terminal, and type `END`.
5. The script validates the JSON and updates `triplets.json` and `knowledge_graph.ttl` automatically!

*(To preview sample output formats for both tools, see [**`output.md`**](output.md)).*


---

## 📁 Repository Structure

```text
KG_Ex/
│
├── README.md                      # Complete project documentation (you are here)
├── output.md                      # Comprehensive sample formats for all outputs
├── requirements.txt               # Project dependencies (spacy, rdflib, networkx, matplotlib)
├── sample_text.txt                # Educational input text corpus
├── sample_questions.txt           # Tailored practice questions for testing
├── llm_bridge.py                  # Local LLM extractor (Ollama, LM Studio, GGUF, APIs)
├── llm_bridge_copypaste.py        # Lightweight manual copy-paste extractor for web chats
│

├── 01_basic_kg/                   # ========================================================
│   ├── README.md                  # Detailed learner guide for Version 1
│   ├── extractor.py               # NLP Dependency Parsing (SPO Triplet Extraction)
│   ├── rdf_store.py               # RDFLib Graph Manager (URIs, Literals, SPARQL, CRUD)
│   ├── conversational_agent.py    # Natural Language Graph-QA Chatbot
│   └── run_basic.py               # One-click beginner-friendly runner for Version 1
│                                  # ========================================================
│
├── 02_visual_kg/                  # ========================================================
│   ├── README.md                  # Detailed learner guide for Version 2
│   ├── visualizer.py              # Visualizer (Matplotlib PNG + Vis.js Interactive HTML)
│   └── run_visual.py              # One-click runner to generate visual graphs
│                                  # ========================================================
│
├── knowledge_graph.ttl            # Generated RDF Knowledge Graph (Turtle format)
├── triplets.json                  # Extracted triplets in structured JSON
├── knowledge_graph.png            # Static visual diagram
└── knowledge_graph.html           # Standalone interactive web application
```

---

## 💡 Contributing & Feedback
This repository is built for learners. Feel free to fork it, add your own custom text files, add new query patterns, or connect local LLMs (like Ollama or HuggingFace) for open-ended reasoning!
