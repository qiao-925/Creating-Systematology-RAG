const pages = figma.root.children.map((p) => ({
  id: p.id,
  name: p.name,
  childCount: p.children.length,
}));
const first = figma.root.children[0];
await figma.setCurrentPageAsync(first);
const top = first.children.map((n) => ({
  id: n.id,
  name: n.name,
  type: n.type,
  w: n.width,
  h: n.height,
}));
return { pages, firstPage: first.name, topLevel: top };
