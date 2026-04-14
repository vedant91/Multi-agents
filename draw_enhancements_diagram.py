#!/usr/bin/env python3
"""Generate SENTINEL future enhancements diagram."""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import os

OUTPUT_FILE = "enhancements_diagram.png"

# Colors
NODE_COLOR = "#1a1f2e"
ENHANCEMENT_COLOR = "#2d2000"
BG_COLOR = "#0a0f1e"
BORDER_COLOR = "#ffaa00"
TEXT_COLOR = "white"

def create_rounded_node(ax, x, y, width, height, label, color):
    """Draw a rounded rectangle node."""
    radius = 0.03
    rect = patches.FancyBboxPatch(
        (x, y), width, height,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        linewidth=1.5,
        edgecolor=BORDER_COLOR,
        facecolor=color,
    )
    ax.add_patch(rect)
    ax.text(x + width/2, y + height/2, label,
            fontsize=9, color=TEXT_COLOR, ha='center', va='center', weight='bold')

# Build graph manually (no complex networkx edges)
core_nodes = [
    ("Document Parser", 0.15, 0.75),
    ("Research Agent", 0.15, 0.6),
    ("Fraud Detector", 0.15, 0.45),
    ("Bull Agent", 0.15, 0.3),
    ("Bear Agent", 0.15, 0.18),
    ("Chairman Agent", 0.35, 0.4),
    ("Stress Test", 0.35, 0.55),
    ("CAM Generator", 0.35, 0.7),
    ("Decision Output", 0.55, 0.4)
]

enhancements = [
    ("Dynamic Coordination", 0.7, 0.8),
    ("Hierarchical Memory", 0.7, 0.65),
    ("Edge Case Framework", 0.7, 0.5),
    ("NLP Parsing", 0.85, 0.8),
    ("ML Fraud Detection", 0.85, 0.65),
    ("Predictive Stress", 0.85, 0.5),
    ("Interactive Dashboard", 0.7, 0.35),
    ("Customizable CAM", 0.85, 0.35),
    ("Mobile Optimized", 0.7, 0.2),
    ("Containerized", 0.85, 0.2),
    ("Real-Time Monitor", 0.55, 0.8),
    ("Swarm Intelligence", 0.55, 0.2)
]

# Create graph
G = nx.DiGraph()
all_nodes = core_nodes + enhancements

# Add all nodes
for name, x, y in all_nodes:
    G.add_node(name, pos=(x, y), is_core=name in [n[0] for n in core_nodes])

# Add flow connections between core nodes (simple arrows)
core_to_core = [
    ("Document Parser", "Research Agent"),
    ("Research Agent", "Fraud Detector"),
    ("Fraud Detector", "Bull Agent"),
    ("Fraud Detector", "Bear Agent"),
    ("Bull Agent", "Chairman Agent"),
    ("Bear Agent", "Chairman Agent"),
    ("Chairman Agent", "Stress Test"),
    ("Stress Test", "CAM Generator"),
    ("CAM Generator", "Decision Output")
]
for src, dst in core_to_core:
    G.add_edge(src, dst)

# Add enhancement connections (dotted lines from core to enhancements)
core_nodes_dict = {name: pos for name, _, _ in core_nodes}
enhance_connections = [
    ("Document Parser", "Dynamic Coordination"),
    ("Research Agent", "Hierarchical Memory"),
    ("Fraud Detector", "Edge Case Framework"),
    ("Fraud Detector", "ML Fraud Detection"),
    ("Chairman Agent", "Predictive Stress"),
    ("CAM Generator", "Customizable CAM"),
    ("CAM Generator", "Interactive Dashboard"),
    ("Stress Test", "Swarm Intelligence"),
    ("Stress Test", "Real-Time Monitor")
]
for src, dst in enhance_connections:
    G.add_edge(src, dst)

# Plot
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_facecolor(BG_COLOR)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# Draw nodes
for node in G.nodes:
    x, y = G.nodes[node]["pos"]
    width = 0.12 if G.nodes[node]["is_core"] else 0.15
    height = 0.06 if G.nodes[node]["is_core"] else 0.07
    color = NODE_COLOR if G.nodes[node]["is_core"] else ENHANCEMENT_COLOR
    create_rounded_node(ax, x, y, width, height, node, color)

# Draw flow arrows (core-to-core)
for src, dst in core_to_core:
    x1, y1 = G.nodes[src]["pos"]
    x2, y2 = G.nodes[dst]["pos"]
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=BORDER_COLOR, lw=1))

# Draw enhancement arrows (dotted)
for src, dst in enhance_connections:
    x1, y1 = G.nodes[src]["pos"]
    x2, y2 = G.nodes[dst]["pos"]
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="dash", color='#ff6666', lw=0.8))

# Title
ax.text(0.5, 0.92, "SENTINEL — Future Enhancements",
        fontsize=14, color="white", ha='center', weight='bold')

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='s', color='w',
          markerfacecolor=NODE_COLOR, markersize=10, label='Current Architecture'),
    Line2D([0], [0], marker='s', color='w',
          markerfacecolor=ENHANCEMENT_COLOR, markersize=10, label='Future Enhancements'),
    Line2D([0], [0], color=BORDER_COLOR, lw=1, label='Data Flow'),
    Line2D([0], [0], color='#ff6666', lw=0.8,
          linestyle='--', label='Enhancement Links')
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9)

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300, facecolor=BG_COLOR, bbox_inches='tight')
print(f"\n✅ SUCCESS! Diagram saved to: {os.path.abspath(OUTPUT_FILE)}\n")