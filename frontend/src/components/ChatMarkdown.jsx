import React, { useState } from 'react';
import { Copy, Check, ExternalLink, Code } from 'lucide-react';

/**
 * Syntax highlighter helper for code blocks.
 * Formats keywords, strings, comments, numbers, and builtins into styled spans.
 */
function highlightCodeLine(line, lang = '') {
  if (!line) return <span>&nbsp;</span>;

  // Simple token matching without heavyweight libraries
  const tokens = [];
  let remaining = line;
  let keyIdx = 0;

  // Regex patterns
  const commentRegex = lang === 'python' || lang === 'bash' || lang === 'sh'
    ? /(#.*$)/
    : /(\/\/.*$|\/\*.*?\*\/)/;

  const commentMatch = remaining.match(commentRegex);
  let commentStr = null;
  let codePart = remaining;
  if (commentMatch) {
    const idx = commentMatch.index;
    codePart = remaining.slice(0, idx);
    commentStr = remaining.slice(idx);
  }

  // Tokenize codePart: strings, keywords, numbers, identifiers
  const tokenRegex = /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\b(?:def|class|return|import|from|as|if|elif|else|for|while|try|except|finally|with|lambda|yield|async|await|const|let|var|function|new|switch|case|break|continue|default|typeof|instanceof|interface|type|public|private|static|SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|JOIN|AND|OR|NOT|IN|GROUP|BY|ORDER)\b|\b(?:True|False|None|true|false|null|undefined|NaN|self|this)\b|\b\d+(?:\.\d+)?\b|[=+\-*/%&|<>!^~:]+|[a-zA-Z_]\w*(?=\s*\())/g;

  let lastIndex = 0;
  let match;

  while ((match = tokenRegex.exec(codePart)) !== null) {
    if (match.index > lastIndex) {
      tokens.push(
        <span key={`text-${keyIdx++}`} className="text-gray-100">
          {codePart.slice(lastIndex, match.index)}
        </span>
      );
    }

    const val = match[0];
    let colorClass = 'text-gray-100';

    if (val.startsWith('"') || val.startsWith("'") || val.startsWith('`')) {
      colorClass = 'text-emerald-300'; // Strings
    } else if (/^(def|class|return|import|from|as|if|elif|else|for|while|try|except|finally|with|lambda|yield|async|await|const|let|var|function|new|switch|case|break|continue|default|typeof|instanceof|interface|type|public|private|static|SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|JOIN|AND|OR|NOT|IN|GROUP|BY|ORDER)$/.test(val)) {
      colorClass = 'text-rose-400 font-semibold'; // Keywords
    } else if (/^(True|False|None|true|false|null|undefined|NaN|self|this)$/.test(val)) {
      colorClass = 'text-amber-300 font-semibold'; // Booleans / special
    } else if (/^\d+(?:\.\d+)?$/.test(val)) {
      colorClass = 'text-sky-300'; // Numbers
    } else if (/^[=+\-*/%&|<>!^~:]+$/.test(val)) {
      colorClass = 'text-pink-300'; // Operators
    } else if (codePart.slice(match.index + val.length).trim().startsWith('(')) {
      colorClass = 'text-yellow-200'; // Function calls
    }

    tokens.push(
      <span key={`token-${keyIdx++}`} className={colorClass}>
        {val}
      </span>
    );
    lastIndex = tokenRegex.lastIndex;
  }

  if (lastIndex < codePart.length) {
    tokens.push(
      <span key={`tail-${keyIdx++}`} className="text-gray-100">
        {codePart.slice(lastIndex)}
      </span>
    );
  }

  if (commentStr) {
    tokens.push(
      <span key={`comment-${keyIdx++}`} className="text-gray-400 italic">
        {commentStr}
      </span>
    );
  }

  return <>{tokens}</>;
}

function CodeBlock({ language, code }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard?.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = code.replace(/\n$/, '').split('\n');

  return (
    <div className="my-3 rounded-2xl overflow-hidden border border-gray-800 bg-gray-950 text-gray-100 shadow-md">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-gray-900 border-b border-gray-800 text-[11px] text-gray-400">
        <div className="flex items-center space-x-1.5 font-mono">
          <Code className="w-3.5 h-3.5 text-brand-400" />
          <span className="uppercase text-[10px] font-bold text-gray-300">
            {language || 'code'}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1 px-2 py-0.5 rounded-md hover:bg-gray-800 text-gray-300 hover:text-white transition-colors"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] text-emerald-400 font-semibold">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span className="text-[10px]">Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-3.5 text-[11px] font-mono overflow-x-auto leading-relaxed select-text">
        <code>
          {lines.map((line, idx) => (
            <div key={idx} className="table-row">
              <span className="table-cell select-none pr-3 text-gray-600 text-right text-[10px]">
                {idx + 1}
              </span>
              <span className="table-cell">{highlightCodeLine(line, language)}</span>
            </div>
          ))}
        </code>
      </pre>
    </div>
  );
}

/**
 * Parses inline formatting: bold, italic, code, links, strikethrough.
 */
function renderInlineFormatting(text) {
  if (!text) return null;

  // Split tokens: links [label](url), inline code `code`, bold ***, **, *, ~~
  const tokenRegex = /(\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|`([^`]+)`|\*\*\*([^*]+)\*\*\*|\*\*([^*]+)\*\*|\*([^*]+)\*|__([^_]+)__|~~([^~]+)~~)/g;

  const parts = [];
  let lastIndex = 0;
  let match;
  let pIdx = 0;

  while ((match = tokenRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    if (match[2] && match[3]) {
      // Link [label](url)
      parts.push(
        <a
          key={`link-${pIdx++}`}
          href={match[3]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-800 hover:text-brand-900 underline font-semibold inline-flex items-center space-x-0.5"
        >
          <span>{match[2]}</span>
          <ExternalLink className="w-2.5 h-2.5 inline ml-0.5 opacity-70" />
        </a>
      );
    } else if (match[4]) {
      // Inline code `code`
      parts.push(
        <code
          key={`code-${pIdx++}`}
          className="px-1.5 py-0.5 rounded-md bg-white border border-warm-border text-brand-900 font-mono text-[11px] font-semibold"
        >
          {match[4]}
        </code>
      );
    } else if (match[5]) {
      // Bold + Italic ***text***
      parts.push(
        <strong key={`bi-${pIdx++}`} className="font-bold text-gray-900 italic">
          {match[5]}
        </strong>
      );
    } else if (match[6] || match[8]) {
      // Bold **text** or __text__
      parts.push(
        <strong key={`b-${pIdx++}`} className="font-bold text-gray-900">
          {match[6] || match[8]}
        </strong>
      );
    } else if (match[7]) {
      // Italic *text*
      parts.push(
        <em key={`i-${pIdx++}`} className="italic text-gray-800">
          {match[7]}
        </em>
      );
    } else if (match[9]) {
      // Strikethrough ~~text~~
      parts.push(
        <del key={`del-${pIdx++}`} className="line-through text-gray-500">
          {match[9]}
        </del>
      );
    }

    lastIndex = tokenRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

/**
 * Main ChatMarkdown component.
 * Converts markdown text into beautifully formatted React elements.
 */
export default function ChatMarkdown({ content }) {
  if (!content) return null;

  // Step 1: Pre-process fenced code blocks to extract them safely
  const blocks = [];
  const lines = content.split('\n');
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 1. Fenced Code Block
    if (line.trim().startsWith('```')) {
      const language = line.trim().slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      blocks.push({
        type: 'code',
        language: language || 'text',
        code: codeLines.join('\n'),
      });
      continue;
    }

    // 2. Horizontal Rule (--- or ***)
    if (/^(?:---|\*\*\*|___)\s*$/.test(line.trim())) {
      blocks.push({ type: 'hr' });
      i++;
      continue;
    }

    // 3. Headings (#, ##, ###, ####)
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      blocks.push({
        type: 'heading',
        level: headingMatch[1].length,
        text: headingMatch[2].trim(),
      });
      i++;
      continue;
    }

    // 4. Blockquotes (> ...)
    if (line.trim().startsWith('>')) {
      const quoteLines = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ''));
        i++;
      }
      blocks.push({
        type: 'blockquote',
        text: quoteLines.join(' '),
      });
      continue;
    }

    // 5. Markdown Tables (| header | ... |)
    if (
      line.trim().startsWith('|') &&
      i + 1 < lines.length &&
      lines[i + 1].trim().startsWith('|') &&
      /^[|\s-:]+$/.test(lines[i + 1].trim())
    ) {
      const headerRow = line
        .trim()
        .split('|')
        .slice(1, -1)
        .map((cell) => cell.trim());

      i += 2; // skip header and separator row
      const dataRows = [];

      while (i < lines.length && lines[i].trim().startsWith('|')) {
        const row = lines[i]
          .trim()
          .split('|')
          .slice(1, -1)
          .map((cell) => cell.trim());
        dataRows.push(row);
        i++;
      }

      blocks.push({
        type: 'table',
        headers: headerRow,
        rows: dataRows,
      });
      continue;
    }

    // 6. Unordered List Items (- or * or +)
    if (/^\s*[-*+]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*+]\s+/, '').trim());
        i++;
      }
      blocks.push({
        type: 'ul',
        items,
      });
      continue;
    }

    // 7. Ordered List Items (1. 2. 3.)
    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        const itemText = lines[i].replace(/^\s*\d+\.\s+/, '').trim();
        items.push(itemText);
        i++;
      }
      blocks.push({
        type: 'ol',
        items,
      });
      continue;
    }

    // 8. Empty lines
    if (!line.trim()) {
      i++;
      continue;
    }

    // 9. Standard Paragraph (gather consecutive non-empty non-special lines)
    const paraLines = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith('```') &&
      !lines[i].trim().startsWith('#') &&
      !lines[i].trim().startsWith('>') &&
      !/^\s*[-*+]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i]) &&
      !(lines[i].trim().startsWith('|') && i + 1 < lines.length && /^[|\s-:]+$/.test(lines[i + 1]?.trim() || ''))
    ) {
      paraLines.push(lines[i]);
      i++;
    }

    if (paraLines.length > 0) {
      blocks.push({
        type: 'paragraph',
        text: paraLines.join('\n'),
      });
    }
  }

  return (
    <div className="space-y-2.5 text-xs text-gray-800 break-words leading-relaxed">
      {blocks.map((block, idx) => {
        switch (block.type) {
          case 'code':
            return (
              <CodeBlock
                key={`code-${idx}`}
                language={block.language}
                code={block.code}
              />
            );

          case 'table':
            return (
              <div
                key={`table-${idx}`}
                className="my-3 overflow-x-auto rounded-2xl border border-warm-border shadow-xs bg-white"
              >
                <table className="min-w-full divide-y divide-warm-border text-left">
                  <thead className="bg-warm-bg text-gray-900 font-bold">
                    <tr>
                      {block.headers.map((h, hIdx) => (
                        <th
                          key={hIdx}
                          className="px-3.5 py-2.5 text-xs uppercase tracking-wider font-bold text-brand-900"
                        >
                          {renderInlineFormatting(h)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-warm-border/60 bg-white">
                    {block.rows.map((row, rIdx) => (
                      <tr
                        key={rIdx}
                        className={rIdx % 2 === 0 ? 'bg-white' : 'bg-warm-bg/40'}
                      >
                        {row.map((cell, cIdx) => (
                          <td
                            key={cIdx}
                            className="px-3.5 py-2 text-xs text-gray-800"
                          >
                            {renderInlineFormatting(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );

          case 'heading': {
            if (block.level === 1) {
              return (
                <h1
                  key={`h-${idx}`}
                  className="text-base font-black text-gray-900 mt-4 mb-2 pb-1 border-b border-warm-border"
                >
                  {renderInlineFormatting(block.text)}
                </h1>
              );
            }
            if (block.level === 2) {
              return (
                <h2
                  key={`h-${idx}`}
                  className="text-sm font-bold text-brand-900 mt-3.5 mb-1.5"
                >
                  {renderInlineFormatting(block.text)}
                </h2>
              );
            }
            if (block.level === 3) {
              return (
                <h3
                  key={`h-${idx}`}
                  className="text-xs font-bold text-gray-900 uppercase tracking-wide mt-2.5 mb-1 text-brand-800"
                >
                  {renderInlineFormatting(block.text)}
                </h3>
              );
            }
            return (
              <h4
                key={`h-${idx}`}
                className="text-xs font-semibold text-gray-900 mt-2 mb-1"
              >
                {renderInlineFormatting(block.text)}
              </h4>
            );
          }

          case 'blockquote':
            return (
              <blockquote
                key={`quote-${idx}`}
                className="border-l-4 border-brand-800 bg-brand-50/50 pl-3.5 py-2 my-2.5 rounded-r-xl text-gray-700 italic text-xs leading-relaxed"
              >
                {renderInlineFormatting(block.text)}
              </blockquote>
            );

          case 'ul':
            return (
              <ul key={`ul-${idx}`} className="space-y-1.5 my-2 pl-1">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="flex items-start space-x-2">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-brand-800 mt-1.5 shrink-0" />
                    <span className="flex-1">{renderInlineFormatting(item)}</span>
                  </li>
                ))}
              </ul>
            );

          case 'ol':
            return (
              <ol key={`ol-${idx}`} className="space-y-1.5 my-2 pl-1">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="flex items-start space-x-2">
                    <span className="font-bold text-brand-800 text-[11px] min-w-[16px] shrink-0">
                      {itemIdx + 1}.
                    </span>
                    <span className="flex-1">{renderInlineFormatting(item)}</span>
                  </li>
                ))}
              </ol>
            );

          case 'hr':
            return <hr key={`hr-${idx}`} className="my-3 border-warm-border" />;

          case 'paragraph':
          default: {
            const subLines = block.text.split('\n');
            return (
              <p key={`p-${idx}`} className="leading-relaxed">
                {subLines.map((sLine, sIdx) => (
                  <React.Fragment key={sIdx}>
                    {renderInlineFormatting(sLine)}
                    {sIdx < subLines.length - 1 && <br />}
                  </React.Fragment>
                ))}
              </p>
            );
          }
        }
      })}
    </div>
  );
}
