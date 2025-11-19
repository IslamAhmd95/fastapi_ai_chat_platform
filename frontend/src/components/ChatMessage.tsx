import { cn } from '@/lib/utils';
import { formatTimestamp } from '@/lib/formatTimestamp';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

const ChatMessage = ({ role, content, created_at }: ChatMessageProps) => {
  const isUser = role === 'user';
  const time = formatTimestamp(created_at);

  return (
    <div className={cn("flex w-full mb-3", isUser ? "justify-end" : "justify-start")}>
      <div className="flex flex-col max-w-[80%]">
        {/* Message bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 shadow-sm",
            isUser
              ? "bg-[hsl(var(--chat-user-bg))] text-[hsl(var(--chat-user-fg))]"
              : "bg-[hsl(var(--chat-ai-bg))] text-[hsl(var(--chat-ai-fg))]"
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>

        {/* Timestamp */}
        <span className={cn("text-[10px] mt-1 opacity-70", isUser ? "text-right" : "text-left")}>
          {time}
        </span>
      </div>
    </div>
  );
};

export default ChatMessage;
