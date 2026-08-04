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

// ============================================================
// Scenario 1: Energy & Climate (能源气候) — 碳定价-补贴-研发
// Keywords: 能源, 气候, 碳, 补贴, 碳排放, 新能源, 温室
// ============================================================
export const mockSystematologyEnergy: SystematologyResponse = {
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
    evidence_tracing: {
      sources: [
        { tier: "T1", title: "Renewable Energy Subsidies and Carbon Emission Reduction: A Causal Analysis", meta: "Nature Energy · 2024 · 被引 89 次" },
        { tier: "T1", title: "The Impact of Feed-in Tariffs on Innovation in Renewable Energy Technologies", meta: "Energy Policy · 2023 · 被引 67 次" },
        { tier: "T2", title: "EU Emissions Trading System: Evidence on Carbon Price and Innovation", meta: "European Commission · 2024" },
        { tier: "T2", title: "Grid Integration Costs of Variable Renewable Energy", meta: "Applied Energy · 2023 · 被引 42 次" },
        { tier: "T3", title: "Global Renewable Energy Investment Trends Report", meta: "IRENA · 2024" },
      ],
    },
    scenario_comparison: {},
  },
};

// ============================================================
// Scenario 2: Public Health (公共卫生) — 老龄化-医疗-预防
// Keywords: 健康, 医疗, 疾病, 疫情, 疫苗, 老龄化, 公共卫生, 医院
// ============================================================
export const mockSystematologyHealth: SystematologyResponse = {
  success: true,
  report: {
    cld_visualization: {
      nodes: [
        { id: "aging", label: "老龄化程度", description: "65岁以上人口占比" },
        { id: "chronic", label: "慢性病发病率", description: "主要慢性病（糖尿病、高血压等）患病率" },
        { id: "med-cost", label: "人均医疗支出", description: "居民人均年度医疗费用" },
        { id: "insurance", label: "医保基金压力", description: "医保基金收支平衡状况" },
        { id: "primary-care", label: "基层医疗覆盖率", description: "社区卫生服务中心覆盖和服务能力" },
        { id: "prevention", label: "预防保健投入", description: "公共卫生和疾病预防支出" },
        { id: "health-literacy", label: "公众健康素养", description: "居民健康知识和自我管理能力" },
        { id: "med-staff", label: "医护人员供给", description: "每千人医护人员数量" },
      ],
      edges: [
        { source: "aging", target: "chronic", relation: "influences", weight: 0.85 },
        { source: "chronic", target: "med-cost", relation: "influences", weight: 0.9 },
        { source: "med-cost", target: "insurance", relation: "influences", weight: 0.8 },
        { source: "insurance", target: "prevention", relation: "inhibits", weight: -0.6 },
        { source: "prevention", target: "chronic", relation: "inhibits", weight: -0.7 },
        { source: "primary-care", target: "chronic", relation: "inhibits", weight: -0.65 },
        { source: "health-literacy", target: "chronic", relation: "inhibits", weight: -0.5 },
        { source: "health-literacy", target: "prevention", relation: "supports", weight: 0.45 },
        { source: "med-staff", target: "primary-care", relation: "enables", weight: 0.75 },
        { source: "insurance", target: "med-staff", relation: "inhibits", weight: -0.55 },
      ],
    },
    leverage_ranking: [
      { node_id: "prevention", node_label: "预防保健投入", impact_score: 0.82, confidence: 0.88, rank: 1 },
      { node_id: "primary-care", node_label: "基层医疗覆盖率", impact_score: 0.75, confidence: 0.85, rank: 2 },
      { node_id: "health-literacy", node_label: "公众健康素养", impact_score: 0.63, confidence: 0.78, rank: 3 },
      { node_id: "med-staff", node_label: "医护人员供给", impact_score: 0.51, confidence: 0.72, rank: 4 },
      { node_id: "aging", node_label: "老龄化程度", impact_score: 0.28, confidence: 0.55, rank: 5 },
    ],
    synthesized_insights:
      "该因果回路图揭示了公共卫生体系中的三个关键反馈：\n\n" +
      "1. **负向平衡回路（核心）**：老龄化 → 慢性病发病率 → 人均医疗支出 → 医保基金压力 → 预防保健投入（抑制）→ 慢性病发病率（抑制）—— 这是一个「支出挤压预防」的恶性循环\n\n" +
      "2. **正向增强回路**：健康素养 → 预防保健投入 → 慢性病发病率降低 → 医疗支出减少 → 医保压力缓解 → 医护人员供给改善 → 基层医疗覆盖提升\n\n" +
      "3. **关键杠杆点**：预防保健投入是最具影响力的干预点（impact=0.82），但当前被医保支出压力挤压。建议打破「重治疗轻预防」的路径依赖，将预防支出从治疗支出中解耦。\n\n" +
      "基层医疗覆盖率（impact=0.75）是次优杠杆点，通过分级诊疗可以有效缓解慢性病管理的成本压力。",
    evidence_tracing: {
      sources: [
        { tier: "T1", title: "Population Aging and Healthcare Expenditure: A Panel Data Analysis", meta: "The Lancet Public Health · 2024 · 被引 124 次" },
        { tier: "T1", title: "Preventive Care Utilization and Chronic Disease Outcomes in Aging Populations", meta: "JAMA · 2023 · 被引 93 次" },
        { tier: "T2", title: "Primary Care Gatekeeping and Cost Containment: Evidence from 15 OECD Countries", meta: "Health Policy · 2024 · 被引 51 次" },
        { tier: "T2", title: "The Impact of Health Literacy on Self-Management of Chronic Conditions", meta: "BMJ Open · 2023 · 被引 38 次" },
        { tier: "T3", title: "Global Burden of Disease Study: Risk Factors and Health System Capacity", meta: "IHME · 2024" },
      ],
    },
    scenario_comparison: {},
  },
};

// ============================================================
// Scenario 3: Economy & Industry (经济产业) — 利率-房价-杠杆
// Keywords: 经济, 产业, 利率, 房地产, 市场, 就业, 创新, 产业升级
// ============================================================
export const mockSystematologyEconomy: SystematologyResponse = {
  success: true,
  report: {
    cld_visualization: {
      nodes: [
        { id: "interest", label: "利率水平", description: "央行基准利率和实际贷款利率" },
        { id: "housing-price", label: "房价", description: "住宅房地产市场价格指数" },
        { id: "demand", label: "购房需求", description: "刚需和投资性购房需求" },
        { id: "developer-invest", label: "开发商投资", description: "房地产开发投资规模" },
        { id: "land-supply", label: "土地供应", description: "地方政府土地出让面积" },
        { id: "leverage", label: "居民杠杆率", description: "居民部门债务/GDP比率" },
        { id: "gdp-growth", label: "经济增速", description: "GDP同比增长率" },
        { id: "employment", label: "就业率", description: "城镇调查失业率" },
        { id: "financial-risk", label: "金融系统风险", description: "银行不良贷款率和系统性风险指标" },
      ],
      edges: [
        { source: "interest", target: "demand", relation: "inhibits", weight: -0.75 },
        { source: "demand", target: "housing-price", relation: "influences", weight: 0.85 },
        { source: "housing-price", target: "developer-invest", relation: "influences", weight: 0.7 },
        { source: "developer-invest", target: "gdp-growth", relation: "supports", weight: 0.65 },
        { source: "gdp-growth", target: "employment", relation: "influences", weight: 0.6 },
        { source: "employment", target: "demand", relation: "influences", weight: 0.55 },
        { source: "housing-price", target: "leverage", relation: "influences", weight: 0.8 },
        { source: "leverage", target: "financial-risk", relation: "influences", weight: 0.7 },
        { source: "financial-risk", target: "interest", relation: "influences", weight: 0.5 },
        { source: "land-supply", target: "housing-price", relation: "inhibits", weight: -0.6 },
        { source: "financial-risk", target: "gdp-growth", relation: "inhibits", weight: -0.55 },
      ],
    },
    leverage_ranking: [
      { node_id: "interest", node_label: "利率水平", impact_score: 0.88, confidence: 0.92, rank: 1 },
      { node_id: "land-supply", node_label: "土地供应", impact_score: 0.72, confidence: 0.83, rank: 2 },
      { node_id: "leverage", node_label: "居民杠杆率", impact_score: 0.65, confidence: 0.8, rank: 3 },
      { node_id: "developer-invest", node_label: "开发商投资", impact_score: 0.48, confidence: 0.72, rank: 4 },
      { node_id: "demand", node_label: "购房需求", impact_score: 0.35, confidence: 0.65, rank: 5 },
    ],
    synthesized_insights:
      "该因果回路图揭示了房地产市场与宏观经济之间的三个关键反馈回路：\n\n" +
      "1. **正向增强回路（繁荣期）**：就业率 → 购房需求 → 房价 → 开发商投资 → 经济增速 → 就业率 —— 这是一个自我强化的增长循环，但也隐含脆弱性\n\n" +
      "2. **负向平衡回路（调控期）**：房价 → 居民杠杆率 → 金融系统风险 → 利率（上行压力）→ 购房需求（抑制）→ 房价（抑制）\n\n" +
      "3. **关键杠杆点**：利率水平是最具影响力的干预点（impact=0.88），但利率工具是「钝器」——同时影响多个回路，可能造成意外后果。\n\n" +
      "土地供应（impact=0.72）是结构性杠杆点，通过供给侧改革可以从根源上缓解房价压力而无需过度依赖货币政策。",
    evidence_tracing: {
      sources: [
        { tier: "T1", title: "Monetary Policy Transmission and Housing Market Dynamics: A SVAR Approach", meta: "Journal of Monetary Economics · 2024 · 被引 112 次" },
        { tier: "T1", title: "Land Supply Constraints and Housing Affordability in Chinese Cities", meta: "Urban Studies · 2023 · 被引 78 次" },
        { tier: "T2", title: "Household Leverage and Financial Stability: The China Case", meta: "BIS Working Papers · 2024 · 被引 45 次" },
        { tier: "T2", title: "Real Estate Investment and GDP Growth: A Multi-Country Panel Analysis", meta: "IMF Economic Review · 2023 · 被引 56 次" },
        { tier: "T3", title: "Global Housing Market Outlook 2024", meta: "OECD · 2024" },
      ],
    },
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

// Legacy alias for backward compatibility
export const mockSystematologyResponse = mockSystematologyEnergy;
