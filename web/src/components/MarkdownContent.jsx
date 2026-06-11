import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { cn } from '@/lib/cn';

// Render a Markdown string as styled React nodes.
// Raw HTML is intentionally NOT enabled (no rehype-raw): any embedded HTML in
// the source is shown as text, so untrusted answer content cannot inject markup.
// Each override forwards only the props it needs (never the internal `node`),
// so react-markdown's hast node is not leaked onto DOM elements.
const MARKDOWN_COMPONENTS = {
  h1: ({ children }) => (
    <h1 className="mt-4 mb-2 text-lg font-semibold text-foreground first:mt-0">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mt-4 mb-2 text-base font-semibold text-foreground first:mt-0">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="mt-3 mb-1.5 text-sm font-semibold text-foreground first:mt-0">{children}</h3>
  ),
  p: ({ children }) => <p className="text-sm leading-relaxed text-foreground">{children}</p>,
  ul: ({ children }) => (
    <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed text-foreground">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal space-y-1 pl-5 text-sm leading-relaxed text-foreground">{children}</ol>
  ),
  li: ({ children }) => <li className="text-sm leading-relaxed">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-border pl-3 text-sm italic text-muted-foreground">
      {children}
    </blockquote>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="break-words text-primary underline underline-offset-2 hover:no-underline"
    >
      {children}
    </a>
  ),
  code: ({ className, children }) => {
    const isBlock = typeof className === 'string' && className.includes('language-');
    if (isBlock) {
      return <code className={cn('font-mono text-xs', className)}>{children}</code>;
    }
    return (
      <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em] text-foreground">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs leading-relaxed">{children}</pre>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  th: ({ children, style }) => (
    <th style={style} className="border border-border px-2 py-1 text-left font-medium">
      {children}
    </th>
  ),
  td: ({ children, style }) => (
    <td style={style} className="border border-border px-2 py-1 align-top">
      {children}
    </td>
  ),
  img: ({ src, alt, title }) => (
    <img src={src} alt={alt} title={title} className="max-w-full rounded-md" />
  ),
  hr: () => <hr className="my-3 border-border" />,
};

const MarkdownContent = ({ content }) => (
  <div className="space-y-3 break-words text-sm leading-relaxed text-foreground [overflow-wrap:anywhere]">
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>
      {content || ''}
    </ReactMarkdown>
  </div>
);

export default React.memo(MarkdownContent);
