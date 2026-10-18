"""
=============================================================================
VERSION 1: BASIC KNOWLEDGE GRAPH - MODULE 1: TRIPLET EXTRACTOR
=============================================================================
Educational Concept:
-------------------
A Knowledge Graph represents real-world information as a collection of
(Subject, Predicate, Object) triplets:
  - Subject:   The actor or primary entity (e.g., "Marie Curie")
  - Predicate: The action, state, or relationship (e.g., "won")
  - Object:    The target entity or value (e.g., "Nobel Prize in Chemistry")

This module uses spaCy's Dependency Parser to identify grammatical roles
in English sentences and extract clean triplets from raw text.
=============================================================================
"""

import os
import re
import json
import argparse
from typing import List, Dict, Tuple, Any
import spacy
from spacy.tokens import Doc, Span, Token


class Triplet:
    """Represents a single Knowledge Graph fact: (Subject -> Predicate -> Object)."""

    def __init__(self, subject: str, predicate: str, object_: str, sentence: str = ""):
        self.subject = subject.strip()
        self.predicate = predicate.strip()
        self.object = object_.strip()
        self.sentence = sentence.strip()

    def to_dict(self) -> Dict[str, str]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "sentence": self.sentence,
        }

    def __repr__(self) -> str:
        return f"({self.subject} -> [{self.predicate}] -> {self.object})"


class BasicTripletExtractor:
    """
    Extracts Subject-Predicate-Object triplets from text using spaCy NLP.
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        print(f"[Extractor] Loading spaCy English NLP model ('{model_name}')...")
        self.nlp = spacy.load(model_name)

    def preprocess_doc(self, doc: Doc) -> Doc:
        """
        Merges hyphenated words (e.g., 'co-founded' -> 'co-founded')
        so they are treated as a single verb token rather than separated.
        """
        with doc.retokenize() as retokenizer:
            for i in range(len(doc) - 2):
                if doc[i + 1].text == "-" and doc[i].whitespace_ == "" and doc[i + 1].whitespace_ == "":
                    retokenizer.merge(doc[i : i + 3])
        return doc

    def get_full_noun_phrase(self, token: Token, doc: Doc) -> str:
        """
        Expands a single noun token into its complete compound name.
        Example: 'Curie' -> 'Marie Curie', 'theory' -> 'theory of general relativity'.
        """
        base_phrase = token.text
        root_token = token

        # 1. Match noun chunk
        for chunk in doc.noun_chunks:
            if token in chunk:
                base_phrase = chunk.text
                root_token = chunk.root
                break

        # 2. Attach qualifying prepositional phrases like 'of' or 'in'
        for right in root_token.rights:
            if right.dep_ == "prep" and right.text.lower() in ("of", "in"):
                for pchild in right.children:
                    if pchild.dep_ == "pobj":
                        for subchunk in doc.noun_chunks:
                            if pchild in subchunk:
                                return f"{base_phrase} {right.text} {subchunk.text}"
                        return f"{base_phrase} {right.text} {pchild.text}"

        return base_phrase

    def get_verb_predicate(self, verb_token: Token) -> str:
        """
        Collects auxiliary verbs, particles, and negations around a verb.
        Example: 'created' + 'was' -> 'was created'
        """
        pred_tokens = []
        for left in verb_token.lefts:
            if left.dep_ in ("aux", "auxpass", "neg", "prt"):
                pred_tokens.append(left)

        pred_tokens.append(verb_token)

        for right in verb_token.rights:
            if right.dep_ in ("prt",):
                pred_tokens.append(right)

        pred_tokens.sort(key=lambda t: t.i)
        return " ".join([t.text for t in pred_tokens])

    def extract_from_sentence(self, sent_doc: Span, full_doc: Doc) -> List[Triplet]:
        """Extracts triplets from a single parsed sentence."""
        triplets: List[Triplet] = []
        sent_text = sent_doc.text.strip()

        for token in sent_doc:
            if token.pos_ not in ("VERB", "AUX"):
                continue

            # Check if passive voice (e.g., 'Python was created by Guido')
            is_passive = any(t.dep_ == "auxpass" for t in token.lefts)
            base_predicate = self.get_verb_predicate(token)

            # Step 1: Extract Subjects (nsubj = nominal subject, nsubjpass = passive subject)
            subjects: List[str] = []
            for child in token.children:
                if child.dep_ in ("nsubj", "nsubjpass"):
                    subjects.append(self.get_full_noun_phrase(child, full_doc))
                    # Handle conjunctions: e.g. "Alice and Bob visited Paris"
                    for conj in child.conjuncts:
                        subjects.append(self.get_full_noun_phrase(conj, full_doc))

            # Step 2: Extract Direct Objects (dobj, attr)
            direct_objects: List[str] = []
            for child in token.children:
                if child.dep_ in ("dobj", "attr", "acomp"):
                    direct_objects.append(self.get_full_noun_phrase(child, full_doc))
                    # Handle conjunctions: e.g. "radium and polonium"
                    for conj in child.conjuncts:
                        direct_objects.append(self.get_full_noun_phrase(conj, full_doc))

            # Step 3: Extract Prepositional Objects & Agents (prep, agent)
            prep_relations: List[Dict[str, Any]] = []
            for child in token.children:
                if child.dep_ in ("prep", "agent"):
                    prep_word = child.text
                    for pchild in child.children:
                        if pchild.dep_ in ("pobj", "dobj"):
                            pobj_phrase = self.get_full_noun_phrase(pchild, full_doc)
                            is_agent = (child.dep_ == "agent" or prep_word.lower() == "by")
                            prep_relations.append({
                                "prep": prep_word,
                                "pobj": pobj_phrase,
                                "is_agent": is_agent
                            })
                            for conj in pchild.conjuncts:
                                prep_relations.append({
                                    "prep": prep_word,
                                    "pobj": self.get_full_noun_phrase(conj, full_doc),
                                    "is_agent": is_agent
                                })

            # Combine into Triplets:
            # Case A: Subject + Predicate + Direct Object
            for subj in subjects:
                for obj in direct_objects:
                    if subj.lower() != obj.lower():
                        triplets.append(Triplet(subj, base_predicate, obj, sent_text))

            # Case B: Passive Voice with Agent ('Python was created by Guido')
            for prep_info in prep_relations:
                if is_passive and prep_info["is_agent"]:
                    for subj in subjects:
                        rel = f"{base_predicate} {prep_info['prep']}"
                        triplets.append(Triplet(subj, rel, prep_info["pobj"], sent_text))
                elif prep_info["prep"].lower() in ("with", "in", "for", "at", "on"):
                    # Prepositional facts: 'co-founded with', 'designed in 1945'
                    for subj in subjects:
                        rel = f"{base_predicate} {prep_info['prep']}"
                        triplets.append(Triplet(subj, rel, prep_info["pobj"], sent_text))

        return triplets

    def extract_from_text(self, text: str) -> List[Triplet]:
        """Parses an entire text string and returns deduplicated triplets."""
        doc = self.nlp(text)
        doc = self.preprocess_doc(doc)

        all_triplets = []
        for sent in doc.sents:
            all_triplets.extend(self.extract_from_sentence(sent, doc))

        # Deduplicate while preserving order
        unique_triplets = []
        seen = set()
        for t in all_triplets:
            key = (t.subject.lower(), t.predicate.lower(), t.object.lower())
            if key not in seen:
                seen.add(key)
                unique_triplets.append(t)

        return unique_triplets

    def extract_from_file(self, file_path: str) -> List[Triplet]:
        """Reads a text file and extracts all triplets."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.extract_from_text(content)


def print_triplets_table(triplets: List[Triplet]):
    """Prints a clean tabular display of triplets to the console."""
    print("\n" + "=" * 90)
    print(f"{'#':<4} | {'SUBJECT':<26} | {'PREDICATE':<22} | {'OBJECT':<32}")
    print("=" * 90)
    for idx, t in enumerate(triplets, 1):
        s = (t.subject[:23] + "...") if len(t.subject) > 26 else t.subject
        p = (t.predicate[:19] + "...") if len(t.predicate) > 22 else t.predicate
        o = (t.object[:29] + "...") if len(t.object) > 32 else t.object
        print(f"{idx:<4} | {s:<26} | {p:<22} | {o:<32}")
    print("=" * 90 + "\n")


def save_triplets_json(triplets: List[Triplet], output_path: str):
    """Saves triplets to a JSON file."""
    data = [t.to_dict() for t in triplets]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[Extractor] Saved {len(triplets)} triplets to JSON: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Basic Knowledge Graph Triplet Extractor")
    parser.add_argument("--file", "-f", default="sample_text.txt", help="Input text file")
    parser.add_argument("--json-out", "-j", default="triplets.json", help="Output JSON path")
    args = parser.parse_args()

    extractor = BasicTripletExtractor()
    print(f"[Extractor] Reading text from '{args.file}'...")
    triplets = extractor.extract_from_file(args.file)

    print_triplets_table(triplets)
    save_triplets_json(triplets, args.json_out)


if __name__ == "__main__":
    main()
