import { Component, createSignal, For, Show } from 'solid-js';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const FloatingChatbot: Component = () => {
  const [isOpen, setIsOpen] = createSignal(false);
  const [messages, setMessages] = createSignal<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m your agricultural AI assistant. How can I help you today?',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = createSignal('');
  const [isTyping, setIsTyping] = createSignal(false);

  const sendMessage = () => {
    const text = inputText().trim();
    if (!text) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages([...messages(), userMessage]);
    setInputText('');

    // Simulate bot response
    setIsTyping(true);
    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `You asked: "${text}". This is a demo response. Real AI integration coming soon.`,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages([...messages(), botMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyPress = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Chat Window */}
      <Show when={isOpen()}>
        <div class="fixed bottom-24 right-6 w-96 h-[600px] bg-white dark:bg-space-900 rounded-2xl shadow-2xl flex flex-col animate-slide-in-right z-[9999] border border-space-200 dark:border-space-700">
          {/* Header */}
          <div class="bg-gradient-to-r from-primary-500 to-primary-600 text-white p-4 rounded-t-2xl flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold">AI Assistant</h3>
                <p class="text-xs opacity-90">Smart agriculture helper</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              class="hover:bg-white/20 p-2 rounded-lg transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <For each={messages()}>
              {(message) => (
                <div
                  class={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    class={`max-w-[80%] rounded-2xl px-4 py-2 ${
                      message.sender === 'user'
                        ? 'bg-primary-500 text-white'
                        : 'bg-space-100 dark:bg-space-800 text-space-900 dark:text-white'
                    }`}
                  >
                    <p class="text-sm">{message.text}</p>
                    <p class={`text-xs mt-1 ${message.sender === 'user' ? 'text-primary-100' : 'text-space-500 dark:text-space-400'}`}>
                      {message.timestamp.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              )}
            </For>

            {/* Typing Indicator */}
            <Show when={isTyping()}>
              <div class="flex justify-start">
                <div class="bg-space-100 dark:bg-space-800 rounded-2xl px-4 py-3">
                  <div class="flex gap-1">
                    <div class="w-2 h-2 bg-space-400 dark:bg-space-500 rounded-full animate-bounce" style={{ 'animation-delay': '0ms' }}></div>
                    <div class="w-2 h-2 bg-space-400 dark:bg-space-500 rounded-full animate-bounce" style={{ 'animation-delay': '150ms' }}></div>
                    <div class="w-2 h-2 bg-space-400 dark:bg-space-500 rounded-full animate-bounce" style={{ 'animation-delay': '300ms' }}></div>
                  </div>
                </div>
              </div>
            </Show>
          </div>

          {/* Input */}
          <div class="p-4 border-t border-space-200 dark:border-space-700">
            <div class="flex gap-2">
              <input
                type="text"
                value={inputText()}
                onInput={(e) => setInputText(e.currentTarget.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question..."
                class="flex-1 px-4 py-2 bg-space-50 dark:bg-space-800 border border-space-200 dark:border-space-700 rounded-lg text-space-900 dark:text-white placeholder-space-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={sendMessage}
                class="bg-primary-500 text-white px-4 py-2 rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
                disabled={!inputText().trim()}
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </Show>

      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen())}
        class="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-2xl shadow-2xl hover:shadow-primary-500/50 hover:scale-105 transition-all flex items-center justify-center z-[9999]"
      >
        <Show
          when={isOpen()}
          fallback={
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          }
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </Show>
        
        {/* Notification Badge */}
        <Show when={!isOpen()}>
          <span class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse"></span>
        </Show>
      </button>
    </>
  );
};

export default FloatingChatbot;
