"""
RDF Graph Manager (using RDFLib)
--------------------------------
Provides full CRUD capabilities (Store, Read/Query with SPARQL, and Modify)
for Knowledge Graph triplets. Supports Turtle, JSON-LD, N-Triples, and XML serialization.
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Union
import rdflib
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD, FOAF


class RDFGraphManager:
    DEFAULT_NAMESPACE = "http://example.org/kg/"

    def __init__(self, base_uri: str = DEFAULT_NAMESPACE):
        """Initializes an RDF Graph and binds default namespaces."""
        self.graph = Graph()
        self.EX = Namespace(base_uri)
        self.base_uri = base_uri

        # Bind namespaces for clean prefixes in Turtle / SPARQL
        self.graph.bind("ex", self.EX)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        self.graph.bind("rdf", RDF)

    def _to_uri_slug(self, text: str) -> str:
        """
        Converts text into a clean URI-safe slug.
        e.g., 'the Nobel Prize in Physics' -> 'Nobel_Prize_in_Physics'
              'was created by' -> 'wasCreatedBy'
        """
        text = text.strip()
        # Remove leading 'the ', 'a ', 'an '
        text = re.sub(r"^(the|a|an)\s+", "", text, flags=re.IGNORECASE)
        # Replace non-alphanumeric chars (except underscore/hyphen) with underscore
        clean = re.sub(r"[^\w\s-]", "", text)
        words = clean.split()
        if not words:
            return "Entity"
        return "_".join(words)

    def _to_predicate_slug(self, text: str) -> str:
        """
        Converts a predicate string into camelCase for clean ontology naming.
        e.g., 'was created by' -> 'wasCreatedBy', 'co-founded with' -> 'coFoundedWith'
        """
        clean = re.sub(r"[^\w\s]", " ", text).strip()
        words = clean.split()
        if not words:
            return "relatesTo"
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])

    def _is_year_or_number(self, text: str) -> bool:
        """Checks if a string is a 4-digit year or numeric value."""
        return bool(re.match(r"^\d{4}$", text.strip()))

    def add_triplet(
        self,
        subject_name: str,
        predicate_name: str,
        object_val: str,
        add_labels: bool = True
    ) -> Tuple[URIRef, URIRef, Union[URIRef, Literal]]:
        """
        Adds a single (Subject, Predicate, Object) triplet into the RDF Graph.
        - Automatically formats URIs for entities.
        - Detects numerical literals (e.g. years).
        - Attaches rdfs:label for human-readable entity discovery.
        """
        s_slug = self._to_uri_slug(subject_name)
        p_slug = self._to_predicate_slug(predicate_name)

        s_uri = self.EX[s_slug]
        p_uri = self.EX[p_slug]

        # Check if object is a year/literal or an entity URI
        if self._is_year_or_number(object_val):
            o_node = Literal(object_val.strip(), datatype=XSD.gYear)
        else:
            o_slug = self._to_uri_slug(object_val)
            o_node = self.EX[o_slug]
            if add_labels:
                clean_obj_label = re.sub(r"^(the|a|an)\s+", "", object_val.strip(), flags=re.IGNORECASE)
                self.graph.add((o_node, RDFS.label, Literal(clean_obj_label)))

        # Add the core relation
        self.graph.add((s_uri, p_uri, o_node))

        # Add human-readable label for subject
        if add_labels:
            clean_subj_label = re.sub(r"^(the|a|an)\s+", "", subject_name.strip(), flags=re.IGNORECASE)
            self.graph.add((s_uri, RDFS.label, Literal(clean_subj_label)))

        return s_uri, p_uri, o_node

    def store_triplets(self, triplets: List[Any], add_labels: bool = True):
        """Stores a collection of Triplet objects or dictionaries into the RDF graph."""
        for t in triplets:
            if hasattr(t, "subject"):
                s, p, o = t.subject, t.predicate, t.object
            else:
                s, p, o = t["subject"], t["predicate"], t["object"]
            self.add_triplet(s, p, o, add_labels=add_labels)

    # -------------------------------------------------------------
    # READ / QUERY CAPABILITIES
    # -------------------------------------------------------------

    def query_sparql(self, sparql_query: str) -> List[Dict[str, str]]:
        """
        Executes a SPARQL query against the RDF graph.
        Returns a list of dictionary mappings (variable -> string value).
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
        """
        Pattern matching query with wildcards (None matches any).
        Returns list of (Subject, Predicate, Object) string representations.
        """
        s_node = self.EX[self._to_uri_slug(subject)] if subject else None
        p_node = self.EX[self._to_predicate_slug(predicate)] if predicate else None
        o_node = None
        if object_:
            if self._is_year_or_number(object_):
                o_node = Literal(object_.strip(), datatype=XSD.gYear)
            else:
                o_node = self.EX[self._to_uri_slug(object_)]

        matched = []
        for s, p, o in self.graph.triples((s_node, p_node, o_node)):
            matched.append((str(s), str(p), str(o)))
        return matched

    # -------------------------------------------------------------
    # MODIFY CAPABILITIES (Update, Remove)
    # -------------------------------------------------------------

    def remove_triplet(self, subject_name: str, predicate_name: str, object_val: str) -> int:
        """
        Removes matching triples from the graph.
        Returns the number of removed triples.
        """
        s_uri = self.EX[self._to_uri_slug(subject_name)]
        p_uri = self.EX[self._to_predicate_slug(predicate_name)]

        if self._is_year_or_number(object_val):
            o_node = Literal(object_val.strip(), datatype=XSD.gYear)
        else:
            o_node = self.EX[self._to_uri_slug(object_val)]

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
        """
        Updates the object of an existing relation.
        (e.g., updates 'released in 2007' -> 'released in 2008')
        """
        removed = self.remove_triplet(subject_name, predicate_name, old_object_val)
        if removed > 0:
            self.add_triplet(subject_name, predicate_name, new_object_val)
            return True
        return False

    def execute_sparql_update(self, update_query: str):
        """Executes a SPARQL 1.1 UPDATE query (INSERT, DELETE, etc.)."""
        self.graph.update(update_query)

    # -------------------------------------------------------------
    # SERIALIZATION / FILE I/O
    # -------------------------------------------------------------

    def serialize(self, format: str = "turtle") -> str:
        """Serializes the graph into string format ('turtle', 'json-ld', 'nt', 'xml')."""
        return self.graph.serialize(format=format)

    def save_to_file(self, file_path: str, format: str = "turtle"):
        """Saves RDF graph to a file."""
        self.graph.serialize(destination=file_path, format=format)
        print(f"✔ RDF Graph saved to: {file_path} (format: {format}, triples: {len(self.graph)})")

    def load_from_file(self, file_path: str, format: str = "turtle"):
        """Loads and parses an existing RDF graph from file."""
        self.graph.parse(file_path, format=format)
        print(f"✔ RDF Graph loaded from: {file_path} (total triples: {len(self.graph)})")

    def __len__(self) -> int:
        return len(self.graph)
