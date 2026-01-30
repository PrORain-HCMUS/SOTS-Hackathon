import { Component, createSignal, For, Show, createEffect } from 'solid-js';
import { 
  OcX2, 
  OcSmiley2,
  OcKebabhorizontal2 
} from 'solid-icons/oc';
import { FaSolidPaperPlane, FaRegularMessage } from 'solid-icons/fa'

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
      text: "Hello! I'm your agricultural AI assistant. How can I help you today?",
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = createSignal('');
  const [isTyping, setIsTyping] = createSignal(false);
  let messageContainer: HTMLDivElement | undefined;

  // Auto-scroll to bottom
  createEffect(() => {
    messages();
    if (messageContainer) {
      messageContainer.scrollTop = messageContainer.scrollHeight;
    }
  });

  const sendMessage = () => {
    const text = inputText().trim();
    if (!text) return;

    const userMessage: Message = {
      id: Math.random().toString(36),
      text,
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setInputText('');

    setIsTyping(true);
    setTimeout(() => {
      const botMessage: Message = {
        id: Math.random().toString(36),
        text: `Analysis complete for: "${text}". The local soil moisture in An Giang is currently optimal at 68%.`,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
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
    <div class="fixed bottom-6 right-6 z-9999 font-sans">
      {/* Chat Window */}
      <Show when={isOpen()}>
        <div class="absolute bottom-20 right-0 w-100 h-150 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl rounded-3xl shadow-[0_20px_50px_rgba(0,0,0,0.15)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.4)] flex flex-col border border-slate-200/50 dark:border-slate-700/50 overflow-hidden animate-in fade-in zoom-in-95 duration-300">
          
          {/* Header */}
          <div class="p-5 bg-linear-to-br from-blue-600 to-indigo-700 text-white flex items-center justify-between shadow-lg">
            <div class="flex items-center gap-3">
              <div class="relative">
                <div class="w-11 h-11 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center border border-white/30">
                  <FaRegularMessage size={24} />
                </div>
                <span class="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-400 border-2 border-indigo-700 rounded-full"></span>
              </div>
              <div>
                <h3 class="font-bold text-base leading-tight">AgriSmart AI</h3>
                <div class="flex items-center gap-1.5">
                  <span class="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                  <p class="text-[11px] font-medium opacity-80 uppercase tracking-wider">System Online</p>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1">
              <button class="p-2 hover:bg-white/10 rounded-xl transition-colors"><OcKebabhorizontal2 size={18} /></button>
              <button onClick={() => setIsOpen(false)} class="p-2 hover:bg-white/10 rounded-xl transition-colors"><OcX2 size={18} /></button>
            </div>
          </div>

          {/* Messages Area */}
          <div 
            ref={messageContainer}
            class="flex-1 overflow-y-auto p-5 space-y-6 scroll-smooth scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700"
          >
            <For each={messages()}>
              {(msg) => (
                <div class={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2`}>
                  <div class={`relative group max-w-[85%] px-4 py-3 shadow-sm ${
                    msg.sender === 'user' 
                      ? 'bg-blue-600 text-white rounded-2xl rounded-tr-none' 
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-2xl rounded-tl-none border border-slate-200/50 dark:border-slate-700/50'
                  }`}>
                    <p class="text-sm leading-relaxed">{msg.text}</p>
                    <span class={`text-[10px] mt-1.5 block font-medium opacity-60 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              )}
            </For>

            {/* Typing Indicator */}
            <Show when={isTyping()}>
              <div class="flex justify-start animate-pulse">
                <div class="bg-slate-100 dark:bg-slate-800 rounded-2xl px-4 py-3 flex gap-1">
                  <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                  <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]"></div>
                  <div class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]"></div>
                </div>
              </div>
            </Show>
          </div>

          {/* Input Area */}
          <div class="p-4 bg-slate-50/50 dark:bg-slate-900/50 border-t border-slate-200 dark:border-slate-800 backdrop-blur-sm">
            <div class="relative flex items-end gap-2 bg-white dark:bg-slate-800 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all">
              <button class="p-2 text-slate-400 hover:text-blue-500 transition-colors">
                <OcSmiley2 size={20} />
              </button>
              <textarea
                rows="1"
                value={inputText()}
                onInput={(e) => setInputText(e.currentTarget.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your agricultural query..."
                class="flex-1 max-h-32 py-2 px-1 bg-transparent text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none resize-none"
              />
              <button
                onClick={sendMessage}
                disabled={!inputText().trim()}
                class="group bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 dark:disabled:bg-slate-700 text-white p-2.5 rounded-xl transition-all active:scale-95"
              >
                <FaSolidPaperPlane size={18} class="group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </Show>

      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen())}
        class={`relative w-16 h-16 rounded-2xl shadow-2xl transition-all duration-500 flex items-center justify-center group active:scale-90 ${
          isOpen() 
            ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 rotate-90' 
            : 'bg-linear-to-br from-blue-500 to-indigo-600 text-white hover:shadow-blue-500/40 hover:-translate-y-1'
        }`}
      >
        <Show when={isOpen()} fallback={<FaRegularMessage size={28} />}>
          <OcX2 size={28} />
        </Show>
        
        <Show when={!isOpen()}>
          <span class="absolute -top-1 -right-1 flex h-5 w-5">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-5 w-5 bg-red-500 items-center justify-center text-[10px] font-bold">1</span>
          </span>
        </Show>
      </button>
    </div>
  );
};

export default FloatingChatbot;