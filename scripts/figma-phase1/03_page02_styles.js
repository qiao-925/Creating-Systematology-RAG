const PAGE_NAME = "02 — Style Explorations (7×)";
const page =
  figma.root.children.find((p) => p.name.includes("02")) ||
  figma.root.children[1];
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

const FONTS = await figma.listAvailableFontsAsync();
const families = new Set(FONTS.map((f) => f.fontName.family));

const STYLES = [
  { name: "Vercel", accent: "#0070f3", canvas: "#ffffff", ink: "#171717", soft: "#f5f5f5", hair: "#ebebeb", font: "Inter", shadow: true },
  { name: "Linear", accent: "#5e6ad2", canvas: "#010102", ink: "#f7f8f8", soft: "#0f1011", hair: "#23252a", font: "Inter", shadow: false },
  { name: "Claude", accent: "#cc785c", canvas: "#faf9f5", ink: "#141413", soft: "#efe9de", hair: "#e6dfd8", font: "Inter", shadow: false },
  { name: "Cursor", accent: "#f54e00", canvas: "#f7f7f4", ink: "#26251e", soft: "#fafaf7", hair: "#e6e5e0", font: "Inter", shadow: false },
  { name: "Notion", accent: "#5645d4", canvas: "#ffffff", ink: "#1a1a1a", soft: "#f6f5f4", hair: "#e5e3df", font: "Inter", shadow: false },
  { name: "Stripe", accent: "#533afd", canvas: "#ffffff", ink: "#0d253d", soft: "#f6f9fc", hair: "#e3e8ee", font: "Inter", shadow: false },
  { name: "Figma DS", accent: "#000000", canvas: "#ffffff", ink: "#000000", soft: "#f7f7f5", hair: "#e6e6e6", font: "Inter", shadow: false },
];

async function loadFont(family, style) {
  await figma.loadFontAsync({ family, style });
}

async function miniFrame(style, x, y) {
  const fam = families.has(style.font) ? style.font : "Inter";
  await loadFont(fam, "Regular");
  await loadFont(fam, "Medium");
  await loadFont(fam, "Semi Bold");

  const frame = figma.createFrame();
  frame.name = `Style: ${style.name}`;
  frame.resize(480, 720);
  frame.x = x;
  frame.y = y;
  frame.fills = solid(style.canvas);
  frame.layoutMode = "VERTICAL";
  frame.itemSpacing = 0;
  frame.clipsContent = true;
  page.appendChild(frame);
  createdNodeIds.push(frame.id);

  const labelBar = figma.createRectangle();
  labelBar.resize(480, 24);
  labelBar.fills = solid(style.accent);
  frame.appendChild(labelBar);
  createdNodeIds.push(labelBar.id);

  const label = figma.createText();
  label.characters = `Style: ${style.name}`;
  label.fontSize = 12;
  label.fontName = { family: fam, style: "Semi Bold" };
  label.fills = solid(style.name === "Linear" ? style.ink : "#ffffff");
  label.x = 12;
  label.y = 4;
  frame.appendChild(label);
  createdNodeIds.push(label.id);

  const body = figma.createAutoLayout("VERTICAL");
  body.name = "Body";
  body.resize(480, 696);
  body.paddingLeft = 12;
  body.paddingRight = 12;
  body.paddingTop = 8;
  body.paddingBottom = 12;
  body.itemSpacing = 8;
  body.fills = [];
  frame.appendChild(body);

  const hdr = figma.createAutoLayout("HORIZONTAL");
  hdr.resize(456, 40);
  hdr.paddingLeft = 8;
  hdr.paddingRight = 8;
  hdr.fills = solid(style.soft);
  hdr.strokes = solid(style.hair);
  hdr.strokeWeight = 1;
  hdr.cornerRadius = 6;
  hdr.primaryAxisAlignItems = "CENTER";
  const logo = figma.createText();
  logo.characters = "CLDFlow";
  logo.fontSize = 14;
  logo.fontName = { family: fam, style: "Semi Bold" };
  logo.fills = solid(style.ink);
  hdr.appendChild(logo);
  body.appendChild(hdr);

  const user = figma.createAutoLayout("VERTICAL");
  user.fills = solid(style.soft);
  user.cornerRadius = 10;
  user.paddingLeft = 10;
  user.paddingRight = 10;
  user.paddingTop = 8;
  user.paddingBottom = 8;
  const ut = figma.createText();
  ut.characters = "分析城市绿化率对居民心理健康的影响路径";
  ut.fontSize = 11;
  ut.fontName = { family: fam, style: "Regular" };
  ut.fills = solid(style.ink);
  ut.textAutoResize = "HEIGHT";
  ut.resize(420, 40);
  user.appendChild(ut);
  body.appendChild(user);

  const think = figma.createAutoLayout("VERTICAL");
  think.fills = solid(style.soft);
  think.strokes = solid(style.hair);
  think.strokeWeight = 1;
  think.cornerRadius = 8;
  think.paddingLeft = 10;
  think.paddingRight = 10;
  think.paddingTop = 8;
  think.paddingBottom = 8;
  think.itemSpacing = 4;
  const steps = [
    "✓ 检索证据 — 24 篇",
    "✓ 构建因果图 — 8 变量",
    "● 评估杠杆 — 计算中…",
  ];
  for (let i = 0; i < steps.length; i++) {
    const st = figma.createText();
    st.characters = steps[i];
    st.fontSize = 10;
    st.fontName = { family: fam, style: "Regular" };
    st.fills = solid(i < 2 ? style.accent : style.ink);
    think.appendChild(st);
    createdNodeIds.push(st.id);
  }
  body.appendChild(think);

  const sum = figma.createText();
  sum.characters = "绿化率→绿色暴露→压力缓解→心理健康（摘要）";
  sum.fontSize = 10;
  sum.fontName = { family: fam, style: "Regular" };
  sum.fills = solid(style.ink);
  sum.textAutoResize = "HEIGHT";
  sum.resize(420, 32);
  body.appendChild(sum);

  const cld = figma.createText();
  cld.characters = "CLD: 绿化率→绿色暴露(+); 绿色暴露→压力(-)";
  cld.fontSize = 9;
  cld.fontName = { family: fam, style: "Regular" };
  cld.fills = solid(style.ink);
  body.appendChild(cld);

  const inp = figma.createAutoLayout("HORIZONTAL");
  inp.itemSpacing = 6;
  inp.fills = solid(style.soft);
  inp.cornerRadius = 8;
  inp.paddingLeft = 8;
  inp.paddingRight = 8;
  inp.paddingTop = 8;
  inp.paddingBottom = 8;
  const ph = figma.createText();
  ph.characters = "输入研究问题…";
  ph.fontSize = 10;
  ph.fontName = { family: fam, style: "Regular" };
  ph.fills = solid(style.ink);
  ph.opacity = 0.6;
  inp.appendChild(ph);
  const btn = figma.createAutoLayout("HORIZONTAL");
  btn.fills = solid(style.accent);
  btn.cornerRadius = style.name === "Vercel" ? 100 : 8;
  btn.paddingLeft = 10;
  btn.paddingRight = 10;
  btn.paddingTop = 6;
  btn.paddingBottom = 6;
  const bl = figma.createText();
  bl.characters = "发送";
  bl.fontSize = 10;
  bl.fontName = { family: fam, style: "Medium" };
  bl.fills = solid(style.name === "Linear" || style.name === "Figma DS" ? "#ffffff" : "#ffffff");
  btn.appendChild(bl);
  inp.appendChild(btn);
  body.appendChild(inp);

  if (style.shadow) {
    frame.effects = [
      {
        type: "DROP_SHADOW",
        color: { r: 0, g: 0, b: 0, a: 0.04 },
        offset: { x: 0, y: 1 },
        radius: 2,
        spread: 0,
        visible: true,
        blendMode: "NORMAL",
      },
      {
        type: "DROP_SHADOW",
        color: { r: 0, g: 0, b: 0, a: 0.08 },
        offset: { x: 0, y: 4 },
        radius: 12,
        spread: 0,
        visible: true,
        blendMode: "NORMAL",
      },
    ];
  }

  createdNodeIds.push(body.id, hdr.id, logo.id, user.id, ut.id, think.id, sum.id, cld.id, inp.id, ph.id, btn.id, bl.id);
  await frame.screenshot({ scale: 0.35 });
  return frame.id;
}

const COL_W = 480;
const GAP_X = 80;
const GAP_Y = 80;
const ids = [];
for (let i = 0; i < STYLES.length; i++) {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = col * (COL_W + GAP_X);
  const y = row * (720 + GAP_Y);
  const id = await miniFrame(STYLES[i], x, y);
  ids.push(id);
  if (i < STYLES.length - 1) await new Promise((r) => setTimeout(r, 200));
}

return { createdNodeIds, frameIds: ids, pageId: page.id };
