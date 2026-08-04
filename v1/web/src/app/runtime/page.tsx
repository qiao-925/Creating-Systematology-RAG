"use client";

import { use } from "react";
import { RuntimePage } from "@/components/systematology/runtime-page";

export default function RuntimeRoute({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const { q } = use(searchParams);
  const question = typeof q === "string" ? q : "";

  return <RuntimePage initialQuestion={question} />;
}
