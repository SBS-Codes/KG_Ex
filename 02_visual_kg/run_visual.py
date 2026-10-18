"""
=============================================================================
VERSION 2: VISUAL KNOWLEDGE GRAPH - MASTER RUNNER
=============================================================================
This script runs the visual extension of the Knowledge Graph project:

  Phase 1: Ingests extracted triplets
  Phase 2: Generates static high-resolution network diagram (.png)
  Phase 3: Generates standalone interactive web application (.html)
=============================================================================
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
basic_kg_dir = os.path.join(parent_dir, "01_basic_kg")

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if basic_kg_dir not in sys.path:
    sys.path.insert(0, basic_kg_dir)

from extractor import BasicTripletExtractor
from visualizer import GraphVisualizer


def main():
    print("=" * 80)
    print("🎨 VERSION 2: VISUAL KNOWLEDGE GRAPH RUNNER")
    print("=" * 80)

    # Locate input text
    sample_path = os.path.join(parent_dir, "sample_text.txt")
    if not os.path.exists(sample_path):
        sample_path = "sample_text.txt"

    output_png = os.path.join(parent_dir, "knowledge_graph.png")
    output_html = os.path.join(parent_dir, "knowledge_graph.html")

    print(f"\n[Step 1] Extracting Triplets from '{sample_path}'...")
    extractor = BasicTripletExtractor()
    triplets = extractor.extract_from_file(sample_path)
    print(f"Extracted {len(triplets)} triplets.")

    print("\n[Step 2] Rendering Visual Knowledge Graphs...")
    visualizer = GraphVisualizer()

    # 1. Static Image
    visualizer.render_static_graph(triplets, output_png)

    # 2. Interactive Web Application
    visualizer.render_interactive_html(triplets, output_html)

    print("\n" + "=" * 80)
    print("✨ Visualization Complete!")
    print("=" * 80)
    print(f"1. Static Diagram:    {output_png}")
    print(f"2. Interactive HTML:  {output_html}")
    print("\nTo view the interactive graph in your web browser:")
    print(f"  macOS:  open {output_html}")
    print(f"  Linux:  xdg-open {output_html}")
    print(f"  Windows: start {output_html}")
    print("=" * 80)


if __name__ == "__main__":
    main()
