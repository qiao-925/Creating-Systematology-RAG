export interface CLDNode {
  id: string;
  label: string;
  x: number;
  y: number;
}

export interface CLDEdge {
  source: string;
  target: string;
  polarity: "+" | "-";
  label?: string;
}

export interface CLDData {
  nodes: CLDNode[];
  edges: CLDEdge[];
}

export const sampleCLDData: CLDData = {
  nodes: [
    { id: "subsidy", label: "补贴力度", x: 180, y: 80 },
    { id: "carbon-price", label: "碳定价机制强度", x: 210, y: 180 },
    { id: "rd", label: "清洁技术研发", x: 420, y: 180 },
    { id: "tech-cost", label: "清洁技术成本", x: 400, y: 300 },
    { id: "adoption", label: "清洁能源采用率", x: 175, y: 300 },
    { id: "emission", label: "碳排放", x: 160, y: 445 },
    { id: "fossil-exit", label: "化石能源退出", x: 600, y: 220 },
    { id: "fiscal", label: "财政压力", x: 110, y: 240 },
    { id: "grid", label: "电网接入能力", x: 635, y: 350 },
    { id: "awareness", label: "公众环保意识", x: 645, y: 440 },
  ],
  edges: [
    { source: "carbon-price", target: "rd", polarity: "+" },
    { source: "rd", target: "tech-cost", polarity: "-" },
    { source: "tech-cost", target: "adoption", polarity: "-" },
    { source: "adoption", target: "emission", polarity: "-" },
    { source: "carbon-price", target: "fossil-exit", polarity: "+" },
    { source: "fossil-exit", target: "adoption", polarity: "+" },
    { source: "subsidy", target: "rd", polarity: "+" },
    { source: "subsidy", target: "fiscal", polarity: "+" },
    { source: "fiscal", target: "subsidy", polarity: "-" },
    { source: "grid", target: "adoption", polarity: "+" },
    { source: "awareness", target: "adoption", polarity: "+" },
    { source: "emission", target: "awareness", polarity: "+" },
  ],
};
