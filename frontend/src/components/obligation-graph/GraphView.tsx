"use client";
import cytoscape from "cytoscape";
import { useEffect, useRef } from "react";
import type { GraphData } from "@/lib/types";


interface GraphViewProps {
  data: GraphData;
}

function buildCytoscapeElements(data: GraphData) {
  const nodes = data.nodes.map((node) => ({
    data: {
      id: node.id,
      label: node.label,
      net_amount: Number(node.net_amount)
    }
  }));

  const edges = data.edges.map((edge) => ({
    data: {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      amount: Number(edge.amount)
    }
  }));

  return { nodes, edges };
}

export function GraphView({ data }: GraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const { nodes, edges } = buildCytoscapeElements(data);

    const cy = cytoscape({
      container: containerRef.current,
      elements: { nodes, edges },
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "background-color": "#6366f1",
            color: "#fff",
            "text-valign": "center",
            "text-halign": "center",
            width: 60,
            height: 60,
            "font-size": 10,
            "text-wrap": "wrap",
            "text-max-width": "80"
          }
        },
        {
          selector: "edge",
          style: {
            width: "mapData(amount, 0, 100000, 1, 8)",
            "line-color": "#94a3b8",
            "target-arrow-color": "#94a3b8",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(amount)",
            "font-size": 9,
            color: "#cbd5e1",
            "text-background-color": "#0f172a",
            "text-background-opacity": 0.8,
            "text-background-padding": "2",
          }
        }
      ],
      layout: {
        name: "cose",
        animate: false,
        padding: 30,
        nodeRepulsion: 4000
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [data]);

  return (
    <div
      ref={containerRef}
      className="h-[600px] w-full rounded-xl border border-slate-800 bg-slate-900"
    />
  );
}