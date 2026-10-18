"""
=============================================================================
VERSION 2: VISUAL KNOWLEDGE GRAPH - MODULE: GRAPH VISUALIZER
=============================================================================
Educational Concept:
-------------------
Visualizing a Knowledge Graph turns abstract mathematical triples into
an intuitive network of nodes (entities) and directed edges (relationships):

1. **Static Graph (NetworkX + Matplotlib)**:
   - Uses a spring-layout force-directed algorithm.
   - Nodes represent entities (Subjects and Objects).
   - Directed edges with arrows represent Predicates.
   - Ideal for research papers, reports, and presentations.

2. **Interactive Graph (Vis.js HTML Network)**:
   - Runs in any standard web browser without needing a backend server.
   - Physics-based simulation: nodes dynamically repel and attract each other.
   - Interactive: drag nodes, zoom with scroll wheel, pan, search entities.
   - Click to inspect: shows details and source sentence context.
=============================================================================
"""

import os
import json
from typing import List, Dict, Any, Union

# Set local writable cache for Matplotlib to avoid sandbox permission errors
os.environ["MPLCONFIGDIR"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".matplotlib_cache"
)

import networkx as nx
import matplotlib.pyplot as plt


class GraphVisualizer:
    """
    Renders Knowledge Graphs as both static PNG images and interactive HTML web pages.
    """

    def __init__(self):
        pass

    def render_static_graph(self, triplets: List[Any], output_image_path: str = "knowledge_graph.png"):
        """
        Builds a directed NetworkX graph and renders a high-resolution static PNG diagram.
        """
        G = nx.DiGraph()

        for t in triplets:
            if hasattr(t, "subject"):
                s, p, o = t.subject, t.predicate, t.object
            else:
                s, p, o = t["subject"], t["predicate"], t["object"]
            G.add_edge(s, o, label=p)

        plt.figure(figsize=(15, 11))
        # Spring layout simulates physical springs between connected nodes
        pos = nx.spring_layout(G, k=2.0, seed=42)

        # 1. Draw Nodes
        nx.draw_networkx_nodes(
            G, pos,
            node_color="#93C5FD",  # Soft blue
            node_size=2800,
            alpha=0.95,
            edgecolors="#1D4ED8",
            linewidths=2
        )

        # 2. Draw Node Text Labels
        nx.draw_networkx_labels(
            G, pos,
            font_size=9,
            font_weight="bold",
            font_family="sans-serif"
        )

        # 3. Draw Directed Edges with Arrows
        nx.draw_networkx_edges(
            G, pos,
            edge_color="#64748B",  # Slate gray
            arrows=True,
            arrowsize=20,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.1",
            width=1.6
        )

        # 4. Draw Predicate Labels on Edges
        edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(
            G, pos,
            edge_labels=edge_labels,
            font_color="#C2410C",  # Burnt orange
            font_size=8,
            font_weight="bold",
            label_pos=0.5
        )

        plt.title(
            "Knowledge Graph Visualization (Subject -> Predicate -> Object)",
            fontsize=16,
            fontweight="bold",
            pad=20
        )
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"[Visualizer] ✔ Static image saved: {output_image_path}")

    def render_interactive_html(self, triplets: List[Any], output_html_path: str = "knowledge_graph.html"):
        """
        Generates a standalone, interactive HTML web application using Vis.js.
        Allows users to drag nodes, zoom, search, and click to view connected facts.
        """
        nodes_set = set()
        edges = []
        raw_triplets = []

        for idx, t in enumerate(triplets):
            if hasattr(t, "subject"):
                s, p, o, sent = t.subject, t.predicate, t.object, getattr(t, "sentence", "")
            else:
                s, p, o, sent = t["subject"], t["predicate"], t["object"], t.get("sentence", "")

            nodes_set.add(s)
            nodes_set.add(o)

            raw_triplets.append({
                "subject": s,
                "predicate": p,
                "object": o,
                "sentence": sent
            })

            edges.append({
                "id": f"e{idx}",
                "from": s,
                "to": o,
                "label": p,
                "title": f"<b>Relation:</b> {p}<br><b>Sentence:</b> <i>{sent}</i>" if sent else p,
                "arrows": "to"
            })

        nodes = [{"id": n, "label": n} for n in sorted(list(nodes_set))]

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Interactive Knowledge Graph Explorer</title>
  <!-- Vis.js Standalone Network Library -->
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
      <h1>Interactive Knowledge Graph Explorer</h1>
      <div class="subtitle">Visual representation of (Subject, Predicate, Object) triplets</div>
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
        <p style="font-size: 0.85rem; line-height: 1.5; margin: 0; color: #475569;">
          • <b>Drag</b> nodes to explore connections.<br>
          • <b>Scroll</b> to zoom in and out.<br>
          • <b>Click</b> any node or edge to inspect details.<br>
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
    const rawTriplets = {json.dumps(raw_triplets)};
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
            <b>Source Sentence:</b><br>
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
        print(f"[Visualizer] ✔ Interactive HTML saved: {output_html_path}")
