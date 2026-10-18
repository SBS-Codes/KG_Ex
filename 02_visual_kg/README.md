# 🎨 Version 2: Visual Knowledge Graph (Static & Interactive Visualizations)

Welcome to **Version 2** of the Knowledge Graph Explainer project!

While **Version 1** covers the data structures and RDF query engine, **Version 2** brings the Knowledge Graph to life visually. Seeing entities connected by directed arrows makes understanding complex relationships effortless.

---

## 🎯 What You Will Learn in Version 2

1. **Graph Theory Basics**: How entities become **nodes** (vertices) and relationships become **directed edges**.
2. **Force-Directed Graph Algorithms**:
   - How algorithms like **Spring Layout** (Fruchterman-Reingold) position nodes so that connected entities stay close while unconnected entities push apart.
3. **Static Visualization**: Using **NetworkX** and **Matplotlib** to render high-resolution PNG network charts.
4. **Interactive Web Visualization**: Using **Vis.js** to build an interactive browser-based network where you can drag nodes, zoom, search, and click to inspect details.

---

## 📂 Files in this Version

| File | Purpose |
| :--- | :--- |
| [`visualizer.py`](file:///Users/shashibetadur/Desktop/Agent_007/KG_Ex/02_visual_kg/visualizer.py) | Contains the `GraphVisualizer` class that generates both the static PNG and the interactive HTML file. |
| [`run_visual.py`](file:///Users/shashibetadur/Desktop/Agent_007/KG_Ex/02_visual_kg/run_visual.py) | Master runner that parses the text and generates both visualizations. |

---

## 🚀 How to Run Version 2

### 1. Generate All Visualizations
```bash
python 02_visual_kg/run_visual.py
```

### 2. View the Interactive Knowledge Graph in Your Browser
- **macOS**:
  ```bash
  open knowledge_graph.html
  ```
- **Linux**:
  ```bash
  xdg-open knowledge_graph.html
  ```
- **Windows**:
  ```cmd
  start knowledge_graph.html
  ```

---

## 🕹️ How to Interact with the Web Graph
- **Drag**: Click and drag any node to move it around and observe the physics simulation.
- **Zoom / Pan**: Scroll your mouse wheel or touchpad to zoom in and out.
- **Click to Inspect**: Click on any entity node or relation arrow to see its connected facts and source sentence.
- **Search**: Use the top-right search box to quickly focus on any specific entity (e.g. `Marie Curie` or `Apple`).
