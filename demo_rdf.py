"""
RDFLib Demonstration: Store, Read/Query, and Modify Knowledge Graph Triplets
----------------------------------------------------------------------------
This script demonstrates the three core operations with RDFLib:
1. STORE: Ingest extracted triplets into an RDF Graph and export to Turtle (.ttl) & JSON-LD.
2. READ & QUERY: Use SPARQL and Python pattern matching to extract knowledge.
3. MODIFY: Add new facts, update existing relationships, and delete facts.
"""

import json
from rdf_manager import RDFGraphManager


def main():
    print("=" * 80)
    print("RDFLib Knowledge Graph Demo: Store, Read, and Modify")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # STEP 1: STORE TRIPLETS IN RDF GRAPH
    # -------------------------------------------------------------------------
    print("\n[STEP 1] STORING TRIPLETS IN RDF GRAPH")
    print("-" * 50)

    # Load extracted triplets from triplets.json
    with open("triplets.json", "r", encoding="utf-8") as f:
        triplets_data = json.load(f)

    rdf_mgr = RDFGraphManager(base_uri="http://example.org/kg/")
    rdf_mgr.store_triplets(triplets_data)

    ttl_file = "knowledge_graph.ttl"
    rdf_mgr.save_to_file(ttl_file, format="turtle")
    print(f"Total RDF statements stored: {len(rdf_mgr)}")

    # Preview first few lines of Turtle
    turtle_preview = rdf_mgr.serialize(format="turtle")
    print("\n--- Preview of Generated Turtle (.ttl) ---")
    print("\n".join(turtle_preview.splitlines()[:20]))
    print("...\n" + "-" * 50)

    # -------------------------------------------------------------------------
    # STEP 2: READ & QUERY WITH SPARQL
    # -------------------------------------------------------------------------
    print("\n[STEP 2] READING & QUERYING TRIPLETS WITH SPARQL")
    print("-" * 50)

    # Query A: Find everything discovered by Marie Curie
    query_curie = """
    PREFIX ex: <http://example.org/kg/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?subjectLabel ?predicate ?objectLabel WHERE {
        ex:Marie_Curie ?predicate ?object .
        ex:Marie_Curie rdfs:label ?subjectLabel .
        OPTIONAL { ?object rdfs:label ?objectLabel }
    }
    """
    print("\nQuery A: What facts exist about 'Marie Curie'?")
    results_a = rdf_mgr.query_sparql(query_curie)
    for r in results_a:
        pred_name = r['predicate'].split('/')[-1].split('#')[-1]
        obj = r.get('objectLabel') or r.get('object') or ""
        if pred_name != "label":  # skip metadata label
            print(f"  • {r['subjectLabel']} --[{pred_name}]--> {obj}")

    # Query B: Find all entities created/designed and their creators or years
    query_creations = """
    PREFIX ex: <http://example.org/kg/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?creation ?creator WHERE {
        ?creation ex:wasCreatedBy ?creator .
    }
    """
    print("\nQuery B: Who created what?")
    results_b = rdf_mgr.query_sparql(query_creations)
    for r in results_b:
        creation = r['creation'].split('/')[-1]
        creator = r['creator'].split('/')[-1]
        print(f"  • Creation: {creation.replace('_', ' ')} | Creator: {creator.replace('_', ' ')}")

    # Query C: Pythonic pattern matching (find all facts about Apple)
    print("\nQuery C: Pythonic pattern matching for 'Apple' as subject:")
    apple_facts = rdf_mgr.find_triples(subject="Apple")
    for s, p, o in apple_facts:
        p_short = p.split('/')[-1]
        o_short = o.split('/')[-1]
        if p_short != "label":
            print(f"  • Apple --[{p_short}]--> {o_short}")

    # -------------------------------------------------------------------------
    # STEP 3: MODIFY TRIPLETS (ADD, UPDATE, DELETE)
    # -------------------------------------------------------------------------
    print("\n[STEP 3] MODIFYING TRIPLETS (ADD, UPDATE, DELETE)")
    print("-" * 50)

    # 3.1 ADD: Insert a new fact into the graph
    print("\n3.1 ADDING NEW FACT:")
    print("  Adding: (Marie Curie -> won in -> 1911)")
    print("  Adding: (Marie Curie -> won -> Nobel Prize in Chemistry)")
    rdf_mgr.add_triplet("Marie Curie", "won in", "1911")
    rdf_mgr.add_triplet("Marie Curie", "won", "Nobel Prize in Chemistry")

    # 3.2 UPDATE: Update an existing fact
    print("\n3.2 UPDATING AN EXISTING FACT:")
    print("  Updating: Apple released the iPhone in 2007 -> 2008 (test update)")
    updated = rdf_mgr.update_triplet_object(
        subject_name="Apple",
        predicate_name="released in",
        old_object_val="2007",
        new_object_val="2008"
    )
    print(f"  Update success: {updated}")

    # Verify update via pattern matching
    print("  Checking updated triples for Apple:")
    for s, p, o in rdf_mgr.find_triples(subject="Apple", predicate="released in"):
        print(f"  • {s.split('/')[-1]} --[{p.split('/')[-1]}]--> {o}")

    # 3.3 DELETE: Remove a fact
    print("\n3.3 DELETING A FACT:")
    print("  Removing: (Alan Turing -> designed in -> 1945)")
    removed_count = rdf_mgr.remove_triplet("Alan Turing", "designed in", "1945")
    print(f"  Triples removed: {removed_count}")

    # Verify deletion
    remaining = rdf_mgr.find_triples(subject="Alan Turing", predicate="designed in")
    print(f"  Remaining 'designed in' triples for Alan Turing: {len(remaining)}")

    # -------------------------------------------------------------------------
    # STEP 4: SAVE MODIFIED GRAPH
    # -------------------------------------------------------------------------
    print("\n[STEP 4] SAVING MODIFIED GRAPH")
    print("-" * 50)
    modified_ttl = "knowledge_graph_modified.ttl"
    modified_jsonld = "knowledge_graph.jsonld"

    rdf_mgr.save_to_file(modified_ttl, format="turtle")
    rdf_mgr.save_to_file(modified_jsonld, format="json-ld")

    print("\n✔ RDFLib demonstration completed successfully!")
    print(f"  - Original Turtle: {ttl_file}")
    print(f"  - Modified Turtle: {modified_ttl}")
    print(f"  - JSON-LD Export:  {modified_jsonld}")


if __name__ == "__main__":
    main()
