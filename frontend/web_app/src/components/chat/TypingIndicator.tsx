"use client";

interface TypingIndicatorProps {
  typingUserNames: string[];
}

export function TypingIndicator({ typingUserNames }: TypingIndicatorProps) {
  if (typingUserNames.length === 0) return null;

  const label =
    typingUserNames.length === 1
      ? `${typingUserNames[0]} is typing...`
      : typingUserNames.length === 2
        ? `${typingUserNames[0]} and ${typingUserNames[1]} are typing...`
        : `${typingUserNames[0]} and ${typingUserNames.length - 1} others are typing...`;

  return (
    <div className="flex items-center gap-2 px-4 py-1.5">
      <div className="flex items-center gap-1">
        <span className="h-1.5 w-1.5 rounded-full bg-text-faint animate-bounce [animation-delay:0ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-text-faint animate-bounce [animation-delay:150ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-text-faint animate-bounce [animation-delay:300ms]" />
      </div>
      <span className="text-[10px] text-text-muted italic">{label}</span>
    </div>
  );
}
