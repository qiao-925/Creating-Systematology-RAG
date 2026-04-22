"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ComponentPropsWithoutRef } from "react";

interface Props {
  content: string;
  onCitationClick?: (index: number) => void;
}

export function MarkdownContent({ content, onCitationClick }: Props) {
  const processedContent = content.replace(
    /\[(\d+)\]/g,
    (_, num) => `<cite data-index="${num}">[${num}]</cite>`,
  );

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: (props: ComponentPropsWithoutRef<"h1">) => (
          <h1 className="text-lg font-semibold mt-5 mb-2 first:mt-0" {...props} />
        ),
        h2: (props: ComponentPropsWithoutRef<"h2">) => (
          <h2 className="text-base font-semibold mt-4 mb-2 first:mt-0" {...props} />
        ),
        h3: (props: ComponentPropsWithoutRef<"h3">) => (
          <h3 className="text-[15px] font-semibold mt-3 mb-1.5 first:mt-0" {...props} />
        ),
        p: (props: ComponentPropsWithoutRef<"p">) => (
          <p className="mb-3 last:mb-0 leading-[1.7]" {...props} />
        ),
        ul: (props: ComponentPropsWithoutRef<"ul">) => (
          <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />
        ),
        ol: (props: ComponentPropsWithoutRef<"ol">) => (
          <ol className="list-decimal pl-5 mb-3 space-y-1" {...props} />
        ),
        li: (props: ComponentPropsWithoutRef<"li">) => (
          <li className="leading-[1.7]" {...props} />
        ),
        code: ({ className, children, ...rest }: ComponentPropsWithoutRef<"code"> & { className?: string }) => {
          const isBlock = className?.startsWith("language-");
          if (isBlock) {
            return (
              <code
                className="block bg-muted/60 rounded-lg p-4 my-3 text-sm overflow-x-auto font-mono leading-relaxed"
                {...rest}
              >
                {children}
              </code>
            );
          }
          return (
            <code className="bg-muted/60 px-1.5 py-0.5 rounded-md text-[13px] font-mono" {...rest}>
              {children}
            </code>
          );
        },
        pre: ({ children }: ComponentPropsWithoutRef<"pre">) => <>{children}</>,
        blockquote: (props: ComponentPropsWithoutRef<"blockquote">) => (
          <blockquote className="border-l-2 border-emerald-500/40 pl-4 my-3 text-muted-foreground/80 italic" {...props} />
        ),
        a: (props: ComponentPropsWithoutRef<"a">) => (
          <a className="text-emerald-500 hover:text-emerald-400 hover:underline underline-offset-2" target="_blank" rel="noopener noreferrer" {...props} />
        ),
        // render <cite> tags produced by processedContent
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        cite: (props: any) => {
          const idx = Number(props["data-index"]);
          return (
            <button
              type="button"
              className="text-emerald-400 hover:text-emerald-300 font-medium cursor-pointer text-sm"
              onClick={() => onCitationClick?.(idx)}
            >
              {props.children}
            </button>
          );
        },
      }}
    >
      {processedContent}
    </ReactMarkdown>
  );
}
