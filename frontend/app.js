const { useState, useRef, useEffect } = React;

const API_URL = "http://localhost:8000/chat";

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Hi! I'm **Basil**, your personal chef assistant. Tell me what ingredients you have and I'll suggest recipes — or ask me anything cooking-related!",
};

function Message({ msg }) {
  const isUser = msg.role === "user";
  // Parse markdown for assistant messages so recipes render with headers/bullets
  const html = isUser ? null : marked.parse(msg.content);

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>
      {!isUser && <div className="avatar">🌿</div>}
      <div
        className={`bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}
        {...(!isUser && { dangerouslySetInnerHTML: { __html: html } })}
      >
        {isUser ? msg.content : null}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message-row assistant-row">
      <div className="avatar">🌿</div>
      <div className="bubble assistant-bubble typing">
        <span /><span /><span />
      </div>
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function handleInput(e) {
    e.target.style.height = "auto";
    e.target.style.height = e.target.scrollHeight + "px";
  }

  function resetTextarea() {
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  function clearChat() {
    setMessages([WELCOME_MESSAGE]);
    setInput("");
    resetTextarea();
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text };
    // Build history excluding the static welcome message
    const history = [...messages.slice(1), userMsg];

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    resetTextarea();
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, something went wrong: ${err.message}. Is the backend running?`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="app">
      <header>
        <span className="logo">🌿</span>
        <h1>Basil</h1>
        <p>AI Recipe Assistant</p>
        <button className="clear-btn" onClick={clearChat} disabled={messages.length <= 1}>
          Clear
        </button>
      </header>

      <div className="chat-window">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div className="input-area">
        <textarea
          ref={textareaRef}
          rows={1}
          placeholder="Tell me what ingredients you have…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
