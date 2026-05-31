import type {
  HealthStatus,
  AppConfig,
  ModelInfo,
  ResearchResult,
  SystematologyResponse,
} from "@/types";

export const mockHealth: HealthStatus = {
  status: "ready",
  message: "Mock server running",
  progress: null,
};

export const mockConfig: AppConfig = {
  selected_model: "deepseek-chat",
  llm_preset: "balanced",
  retrieval_strategy: "vector",
  use_agentic_rag: false,
  similarity_top_k: 5,
  similarity_threshold: 0.3,
  enable_rerank: false,
  show_reasoning: true,
  research_mode: false,
};

export const mockModels: ModelInfo[] = [
  { id: "deepseek-chat", name: "DeepSeek Chat", supports_reasoning: false },
  { id: "deepseek-reasoner", name: "DeepSeek Reasoner", supports_reasoning: true },
  { id: "gpt-4o", name: "GPT-4o", supports_reasoning: false },
  { id: "claude-sonnet-4-6", name: "Claude Sonnet 4.6", supports_reasoning: true },
];

export const mockResearchResult: ResearchResult = {
  judgment:
    "新能源补贴通过降低清洁技术成本和激励研发投入，显著促进了碳排放减少。证据表明该路径存在正反馈效应，但也面临财政压力和电网接入等技术瓶颈。",
  evidence: [
    {
      query: "新能源补贴对碳排放的因果影响",
      text: "可再生能源补贴每增加1%，碳排放强度下降约0.3-0.5%，主要通过清洁能源采用率提升和技术成本降低两条路径实现。",
      source_ref: "Nature Energy, 2024",
      score: 0.94,
    },
    {
      query: "碳定价机制对清洁技术创新的影响",
      text: "碳定价每提高10欧元/吨，清洁技术专利申请量增加约5.2%，表明价格信号对研发方向有显著引导作用。",
      source_ref: "Energy Policy, 2023",
      score: 0.89,
    },
    {
      query: "化石能源退出与电网接入的关系",
      text: "电网接入能力不足是化石能源退出的主要瓶颈，每GW新增可再生能源装机需要约2亿欧元的电网升级投资。",
      source_ref: "IRENA, 2024",
      score: 0.82,
    },
  ],
  confidence: "high",
  tensions: [
    "财政补贴的长期可持续性与短期减排紧迫性之间的权衡",
    "碳定价引发的竞争力担忧与实际产业调整成本的差距",
  ],
  next_questions: [
    "碳边境调节机制(CBAM)如何影响全球碳定价的有效性？",
    "储能技术突破对清洁能源系统反馈结构的改变？",
  ],
};

export const mockSystematologyResponse: SystematologyResponse = {
  success: true,
  report: {
    cld_visualization: {
      nodes: [
        { id: "subsidy", label: "补贴力度", description: "政府新能源补贴力度" },
        { id: "carbon-price", label: "碳定价机制强度", description: "碳税和碳交易价格" },
        { id: "rd", label: "清洁技术研发", description: "清洁能源技术研发投入" },
        { id: "tech-cost", label: "清洁技术成本", description: "清洁能源技术平准化成本" },
        { id: "adoption", label: "清洁能源采用率", description: "清洁能源在能源结构中的占比" },
        { id: "emission", label: "碳排放", description: "温室气体排放总量" },
        { id: "fossil-exit", label: "化石能源退出", description: "化石能源产能退出速度" },
        { id: "fiscal", label: "财政压力", description: "政府财政可持续性压力" },
        { id: "grid", label: "电网接入能力", description: "电网对可再生能源的接纳能力" },
        { id: "awareness", label: "公众环保意识", description: "公众对气候变化的认知和行动意愿" },
      ],
      edges: [
        { source: "carbon-price", target: "rd", relation: "influences", weight: 0.8 },
        { source: "rd", target: "tech-cost", relation: "inhibits", weight: -0.7 },
        { source: "tech-cost", target: "adoption", relation: "inhibits", weight: -0.9 },
        { source: "adoption", target: "emission", relation: "inhibits", weight: -0.85 },
        { source: "carbon-price", target: "fossil-exit", relation: "influences", weight: 0.6 },
        { source: "fossil-exit", target: "adoption", relation: "influences", weight: 0.5 },
        { source: "subsidy", target: "rd", relation: "supports", weight: 0.75 },
        { source: "subsidy", target: "fiscal", relation: "influences", weight: 0.9 },
        { source: "fiscal", target: "subsidy", relation: "inhibits", weight: -0.65 },
        { source: "grid", target: "adoption", relation: "enables", weight: 0.7 },
        { source: "awareness", target: "adoption", relation: "supports", weight: 0.4 },
        { source: "emission", target: "awareness", relation: "influences", weight: 0.55 },
      ],
    },
    leverage_ranking: [
      { node_id: "carbon-price", node_label: "碳定价机制强度", impact_score: 0.87, confidence: 0.9, rank: 1 },
      { node_id: "rd", node_label: "清洁技术研发", impact_score: 0.72, confidence: 0.85, rank: 2 },
      { node_id: "grid", node_label: "电网接入能力", impact_score: 0.58, confidence: 0.75, rank: 3 },
      { node_id: "fossil-exit", node_label: "化石能源退出", impact_score: 0.45, confidence: 0.7, rank: 4 },
      { node_id: "awareness", node_label: "公众环保意识", impact_score: 0.31, confidence: 0.6, rank: 5 },
    ],
    synthesized_insights:
      "该因果回路图揭示了能源转型中的三个关键反馈回路：\n\n" +
      "1. **正向增强回路**：碳定价 → 清洁技术研发 → 技术成本下降 → 清洁能源采用率上升 → 碳排放减少 → 公众环保意识增强 → 清洁能源采用率（强化）\n\n" +
      "2. **负向平衡回路**：补贴 → 财政压力 → 补贴力度（抑制）→ 这是一个内在的财政可持续性约束\n\n" +
      "3. **关键杠杆点**：碳定价机制强度是最具影响力的干预点（impact=0.87），其次是清洁技术研发投入（impact=0.72）。电网接入能力是重要的结构性瓶颈。\n\n" +
      "建议优先强化碳定价机制，同时投资电网基础设施以消除结构性瓶颈。",
    evidence_tracing: {},
    scenario_comparison: {},
  },
};

export const mockFailureResponse: SystematologyResponse = {
  success: false,
  report: {
    run_id: "fail-001",
    stage: "建图",
    reason: "无法从文献中提取足够的因果节点（仅找到2个节点，需要至少3个）。建议提供更多上下文或缩小问题范围。",
    details: { node_count: 2, min_required: 3 },
  },
};
