"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }) => (
          <h1 className="text-base font-bold text-azul-navy mt-2 mb-1">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-sm font-bold text-azul-navy mt-2 mb-1">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-xs font-semibold text-azul-navy mt-1.5 mb-0.5">{children}</h3>
        ),
        p: ({ children }) => (
          <p className="mb-1.5 leading-relaxed text-text-primary text-xs last:mb-0">{children}</p>
        ),
        strong: ({ children }) => (
          <strong className="font-bold text-azul-navy">{children}</strong>
        ),
        ul: ({ children }) => (
          <ul className="list-disc list-outside pl-4 space-y-0.5 mb-2 text-xs">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-outside pl-4 space-y-0.5 mb-2 text-xs">{children}</ol>
        ),
        li: ({ children }) => (
          <li className="text-text-primary">{children}</li>
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-azul-action/60 bg-muted/30 pl-2.5 py-1 my-1.5 italic text-text-secondary text-xs rounded-r">
            {children}
          </blockquote>
        ),
        // Fenced code blocks: estilizados no container <pre> com reset descendente em <code>
        pre: ({ children }) => (
          <pre className="my-2 rounded-md bg-[#0B1E2E] text-slate-100 p-3 font-mono text-[11px] overflow-x-auto border border-azul-navy/30 leading-relaxed [&>code]:bg-transparent [&>code]:p-0 [&>code]:text-inherit [&>code]:border-0 [&>code]:rounded-none">
            {children}
          </pre>
        ),
        // Inline code (isolado): recebe pill/badge institucional; quando dentro de <pre>, é resetado pelas classes acima
        code: ({ className, children, node: _node, ...props }) => (
          <code
            className={`font-mono text-[11px] bg-muted px-1.5 py-0.5 rounded text-azul-navy border border-border-subtle ${className ?? ""}`}
            {...props}
          >
            {children}
          </code>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-2 border border-border-subtle rounded-md">
            <table className="w-full text-[11px] text-left border-collapse">{children}</table>
          </div>
        ),
        th: ({ children }) => (
          <th className="bg-muted/80 p-1.5 font-semibold text-azul-navy border-b border-border-subtle">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="p-1.5 border-b border-border-subtle/60 text-text-secondary">
            {children}
          </td>
        ),
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-azul-action font-semibold underline underline-offset-2 hover:text-azul-deep transition-colors"
          >
            {children}
          </a>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
