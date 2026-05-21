const PAGE_NAME = "03 — Thinking & Workflow";
const page =
  figma.root.children.find((p) => p.name.includes("03")) ||
  figma.root.children[2];
await figma.setCurrentPageAsync(page);

for (const child of [...page.children]) child.remove();

const createdNodeIds = [];

function hex(h) {
  const n = parseInt(h.replace("#", ""), 16);
  return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 };
}
function solid(color) {
  return [{ type: "SOLID", color: hex(color) }];
}

await figma.loadFontAsync({ family: "Inter", style: "Regular" });
await figma.loadFontAsync({ family: "Inter", style: "Medium" });
await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });

const LIGHT = {
  accent: "#0070f3",
  canvas: "#fafafa",
  ink: "#171717",
  hair: "#ebebeb",
  error: "#e00",
  pending: "#a3a3a3",
};
const DARK = {
  accent: "#5e6ad2",
  canvas: "#0f1011",
  ink: "#f7f8f8",
  hair: "#23252a",
  error: "#ff6b6b",
  pending: "#6b6f76",
};

function makeSpec(tokens, title, x, y, mode) {
  const wrap = figma.createFrame();
  wrap.name = `${title} (${mode})`;
  wrap.resize(960, 800);
  wrap.x = x;
  wrap.y = y;
  wrap.fills = solid(mode === "dark" ? "#010102" : "#ffffff");
  wrap.layoutMode = "VERTICAL";
  wrap.paddingLeft = 24;
  wrap.paddingRight = 24;
  wrap.paddingTop = 24;
  wrap.paddingBottom = 24;
  wrap.itemSpacing = 16;
  page.appendChild(wrap);
  createdNodeIds.push(wrap.id);

  const h = figma.createText();
  h.characters = title;
  h.fontSize = 16;
  h.fontName = { family: "Inter", style: "Semi Bold" };
  h.fills = solid(mode === "dark" ? DARK.ink : "#171717");
  wrap.appendChild(h);

  const states = [
    { state: "pending", icon: "○", line: "检索证据 — 等待开始", color: tokens.pending },
    { state: "active", icon: "◌", line: "构建因果图 — 正在识别变量与路径…", color: tokens.accent },
    { state: "done", icon: "✓", line: "评估杠杆 — 已计算 Top-3 杠杆系数", color: tokens.accent },
    { state: "error", icon: "✗", line: "检索证据 — 知识库连接超时", color: tokens.error },
  ];

  const grid = figma.createAutoLayout("VERTICAL");
  grid.itemSpacing = 12;
  grid.fills = [];
  wrap.appendChild(grid);

  const row1 = figma.createAutoLayout("HORIZONTAL");
  row1.itemSpacing = 16;
  row1.fills = [];
  const row2 = figma.createAutoLayout("HORIZONTAL");
  row2.itemSpacing = 16;
  row2.fills = [];
  grid.appendChild(row1);
  grid.appendChild(row2);

  for (let si = 0; si < states.length; si++) {
    const s = states[si];
    const card = figma.createAutoLayout("VERTICAL");
    card.name = `State: ${s.state}`;
    card.resize(200, 120);
    card.fills = solid(tokens.canvas);
    card.strokes = solid(tokens.hair);
    card.strokeWeight = 1;
    card.cornerRadius = 8;
    card.paddingLeft = 12;
    card.paddingRight = 12;
    card.paddingTop = 12;
    card.paddingBottom = 12;
    card.itemSpacing = 8;

    const st = figma.createText();
    st.characters = s.state.toUpperCase();
    st.fontSize = 10;
    st.fontName = { family: "Inter", style: "Medium" };
    st.fills = solid(s.color);
    card.appendChild(st);

    const row = figma.createAutoLayout("HORIZONTAL");
    row.itemSpacing = 6;
    row.fills = [];
    const ic = figma.createText();
    ic.characters = s.icon;
    ic.fontSize = 13;
    ic.fontName = { family: "Inter", style: "Regular" };
    ic.fills = solid(s.color);
    const ln = figma.createText();
    ln.characters = s.line;
    ln.fontSize = 12;
    ln.fontName = { family: "Inter", style: "Regular" };
    ln.fills = solid(tokens.ink);
    ln.textAutoResize = "HEIGHT";
    ln.resize(160, 40);
    row.appendChild(ic);
    row.appendChild(ln);
    card.appendChild(row);
    (si < 2 ? row1 : row2).appendChild(card);
    createdNodeIds.push(card.id, st.id, ic.id, ln.id);
  }
  createdNodeIds.push(row1.id, row2.id, grid.id);

  const flow = figma.createAutoLayout("VERTICAL");
  flow.name = "3-step flow";
  flow.itemSpacing = 8;
  flow.fills = solid(tokens.canvas);
  flow.strokes = solid(tokens.hair);
  flow.strokeWeight = 1;
  flow.cornerRadius = 8;
  flow.paddingLeft = 16;
  flow.paddingRight = 16;
  flow.paddingTop = 12;
  flow.paddingBottom = 12;
  flow.layoutSizingHorizontal = "FILL";

  const flowTitle = figma.createText();
  flowTitle.characters = "◌ 正在分析因果关系...";
  flowTitle.fontSize = 14;
  flowTitle.fontName = { family: "Inter", style: "Medium" };
  flowTitle.fills = solid(tokens.ink);
  flow.appendChild(flowTitle);

  const steps = [
    ["✓", "检索证据 — 找到 24 篇相关论文", tokens.accent],
    ["✓", "构建因果图 — 8 变量、12 条路径", tokens.accent],
    ["●", "评估杠杆 — 计算 FCM / D2D…", tokens.ink],
  ];
  for (const [icon, text, col] of steps) {
    const row = figma.createAutoLayout("HORIZONTAL");
    row.itemSpacing = 8;
    row.paddingLeft = 22;
    row.fills = [];
    const i = figma.createText();
    i.characters = icon;
    i.fontSize = 13;
    i.fills = solid(col);
    const t = figma.createText();
    t.characters = text;
    t.fontSize = 13;
    t.fills = solid(col);
    row.appendChild(i);
    row.appendChild(t);
    flow.appendChild(row);
    createdNodeIds.push(row.id, i.id, t.id);
  }
  wrap.appendChild(flow);
  createdNodeIds.push(flow.id, flowTitle.id);

  const ann = figma.createText();
  ann.characters =
    "间距: 容器 p=16 | 步骤 gap=8px | 左缩进 22px | 状态卡 p=12 | 圆角 8px";
  ann.fontSize = 11;
  ann.fills = solid(mode === "dark" ? "#6b6f76" : "#737373");
  wrap.appendChild(ann);
  createdNodeIds.push(ann.id);

  return wrap.id;
}

const lightId = makeSpec(LIGHT, "Thinking spec — Light (Vercel)", 0, 0, "light");
const darkId = makeSpec(DARK, "Thinking spec — Dark (Linear tokens)", 1000, 0, "dark");

return { createdNodeIds, lightId, darkId, pageId: page.id };
