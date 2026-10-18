"""
=============================================================================
VERSION 1: BASIC KNOWLEDGE GRAPH - MODULE 2: RDF GRAPH STORE (RDFLib)
=============================================================================
Educational Concept:
-------------------
In computer science, strings alone (like "Marie Curie") can be ambiguous.
The W3C Semantic Web standard solves this using **RDF** (Resource Description Framework):

1. **URIs (Uniform Resource Identifiers)**:
   Every entity gets a unique identifier.
   Example: `http://example.org/kg/Marie_Curie` (shortened to `ex:Marie_Curie`)

2. **Literals**:
   Values like numbers, dates, and strings with specific data types.
   Example: `"1911"^^xsd:gYear`

3. **Prefixes / Namespaces**:
   Shortcuts for long web URLs:
   - `ex:`   -> `http://example.org/kg/` (Our custom domain)
   - `rdfs:` -> `http://www.w3.org/2000/01/rdf-schema#` (Standard schema vocabulary)
   - `xsd:`  -> `http://www.w3.org/2001/XMLSchema#` (Standard datatypes: year, string, int)

4. **SPARQL**:
   The SQL-equivalent query language designed specifically for Knowledge Graphs.
=============================================================================
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Union
import rdflib
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD


class BasicRDFStore:
    """
    Manages an in-memory RDF Graph using RDFLib.
    Supports storing triplets, running SPARQL queries, and modifying facts.
    """

    DEFAULT_BASE_URI = "http://example.org/kg/"

    def __init__(self, base_uri: str = DEFAULT_BASE_URI):
        self.graph = Graph()
        self.base_uri = base_uri
        self.EX = Namespace(base_uri)

        # Bind namespaces for clean serialization in Turtle and queries
        self.graph.bind("ex", self.EX)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)

    def to_uri_slug(self, text: str) -> str:
        """
        Converts human text into a clean URI-safe slug.
        Example: 'Nobel Prize in Chemistry' -> 'Nobel_Prize_in_Chemistry'
        """
        text = text.strip()
        # Remove leading articles ('the', 'a', 'an')
        text = re.sub(r"^(the|a|an)\s+", "", text, flags=re.IGNORECASE)
        # Keep alphanumeric, underscores, and hyphens
        clean = re.sub(r"[^\w\s-]", "", text)
        words = clean.split()
        return "_".join(words) if words else "Entity"

    def to_predicate_slug(self, text: str) -> str:
        """
        Converts relationship text into camelCase for ontology naming.
        Example: 'was created by' -> 'wasCreatedBy', 'won in' -> 'wonIn'
        """
        clean = re.sub(r"[^\w\s]", " ", text).strip()
        words = clean.split()
        if not words:
            return "relatesTo"
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])

    def is_year_or_number(self, text: str) -> bool:
        """Detects if a string is a 4-digit year (e.g., '1911', '2007')."""
        return bool(re.match(r"^\d{4}$", text.strip()))

    def add_triplet(
        self,
        subject_name: str,
        predicate_name: str,
        object_val: str,
        add_labels: bool = True
    ) -> Tuple[URIRef, URIRef, Union[URIRef, Literal]]:
        """
        Converts (Subject, Predicate, Object) into RDF terms and adds them to the graph.
        - Automatically creates URIs for subjects and objects.
        - Casts 4-digit years into typed literals (`xsd:gYear`).
        - Attaches `rdfs:label` for human-readable discovery.
        """
        s_uri = self.EX[self.to_uri_slug(subject_name)]
        p_uri = self.EX[self.to_predicate_slug(predicate_name)]

        # Check if object is a literal year or an entity URI
        if self.is_year_or_number(object_val):
            o_node = Literal(object_val.strip(), datatype=XSD.gYear)
        else:
            o_uri = self.EX[self.to_uri_slug(object_val)]
            o_node = o_uri
            if add_labels:
                clean_obj_label = re.sub(r"^(the|a|an)\s+", "", object_val.strip(), flags=re.IGNORECASE)
                self.graph.add((o_node, RDFS.label, Literal(clean_obj_label)))

        # Add the core relation triple
        self.graph.add((s_uri, p_uri, o_node))

        # Add human-readable label for subject
        if add_labels:
            clean_subj_label = re.sub(r"^(the|a|an)\s+", "", subject_name.strip(), flags=re.IGNORECASE)
            self.graph.add((s_uri, RDFS.label, Literal(clean_subj_label)))

        return s_uri, p_uri, o_node

    def store_triplets(self, triplets: List[Any], add_labels: bool = True):
        """Batch loads a list of Triplet objects or dictionaries into the RDF graph."""
        for t in triplets:
            if hasattr(t, "subject"):
                s, p, o = t.subject, t.predicate, t.object
            else:
                s, p, o = t["subject"], t["predicate"], t["object"]
            self.add_triplet(s, p, o, add_labels=add_labels)

    # -------------------------------------------------------------------------
    # QUERYING (SPARQL & PATTERN MATCHING)
    # -------------------------------------------------------------------------

    def query_sparql(self, sparql_query: str) -> List[Dict[str, str]]:
        """
        Executes a SPARQL query against the graph and returns dictionary rows.
        Example query:
          SELECT ?who WHERE { ?who ex:discovered ex:radium . }
        """
        results = self.graph.query(sparql_query)
        output = []
        for row in results:
            row_dict = {}
            for var in results.vars:
                val = row[var]
                row_dict[str(var)] = str(val) if val is not None else ""
            output.append(row_dict)
        return output

    def find_triples(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object_: Optional[str] = None
    ) -> List[Tuple[str, str, str]]:
        """Finds triples using simple pattern matching with optional wildcards (None)."""
        s_node = self.EX[self.to_uri_slug(subject)] if subject else None
        p_node = self.EX[self.to_predicate_slug(predicate)] if predicate else None
        o_node = None
        if object_:
            if self.is_year_or_number(object_):
                o_node = Literal(object_.strip(), datatype=XSD.gYear)
            else:
                o_node = self.EX[self.to_uri_slug(object_)]

        matched = []
        for s, p, o in self.graph.triples((s_node, p_node, o_node)):
            matched.append((str(s), str(p), str(o)))
        return matched

    # -------------------------------------------------------------------------
    # MODIFICATIONS (ADD, UPDATE, DELETE)
    # -------------------------------------------------------------------------

    def remove_triplet(self, subject_name: str, predicate_name: str, object_val: str) -> int:
        """Removes a fact from the Knowledge Graph."""
        s_uri = self.EX[self.to_uri_slug(subject_name)]
        p_uri = self.EX[self.to_predicate_slug(predicate_name)]
        if self.is_year_or_number(object_val):
            o_node = Literal(object_val.strip(), datatype=XSD.gYear)
        else:
            o_node = self.EX[self.to_uri_slug(object_val)]

        initial_len = len(self.graph)
        self.graph.remove((s_uri, p_uri, o_node))
        return initial_len - len(self.graph)

    def update_triplet_object(
        self,
        subject_name: str,
        predicate_name: str,
        old_object_val: str,
        new_object_val: str
    ) -> bool:
        """Updates the object value of an existing relationship."""
        removed = self.remove_triplet(subject_name, predicate_name, old_object_val)
        if removed > 0:
            self.add_triplet(subject_name, predicate_name, new_object_val)
            return True
        return False

    # -------------------------------------------------------------------------
    # FILE I/O (TURTLE & JSON-LD)
    # -------------------------------------------------------------------------

    def save_to_file(self, file_path: str, format: str = "turtle"):
        """Serializes the RDF graph to a file (default: Turtle .ttl format)."""
        self.graph.serialize(destination=file_path, format=format)
        print(f"[RDF Store] Saved {len(self.graph)} RDF triples to '{file_path}' ({format})")

    def load_from_file(self, file_path: str, format: str = "turtle"):
        """Loads and parses an existing RDF file."""
        self.graph.parse(file_path, format=format)
        print(f"[RDF Store] Loaded {len(self.graph)} triples from '{file_path}'")

    def __len__(self) -> int:
        return len(self.graph)
