const PAGE_NAME = "01 — Canonical (Vercel)";
const page =
  figma.root.children.find((p) => p.name === PAGE_NAME) || figma.root.children[0];
await figma.setCurrentPageAsync(page);

const createdNodeIds = [];

function hex(h) {
  const n = parseInt(h.replace("#", ""), 16);
  return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 };
}
function solid(color, opacity = 1) {
  return [{ type: "SOLID", color: hex(color), opacity }];
}

const FONTS = await figma.listAvailableFontsAsync();
const families = new Set(FONTS.map((f) => f.fontName.family));
const sans = families.has("Geist Sans") ? "Geist Sans" : "Inter";
const mono = families.has("Geist Mono") ? "Geist Mono" : "Roboto Mono";
const semiStyle = FONTS.find(
  (f) => f.fontName.family === sans && /semi/i.test(f.fontName.style)
)?.fontName.style || "Semi Bold";
const regStyle = "Regular";
const medStyle = FONTS.find(
  (f) => f.fontName.family === sans && /medium/i.test(f.fontName.style)
)?.fontName.style || "Medium";

async function loadSans(style) {
  await figma.loadFontAsync({ family: sans, style });
}
async function loadMono() {
  await figma.loadFontAsync({ family: mono, style: "Regular" });
}
async function text(content, size, style, color, opts = {}) {
  await loadSans(style);
  const t = figma.createText();
  t.characters = content;
  t.fontSize = size;
  t.fontName = { family: sans, style };
  t.fills = solid(color);
  t.textAutoResize = opts.width ? "HEIGHT" : "WIDTH_AND_HEIGHT";
  if (opts.width) {
    t.resize(opts.width, 20);
    t.layoutSizingHorizontal = "FILL";
  }
  return t;
}

const ACCENT = "#0070f3";
const CANVAS = "#ffffff";
const INK = "#171717";
const SOFT = "#f5f5f5";
const HAIR = "#ebebeb";
const SOFT_BG = "#fafafa";

const root = figma.createFrame();
root.name = "Canonical — Agent Chat 1280×900";
root.resize(1280, 900);
root.fills = solid(CANVAS);
root.layoutMode = "VERTICAL";
root.primaryAxisSizingMode = "FIXED";
root.counterAxisSizingMode = "FIXED";
root.itemSpacing = 0;
root.clipsContent = true;
root.x = 80;
root.y = 80;
page.appendChild(root);
createdNodeIds.push(root.id);

// --- Header 56px ---
const header = figma.createAutoLayout("HORIZONTAL");
header.name = "Header";
header.resize(1280, 56);
header.layoutSizingHorizontal = "FILL";
header.primaryAxisAlignItems = "CENTER";
header.counterAxisAlignItems = "CENTER";
header.paddingLeft = 16;
header.paddingRight = 16;
header.strokes = solid(HAIR);
header.strokeWeight = 1;
header.strokeAlign = "INSIDE";
header.fills = solid(CANVAS);
root.appendChild(header);

const logo = await text("CLDFlow", 18, semiStyle, INK);
header.appendChild(logo);

const headerSpacer = figma.createFrame();
headerSpacer.resize(1, 1);
headerSpacer.fills = [];
headerSpacer.layoutGrow = 1;
header.appendChild(headerSpacer);
headerSpacer.layoutSizingHorizontal = "FILL";

const icons = figma.createAutoLayout("HORIZONTAL");
icons.itemSpacing = 12;
icons.fills = [];
const gear = await text("⚙", 16, regStyle, INK);
const theme = await text("◐", 16, regStyle, INK);
icons.appendChild(gear);
icons.appendChild(theme);
header.appendChild(icons);
createdNodeIds.push(header.id, logo.id, icons.id);

// --- Message stream ---
const stream = figma.createAutoLayout("VERTICAL");
stream.name = "Message stream";
stream.resize(1280, 772);
stream.layoutSizingHorizontal = "FILL";
stream.layoutSizingVertical = "FILL";
stream.paddingLeft = 16;
stream.paddingRight = 16;
stream.paddingTop = 16;
stream.paddingBottom = 16;
stream.itemSpacing = 16;
stream.fills = [];
root.appendChild(stream);

// User message (right)
const userRow = figma.createAutoLayout("HORIZONTAL");
userRow.name = "User message row";
userRow.layoutSizingHorizontal = "FILL";
userRow.fills = [];
userRow.primaryAxisAlignItems = "MAX";
const userSpacer = figma.createFrame();
userSpacer.resize(200, 1);
userSpacer.fills = [];
userSpacer.layoutGrow = 1;
userRow.appendChild(userSpacer);
userSpacer.layoutSizingHorizontal = "FILL";

const userBubble = figma.createAutoLayout("VERTICAL");
userBubble.name = "User message";
userBubble.fills = solid(SOFT);
userBubble.cornerRadius = 12;
userBubble.paddingLeft = 16;
userBubble.paddingRight = 16;
userBubble.paddingTop = 12;
userBubble.paddingBottom = 12;
const userTxt = await text(
  "分析城市绿化率对居民心理健康的影响路径",
  14,
  regStyle,
  INK,
  { width: 520 }
);
userBubble.appendChild(userTxt);
userRow.appendChild(userBubble);
stream.appendChild(userRow);
createdNodeIds.push(userRow.id, userBubble.id, userTxt.id);

// Thinking block
const thinking = figma.createAutoLayout("VERTICAL");
thinking.name = "Thinking";
thinking.fills = solid(SOFT_BG);
thinking.strokes = solid(HAIR);
thinking.strokeWeight = 1;
thinking.cornerRadius = 8;
thinking.paddingLeft = 16;
thinking.paddingRight = 16;
thinking.paddingTop = 12;
thinking.paddingBottom = 12;
thinking.itemSpacing = 8;
thinking.layoutSizingHorizontal = "FILL";
thinking.maxWidth = 720;

const thinkTitle = await text("◌ 正在分析因果关系...", 14, medStyle, INK);
thinking.appendChild(thinkTitle);

const steps = [
  ["✓", "检索证据 — 找到 24 篇相关论文", ACCENT, true],
  ["✓", "构建因果图 — 识别 8 变量、12 条因果路径", ACCENT, true],
  ["●", "评估杠杆 — 正在计算 FCM 稳态与 D2D 杠杆系数…", INK, false],
];
for (const [icon, line, col] of steps) {
  const row = figma.createAutoLayout("HORIZONTAL");
  row.itemSpacing = 8;
  row.fills = [];
  const ic = await text(icon, 13, regStyle, col);
  const ln = await text(line, 13, regStyle, col);
  row.appendChild(ic);
  row.appendChild(ln);
  thinking.appendChild(row);
  createdNodeIds.push(row.id, ic.id, ln.id);
}
stream.appendChild(thinking);
createdNodeIds.push(thinking.id, thinkTitle.id);

// Assistant block
const assistant = figma.createAutoLayout("VERTICAL");
assistant.name = "Assistant message";
assistant.itemSpacing = 12;
assistant.fills = [];
assistant.layoutSizingHorizontal = "FILL";
assistant.maxWidth = 720;

const summary = await text(
  "基于检索证据，城市绿化率通过「绿色暴露 → 压力缓解 → 心理健康」主路径产生间接效应；公园可达性与社区凝聚力为关键中介。下方为当前 CLD 结构与杠杆排序（演示数据）。",
  14,
  regStyle,
  INK,
  { width: 680 }
);
assistant.appendChild(summary);

await loadMono();
const cld = figma.createText();
cld.characters =
  "nodes: 绿化率, 绿色暴露, 压力水平, 社交凝聚, 心理健康\nedges: 绿化率→绿色暴露(+), 绿色暴露→压力水平(-), 压力水平→心理健康(+), 社交凝聚→心理健康(+)";
cld.fontSize = 12;
cld.fontName = { family: mono, style: "Regular" };
cld.fills = solid(INK);
cld.textAutoResize = "HEIGHT";
cld.resize(680, 60);
cld.layoutSizingHorizontal = "FILL";
assistant.appendChild(cld);

const cardsRow = figma.createAutoLayout("HORIZONTAL");
cardsRow.name = "Source cards";
cardsRow.itemSpacing = 8;
cardsRow.fills = [];
cardsRow.layoutSizingHorizontal = "FILL";
const cardTitles = [
  "[1] 城市绿地与心理健康综述",
  "[2] 绿化率与社区凝聚力",
  "[3] CLD 方法论手册",
];
for (const title of cardTitles) {
  const card = figma.createAutoLayout("VERTICAL");
  card.fills = solid(SOFT);
  card.cornerRadius = 8;
  card.paddingLeft = 12;
  card.paddingRight = 12;
  card.paddingTop = 10;
  card.paddingBottom = 10;
  card.layoutGrow = 1;
  const ct = await text(title, 12, regStyle, INK, { width: 200 });
  card.appendChild(ct);
  cardsRow.appendChild(card);
  card.layoutSizingHorizontal = "FILL";
  createdNodeIds.push(card.id, ct.id);
}
assistant.appendChild(cardsRow);

const table = figma.createAutoLayout("VERTICAL");
table.name = "Leverage table";
table.itemSpacing = 6;
table.fills = [];
table.layoutSizingHorizontal = "FILL";
const tableTitle = await text("杠杆点排序（D2D）", 13, medStyle, INK);
table.appendChild(tableTitle);
const rows = [
  ["1", "绿色暴露", "0.82"],
  ["2", "压力水平", "0.71"],
  ["3", "社交凝聚", "0.54"],
];
for (const [rank, varName, coef] of rows) {
  const tr = figma.createAutoLayout("HORIZONTAL");
  tr.itemSpacing = 8;
  tr.fills = [];
  tr.layoutSizingHorizontal = "FILL";
  const r1 = await text(rank, 12, medStyle, INK);
  const r2 = await text(varName, 12, regStyle, INK);
  const r3 = await text(coef, 12, regStyle, ACCENT);
  const barBg = figma.createRectangle();
  barBg.resize(120, 6);
  barBg.fills = solid(SOFT);
  barBg.cornerRadius = 3;
  const barFill = figma.createRectangle();
  barFill.resize(parseFloat(coef) * 120, 6);
  barFill.fills = solid(ACCENT);
  barFill.cornerRadius = 3;
  const barWrap = figma.createFrame();
  barWrap.appendChild(barBg);
  barWrap.appendChild(barFill);
  barFill.x = 0;
  barFill.y = 0;
  barWrap.resize(120, 6);
  barWrap.fills = [];
  tr.appendChild(r1);
  tr.appendChild(r2);
  tr.appendChild(barWrap);
  tr.appendChild(r3);
  table.appendChild(tr);
  createdNodeIds.push(tr.id, r1.id, r2.id, r3.id, barBg.id, barFill.id);
}
assistant.appendChild(table);
stream.appendChild(assistant);
createdNodeIds.push(assistant.id, summary.id, cld.id, cardsRow.id, table.id);

// Input area
const inputArea = figma.createAutoLayout("HORIZONTAL");
inputArea.name = "Input";
inputArea.resize(1280, 72);
inputArea.layoutSizingHorizontal = "FILL";
inputArea.paddingLeft = 16;
inputArea.paddingRight = 16;
inputArea.paddingTop = 12;
inputArea.paddingBottom = 12;
inputArea.itemSpacing = 8;
inputArea.strokes = solid(HAIR);
inputArea.strokeWeight = 1;
inputArea.strokeAlign = "INSIDE";
inputArea.fills = solid(CANVAS);
inputArea.primaryAxisAlignItems = "CENTER";

const inputBox = figma.createAutoLayout("VERTICAL");
inputBox.name = "textarea";
inputBox.fills = solid(SOFT);
inputBox.cornerRadius = 8;
inputBox.paddingLeft = 12;
inputBox.paddingRight = 12;
inputBox.paddingTop = 10;
inputBox.paddingBottom = 10;
inputBox.layoutGrow = 1;
const ph = await text(
  "输入研究问题，Agent 将自动进行因果分析...",
  14,
  regStyle,
  "#737373",
  { width: 1000 }
);
inputBox.appendChild(ph);
inputBox.layoutSizingHorizontal = "FILL";
inputArea.appendChild(inputBox);

const send = figma.createAutoLayout("HORIZONTAL");
send.name = "Send button";
send.fills = solid(ACCENT);
send.cornerRadius = 8;
send.paddingLeft = 16;
send.paddingRight = 16;
send.paddingTop = 10;
send.paddingBottom = 10;
const sendLbl = await text("发送", 14, medStyle, "#ffffff");
send.appendChild(sendLbl);
inputArea.appendChild(send);
root.appendChild(inputArea);
createdNodeIds.push(inputArea.id, inputBox.id, ph.id, send.id, sendLbl.id);

// Annotations (dimensions)
const ann = figma.createAutoLayout("VERTICAL");
ann.name = "Annotations";
ann.itemSpacing = 4;
ann.fills = [];
ann.x = 1320;
ann.y = 80;
page.appendChild(ann);
const annLines = [
  "Header: h=56, px=16",
  "User bubble: radius=12, p=16/12",
  "Thinking: radius=8, border=1px #ebebeb",
  "Step gap: 8px, font=13px",
  "Input: h=72, gap=8, btn accent #0070f3",
];
for (const line of annLines) {
  const at = await text(line, 11, regStyle, "#737373");
  ann.appendChild(at);
  createdNodeIds.push(at.id);
}
createdNodeIds.push(ann.id);

await root.screenshot({ scale: 0.5 });

return {
  createdNodeIds,
  rootId: root.id,
  pageId: page.id,
  fonts: { sans, mono, semiStyle },
};
