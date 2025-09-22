#!/usr/bin/env python3
"""
Network Topology Visualizer

- Loads network devices and connections from a JSON file
- Builds NetworkX graph
- Computes shortest path (Dijkstra)
- Displays static matplotlib visualization (highlight shortest path)
- Generates interactive pyvis HTML visualization
"""

import json
import argparse
import sys
import os
from pathlib import Path

import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network


def load_network(file_path):
    """Load network JSON from file_path."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {file_path}: {e}")
        sys.exit(1)

    if "devices" not in data or "connections" not in data:
        print("Error: JSON must contain 'devices' and 'connections' keys.")
        sys.exit(1)

    return data


def build_graph(data):
    """Build and return an undirected NetworkX graph from data."""
    G = nx.Graph()
    for d in data.get("devices", []):
        G.add_node(d)
    for conn in data.get("connections", []):
        if len(conn) < 2:
            continue
        u, v = conn[0], conn[1]
        w = float(conn[2]) if len(conn) >= 3 else 1.0
        G.add_edge(u, v, weight=w)
    return G


def compute_shortest_path(G, source, target):
    """Return (path_list, total_cost)."""
    if source not in G or target not in G:
        print(f"Error: source or target not in graph")
        return None, None
    try:
        path = nx.dijkstra_path(G, source, target, weight="weight")
        cost = nx.dijkstra_path_length(G, source, target, weight="weight")
        return path, cost
    except nx.NetworkXNoPath:
        print(f"No path found between '{source}' and '{target}'")
        return None, None


def visualize_static(G, path=None, output_file=None):
  
    """Draw static graph with matplotlib."""
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(8, 6))
    nx.draw_networkx_nodes(G, pos, node_size=900, node_color="lightblue")
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold")
    nx.draw_networkx_edges(G, pos, width=1.2)
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    if path and len(path) >= 2:
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, width=3, edge_color="red")

    plt.title("Network Topology")
    plt.axis("off")

    if output_file:
        # Create folder if it doesn't exist
        folder = os.path.dirname(output_file)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        plt.savefig(output_file, bbox_inches="tight", dpi=150)
        print(f"Static graph saved as {output_file}")

    plt.show()



def visualize_interactive(G, output_file="network.html"):
    """Generate interactive HTML graph using pyvis."""
    from pyvis.network import Network

    net = Network(height="700px", width="100%", bgcolor="white", font_color="black")
    net.from_nx(G)

    # Add edge labels for weights
    for e in net.edges:
        src, dst = e["from"], e["to"]
        # Safely get weight (check both directions)
        w = G.edges.get((src, dst), G.edges.get((dst, src), {})).get("weight", "")
        e["title"] = f"weight: {w}"
        e["label"] = str(w)

    net.toggle_physics(True)
    net.show(output_file)
    print(f"Interactive graph saved as {output_file}")


def parse_args():
    p = argparse.ArgumentParser(description="Network Topology Visualizer")
    p.add_argument("--file", "-f", default="network.json", help="Path to network JSON file")
    p.add_argument("--source", "-s", default=None, help="Source node for shortest path")
    p.add_argument("--target", "-t", default=None, help="Target node for shortest path")
    p.add_argument("--save-static", action="store_true", help="Save static graph as PNG")
    p.add_argument("--static-out", default="screenshots/static.png", help="Static PNG filename")
    p.add_argument("--html-out", default="network.html", help="Interactive HTML filename")
    return p.parse_args()


def main():
    args = parse_args()
    data = load_network(args.file)
    G = build_graph(data)
    print(f"Graph loaded: {len(G.nodes())} nodes, {len(G.edges())} edges")

    devices = list(G.nodes())
    src = args.source if args.source else devices[0]
    tgt = args.target if args.target else devices[-1]

    print(f"Computing shortest path from '{src}' to '{tgt}'...")
    path, cost = compute_shortest_path(G, src, tgt)
    if path:
        print(f"Shortest path: {path} (cost={cost})")
    else:
        print("No path to display.")

    # Static visualization
    static_out = args.static_out if args.save_static else None
    visualize_static(G, path=path, output_file=static_out)

    # Interactive visualization
    visualize_interactive(G, output_file=args.html_out)


if __name__ == "__main__":
    main()
