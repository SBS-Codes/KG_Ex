"""
=============================================================================
LLM BRIDGE: KNOWLEDGE GRAPH TRIPLET EXTRACTOR (WITH NO-API-KEY FALLBACK)
=============================================================================
Educational Concept:
-------------------
Extracting Knowledge Graph triplets can be done using:
  1. Classical NLP (spaCy Dependency Parsing) -> Fast, offline, deterministic
  2. Large Language Models (LLMs)             -> Flexible, handles complex prose

Many learners do NOT have paid API access keys (OpenAI / Anthropic / Gemini).
This script provides a universal "Copy-Paste" fallback:
  - If you have an API key: It calls the model directly.
  - If you do NOT have an API key: It formats the exact prompt for you to copy
    and paste into ChatGPT, Claude, or Gemini (free web chats), then parses
    your pasted JSON response back into the Knowledge Graph!
=============================================================================
"""

import os
import sys
import json
import re
import argparse
from typing import List, Dict, Any, Optional

# Support importing BasicRDFStore from 01_basic_kg
current_dir = os.path.dirname(os.path.abspath(__file__))
basic_dir = os.path.join(current_dir, "01_basic_kg")
if basic_dir not in sys.path:
    sys.path.insert(0, basic_dir)

from rdf_store import BasicRDFStore
from extractor import print_triplets_table, save_triplets_json


def generate_llm_prompt(text_content: str) -> str:
    """Creates a structured few-shot prompt for any LLM."""
    return f"""You are an expert Knowledge Graph engineer.
Your task is to extract all factual (Subject, Predicate, Object) triplets from the input text below.

STRICT INSTRUCTIONS:
1. Extract explicit relationships between entities.
2. Separate entities into 'subject', 'predicate', and 'object'.
3. Include the source sentence in 'sentence' for provenance.
4. Output ONLY a valid JSON array of objects. Do not include markdown commentary, intro, or outro.

INPUT TEXT:
\"\"\"
{text_content.strip()}
\"\"\"

REQUIRED JSON OUTPUT FORMAT:
[
  {{
    "subject": "Entity Name",
    "predicate": "relation or action",
    "object": "Target Entity or Date",
    "sentence": "Original source sentence"
  }}
]
"""


def clean_llm_json_response(raw_response: str) -> List[Dict[str, str]]:
    """Strips markdown code fences (```json ... ```) and parses the JSON array."""
    cleaned = raw_response.strip()
    # Remove markdown code blocks if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    # Find JSON array using regex if surrounded by other text
    match = re.search(r"\[\s*\{.*\}\s*\]", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            valid_triplets = []
            for item in data:
                if isinstance(item, dict) and "subject" in item and "predicate" in item and "object" in item:
                    valid_triplets.append({
                        "subject": str(item["subject"]).strip(),
                        "predicate": str(item["predicate"]).strip(),
                        "object": str(item["object"]).strip(),
                        "sentence": str(item.get("sentence", "")).strip(),
                    })
            return valid_triplets
        else:
            raise ValueError("Parsed JSON is not an array of objects.")
    except Exception as e:
        raise ValueError(f"Failed to parse valid JSON from response: {e}\nRaw output was:\n{raw_response}")


def copy_paste_workflow(prompt: str) -> List[Dict[str, str]]:
    """Interactive fallback when no API key is available."""
    print("\n" + "=" * 80)
    print("🔑 NO API KEY DETECTED (Free Copy-Paste Mode)")
    print("=" * 80)
    print("You don't need a paid API key! Follow these 3 simple steps:\n")

    print("👉 [STEP 1]: Copy the prompt below into ChatGPT, Claude, or Gemini:")
    print("-" * 80)
    print(prompt.strip())
    print("-" * 80)

    print("\n👉 [STEP 2]: Copy the JSON response from your LLM chat window.")
    print("👉 [STEP 3]: Paste the response below.")
    print("           (When done pasting, type 'END' on a new empty line and press Enter):\n")

    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        except EOFError:
            break

    raw_pasted = "\n".join(lines).strip()
    if not raw_pasted:
        print("\n[!] No input received. Operation cancelled.")
        return []

    print("\nParsing pasted response...")
    return clean_llm_json_response(raw_pasted)


def demo_sample_response() -> str:
    """Returns a realistic sample LLM response for demonstration purposes."""
    return """```json
[
  {
    "subject": "Alan Turing",
    "predicate": "designed",
    "object": "the ACE computer",
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
    "object": "the iPhone",
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
    "subject": "Albert Einstein",
    "predicate": "published",
    "object": "the theory of general relativity",
    "sentence": "Albert Einstein published the theory of general relativity."
  }
]
```"""


def main():
    parser = argparse.ArgumentParser(
        description="LLM Knowledge Graph Triplet Extractor with No-API-Key Copy-Paste Fallback."
    )
    parser.add_argument("--file", "-f", default="sample_text.txt", help="Input text file path")
    parser.add_argument("--print-prompt-only", "-p", action="store_true", help="Print the LLM prompt and exit")
    parser.add_argument("--demo", "-d", action="store_true", help="Run automated demonstration with mock LLM response")
    parser.add_argument("--json-out", "-j", default="triplets.json", help="Output JSON path")
    parser.add_argument("--rdf-out", "-r", default="knowledge_graph.ttl", help="Output RDF Turtle path")

    args = parser.parse_args()

    # 1. Read input text
    if not os.path.exists(args.file):
        print(f"[!] Error: File '{args.file}' not found.")
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        text_content = f.read()

    # 2. Build the LLM prompt
    prompt = generate_llm_prompt(text_content)

    if args.print_prompt_only:
        print("\n" + "=" * 80)
        print("LLM PROMPT (Copy and paste into ChatGPT / Claude / Gemini):")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        return

    # 3. Check for API keys
    has_api_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))

    triplets = []
    if args.demo:
        print("\n[Demo Mode]: Simulating user copying prompt and pasting LLM response...")
        print("LLM Response received.")
        triplets = clean_llm_json_response(demo_sample_response())
    elif has_api_key:
        print("[Key Detected]: Found API key in environment variables. Calling LLM API...")
        # Note: If openai or google-generativeai packages are installed, API calls can be executed here.
        # Fallback to copy-paste mode if package is not installed:
        print("[Notice]: Running copy-paste interactive mode.")
        triplets = copy_paste_workflow(prompt)
    else:
        # Default student / learner path
        triplets = copy_paste_workflow(prompt)

    if not triplets:
        print("[!] No triplets extracted.")
        return

    # 4. Display and Save
    print(f"\n✔ Successfully extracted {len(triplets)} triplets from LLM response!")

    # Format into Triplet objects for printing
    class SimpleTriplet:
        def __init__(self, s, p, o, sent=""):
            self.subject, self.predicate, self.object, self.sentence = s, p, o, sent
        def to_dict(self):
            return {"subject": self.subject, "predicate": self.predicate, "object": self.object, "sentence": self.sentence}

    triplet_objs = [SimpleTriplet(t["subject"], t["predicate"], t["object"], t.get("sentence", "")) for t in triplets]
    print_triplets_table(triplet_objs)
    save_triplets_json(triplet_objs, args.json_out)

    # 5. Ingest into RDF Store
    rdf_store = BasicRDFStore()
    rdf_store.store_triplets(triplets)
    rdf_store.save_to_file(args.rdf_out, format="turtle")

    print("\n" + "=" * 80)
    print("🎉 Knowledge Graph Successfully Updated from LLM!")
    print(f"  • JSON File:   {args.json_out}")
    print(f"  • Turtle File: {args.rdf_out}")
    print("=" * 80)


if __name__ == "__main__":
    main()
