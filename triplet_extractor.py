"""
Knowledge Graph Triplet Extractor
---------------------------------
Extracts (Subject, Predicate, Object) triplets from raw text using spaCy dependency parsing,
outputs structured tabular & JSON results, and generates both static & interactive visualizations.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional

# Set a local writable directory for Matplotlib cache to avoid sandbox/permission warnings
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".matplotlib_cache")

import spacy
from spacy.tokens import Doc, Span, Token
import networkx as nx
import matplotlib.pyplot as plt


class Triplet:
    def __init__(self, subject: str, predicate: str, object_: str, sentence: str = ""):
        # Strip extraneous whitespace and normalize
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

    def __eq__(self, other) -> bool:
        if not isinstance(other, Triplet):
            return False
        return (
            self.subject.lower() == other.subject.lower()
            and self.predicate.lower() == other.predicate.lower()
            and self.object.lower() == other.object.lower()
        )

    def __hash__(self) -> int:
        return hash((self.subject.lower(), self.predicate.lower(), self.object.lower()))


class TripletExtractor:
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize spaCy NLP model."""
        print(f"Loading spaCy NLP model: {model_name}...")
        self.nlp = spacy.load(model_name)

    def _preprocess_doc(self, doc: Doc) -> Doc:
        """
        Merge hyphenated compound tokens (e.g., 'co-founded' -> 'co-founded')
        so verbs and compound adjectives stay intact in the dependency parse tree.
        """
        with doc.retokenize() as retokenizer:
            for i in range(len(doc) - 2):
                if doc[i + 1].text == "-" and doc[i].whitespace_ == "" and doc[i + 1].whitespace_ == "":
                    retokenizer.merge(doc[i : i + 3])
        return doc

    def _get_full_noun_phrase(self, token: Token, doc: Doc) -> str:
        """
        Finds the complete noun phrase for a given token using noun chunks
        and attaches prepositional qualifiers like 'of' or 'in'
        (e.g., 'the theory of general relativity', 'the Nobel Prize in Physics').
        """
        base_phrase = token.text
        root_token = token

        # Check if the token belongs to any detected noun chunk
        for chunk in doc.noun_chunks:
            if token in chunk:
                base_phrase = chunk.text
                root_token = chunk.root
                break

        # Check for trailing qualifying prepositional phrases (e.g. 'of general relativity', 'in Physics')
        for right in root_token.rights:
            if right.dep_ == "prep" and right.text.lower() in ("of", "in"):
                for pchild in right.children:
                    if pchild.dep_ == "pobj":
                        for subchunk in doc.noun_chunks:
                            if pchild in subchunk:
                                return f"{base_phrase} {right.text} {subchunk.text}"
                        return f"{base_phrase} {right.text} {pchild.text}"

        return base_phrase

    def _get_verb_predicate(self, verb_token: Token) -> str:
        """
        Builds the verb phrase by collecting auxiliaries (e.g., 'was created', 'has developed', 'did not see').
        """
        pred_tokens = []

        # Collect preceding auxiliaries, negations, and particles
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
        """
        Extracts (Subject, Predicate, Object) triplets from a single sentence.
        Handles:
          - Active voice (Subject -> Verb -> Direct Object)
          - Passive voice (Object -> was Verb by -> Agent)
          - Conjoined subjects & objects (e.g. 'radium and polonium')
          - Prepositional relations (e.g. 'co-founded with', 'designed in')
        """
        triplets: List[Triplet] = []
        sent_text = sent_doc.text.strip()

        for token in sent_doc:
            if token.pos_ not in ("VERB", "AUX"):
                continue

            # Identify if this verb is passive (has an 'auxpass' left child)
            is_passive = any(t.dep_ == "auxpass" for t in token.lefts)
            base_predicate = self._get_verb_predicate(token)

            # 1. Collect Subjects
            subjects: List[str] = []
            for child in token.children:
                if child.dep_ in ("nsubj", "nsubjpass"):
                    subjects.append(self._get_full_noun_phrase(child, full_doc))
                    # Handle conjoined subjects ("Marie and Pierre...")
                    for conj in child.conjuncts:
                        subjects.append(self._get_full_noun_phrase(conj, full_doc))

            # 2. Collect Direct Objects & Complements
            direct_objects: List[str] = []
            for child in token.children:
                if child.dep_ in ("dobj", "attr", "acomp"):
                    direct_objects.append(self._get_full_noun_phrase(child, full_doc))
                    # Handle conjoined objects ("radium and polonium")
                    for conj in child.conjuncts:
                        direct_objects.append(self._get_full_noun_phrase(conj, full_doc))

            # 3. Collect Prepositional Objects & Agents (e.g., 'by Guido van Rossum', 'with Steve Wozniak', 'in 1991')
            prep_relations: List[Dict[str, str]] = []
            for child in token.children:
                if child.dep_ in ("prep", "agent"):
                    prep_word = child.text
                    for pchild in child.children:
                        if pchild.dep_ in ("pobj", "dobj"):
                            pobj_phrase = self._get_full_noun_phrase(pchild, full_doc)
                            prep_relations.append({
                                "prep": prep_word,
                                "pobj": pobj_phrase,
                                "is_agent": (child.dep_ == "agent" or prep_word.lower() == "by")
                            })
                            for conj in pchild.conjuncts:
                                prep_relations.append({
                                    "prep": prep_word,
                                    "pobj": self._get_full_noun_phrase(conj, full_doc),
                                    "is_agent": (child.dep_ == "agent" or prep_word.lower() == "by")
                                })

            # Combine into Triplets

            # Case A: Standard Subject + Predicate + Direct Object
            for subj in subjects:
                for obj in direct_objects:
                    if subj.lower() != obj.lower():
                        triplets.append(Triplet(subj, base_predicate, obj, sent_text))

            # Case B: Passive voice with agent (e.g. 'Python was created by Guido van Rossum')
            for prep_info in prep_relations:
                if is_passive and prep_info["is_agent"]:
                    # Can be represented as (Python -> was created by -> Guido van Rossum)
                    for subj in subjects:
                        triplets.append(
                            Triplet(subj, f"{base_predicate} {prep_info['prep']}", prep_info["pobj"], sent_text)
                        )
                elif prep_info["prep"].lower() in ("with", "in", "for", "at", "on"):
                    # Prepositional relationships like:
                    # (Steve Jobs -> co-founded with -> Steve Wozniak)
                    # (Alan Turing -> designed in -> 1945)
                    # (Apple -> released in -> 2007)
                    for subj in subjects:
                        rel_pred = f"{base_predicate} {prep_info['prep']}"
                        triplets.append(Triplet(subj, rel_pred, prep_info["pobj"], sent_text))

        return triplets

    def extract_from_text(self, text: str) -> List[Triplet]:
        """Processes entire text and extracts unique triplets."""
        doc = self.nlp(text)
        doc = self._preprocess_doc(doc)

        all_triplets: List[Triplet] = []
        for sent in doc.sents:
            sent_triplets = self.extract_from_sentence(sent, doc)
            all_triplets.extend(sent_triplets)

        # Deduplicate while preserving original order
        unique_triplets: List[Triplet] = []
        seen = set()
        for t in all_triplets:
            key = (t.subject.lower(), t.predicate.lower(), t.object.lower())
            if key not in seen:
                seen.add(key)
                unique_triplets.append(t)

        return unique_triplets

    def extract_from_file(self, file_path: str) -> List[Triplet]:
        """Reads text from a file and extracts triplets."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return self.extract_from_text(text)


def display_triplets_table(triplets: List[Triplet]):
    """Prints a clean, formatted table of triplets to stdout."""
    print("\n" + "=" * 94)
    print(f"{'#':<4} | {'SUBJECT':<26} | {'PREDICATE':<24} | {'OBJECT':<32}")
    print("=" * 94)
    for idx, t in enumerate(triplets, 1):
        subj = (t.subject[:23] + "...") if len(t.subject) > 26 else t.subject
        pred = (t.predicate[:21] + "...") if len(t.predicate) > 24 else t.predicate
        obj = (t.object[:29] + "...") if len(t.object) > 32 else t.object
        print(f"{idx:<4} | {subj:<26} | {pred:<24} | {obj:<32}")
    print("=" * 94 + "\n")


def export_triplets_json(triplets: List[Triplet], output_path: str):
    """Saves triplets to JSON."""
    data = [t.to_dict() for t in triplets]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✔ Saved {len(triplets)} triplets to JSON: {output_path}")


def visualize_static_graph(triplets: List[Triplet], output_image_path: str = "knowledge_graph.png"):
    """Generates a static Knowledge Graph visualization using NetworkX and Matplotlib."""
    G = nx.DiGraph()

    for t in triplets:
        G.add_edge(t.subject, t.object, label=t.predicate)

    plt.figure(figsize=(15, 11))
    pos = nx.spring_layout(G, k=2.0, seed=42)

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos,
        node_color="#93C5FD",
        node_size=2800,
        alpha=0.95,
        edgecolors="#1D4ED8",
        linewidths=2
    )

    # Draw node labels
    nx.draw_networkx_labels(
        G, pos,
        font_size=9,
        font_weight="bold",
        font_family="sans-serif"
    )

    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        edge_color="#64748B",
        arrows=True,
        arrowsize=20,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.1",
        width=1.6
    )

    # Draw edge labels (predicates)
    edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        font_color="#C2410C",
        font_size=8,
        font_weight="bold",
        label_pos=0.5
    )

    plt.title("Extracted Knowledge Graph (Subject -> Predicate -> Object)", fontsize=16, fontweight="bold", pad=20)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✔ Saved static graph visualization: {output_image_path}")


def generate_interactive_html(triplets: List[Triplet], output_html_path: str = "knowledge_graph.html"):
    """
    Generates a standalone, interactive HTML visualization with Vis.js network.
    Users can drag nodes, zoom, pan, search entities, and click on nodes/edges to inspect them.
    """
    nodes_set = set()
    edges = []

    for idx, t in enumerate(triplets):
        nodes_set.add(t.subject)
        nodes_set.add(t.object)
        edges.append({
            "id": f"e{idx}",
            "from": t.subject,
            "to": t.object,
            "label": t.predicate,
            "title": f"<b>Relation:</b> {t.predicate}<br><b>Context:</b> <i>{t.sentence}</i>",
            "arrows": "to"
        })

    nodes = [{"id": n, "label": n} for n in sorted(list(nodes_set))]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Interactive Knowledge Graph - Triplet Visualization</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background-color: #f8fafc;
      color: #0f172a;
      overflow: hidden;
    }}
    header {{
      background: #0f172a;
      color: #f8fafc;
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
      height: 64px;
    }}
    h1 {{
      margin: 0;
      font-size: 1.2rem;
      font-weight: 600;
    }}
    .subtitle {{
      color: #94a3b8;
      font-size: 0.8rem;
    }}
    .controls {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .badge {{
      background: #3b82f6;
      color: white;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 600;
    }}
    .badge-green {{
      background: #10b981;
    }}
    #search-input {{
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid #334155;
      background: #1e293b;
      color: white;
      font-size: 0.85rem;
      outline: none;
    }}
    #search-input::placeholder {{
      color: #64748b;
    }}
    #main-container {{
      display: flex;
      height: calc(100vh - 64px);
    }}
    #network-container {{
      flex: 1;
      height: 100%;
      background: #ffffff;
    }}
    #sidebar {{
      width: 320px;
      background: #f1f5f9;
      border-left: 1px solid #e2e8f0;
      padding: 18px;
      overflow-y: auto;
    }}
    .card {{
      background: white;
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 14px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      border: 1px solid #e2e8f0;
    }}
    .card-title {{
      font-size: 0.85rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #64748b;
      margin-bottom: 8px;
    }}
    .triplet-item {{
      font-size: 0.85rem;
      padding: 8px 0;
      border-bottom: 1px dashed #e2e8f0;
    }}
    .triplet-item:last-child {{
      border-bottom: none;
    }}
    .tag-subj {{ color: #2563eb; font-weight: 600; }}
    .tag-pred {{ color: #d97706; font-style: italic; }}
    .tag-obj {{ color: #059669; font-weight: 600; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Knowledge Graph Triplet Explorer</h1>
      <div class="subtitle">Interactive Subject-Predicate-Object network visualization</div>
    </div>
    <div class="controls">
      <input type="text" id="search-input" placeholder="Search entity..." oninput="handleSearch(this.value)">
      <span class="badge">{len(triplets)} Triplets</span>
      <span class="badge badge-green">{len(nodes)} Entities</span>
    </div>
  </header>
  
  <div id="main-container">
    <div id="network-container"></div>
    <div id="sidebar">
      <div class="card">
        <div class="card-title">How to Interact</div>
        <p style="font-size: 0.85rem; line-height: 1.4; margin: 0; color: #475569;">
          • <b>Drag</b> nodes to explore connections.<br>
          • <b>Scroll</b> to zoom in and out.<br>
          • <b>Click</b> any node or edge to inspect context.<br>
          • <b>Search</b> in the top bar to focus an entity.
        </p>
      </div>
      <div class="card">
        <div class="card-title">Selected Details</div>
        <div id="details-view" style="font-size: 0.85rem; color: #64748b;">
          Click on a node or edge to see extracted context.
        </div>
      </div>
    </div>
  </div>

  <script type="text/javascript">
    const rawTriplets = {json.dumps([t.to_dict() for t in triplets])};
    const nodes = new vis.DataSet({json.dumps(nodes)});
    const edges = new vis.DataSet({json.dumps(edges)});

    const container = document.getElementById('network-container');
    const data = {{ nodes: nodes, edges: edges }};
    const options = {{
      nodes: {{
        shape: 'box',
        margin: 10,
        font: {{ size: 14, color: '#0f172a', face: 'system-ui' }},
        color: {{
          border: '#3b82f6',
          background: '#eff6ff',
          highlight: {{ border: '#1d4ed8', background: '#dbeafe' }}
        }},
        shadow: {{ enabled: true, color: 'rgba(0,0,0,0.06)', size: 6, x: 2, y: 3 }}
      }},
      edges: {{
        font: {{ size: 12, color: '#c2410c', strokeWidth: 3, strokeColor: '#ffffff', align: 'top' }},
        color: {{ color: '#94a3b8', highlight: '#2563eb' }},
        arrows: {{ to: {{ enabled: true, scaleFactor: 0.85 }} }},
        smooth: {{ type: 'cubicBezier', forceDirection: 'none', roundness: 0.18 }}
      }},
      physics: {{
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {{
          gravitationalConstant: -80,
          centralGravity: 0.015,
          springLength: 150,
          springConstant: 0.08,
          damping: 0.4
        }},
        stabilization: {{ iterations: 200 }}
      }},
      interaction: {{ hover: true, tooltipDelay: 100 }}
    }};

    const network = new vis.Network(container, data, options);

    // Click handler for details view
    network.on('click', function(params) {{
      const detailsView = document.getElementById('details-view');
      if (params.nodes.length > 0) {{
        const nodeId = params.nodes[0];
        const related = rawTriplets.filter(t => t.subject === nodeId || t.object === nodeId);
        let html = `<b>Entity:</b> <span class="tag-subj">${{nodeId}}</span><br><br><b>Connected Triplets:</b><br>`;
        related.forEach(t => {{
          html += `<div class="triplet-item">
            <span class="tag-subj">${{t.subject}}</span> 
            <span class="tag-pred">--[${{t.predicate}}]--></span> 
            <span class="tag-obj">${{t.object}}</span>
          </div>`;
        }});
        detailsView.innerHTML = html;
      }} else if (params.edges.length > 0) {{
        const edgeId = params.edges[0];
        const edgeObj = edges.get(edgeId);
        const match = rawTriplets.find(t => t.subject === edgeObj.from && t.object === edgeObj.to && t.predicate === edgeObj.label);
        if (match) {{
          detailsView.innerHTML = `
            <b>Triplet:</b><br>
            <span class="tag-subj">${{match.subject}}</span> 
            <span class="tag-pred">--[${{match.predicate}}]--></span> 
            <span class="tag-obj">${{match.object}}</span><br><br>
            <b>Original Sentence:</b><br>
            <i>"${{match.sentence}}"</i>
          `;
        }}
      }}
    }});

    function handleSearch(term) {{
      if (!term.trim()) return;
      const found = nodes.get({{
        filter: function(item) {{
          return item.label.toLowerCase().includes(term.toLowerCase());
        }}
      }});
      if (found.length > 0) {{
        network.focus(found[0].id, {{ scale: 1.2, animation: true }});
      }}
    }}
  </script>
</body>
</html>
"""
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✔ Saved interactive HTML visualization: {output_html_path}")


from rdf_manager import RDFGraphManager


def main():
    parser = argparse.ArgumentParser(description="Extract (Subject, Predicate, Object) triplets from a text file.")
    parser.add_argument(
        "--file", "-f",
        default="sample_text.txt",
        help="Path to the text file to analyze (default: sample_text.txt)"
    )
    parser.add_argument(
        "--json-out", "-j",
        default="triplets.json",
        help="Output path for JSON export (default: triplets.json)"
    )
    parser.add_argument(
        "--rdf-out", "-r",
        default="knowledge_graph.ttl",
        help="Output path for RDF Turtle export (default: knowledge_graph.ttl)"
    )
    parser.add_argument(
        "--img-out", "-i",
        default="knowledge_graph.png",
        help="Output path for static image visualization (default: knowledge_graph.png)"
    )
    parser.add_argument(
        "--html-out",
        default="knowledge_graph.html",
        help="Output path for interactive HTML visualization (default: knowledge_graph.html)"
    )

    args = parser.parse_args()

    # Step 1: Read and extract
    extractor = TripletExtractor()
    print(f"Reading file: {args.file}...")
    triplets = extractor.extract_from_file(args.file)

    # Step 2: Tabular Display
    display_triplets_table(triplets)

    # Step 3: Export to JSON
    export_triplets_json(triplets, args.json_out)

    # Step 4: Export to RDF Graph (RDFLib Turtle)
    rdf_mgr = RDFGraphManager()
    rdf_mgr.store_triplets(triplets)
    rdf_mgr.save_to_file(args.rdf_out, format="turtle")

    # Step 5: Static PNG graph visualization
    visualize_static_graph(triplets, args.img_out)

    # Step 6: Interactive HTML graph visualization
    generate_interactive_html(triplets, args.html_out)

    print("\nExtraction, RDFLib Storage & Visualization pipeline completed successfully!")


if __name__ == "__main__":
    main()

