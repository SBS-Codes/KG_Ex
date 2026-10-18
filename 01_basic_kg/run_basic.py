"""
=============================================================================
VERSION 1: BASIC KNOWLEDGE GRAPH - MASTER RUNNER
=============================================================================
This script executes the entire basic Knowledge Graph lifecycle step-by-step
with clear educational explanations printed at each phase:

  Phase 1: Read raw text from file
  Phase 2: Extract (Subject, Predicate, Object) triplets using NLP
  Phase 3: Convert triplets to RDF Semantic Web format & save Turtle (.ttl)
  Phase 4: Run test SPARQL queries
  Phase 5: Run Conversational Agent with questions tailored to the text!
=============================================================================
"""

import os
import sys

# Ensure local imports work regardless of working directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from extractor import BasicTripletExtractor, print_triplets_table, save_triplets_json
from rdf_store import BasicRDFStore
from conversational_agent import BasicConversationalAgent


def main():
    print("=" * 80)
    print("🎓 VERSION 1: BASIC KNOWLEDGE GRAPH EXPLAINER & PIPELINE")
    print("=" * 80)

    # Locate sample text
    sample_path = os.path.join(parent_dir, "sample_text.txt")
    if not os.path.exists(sample_path):
        sample_path = "sample_text.txt"

    ttl_output_path = os.path.join(parent_dir, "knowledge_graph.ttl")
    json_output_path = os.path.join(parent_dir, "triplets.json")

    # -------------------------------------------------------------------------
    # PHASE 1: READ TEXT
    # -------------------------------------------------------------------------
    print("\n[PHASE 1] Reading Input Text File")
    print("-" * 50)
    with open(sample_path, "r", encoding="utf-8") as f:
        text_content = f.read().strip()
    print(f"Loaded file: {sample_path}")
    print("Content preview:")
    for line in text_content.splitlines()[:5]:
        print(f"  > {line}")
    print("  ...")

    # -------------------------------------------------------------------------
    # PHASE 2: EXTRACT TRIPLETS (NLP DEPENDENCY PARSING)
    # -------------------------------------------------------------------------
    print("\n[PHASE 2] Extracting (Subject, Predicate, Object) Triplets")
    print("-" * 50)
    print("Concept: spaCy parses sentences to identify:")
    print("  • Subjects (who/what performs action)")
    print("  • Predicates (verbs/actions)")
    print("  • Objects (who/what receives action)")
    
    extractor = BasicTripletExtractor()
    triplets = extractor.extract_from_text(text_content)
    print_triplets_table(triplets)
    save_triplets_json(triplets, json_output_path)

    # -------------------------------------------------------------------------
    # PHASE 3: STORE IN RDF GRAPH (RDFLib TURTLE)
    # -------------------------------------------------------------------------
    print("\n[PHASE 3] Ingesting into RDF Graph Store (RDFLib)")
    print("-" * 50)
    print("Concept: We map text into unambiguous Semantic Web URIs:")
    print("  • 'Marie Curie' -> <http://example.org/kg/Marie_Curie>")
    print("  • '1911'        -> \"1911\"^^<http://www.w3.org/2001/XMLSchema#gYear>")
    
    rdf_store = BasicRDFStore()
    rdf_store.store_triplets(triplets)
    rdf_store.save_to_file(ttl_output_path, format="turtle")
    print(f"Total RDF Statements stored: {len(rdf_store)}")

    # -------------------------------------------------------------------------
    # PHASE 4: QUERYING WITH SPARQL
    # -------------------------------------------------------------------------
    print("\n[PHASE 4] Direct SPARQL Query Demonstration")
    print("-" * 50)
    query = """
    PREFIX ex: <http://example.org/kg/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?personLabel ?awardLabel WHERE {
        ?person ex:won ?award .
        ?person rdfs:label ?personLabel .
        ?award rdfs:label ?awardLabel .
        FILTER(CONTAINS(LCASE(?awardLabel), 'chemistry'))
    }
    """
    print("Running SPARQL Query: 'Find who won an award containing Chemistry'")
    results = rdf_store.query_sparql(query)
    for r in results:
        print(f"  Result: {r['personLabel']} won the {r['awardLabel']}")

    # -------------------------------------------------------------------------
    # PHASE 5: CONVERSATIONAL AGENT ON TAILORED QUESTIONS
    # -------------------------------------------------------------------------
    print("\n[PHASE 5] Testing Conversational Agent on Tailored Questions")
    print("-" * 50)
    agent = BasicConversationalAgent(graph_path=ttl_output_path)

    tailored_questions = [
        "Who won the nobel prize for chemistry?",
        "What did Marie Curie discover?",
        "Who created Python and when?",
        "Who designed the ACE computer?",
        "Who co-founded Apple?",
        "What did Google develop?",
        "Tell me about Albert Einstein",
    ]

    for q in tailored_questions:
        ans = agent.answer_question(q)
        print(f"Q: {q}")
        print(f"A: {ans}\n")

    print("=" * 80)
    print("🎉 Version 1 Pipeline Complete!")
    print(f"  • JSON File:   {json_output_path}")
    print(f"  • Turtle File: {ttl_output_path}")
    print("To chat interactively: python 01_basic_kg/conversational_agent.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
