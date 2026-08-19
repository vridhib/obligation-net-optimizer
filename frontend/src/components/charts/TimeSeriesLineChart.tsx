"use client";
import * as d3 from "d3";
import { useEffect, useRef } from "react";


export interface Series {
  name: string;
  color: string;
  data: { label: string; value: number }[];
}

interface TimeSeriesLineChartProps {
  series: Series[];
  height?: number;
}

export function TimeSeriesLineChart({
  series,
  height = 300,
}: TimeSeriesLineChartProps) {
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!ref.current || series.length === 0) return;

    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const width = 800;
    const margin = { top: 20, right: 130, bottom: 50, left: 40 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Flatten labels from all series for x domain (union)
    const allLabels = Array.from(
      new Set(series.flatMap((s) => s.data.map((d) => d.label)))
    ).sort();

    const x = d3
      .scalePoint()
      .domain(allLabels)
      .range([0, innerWidth]);

    const allValues = series.flatMap((s) => s.data.map((d) => d.value));
    const yMin = d3.min(allValues) ?? 0;
    const yMax = d3.max(allValues) ?? 1;

    const y = d3
      .scaleLinear()
      .domain([Math.min(0, yMin), yMax * 1.1])
      .range([innerHeight, 0]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Grid lines
    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x).tickSizeOuter(0))
      .selectAll("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -8)
      .attr("y", 0)
      .attr("dy", ".35em")
      .attr("text-anchor", "end")

    g.append("g")
      .call(d3.axisLeft(y).tickFormat((d) => d3.format("~s")(d as number)));

    // Draw lines for each series
    series.forEach((s) => {
      const line = d3
        .line<{ label: string; value: number }>()
        .x((d) => x(d.label)!)
        .y((d) => y(d.value));

      g.append("path")
        .datum(s.data)
        .attr("fill", "none")
        .attr("stroke", s.color)
        .attr("stroke-width", 2)
        .attr("d", line);

      g.selectAll(`circle.${s.name.replace(/\s+/g, "-")}`)
        .data(s.data)
        .join("circle")
        .attr("class", s.name.replace(/\s+/g, "-"))
        .attr("cx", (d) => x(d.label)!)
        .attr("cy", (d) => y(d.value))
        .attr("r", 3)
        .attr("fill", s.color);
    });

    // Legend
    const legend = svg
      .append("g")
      .attr(
        "transform",
        `translate(${margin.left + innerWidth + 20}, ${margin.top})`
      );

    series.forEach((s, i) => {
      const row = legend.append("g").attr("transform", `translate(0, ${i * 20})`);
      row.append("rect").attr("width", 12).attr("height", 12).attr("fill", s.color);
      row
        .append("text")
        .attr("x", 18)
        .attr("y", 10)
        .text(s.name)
        .attr("class", "text-xs fill-neutral-600");
    });
  }, [series, height]);

  return (
    <svg
      ref={ref}
      viewBox={`0 0 800 ${height}`}
      className="w-full h-auto"
    />
  );
}