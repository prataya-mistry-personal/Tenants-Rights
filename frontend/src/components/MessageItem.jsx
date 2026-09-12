import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Scale } from 'lucide-react';
import Citations from './Citations';

export default function MessageItem({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <div className={`avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? <User size={18} /> : <Scale size={18} />}
      </div>

      <div className="message-bubble">
        {isUser ? (
          <div>{message.content}</div>
        ) : (
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>

            {message.citations && message.citations.length > 0 && (
              <Citations citations={message.citations} />
            )}

            {message.disclaimer && (
              <div style={{ marginTop: '0.85rem', paddingTop: '0.6rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.75rem', color: '#64748B', fontStyle: 'italic' }}>
                {message.disclaimer}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
