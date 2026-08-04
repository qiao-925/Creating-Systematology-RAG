const PAGE_NAME = "01 — Canonical (Vercel)";
const page =
  figma.root.children.find((p) => p.name === PAGE_NAME) || figma.root.children[0];
await figma.setCurrentPageAsync(page);

const removed = [];
for (const child of [...page.children]) {
  removed.push({ id: child.id, name: child.name });
  child.remove();
}

return { pageId: page.id, pageName: page.name, removedCount: removed.length, removed };
