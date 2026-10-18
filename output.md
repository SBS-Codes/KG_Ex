# 📋 Sample Output Formats (`output.md`)

This document provides sample formats for all outputs generated across the Knowledge Graph pipeline, including console tables, JSON exports, RDF Turtle files, SPARQL query results, conversational agent transcripts, and the **No-API-Key LLM Prompt/Response format**.

---

## 📌 Table of Contents
1. [Extracted Triplets: Console Table Format](#1-extracted-triplets-console-table-format)
2. [Extracted Triplets: JSON Format (`triplets.json`)](#2-extracted-triplets-json-format-tripletsjson)
3. [RDF Knowledge Graph: Turtle Format (`knowledge_graph.ttl`)](#3-rdf-knowledge-graph-turtle-format-knowledge_graphttl)
4. [RDF Knowledge Graph: JSON-LD Format (`knowledge_graph.jsonld`)](#4-rdf-knowledge-graph-json-ld-format-knowledge_graphjsonld)
5. [SPARQL Query & Result Format](#5-sparql-query--result-format)
6. [Conversational Agent Dialogue Format](#6-conversational-agent-dialogue-format)
7. [No-API-Key LLM Copy-Paste Format (Input Prompt & LLM Output)](#7-no-api-key-llm-copy-paste-format)

---

## 1. Extracted Triplets: Console Table Format

When you run `python 01_basic_kg/extractor.py` or `python 01_basic_kg/run_basic.py`, the extracted triplets are displayed in this clean tabular format:

```text
==========================================================================================
#    | SUBJECT                    | PREDICATE              | OBJECT                          
==========================================================================================
1    | Alan Turing                | designed               | the ACE computer                
2    | Alan Turing                | designed in            | 1945                            
3    | Steve Jobs                 | co-founded             | Apple                           
4    | Steve Jobs                 | co-founded with        | Steve Wozniak                   
5    | Apple                      | released               | the iPhone                      
6    | Apple                      | released in            | 2007                            
7    | Google                     | developed              | TensorFlow                      
8    | Google                     | developed for          | machine learning                
9    | Python                     | was created by         | Guido van Rossum                
10   | Python                     | was created in         | 1991                            
11   | Marie Curie                | discovered             | radium                          
12   | Marie Curie                | discovered             | polonium                        
13   | Marie Curie                | won                    | the Nobel Prize in Physics      
14   | Marie Curie                | won                    | the Nobel Prize in Chemistry    
15   | Marie Curie                | won in                 | 1911                            
16   | Albert Einstein            | published              | the theory of general relativity
==========================================================================================
```

---

## 2. Extracted Triplets: JSON Format (`triplets.json`)

The extracted facts are saved as a machine-readable JSON array. Each object preserves the **Subject**, **Predicate**, **Object**, and the original **Sentence** for provenance:

```json
[
  {
    "subject": "Marie Curie",
    "predicate": "won",
    "object": "the Nobel Prize in Chemistry",
    "sentence": "Marie Curie won the Nobel Prize in Chemistry in 1911."
  },
  {
    "subject": "Marie Curie",
    "predicate": "won in",
    "object": "1911",
    "sentence": "Marie Curie won the Nobel Prize in Chemistry in 1911."
  },
  {
    "subject": "Python",
    "predicate": "was created by",
    "object": "Guido van Rossum",
    "sentence": "Python was created by Guido van Rossum in 1991."
  },
  {
    "subject": "Python",
    "predicate": "was created in",
    "object": "1991",
    "sentence": "Python was created by Guido van Rossum in 1991."
  },
  {
    "subject": "Steve Jobs",
    "predicate": "co-founded",
    "object": "Apple",
    "sentence": "Steve Jobs co-founded Apple with Steve Wozniak."
  },
  {
    "subject": "Steve Jobs",
    "predicate": "co-founded with",
    "object": "Steve Wozniak",
    "sentence": "Steve Jobs co-founded Apple with Steve Wozniak."
  }
]
```

---

## 3. RDF Knowledge Graph: Turtle Format (`knowledge_graph.ttl`)

In **Turtle (`.ttl`)**, human text is mapped to unambiguous W3C URIs, typed literals (`xsd:gYear`), and labels (`rdfs:label`):

```turtle
@prefix ex: <http://example.org/kg/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:Alan_Turing rdfs:label "Alan Turing" ;
    ex:designed ex:ACE_computer ;
    ex:designedIn "1945"^^xsd:gYear .

ex:Albert_Einstein rdfs:label "Albert Einstein" ;
    ex:published ex:theory_of_general_relativity .

ex:Apple rdfs:label "Apple" ;
    ex:released ex:iPhone ;
    ex:releasedIn "2007"^^xsd:gYear .

ex:Google rdfs:label "Google" ;
    ex:developed ex:TensorFlow ;
    ex:developedFor ex:machine_learning .

ex:Marie_Curie rdfs:label "Marie Curie" ;
    ex:discovered ex:polonium,
        ex:radium ;
    ex:won ex:Nobel_Prize_in_Chemistry,
        ex:Nobel_Prize_in_Physics ;
    ex:wonIn "1911"^^xsd:gYear .

ex:Python rdfs:label "Python" ;
    ex:wasCreatedBy ex:Guido_van_Rossum ;
    ex:wasCreatedIn "1991"^^xsd:gYear .

ex:Steve_Jobs rdfs:label "Steve Jobs" ;
    ex:coFounded ex:Apple ;
    ex:coFoundedWith ex:Steve_Wozniak .

ex:ACE_computer rdfs:label "ACE computer" .
ex:Guido_van_Rossum rdfs:label "Guido van Rossum" .
ex:Nobel_Prize_in_Chemistry rdfs:label "Nobel Prize in Chemistry" .
ex:Nobel_Prize_in_Physics rdfs:label "Nobel Prize in Physics" .
ex:Steve_Wozniak rdfs:label "Steve Wozniak" .
ex:TensorFlow rdfs:label "TensorFlow" .
ex:iPhone rdfs:label "iPhone" .
ex:machine_learning rdfs:label "machine learning" .
ex:polonium rdfs:label "polonium" .
ex:radium rdfs:label "radium" .
ex:theory_of_general_relativity rdfs:label "theory of general relativity" .
```

---

## 4. RDF Knowledge Graph: JSON-LD Format (`knowledge_graph.jsonld`)

JSON-LD is standard Linked Data format widely used for web APIs and search engines:

```json
[
  {
    "@id": "http://example.org/kg/Marie_Curie",
    "http://example.org/kg/discovered": [
      { "@id": "http://example.org/kg/polonium" },
      { "@id": "http://example.org/kg/radium" }
    ],
    "http://example.org/kg/won": [
      { "@id": "http://example.org/kg/Nobel_Prize_in_Chemistry" },
      { "@id": "http://example.org/kg/Nobel_Prize_in_Physics" }
    ],
    "http://example.org/kg/wonIn": [
      { "@value": "1911", "@type": "http://www.w3.org/2001/XMLSchema#gYear" }
    ],
    "http://www.w3.org/2000/01/rdf-schema#label": [
      { "@value": "Marie Curie" }
    ]
  }
]
```

---

## 5. SPARQL Query & Result Format

### Example SPARQL Query
```sparql
PREFIX ex: <http://example.org/kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?winnerLabel ?awardLabel ?year WHERE {
    ?winner ex:won ?award .
    ?winner rdfs:label ?winnerLabel .
    ?award rdfs:label ?awardLabel .
    OPTIONAL { ?winner ex:wonIn ?year }
    FILTER(CONTAINS(LCASE(?awardLabel), 'chemistry'))
}
```

### Result Format (Python Dictionary List)
```python
[
  {
    'winnerLabel': 'Marie Curie',
    'awardLabel': 'Nobel Prize in Chemistry',
    'year': '1911'
  }
]
```

---

## 6. Conversational Agent Dialogue Format

When running `python 01_basic_kg/conversational_agent.py`:

```text
======================================================================
🤖 Knowledge Graph Conversational Agent
Type your questions below. Type 'exit', 'quit', or 'q' to stop.
======================================================================
Hello! I am your Knowledge Graph Conversational Agent.
You can ask me questions like:
 • 'Who won the Nobel prize for chemistry?'
 • 'Who created Python and when?'
 • 'What did Marie Curie discover?'
 • 'Who designed the ACE computer?'
 • 'Tell me about Apple'
 • 'What topics do you know about?'

You: Who won the nobel prize for chemistry?
Agent: Marie Curie won the Nobel Prize in Chemistry in 1911.

You: What did Marie Curie discover?
Agent: Marie Curie discovered polonium and radium.

You: Who created Python?
Agent: Python was created by Guido van Rossum in 1991.

You: When was the iPhone released?
Agent: iPhone was released in 2007.

You: Tell me about Apple
Agent: Here is what I know about **Apple**:
• Apple released iPhone
• Apple releasedIn 2007
• Steve Jobs coFounded Apple

You: exit
Agent: Goodbye! Keep learning Knowledge Graphs!
```

---

## 7. No-API-Key LLM Copy-Paste Format

If a user **does not have an API key** (e.g. OpenAI or Gemini), the system generates this structured prompt so the user can paste it into **ChatGPT, Claude, or Gemini web chat**, then copy the JSON response back into the program.

### A. The Input Prompt Formatted for the LLM
*(Copy everything inside this box and paste into any LLM chat window)*

```text
You are an expert Knowledge Graph engineer.
Your task is to extract all factual (Subject, Predicate, Object) triplets from the input text below.

STRICT INSTRUCTIONS:
1. Extract explicit relationships between entities.
2. Separate entities into 'subject', 'predicate', and 'object'.
3. Include the original sentence in 'sentence' for provenance.
4. Output ONLY a valid JSON array of objects. Do not include markdown commentary or explanations.

INPUT TEXT:
"""
Alan Turing designed the ACE computer in 1945.
Steve Jobs co-founded Apple with Steve Wozniak.
Apple released the iPhone in 2007.
Google developed TensorFlow for machine learning.
Python was created by Guido van Rossum in 1991.
Marie Curie discovered radium and polonium.
Marie Curie won the Nobel Prize in Physics.
Marie Curie won the Nobel Prize in Chemistry in 1911.
Albert Einstein published the theory of general relativity.
"""

REQUIRED JSON OUTPUT FORMAT:
[
  {
    "subject": "Entity Name",
    "predicate": "relation or action",
    "object": "Target Entity or Date",
    "sentence": "Original source sentence"
  }
]
```

### B. The Expected Response Format from the LLM
*(Paste the LLM's response directly into the terminal prompt or save as `llm_response.json`)*

```json
[
  {
    "subject": "Alan Turing",
    "predicate": "designed",
    "object": "ACE computer",
    "sentence": "Alan Turing designed the ACE computer in 1945."
  },
  {
    "subject": "Alan Turing",
    "predicate": "designed in",
    "object": "1945",
    "sentence": "Alan Turing designed the ACE computer in 1945."
  },
  {
    "subject": "Steve Jobs",
    "predicate": "co-founded",
    "object": "Apple",
    "sentence": "Steve Jobs co-founded Apple with Steve Wozniak."
  },
  {
    "subject": "Steve Jobs",
    "predicate": "co-founded with",
    "object": "Steve Wozniak",
    "sentence": "Steve Jobs co-founded Apple with Steve Wozniak."
  },
  {
    "subject": "Apple",
    "predicate": "released",
    "object": "iPhone",
    "sentence": "Apple released the iPhone in 2007."
  },
  {
    "subject": "Apple",
    "predicate": "released in",
    "object": "2007",
    "sentence": "Apple released the iPhone in 2007."
  },
  {
    "subject": "Google",
    "predicate": "developed",
    "object": "TensorFlow",
    "sentence": "Google developed TensorFlow for machine learning."
  },
  {
    "subject": "Python",
    "predicate": "was created by",
    "object": "Guido van Rossum",
    "sentence": "Python was created by Guido van Rossum in 1991."
  },
  {
    "subject": "Python",
    "predicate": "was created in",
    "object": "1991",
    "sentence": "Python was created by Guido van Rossum in 1991."
  },
  {
    "subject": "Marie Curie",
    "predicate": "discovered",
    "object": "radium",
    "sentence": "Marie Curie discovered radium and polonium."
  },
  {
    "subject": "Marie Curie",
    "predicate": "discovered",
    "object": "polonium",
    "sentence": "Marie Curie discovered radium and polonium."
  },
  {
    "subject": "Marie Curie",
    "predicate": "won",
    "object": "Nobel Prize in Chemistry",
    "sentence": "Marie Curie won the Nobel Prize in Chemistry in 1911."
  },
  {
    "subject": "Marie Curie",
    "predicate": "won in",
    "object": "1911",
    "sentence": "Marie Curie won the Nobel Prize in Chemistry in 1911."
  },
  {
    "subject": "Albert Einstein",
    "predicate": "published",
    "object": "theory of general relativity",
    "sentence": "Albert Einstein published the theory of general relativity."
  }
]
```

### C. Terminal Workflow in Action
When running `python llm_bridge.py`:

```text
================================================================================
🔑 NO API KEY DETECTED (Free Copy-Paste Mode)
================================================================================
You don't need a paid API key! Follow these 3 simple steps:

[STEP 1]: Copy the prompt below into ChatGPT, Claude, or Gemini:
--------------------------------------------------------------------------------
You are an expert Knowledge Graph engineer.
Extract all (Subject, Predicate, Object) triplets from this text:
...
--------------------------------------------------------------------------------

[STEP 2]: Copy the JSON response from your LLM chat window.

[STEP 3]: Paste it below (Type 'END' on a new empty line when finished):
>>> [
>>>   {"subject": "Marie Curie", "predicate": "won", "object": "Nobel Prize in Chemistry", ...}
>>> ]
>>> END

✔ Successfully parsed 14 triplets from LLM response!
✔ Stored into knowledge_graph.ttl and triplets.json.
```
