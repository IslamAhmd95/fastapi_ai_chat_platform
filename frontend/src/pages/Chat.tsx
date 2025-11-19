import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { authAPI, chatAPI } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import ChatMessage from '@/components/ChatMessage';
import { Loader2, LogOut, Send } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

const Chat = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState<string>('');
  const [models, setModels] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const bcRef = useRef<BroadcastChannel | null>(null);
  const [waiting, setWaiting] = useState(false);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => scrollToBottom(), [messages]);

  // Load platforms
  useEffect(() => {
    async function fetchPlatforms() {
      try {
        const platformList = await chatAPI.getPlatforms();
        setModels(platformList);
        if (platformList.length > 0) setModel(platformList[0]);
      } catch {
        toast.error("Failed to load AI models");
      }
    }
    fetchPlatforms();
  }, []);

  // Load chat history when model changes
  useEffect(() => {
    if (!model) return;

    setWaiting(false);

    async function fetchHistory() {
      try {
        const history = await chatAPI.getChatHistory(model);
        const formatted: Message[] = [];

        history.forEach((h: any) => {
          formatted.push({ role: 'user', content: h.prompt, created_at: h.created_at });
          formatted.push({ role: 'assistant', content: h.response, created_at: h.created_at });
        });

        setMessages(formatted);
      } catch {
        toast.error("Failed to load chat history");
      }
    }

    fetchHistory();
  }, [model]);

  // WebSocket + BroadcastChannel setup
  useEffect(() => {
    if (!model) return;

    // Close previous WS if exists
    wsRef.current?.close();

    const token = localStorage.getItem("auth_token");
    if (!token) return;

    // ---- SETUP WEBSOCKET ----
    const ws = chatAPI.connectWS(token);
    wsRef.current = ws;

    ws.onopen = () => console.log("WebSocket connected");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.error) {
        toast.error(data.error);
        setWaiting(false);  
        return;
      }

      const aiMessage: Message = {
        role: "assistant",
        content: data.response,
        created_at: data.created_at,
      };

      setWaiting(false);

      setMessages((prev) => [...prev, aiMessage]);

      // Broadcast assistant message
      bcRef.current?.postMessage(aiMessage);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setWaiting(false);  // <-- FIX
    };

    ws.onerror = (err) => console.error("WebSocket error:", err);

    // ---- SETUP BROADCAST CHANNEL ----
    const bc = new BroadcastChannel(model);
    bcRef.current = bc;

    // LISTEN to other tabs
    bc.onmessage = (event) => {
      const msg = event.data;
      // Add to chat
      setMessages((prev) => [...prev, msg]);
    };

    // Cleanup on model change/unmount
    return () => {
      ws.close();
      bc.close(); 
    };

  }, [model]);



  const handleLogout = () => {
    logout();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return toast.error("Please enter a message");

    const nowIso = new Date().toISOString();
    const userMessage: Message = { role: "user", content: input, created_at: nowIso };
    setMessages((prev) => [...prev, userMessage]);

    // Broadcast user message to other tabs
    bcRef.current?.postMessage(userMessage);

    setInput("");
    setWaiting(true);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ model_name: model, prompt: input }));
    } else {
      toast.error("WebSocket not connected");
      setWaiting(false);
    }
  };


  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-foreground">AI Chat</h1>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger className="w-[140px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                {models.map(m => (
                  <SelectItem key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" /> Logout
          </Button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <div className="bg-primary/10 rounded-full p-4 mb-4"><Send className="h-8 w-8 text-primary" /></div>
              <h2 className="text-2xl font-semibold mb-2">Start a conversation</h2>
              <p className="text-muted-foreground">Send a message to begin chatting with AI</p>
            </div>
          ) : messages.map((m, i) => (
            <ChatMessage key={i} role={m.role} content={m.content} created_at={m.created_at} />
          ))}
          {waiting && (
            <div className="text-sm text-muted-foreground px-2 py-1">
              AI is typing...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-card shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="flex gap-2 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Type your message..."
              className="flex-1 min-h-[48px] max-h-[200px] p-3 rounded-md border bg-background text-foreground resize-none"
            />

            <Button type="submit" size="icon" disabled={waiting}>
              {waiting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>

        </div>
      </div>
    </div>
  );
};

export default Chat;
