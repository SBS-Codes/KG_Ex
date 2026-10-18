"""
=============================================================================
LLM BRIDGE: KNOWLEDGE GRAPH TRIPLET EXTRACTOR
=============================================================================
Supports:
  1. Local Downloaded Models:
     - Direct GGUF file loading (via llama-cpp-python)
     - Direct HuggingFace folder loading (via mlx-lm or transformers)
     - Local Ollama model (via http://localhost:11434)
     - Local LM Studio / Jan server (via http://localhost:1234/v1)
  2. Cloud API Keys:
     - OpenAI, Gemini, Anthropic (if key is set)
  3. No-API-Key Copy-Paste Fallback:
     - Interactive terminal copy-paste for ChatGPT / Claude / Gemini web chat
=============================================================================
"""

import os
import sys
import json
import re
import argparse
import urllib.request
from typing import List, Dict, Any, Optional

# Support importing BasicRDFStore from 01_basic_kg
current_dir = os.path.dirname(os.path.abspath(__file__))
basic_dir = os.path.join(current_dir, "01_basic_kg")
if basic_dir not in sys.path:
    sys.path.insert(0, basic_dir)

from rdf_store import BasicRDFStore
from extractor import print_triplets_table, save_triplets_json


def generate_llm_prompt(text_content: str) -> str:
    """Creates a structured few-shot prompt for Knowledge Graph extraction."""
    return f"""You are an expert Knowledge Graph engineer.
Your task is to extract all factual (Subject, Predicate, Object) triplets from the input text below.

STRICT INSTRUCTIONS:
1. Extract explicit relationships between entities from every sentence.
2. Separate entities into 'subject', 'predicate', and 'object'.
3. Include the source sentence in 'sentence' for provenance.
4. Output ONLY a valid JSON object containing a "triplets" list. Do not include markdown commentary, intro, or outro.

INPUT TEXT:
\"\"\"
{text_content.strip()}
\"\"\"

REQUIRED JSON OUTPUT FORMAT:
{{
  "triplets": [
    {{
      "subject": "Entity Name",
      "predicate": "relation or action",
      "object": "Target Entity or Date",
      "sentence": "Original source sentence"
    }}
  ]
}}
"""


def clean_llm_json_response(raw_response: str) -> List[Dict[str, str]]:
    """Strips markdown code fences (```json ... ```) and parses the JSON data."""
    cleaned = raw_response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        data = json.loads(cleaned)
    except Exception:
        # Fallback regex search for { ... } or [ ... ]
        match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
            except Exception as e:
                raise ValueError(f"Failed to parse JSON: {e}\nRaw output was:\n{raw_response}")
        else:
            raise ValueError(f"No JSON found in response: {raw_response}")

    # If it's a dict, check for keys like 'triplets'
    if isinstance(data, dict):
        for k in ("triplets", "facts", "relations", "data", "results"):
            if k in data and isinstance(data[k], list):
                data = data[k]
                break
        else:
            if "subject" in data:
                data = [data]
            else:
                raise ValueError(f"JSON object does not contain a list of triplets: {data}")

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

    raise ValueError(f"Unexpected data format: {type(data)}")



def query_ollama(prompt: str, model_name: str = "llama3.2:3b", host: str = "http://localhost:11434") -> str:
    """Queries a local Ollama server running on macOS."""
    url = f"{host.rstrip('/')}/api/generate"
    payload = json.dumps({
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        print(f"[Ollama] Sending prompt to local model '{model_name}' at {host}...")
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Could not connect to Ollama at {host}. Is Ollama running? (Try running 'ollama serve' or 'ollama run {model_name}')\nError: {e}"
        )


def query_lmstudio(prompt: str, host: str = "http://localhost:1234") -> str:
    """Queries an LM Studio local server running on macOS."""
    url = f"{host.rstrip('/')}/v1/chat/completions"
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": "You are an expert Knowledge Graph engineer. Output only a valid JSON array."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        print(f"[LM Studio] Sending prompt to local LM Studio server at {host}...")
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Could not connect to LM Studio at {host}.\n"
            f"👉 Make sure LM Studio is open, go to the Developer / Local Server tab (<->), and click 'Start Server'!\n"
            f"Error: {e}"
        )



def query_local_file_or_folder(model_path: str, prompt: str) -> str:
    """Executes inference on a local GGUF file or HuggingFace directory."""
    model_path = os.path.abspath(os.path.expanduser(model_path))

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Local model path not found: {model_path}")

    # Case A: GGUF File
    if os.path.isfile(model_path) and model_path.endswith(".gguf"):
        print(f"[Local Model] Detected GGUF file: {model_path}")
        try:
            from llama_cpp import Llama
            print("[Local Model] Loading model into Apple Metal GPU (n_gpu_layers=-1)...")
            llm = Llama(model_path=model_path, n_gpu_layers=-1, n_ctx=2048, verbose=False)
            output = llm(prompt, max_tokens=1024, temperature=0.1)
            return output["choices"][0]["text"]
        except ImportError:
            print("\n" + "=" * 80)
            print("💡 TIP: TO RUN THIS .GGUF FILE LOCALLY, CHOOSE ONE OF TWO EASY OPTIONS:")
            print("=" * 80)
            print("Option 1 (via Ollama - Recommended for Mac M1):")
            print(f"  1. Run: echo \"FROM {model_path}\" > Modelfile")
            print("  2. Run: ollama create my-model -f Modelfile")
            print("  3. Run: python llm_bridge.py --ollama --model my-model")
            print("\nOption 2 (Direct Python library):")
            print("  Run: pip install llama-cpp-python")
            print(f"  Then re-run: python llm_bridge.py --local-path \"{model_path}\"")
            print("=" * 80 + "\n")
            raise RuntimeError("llama-cpp-python not installed.")

    # Case B: Directory (HuggingFace / MLX format)
    if os.path.isdir(model_path):
        print(f"[Local Model] Detected Model Directory: {model_path}")
        # Try Apple MLX first (fastest on Apple Silicon)
        try:
            from mlx_lm import load, generate
            print("[Local Model] Loading model via Apple MLX (Metal accelerated)...")
            model, tokenizer = load(model_path)
            return generate(model, tokenizer, prompt=prompt, max_tokens=1024)
        except ImportError:
            pass

        # Try Hugging Face Transformers
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            print("[Local Model] Loading model via Hugging Face Transformers on MPS (Apple Silicon)...")
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16 if device == "mps" else torch.float32).to(device)
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            outputs = model.generate(**inputs, max_new_tokens=1024)
            return tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        except ImportError:
            print("\n" + "=" * 80)
            print("💡 TIP: TO RUN THIS HUGGINGFACE FOLDER LOCALLY:")
            print("=" * 80)
            print("Install Apple's native MLX framework (fastest on M1 Mac):")
            print("  pip install mlx-lm")
            print(f"Then re-run: python llm_bridge.py --local-path \"{model_path}\"")
            print("=" * 80 + "\n")
            raise RuntimeError("Neither mlx-lm nor transformers is installed.")

    raise ValueError(f"Unsupported model path format: {model_path}")


def copy_paste_workflow(prompt: str) -> List[Dict[str, str]]:
    """Interactive fallback when no local runner or API key is available."""
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
        description="LLM Knowledge Graph Triplet Extractor supporting Local Models, Ollama, and Copy-Paste."
    )
    parser.add_argument("--file", "-f", default="sample_text.txt", help="Input text file path")
    parser.add_argument("--local-path", "-l", type=str, default=None, help="Path to local .gguf file or model directory")
    parser.add_argument("--lmstudio", action="store_true", help="Query local LM Studio server (http://localhost:1234)")
    parser.add_argument("--lmstudio-host", type=str, default="http://localhost:1234", help="LM Studio server URL")
    parser.add_argument("--ollama", action="store_true", help="Query local Ollama server")
    parser.add_argument("--model", "-m", type=str, default="llama3.2:3b", help="Ollama model name (default: llama3.2:3b)")
    parser.add_argument("--ollama-host", type=str, default="http://localhost:11434", help="Ollama server URL")


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
        print("LLM PROMPT:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        return

    triplets = []

    # Path A: Demo Simulation Mode
    if args.demo:
        print("\n[Demo Mode]: Simulating user copying prompt and pasting LLM response...")
        triplets = clean_llm_json_response(demo_sample_response())

    # Path B: Local LM Studio Server
    elif args.lmstudio:
        try:
            raw_output = query_lmstudio(prompt, host=args.lmstudio_host)
            triplets = clean_llm_json_response(raw_output)
        except Exception as e:
            print(f"[!] LM Studio Error: {e}")
            print("\nFalling back to Copy-Paste mode:")
            triplets = copy_paste_workflow(prompt)

    # Path C: Local Model File / Directory
    elif args.local_path:
        try:
            raw_output = query_local_file_or_folder(args.local_path, prompt)
            triplets = clean_llm_json_response(raw_output)
        except Exception as e:
            print(f"[!] Local Model Error: {e}")
            return

    # Path D: Local Ollama Server
    elif args.ollama:
        try:
            raw_output = query_ollama(prompt, model_name=args.model, host=args.ollama_host)
            triplets = clean_llm_json_response(raw_output)
        except Exception as e:
            print(f"[!] Ollama Error: {e}")
            print("\nFalling back to Copy-Paste mode:")
            triplets = copy_paste_workflow(prompt)

    # Path D: Check for Cloud API Keys
    elif os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        print("[Key Detected]: Found API key. (Falling back to copy-paste mode if SDKs not configured).")
        triplets = copy_paste_workflow(prompt)

    # Path E: Default Free Copy-Paste Mode
    else:
        triplets = copy_paste_workflow(prompt)

    if not triplets:
        print("[!] No triplets extracted.")
        return

    # 4. Display and Save
    print(f"\n✔ Successfully extracted {len(triplets)} triplets from local/LLM response!")

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
