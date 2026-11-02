import {
    useLayoutEffect,
    useRef,
    useState,
} from "react";
import type { GraphResponse, GraphNode } from "../types/api";

interface NetworkGraphProps {
    graph: GraphResponse;
}

const columnTypes = [
    { type: "supplier", label: "Suppliers" },
    { type: "route", label: "Routes" },
    { type: "port", label: "Ports" },
    { type: "refinery", label: "Refineries" },
];

interface Point {
    x: number;
    y: number;
}

interface GraphLine {
    sourceId: string;
    targetId: string;
    source: Point;
    target: Point;
}

function NetworkGraph({ graph }: NetworkGraphProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const nodeRefs = useRef<Record<string, HTMLDivElement | null>>({});
    const [lines, setLines] = useState<GraphLine[]>([]);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

    useLayoutEffect(() => {
        function updateLines() {
            const container = containerRef.current;

            if (!container) {
                return;
            }

            const containerRect = container.getBoundingClientRect();

            const nextLines = graph.edges
                .filter(
                    (edge) =>
                        edge.source !== edge.target &&
                        nodeRefs.current[edge.source] &&
                        nodeRefs.current[edge.target],
                )
                .map((edge) => {
                    const sourceRect =
                        nodeRefs.current[edge.source]!.getBoundingClientRect();

                    const targetRect =
                        nodeRefs.current[edge.target]!.getBoundingClientRect();

                    return {
                        sourceId: edge.source,
                        targetId: edge.target,
                        source: {
                            x: sourceRect.right - containerRect.left,
                            y:
                                sourceRect.top +
                                sourceRect.height / 2 -
                                containerRect.top,
                        },
                        target: {
                            x: targetRect.left - containerRect.left,
                            y:
                                targetRect.top +
                                targetRect.height / 2 -
                                containerRect.top,
                        },
                    };
                });

            setLines(nextLines);
        }

        updateLines();

        const observer = new ResizeObserver(updateLines);

        if (containerRef.current) {
            observer.observe(containerRef.current);
        }

        window.addEventListener("resize", updateLines);

        return () => {
            observer.disconnect();
            window.removeEventListener("resize", updateLines);
        };
    }, [graph]);

    function isConnected(nodeId: string) {
        if (!hoveredNode) {
            return true;
        }

        return (
            nodeId === hoveredNode ||
            graph.edges.some(
                (edge) =>
                    (edge.source === hoveredNode &&
                        edge.target === nodeId) ||
                    (edge.target === hoveredNode &&
                        edge.source === nodeId),
            )
        );
    }

    function isLineConnected(line: GraphLine) {
        if (!hoveredNode) {
            return true;
        }

        return (
            line.sourceId === hoveredNode ||
            line.targetId === hoveredNode
        );
    }

    return (
        <div
            className="network-graph-layout"
            ref={containerRef}
        >
            <svg
                className="network-graph-lines"
                aria-hidden="true"
                viewBox={`0 0 ${containerRef.current?.clientWidth ?? 1000} ${containerRef.current?.clientHeight ?? 600
                    }`}
                preserveAspectRatio="none"
            >
                {lines.map((line, index) => {
                    const distance = line.target.x - line.source.x;
                    const curve = Math.max(30, distance * 0.4);

                    return (
                        <path
                            key={index}
                            d={`M ${line.source.x} ${line.source.y}
                  C ${line.source.x + curve} ${line.source.y},
                    ${line.target.x - curve} ${line.target.y},
                    ${line.target.x} ${line.target.y}`}
                            fill="none"
                            stroke="#d6dee7"
                            strokeWidth="1"
                            opacity={
                                isLineConnected(line)
                                    ? 0.75
                                    : 0.03
                            }
                        />
                    );
                })}
            </svg>

            {columnTypes.map((column) => {
                const nodes = graph.nodes.filter(
                    (node) => node.type === column.type,
                );

                return (
                    <div className="network-column" key={column.type}>
                        <h4>{column.label}</h4>

                        <div className="network-column-nodes">
                            {nodes.map((node: GraphNode) => (
                                <div
                                    className={`network-node-card network-node-${node.type} ${selectedNode?.id === node.id ? "network-node-selected" : ""
                                        }`}
                                    key={node.id}
                                    ref={(element) => {
                                        nodeRefs.current[node.id] = element;
                                    }}
                                    onMouseEnter={() =>
                                        setHoveredNode(node.id)
                                    }
                                    onMouseLeave={() =>
                                        setHoveredNode(null)
                                    }
                                    onClick={() => setSelectedNode(node)}
                                    style={{
                                        opacity: isConnected(node.id)
                                            ? 1
                                            : 0.35,
                                    }}
                                >
                                    {String(node.name ?? node.id)}
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })}

            {selectedNode && (
                <div className="network-node-details">
                    <h4>Selected Node</h4>

                    <strong>
                        {String(selectedNode.name ?? selectedNode.id)}
                    </strong>

                    {Object.entries(selectedNode)
                        .filter(
                            ([key]) =>
                                key !== "id" && key !== "name",
                        )
                        .map(([key, value]) => (
                            <div key={key}>
                                <span>
                                    {key.replace(/_/g, " ")}:
                                </span>{" "}
                                {typeof value === "object"
                                    ? Object.entries(value as Record<string, unknown>)
                                        .map(
                                            ([key, item]) =>
                                                `${key.replace(/_/g, " ")}: ${item}`,
                                        )
                                        .join(" · ")
                                    : String(value)}
                            </div>
                        ))}
                    <div className="network-node-connections">
                        <span>Connections:</span>{" "}
                        {graph.edges
                            .filter(
                                (edge) =>
                                    edge.source === selectedNode.id ||
                                    edge.target === selectedNode.id,
                            )
                            .map((edge, index) => {
                                const connectedId =
                                    edge.source === selectedNode.id
                                        ? edge.target
                                        : edge.source;

                                const connectedNode = graph.nodes.find(
                                    (node) => node.id === connectedId,
                                );

                                return (
                                    <span key={`${connectedId}-${index}`}>
                                        {String(
                                            connectedNode?.name ??
                                            connectedId,
                                        )}
                                        {index <
                                            graph.edges.filter(
                                                (item) =>
                                                    item.source === selectedNode.id ||
                                                    item.target === selectedNode.id,
                                            ).length -
                                            1
                                            ? " · "
                                            : ""}
                                    </span>
                                );
                            })}
                    </div>
                </div>
            )}
        </div>
    );
}

export default NetworkGraph;