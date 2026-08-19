"use client";
import * as d3 from "d3";
import { useEffect, useRef } from "react";


interface BarDatum {
  label: string;
  value: number;
  color: string;
}

export function HorizontalBarChart({ data }: { data: BarDatum[] }) {
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!ref.current || data.length === 0) return;

    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const width = 800;
    const height = Math.max(300, data.length * 35);
    const margin = { top: 20, right: 50, bottom: 20, left: 100 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const x = d3
      .scaleLinear()
      .domain([
        d3.min(data, (d) => Math.min(0, d.value)) ?? 0,
        d3.max(data, (d) => Math.max(0, d.value)) ?? 1,
      ])
      .range([0, innerWidth]);

    const y = d3
      .scaleBand()
      .domain(data.map((d) => d.label))
      .range([0, innerHeight])
      .padding(0.2);

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    g.append("g")
      .call(d3.axisLeft(y).tickSize(0))
      .selectAll("text")
      .attr("class", "text-xs fill-neutral-600");

    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x).tickFormat((d) => d3.format("~s")(d as number)));

    g.selectAll("rect")
      .data(data)
      .join("rect")
      .attr("y", (d) => y(d.label)!)
      .attr("x", (d) => x(Math.min(0, d.value)))
      .attr("width", (d) => Math.abs(x(d.value) - x(0)))
      .attr("height", y.bandwidth())
      .attr("fill", (d) => d.color);
  }, [data]);

  return (
    <svg
      ref={ref}
      viewBox={`0 0 800 ${Math.max(300, data.length * 35)}`}
      className="w-full h-auto"
    />
  );
}