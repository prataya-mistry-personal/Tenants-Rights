import React, { useState, useRef, useEffect } from 'react';
import { Send, Scale, AlertTriangle } from 'lucide-react';
import MessageItem from './MessageItem';
import SuggestionChips from './SuggestionChips';
import { askQuestion } from '../api/client';

export default function ChatBox({ jurisdiction }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        '**Namaste! I am your Indian Tenant Rights Legal Assistant.**\n\n' +
        'I provide grounded legal information under the **Karnataka Rent Act 1999**, **Model Tenancy Act 2021**, **Delhi Rent Act 1958**, **Transfer of Property Act 1882**, and Indian court precedents.\n\n' +
        'Ask any question regarding security deposits, unlawful eviction, notice periods, or maintenance issues.',
      citations: [],
      disclaimer: null,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (questionText) => {
    const queryToSend = (questionText || input).trim();
    if (!queryToSend || loading) return;

    setError(null);
    setInput('');

    // Add user message
    const userMessage = { role: 'user', content: queryToSend };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const data = await askQuestion(queryToSend, jurisdiction);

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations || [],
        disclaimer: data.disclaimer || null,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Query failed:', err);
      setError(err.message || 'Failed to connect to the legal backend.');
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            `⚠️ **Error connecting to assistant:** ${err.message || 'Unable to retrieve answer.'}\n\n` +
            'Please ensure the FastAPI backend is running (`uvicorn src.backend.main:app --port 8000`).',
          citations: [],
          disclaimer: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSend();
  };

  return (
    <div className="chat-container">
      <div className="messages-list">
        {messages.map((msg, idx) => (
          <MessageItem key={idx} message={msg} />
        ))}

        {loading && (
          <div className="message-row assistant">
            <div className="avatar assistant">
              <Scale size={18} />
            </div>
            <div className="message-bubble">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '0.85rem', color: '#94A3B8' }}>
                  Retrieving statutes & analyzing legal precedents...
                </span>
                <div className="loading-dots">
                  <div className="dot"></div>
                  <div className="dot"></div>
                  <div className="dot"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {messages.length <= 2 && (
        <SuggestionChips onSelect={(text) => handleSend(text)} />
      )}

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#EF4444', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
          <AlertTriangle size={14} />
          <span>{error}</span>
        </div>
      )}

      <div className="input-section">
        <form className="input-form" onSubmit={handleSubmit}>
          <input
            id="tenant-question-input"
            type="text"
            className="chat-input"
            placeholder={`Ask a question under ${jurisdiction || 'All India'} tenancy law...`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            id="send-question-btn"
            type="submit"
            className="send-btn"
            disabled={!input.trim() || loading}
            title="Send query"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
