import React, { useState, useRef, useEffect } from 'react';
import logger from '../../utils/logger';
import { API_ENDPOINTS } from '../../config/api.config';
import '../../style/ChatbotWidget.css';

const ChatbotWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            text: "👋 Chào bạn! Mình là trợ lý ảo AI. Mình có thể giúp bạn tìm quần áo, check size hoặc phối đồ. Bạn cần tìm gì hôm nay?",
            sender: 'bot',
            isWelcome: true
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = { text: input, sender: 'user' };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // Prepare history for API (excluding current message)
            // Filter out welcome message if needed, or map correctly
            const history = messages
                .filter(msg => !msg.isWelcome)
                .map(msg => ({
                    role: msg.sender === 'user' ? 'user' : 'model', // Map 'bot' to 'model' if Gemini/standard
                    parts: [{ text: msg.text }]
                }));

            // Call API
            const response = await fetch(`${API_ENDPOINTS.CHATBOT.CHAT}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Add Authorization header if your API requires it for guest/user
                    'Authorization': `Bearer ${localStorage.getItem('token')}` // Optional: if auth is needed
                },
                body: JSON.stringify({
                    message: userMessage.text,
                    history: [] // Passing empty history for now as per simple demo, OR pass 'history' variable if backend supports it context-aware
                    // Note: If backend expects specific "history" format, ensure it matches.
                    // For now, assuming backend wants simple message or handle history internally/statelessly.
                    // The prompt said "history" is an array, let's include it if the backend supports context. 
                    // Based on "basic" chatbot, usually it's persistent or session-based.
                    // Let's send history if the API spec usually demands it for stateless RAG.
                })
            });

            const data = await response.json();

            if (response.ok) {
                const botMessage = { text: data.reply, sender: 'bot' }; // Adjust 'reply' key based on actual API response
                setMessages(prev => [...prev, botMessage]);
            } else {
                throw new Error('Failed to get response');
            }
        } catch (error) {
            logger.error('Chatbot error:', error);
            const errorMessage = { text: "Xin lỗi, mình đang gặp chút sự cố kết nối. Bạn thử lại sau nhé!", sender: 'bot' };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chatbot-widget">
            {/* Chat Window */}
            {isOpen && (
                <div className="chatbot-window">
                    <div className="chatbot-header">
                        <div className="chatbot-title">
                            <div className="bot-avatar-small">
                                🤖
                            </div>
                            <div>
                                <h3>Trợ lý StyleX</h3>
                                <div className="chatbot-status">
                                    <span className="status-dot"></span> Sẵn sàng tư vấn
                                </div>
                            </div>
                        </div>
                        <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
                    </div>

                    <div className="chatbot-messages">
                        {messages.map((msg, index) => (
                            <div key={index} className={`message ${msg.sender} ${msg.isWelcome ? 'welcome' : ''}`}>
                                {msg.text}
                            </div>
                        ))}
                        {isLoading && (
                            <div className="typing-indicator">
                                <span className="typing-dot"></span>
                                <span className="typing-dot"></span>
                                <span className="typing-dot"></span>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <form className="chatbot-input-area" onSubmit={handleSendMessage}>
                        <input
                            type="text"
                            className="chatbot-input"
                            placeholder="Nhập câu hỏi..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={isLoading}
                        />
                        <button type="submit" className="send-btn" disabled={isLoading || !input.trim()}>
                            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
                            </svg>
                        </button>
                    </form>
                </div>
            )}

            {/* Floating Toggle Button */}
            {!isOpen && (
                <button className="chatbot-toggle" onClick={() => setIsOpen(true)}>
                    <svg viewBox="0 0 24 24">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
                    </svg>
                </button>
            )}
        </div>
    );
};

export default ChatbotWidget;
