"""
=============================================================================
VERSION 1: BASIC KNOWLEDGE GRAPH - MODULE 3: CONVERSATIONAL AGENT (KG-QA)
=============================================================================
Educational Concept:
-------------------
A Knowledge Graph Conversational Agent turns natural language questions into
graph queries (SPARQL) to produce 100% grounded, hallucination-free answers:

1. **Entity Linking**:
   Identifies the entity being discussed in the question (e.g., "chemistry" ->
   `ex:Nobel_Prize_in_Chemistry`, "Python" -> `ex:Python`).

2. **Intent & Relation Mapping**:
   Translates question intent ("Who won", "When was", "Who created") into
   the corresponding predicate in the graph (`ex:won`, `ex:wasCreatedIn`, `ex:wasCreatedBy`).

3. **SPARQL Execution**:
   Executes the query against the RDF graph.

4. **Natural Language Generation (NLG)**:
   Takes the structured RDF result and formats it into a human-friendly sentence.
=============================================================================
"""

import os
import sys
import argparse
from typing import List, Dict, Any, Optional

# Support importing rdf_store from the same folder or parent
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from rdf_store import BasicRDFStore


class BasicConversationalAgent:
    """
    Translates English questions into SPARQL queries over the RDF Knowledge Graph
    and returns factual, grounded responses.
    """

    def __init__(self, graph_path: str = "knowledge_graph.ttl", verbose: bool = False):
        self.verbose = verbose
        self.graph_path = graph_path
        self.store = BasicRDFStore()

        if not os.path.exists(graph_path):
            # Also check one directory up in case run from inside 01_basic_kg
            parent_graph = os.path.join(os.path.dirname(current_dir), os.path.basename(graph_path))
            if os.path.exists(parent_graph):
                graph_path = parent_graph
            else:
                raise FileNotFoundError(f"Knowledge Graph file not found at: {graph_path}")

        self.store.load_from_file(graph_path)
        self._index_entities()

    def _index_entities(self):
        """Discovers all entities and their labels stored in the RDF graph."""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?entity ?label WHERE {
            ?entity rdfs:label ?label .
        }
        """
        rows = self.store.query_sparql(query)
        self.entity_index: Dict[str, Dict[str, str]] = {}
        for r in rows:
            entity_uri = r["entity"]
            label = r["label"]
            self.entity_index[label.lower()] = {
                "uri": entity_uri,
                "label": label,
                "slug": entity_uri.split("/")[-1]
            }

    def _find_matching_entities(self, query_text: str) -> List[Dict[str, str]]:
        """Scans the user prompt to find known entities from the graph."""
        q_lower = query_text.lower()
        matches = []
        # Sort by label length descending (matches 'Nobel Prize in Chemistry' before 'Chemistry')
        for label_key, info in sorted(self.entity_index.items(), key=lambda x: len(x[0]), reverse=True):
            if label_key in q_lower:
                matches.append(info)
            elif any(word in q_lower.split() for word in label_key.split() if len(word) > 4):
                if info not in matches:
                    matches.append(info)
        return matches

    def _execute_query(self, sparql: str) -> List[Dict[str, str]]:
        if self.verbose:
            print("\n[Generated SPARQL Query]:")
            print(sparql.strip())
        return self.store.query_sparql(sparql)

    def answer_question(self, question: str) -> str:
        """Answers a user question using SPARQL graph querying."""
        q = question.strip()
        q_lower = q.lower()

        # Greetings & Help
        if q_lower in ("hi", "hello", "hey", "help"):
            return (
                "Hello! I am your Knowledge Graph Conversational Agent.\n"
                "Try asking questions based on the text:\n"
                " • 'Who won the nobel prize for chemistry?'\n"
                " • 'What did Marie Curie discover?'\n"
                " • 'Who created Python?'\n"
                " • 'When was the iPhone released?'\n"
                " • 'Tell me about Apple'\n"
                " • 'What topics do you know about?'"
            )

        if "what topics" in q_lower or "what do you know" in q_lower or "list entities" in q_lower:
            entities = sorted(list({info["label"] for info in self.entity_index.values()}))
            return "Here are the primary entities in my Knowledge Graph:\n • " + "\n • ".join(entities)

        # ---------------------------------------------------------------------
        # PATTERN 1: WHO WON [AWARD]?
        # ---------------------------------------------------------------------
        if "who won" in q_lower or "winner" in q_lower or "nobel" in q_lower:
            award_filter = ""
            if "chemistry" in q_lower:
                award_filter = "FILTER(CONTAINS(LCASE(?awardLabel), 'chemistry'))"
            elif "physics" in q_lower:
                award_filter = "FILTER(CONTAINS(LCASE(?awardLabel), 'physics'))"

            sparql = f"""
            PREFIX ex: <http://example.org/kg/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?winnerLabel ?awardLabel ?year WHERE {{
                ?winner ex:won ?award .
                ?winner rdfs:label ?winnerLabel .
                ?award rdfs:label ?awardLabel .
                OPTIONAL {{ ?winner ex:wonIn ?year }}
                {award_filter}
            }}
            """
            results = self._execute_query(sparql)
            if results:
                answers = []
                for r in results:
                    ans = f"{r['winnerLabel']} won the {r['awardLabel']}"
                    if r.get("year"):
                        ans += f" in {r['year']}"
                    answers.append(ans)
                return ". ".join(answers) + "."

        # ---------------------------------------------------------------------
        # PATTERN 2: WHO CREATED / DESIGNED / DEVELOPED / CO-FOUNDED
        # ---------------------------------------------------------------------
        if any(w in q_lower for w in ("who created", "who designed", "who developed", "who founded", "who co-founded")):
            matches = self._find_matching_entities(q_lower)
            if matches:
                target = matches[0]
                target_uri = target["uri"]

                sparql = f"""
                PREFIX ex: <http://example.org/kg/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT ?creatorLabel ?relation ?year WHERE {{
                    {{
                        <{target_uri}> ex:wasCreatedBy ?creator .
                        ?creator rdfs:label ?creatorLabel .
                        BIND('created' AS ?relation)
                        OPTIONAL {{ <{target_uri}> ex:wasCreatedIn ?year }}
                    }} UNION {{
                        ?creator ex:designed <{target_uri}> .
                        ?creator rdfs:label ?creatorLabel .
                        BIND('designed' AS ?relation)
                        OPTIONAL {{ ?creator ex:designedIn ?year }}
                    }} UNION {{
                        ?creator ex:developed <{target_uri}> .
                        ?creator rdfs:label ?creatorLabel .
                        BIND('developed' AS ?relation)
                    }} UNION {{
                        ?creator ex:coFounded <{target_uri}> .
                        ?creator rdfs:label ?creatorLabel .
                        BIND('co-founded' AS ?relation)
                    }}
                }}
                """
                results = self._execute_query(sparql)
                if results:
                    r = results[0]
                    resp = f"{target['label']} was {r['relation']} by {r['creatorLabel']}"
                    if r.get("year"):
                        resp += f" in {r['year']}"
                    return resp + "."

        # ---------------------------------------------------------------------
        # PATTERN 3: WHEN WAS [ENTITY] CREATED / RELEASED / DESIGNED?
        # ---------------------------------------------------------------------
        if "when" in q_lower or "what year" in q_lower:
            matches = self._find_matching_entities(q_lower)
            if matches:
                target = matches[0]
                target_uri = target["uri"]

                sparql = f"""
                PREFIX ex: <http://example.org/kg/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT ?year ?rel WHERE {{
                    {{ <{target_uri}> ex:wasCreatedIn ?year . BIND('created' AS ?rel) }}
                    UNION
                    {{ <{target_uri}> ex:releasedIn ?year . BIND('released' AS ?rel) }}
                    UNION
                    {{ ?creator ex:designed <{target_uri}> ; ex:designedIn ?year . BIND('designed' AS ?rel) }}
                    UNION
                    {{ ?winner ex:won <{target_uri}> ; ex:wonIn ?year . BIND('awarded' AS ?rel) }}
                }}
                """
                results = self._execute_query(sparql)
                if results:
                    r = results[0]
                    return f"{target['label']} was {r['rel']} in {r['year']}."

        # ---------------------------------------------------------------------
        # PATTERN 4: WHAT DID [ENTITY] DISCOVER / DEVELOP / PUBLISH / RELEASE?
        # ---------------------------------------------------------------------
        if any(w in q_lower for w in ("what did", "discover", "develop", "publish", "release")):
            matches = self._find_matching_entities(q_lower)
            if matches:
                target = matches[0]
                target_uri = target["uri"]

                pred_filter = ""
                if "discover" in q_lower:
                    pred_filter = "FILTER(?pred = ex:discovered)"
                elif "develop" in q_lower:
                    pred_filter = "FILTER(?pred = ex:developed)"
                elif "publish" in q_lower:
                    pred_filter = "FILTER(?pred = ex:published)"
                elif "release" in q_lower:
                    pred_filter = "FILTER(?pred = ex:released)"
                else:
                    pred_filter = "FILTER(?pred IN (ex:discovered, ex:developed, ex:won, ex:released, ex:published))"

                sparql = f"""
                PREFIX ex: <http://example.org/kg/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                SELECT ?pred ?itemLabel WHERE {{
                    <{target_uri}> ?pred ?item .
                    ?item rdfs:label ?itemLabel .
                    {pred_filter}
                }}
                """
                results = self._execute_query(sparql)
                if results:
                    grouped: Dict[str, List[str]] = {}
                    for r in results:
                        pred_name = r["pred"].split("/")[-1]
                        grouped.setdefault(pred_name, []).append(r["itemLabel"])

                    parts = []
                    for pred, items in grouped.items():
                        items_str = ", ".join(items[:-1]) + (" and " + items[-1] if len(items) > 1 else items[0])
                        parts.append(f"{pred} {items_str}")
                    return f"{target['label']} {', and '.join(parts)}."

        # ---------------------------------------------------------------------
        # PATTERN 5: "TELL ME ABOUT [ENTITY]" OR GENERAL GRAPH SEARCH
        # ---------------------------------------------------------------------
        matches = self._find_matching_entities(q_lower)
        if matches:
            target = matches[0]
            target_uri = target["uri"]

            sparql = f"""
            PREFIX ex: <http://example.org/kg/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?direction ?relName ?otherLabel WHERE {{
                {{
                    <{target_uri}> ?p ?obj .
                    ?obj rdfs:label ?otherLabel .
                    BIND('out' AS ?direction)
                    BIND(STRAFTER(STR(?p), 'http://example.org/kg/') AS ?relName)
                    FILTER(?p != rdfs:label)
                }} UNION {{
                    <{target_uri}> ?p ?otherLiteral .
                    FILTER(isLiteral(?otherLiteral))
                    BIND('out' AS ?direction)
                    BIND(STRAFTER(STR(?p), 'http://example.org/kg/') AS ?relName)
                    BIND(STR(?otherLiteral) AS ?otherLabel)
                    FILTER(?p != rdfs:label)
                }} UNION {{
                    ?subj ?p <{target_uri}> .
                    ?subj rdfs:label ?otherLabel .
                    BIND('in' AS ?direction)
                    BIND(STRAFTER(STR(?p), 'http://example.org/kg/') AS ?relName)
                }}
            }}
            """
            results = self._execute_query(sparql)
            if results:
                facts = []
                for r in results:
                    rel = r["relName"]
                    other = r["otherLabel"]
                    if r["direction"] == "out":
                        facts.append(f"• {target['label']} {rel} {other}")
                    else:
                        facts.append(f"• {other} {rel} {target['label']}")
                return f"Here is what I know about **{target['label']}**:\n" + "\n".join(facts)

        # Fallback if no matching entity or pattern
        return (
            "I could not find an answer in the Knowledge Graph for that question.\n"
            "Try asking about: Marie Curie, Python, Apple, Steve Jobs, "
            "Alan Turing, Google, or Albert Einstein."
        )


def run_interactive_chat(agent: BasicConversationalAgent):
    """Runs a live conversational chat in the terminal."""
    print("=" * 70)
    print("🤖 Version 1: Basic Knowledge Graph Conversational Agent")
    print("Type your questions below. Type 'exit', 'quit', or 'q' to stop.")
    print("=" * 70)
    print(agent.answer_question("help") + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Agent: Goodbye! Keep learning Knowledge Graphs!")
                break
            response = agent.answer_question(user_input)
            print(f"Agent: {response}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nAgent: Goodbye!")
            break


def run_demo(agent: BasicConversationalAgent):
    """Runs through the benchmark questions tailored to sample_text.txt."""
    questions = [
        "Who won the nobel prize for chemistry?",
        "What did Marie Curie discover?",
        "Who created Python?",
        "When was Python created?",
        "Who designed the ACE computer?",
        "Who co-founded Apple?",
        "What did Google develop?",
        "What did Albert Einstein publish?",
        "Tell me about Apple",
    ]

    print("=" * 75)
    print("🤖 Version 1: Knowledge Graph Benchmark QA Demo")
    print("=" * 75)
    for idx, q in enumerate(questions, 1):
        print(f"\n[Q{idx}]: {q}")
        ans = agent.answer_question(q)
        print(f"[Answer]: {ans}")
        print("-" * 75)


def main():
    parser = argparse.ArgumentParser(description="Basic Knowledge Graph Conversational Agent")
    parser.add_argument("--graph", "-g", default="knowledge_graph.ttl", help="Path to RDF Turtle graph")
    parser.add_argument("--ask", "-a", type=str, default=None, help="Ask a single question directly")
    parser.add_argument("--demo", "-d", action="store_true", help="Run benchmark QA demo")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show generated SPARQL queries")
    args = parser.parse_args()

    agent = BasicConversationalAgent(graph_path=args.graph, verbose=args.verbose)

    if args.ask:
        ans = agent.answer_question(args.ask)
        print(f"\nQuestion: {args.ask}")
        print(f"Answer:   {ans}\n")
    elif args.demo:
        run_demo(agent)
    else:
        run_interactive_chat(agent)


if __name__ == "__main__":
    main()
