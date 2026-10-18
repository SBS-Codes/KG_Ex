"""
Knowledge Graph Conversational Agent (KG-QA)
--------------------------------------------
A conversational question-answering agent that queries the RDF Knowledge Graph
using SPARQL to answer natural language questions (e.g., "Who won the nobel prize for chemistry?").

Features:
- Entity Linking: Matches entities mentioned in user queries to RDF nodes.
- Intent & Relation Mapping: Converts natural language questions into SPARQL queries.
- Conversational Response Generation: Formats RDF query results into natural English answers.
- Fallback Entity Explorer: Provides contextual summaries for "Tell me about X" or open queries.
- Interactive terminal chat mode & one-shot CLI query mode.
"""

import sys
import os
import re
import argparse
from typing import List, Dict, Any, Optional, Tuple

from rdf_manager import RDFGraphManager


class KnowledgeGraphAgent:
    def __init__(self, graph_path: str = "knowledge_graph.ttl", verbose: bool = False):
        self.verbose = verbose
        self.graph_path = graph_path
        self.rdf_mgr = RDFGraphManager()

        if not os.path.exists(graph_path):
            raise FileNotFoundError(f"RDF Knowledge Graph file not found: {graph_path}")

        self.rdf_mgr.load_from_file(graph_path)
        self._index_entities()

    def _index_entities(self):
        """Indexes all entity URIs and human-readable rdfs:label values from the graph."""
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?entity ?label WHERE {
            ?entity rdfs:label ?label .
        }
        """
        rows = self.rdf_mgr.query_sparql(query)
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
        """Identifies entities in user query by searching indexed entity labels."""
        q_lower = query_text.lower()
        matches = []
        # Sort keys by length descending to match longest phrases first (e.g. 'Nobel Prize in Chemistry')
        for label_key, info in sorted(self.entity_index.items(), key=lambda x: len(x[0]), reverse=True):
            # Check full phrase or significant subphrase
            if label_key in q_lower or (len(label_key) > 4 and label_key in q_lower):
                matches.append(info)
            # Match partial keywords (e.g. 'chemistry' matches 'Nobel Prize in Chemistry')
            elif any(word in q_lower.split() for word in label_key.split() if len(word) > 4):
                if info not in matches:
                    matches.append(info)
        return matches

    def _execute_query(self, sparql: str) -> List[Dict[str, str]]:
        if self.verbose:
            print("\n[Generated SPARQL Query]:")
            print(sparql.strip())
        return self.rdf_mgr.query_sparql(sparql)

    def answer_question(self, question: str) -> str:
        """Processes a natural language question and generates a grounded response."""
        q = question.strip()
        q_lower = q.lower()

        # Check for greetings or help
        if q_lower in ("hi", "hello", "hey", "help"):
            return (
                "Hello! I am your Knowledge Graph Conversational Agent.\n"
                "You can ask me questions like:\n"
                " • 'Who won the Nobel prize for chemistry?'\n"
                " • 'Who created Python and when?'\n"
                " • 'What did Marie Curie discover?'\n"
                " • 'Who designed the ACE computer?'\n"
                " • 'Tell me about Apple'\n"
                " • 'What topics do you know about?'"
            )

        if "what topics" in q_lower or "what do you know" in q_lower or "list entities" in q_lower:
            entities = sorted(list({info["label"] for info in self.entity_index.values()}))
            return "Here are the primary entities in my Knowledge Graph:\n • " + "\n • ".join(entities)

        # -------------------------------------------------------------
        # PATTERN 1: WHO WON [AWARD]? / AWARDS
        # -------------------------------------------------------------
        if "who won" in q_lower or "winner" in q_lower or "nobel" in q_lower:
            # Check if specific award mentioned (e.g. chemistry, physics)
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

        # -------------------------------------------------------------
        # PATTERN 2: WHO CREATED / DESIGNED / DEVELOPED / CO-FOUNDED
        # -------------------------------------------------------------
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

        # -------------------------------------------------------------
        # PATTERN 3: WHEN WAS [ENTITY] CREATED / RELEASED / DESIGNED?
        # -------------------------------------------------------------
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

        # -------------------------------------------------------------
        # PATTERN 4: WHAT DID [ENTITY] DISCOVER / DEVELOP / WIN?
        # -------------------------------------------------------------
        if any(w in q_lower for w in ("what did", "discover", "develop", "publish", "release")):
            matches = self._find_matching_entities(q_lower)
            if matches:
                target = matches[0]
                target_uri = target["uri"]

                # Target specific predicate if explicitly requested
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


        # -------------------------------------------------------------
        # PATTERN 5: "TELL ME ABOUT [ENTITY]" OR GENERAL GRAPH SEARCH
        # -------------------------------------------------------------
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
            "I could not find a direct answer in the Knowledge Graph for that question.\n"
            "Try asking about entities such as: Marie Curie, Python, Apple, Steve Jobs, "
            "Alan Turing, Google, or Albert Einstein."
        )


def run_interactive_chat(agent: KnowledgeGraphAgent):
    """Runs a conversational interactive loop in the terminal."""
    print("=" * 70)
    print("🤖 Knowledge Graph Conversational Agent")
    print("Type your questions below. Type 'exit', 'quit', or 'q' to stop.")
    print("=" * 70)

    # Initial greeting
    print(agent.answer_question("help") + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Agent: Goodbye! Have a great day!")
                break
            response = agent.answer_question(user_input)
            print(f"Agent: {response}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nAgent: Goodbye!")
            break


def run_demo(agent: KnowledgeGraphAgent):
    """Demonstrates question answering on a predefined list of benchmark queries."""
    benchmark_questions = [
        "Who won the nobel prize for chemistry?",
        "Who won the nobel prize in physics?",
        "What did Marie Curie discover?",
        "Who created Python and when was it created?",
        "When was Python created?",
        "Who designed the ACE computer?",
        "Who co-founded Apple?",
        "What did Google develop?",
        "Tell me about Albert Einstein",
    ]

    print("=" * 75)
    print("🤖 Conversational Agent Benchmark Demonstration")
    print("=" * 75)

    for idx, q in enumerate(benchmark_questions, 1):
        print(f"\n[Q{idx}]: {q}")
        answer = agent.answer_question(q)
        print(f"[Answer]: {answer}")
        print("-" * 75)


def main():
    parser = argparse.ArgumentParser(description="Conversational Agent for Knowledge Graph QA.")
    parser.add_argument(
        "--graph", "-g",
        default="knowledge_graph.ttl",
        help="Path to RDF Turtle graph file (default: knowledge_graph.ttl)"
    )
    parser.add_argument(
        "--ask", "-a",
        type=str,
        default=None,
        help="Ask a single question directly via CLI and exit"
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run the automated question-answering benchmark demo"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print generated SPARQL queries"
    )

    args = parser.parse_args()

    agent = KnowledgeGraphAgent(graph_path=args.graph, verbose=args.verbose)

    if args.ask:
        answer = agent.answer_question(args.ask)
        print(f"\nQuestion: {args.ask}")
        print(f"Answer:   {answer}\n")
    elif args.demo:
        run_demo(agent)
    else:
        run_interactive_chat(agent)


if __name__ == "__main__":
    main()
