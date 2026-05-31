import { http, HttpResponse, delay } from "msw";
import {
  mockHealth,
  mockConfig,
  mockModels,
  mockResearchResult,
  mockSystematologyResponse,
  mockFailureResponse,
} from "./data";

let currentConfig = { ...mockConfig };

export const handlers = [
  http.get("/api/health", async () => {
    await delay(200);
    return HttpResponse.json(mockHealth);
  }),

  http.get("/api/config", async () => {
    await delay(100);
    return HttpResponse.json(currentConfig);
  }),

  http.put("/api/config", async ({ request }) => {
    await delay(150);
    const body = (await request.json()) as Record<string, unknown>;
    currentConfig = { ...currentConfig, ...body };
    return HttpResponse.json(currentConfig);
  }),

  http.get("/api/config/models", async () => {
    await delay(100);
    return HttpResponse.json(mockModels);
  }),

  http.post("/api/chat", async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        const events: [string, string][] = [
          ["reasoning", "正在分析问题..."],
          ["token", "根据"],
          ["token", "分析"],
          ["token", "，"],
          ["token", "新能源"],
          ["token", "补贴"],
          ["token", "通过"],
          ["token", "多条"],
          ["token", "路径"],
          ["token", "影响"],
          ["token", "碳排放"],
          ["token", "。"],
          ["sources", JSON.stringify([
            { title: "Renewable Energy Subsidies and Carbon Emission Reduction", file_path: "/papers/nature-energy-2024.pdf", score: 0.94 },
            { title: "The Impact of Feed-in Tariffs on Innovation", file_path: "/papers/energy-policy-2023.pdf", score: 0.89 },
          ])],
          ["token", "主要"],
          ["token", "路径"],
          ["token", "包括"],
          ["token", "技术"],
          ["token", "成本"],
          ["token", "降低"],
          ["token", "和"],
          ["token", "研发"],
          ["token", "投入"],
          ["token", "增加"],
          ["token", "。"],
          ["done", "{}"],
        ];

        for (const [event, data] of events) {
          const chunk = `event: ${event}\ndata: ${data}\n\n`;
          controller.enqueue(encoder.encode(chunk));
          await delay(50);
        }
        controller.close();
      },
    });

    return new HttpResponse(stream, {
      headers: { "Content-Type": "text/event-stream" },
    });
  }),

  http.post("/api/research", async ({ request }) => {
    await delay(600);
    const body = (await request.json()) as { question?: string };
    if (body.question?.includes("失败") || body.question?.includes("fail")) {
      return HttpResponse.json(
        { error: "Research failed" },
        { status: 500 }
      );
    }
    return HttpResponse.json(mockResearchResult);
  }),

  http.post("/api/systematology/analyze", async ({ request }) => {
    await delay(800);
    const body = (await request.json()) as { question?: string };
    if (body.question?.includes("失败") || body.question?.includes("fail")) {
      return HttpResponse.json(mockFailureResponse);
    }
    return HttpResponse.json(mockSystematologyResponse);
  }),
];
