import React, { useState, useEffect, useRef } from 'react';
import api from '../api'; // Используем настроенный axios инстанс
import './ChatWidget.css';

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const messagesEndRef = useRef(null);

  // Инициализация сессии и приветствия
  useEffect(() => {
    let sid = localStorage.getItem('chat_session_id');
    if (!sid) {
      sid = 'sess_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('chat_session_id', sid);
    }
    setSessionId(sid);

    // Приветственное сообщение, если история пуста
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        sender: 'bot',
        message: 'Привет! Я AI-помощник SiteOfSites. Готов ответить на вопросы по хостингу, настройке профиля или загрузке сайтов.'
      }]);
    }
  }, []);

  // Загрузка истории при открытии
  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen]);

  // Автоскролл вниз
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const token = localStorage.getItem('access_token');
      // Если токена нет, используем session_id в параметрах (нужна поддержка на бэке)
      // В текущей реализации бэкенда мы передаем session_id в query params
      const config = token ? { headers: { 'Authorization': `Bearer ${token}` } } : {};
      
      const response = await api.get(`/api/chat/history?session_id=${sessionId}`, config);
      
      if (response.data && response.data.length > 0) {
        setMessages(response.data);
      }
    } catch (error) {
      console.error("Ошибка загрузки истории чата:", error);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsgText = input;
    setInput('');
    setLoading(true);

    // Оптимистичное добавление сообщения
    const tempId = Date.now();
    setMessages(prev => [...prev, { id: tempId, sender: 'user', message: userMsgText }]);

    try {
      const token = localStorage.getItem('access_token');
      const config = token ? { headers: { 'Authorization': `Bearer ${token}` } } : {};
      
      const response = await api.post('/api/chat/send', {
        message: userMsgText,
        session_id: sessionId
      }, config);

      // Обновляем список сообщений ответом от сервера (там и наш месседж, и ответ бота)
      // Но проще просто добавить ответ бота, так как наш уже там
      if (response.data) {
        setMessages(prev => [...prev, response.data]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        sender: 'bot', 
        message: 'Ошибка соединения. Попробуйте позже.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-widget-container">
      {!isOpen && (
        <button className="chat-toggle-btn" onClick={() => setIsOpen(true)}>
          💬
        </button>
      )}

      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <h3>Поддержка SiteOfSites</h3>
            <button className="close-chat" onClick={() => setIsOpen(false)}>×</button>
          </div>
          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.sender}`}>
                {msg.message}
              </div>
            ))}
            {loading && <div className="message bot">...</div>}
            <div ref={messagesEndRef} />
          </div>
          <form className="chat-input-area" onSubmit={handleSend}>
            <input 
              type="text" 
              value={input} 
              onChange={(e) => setInput(e.target.value)} 
              placeholder="Задайте вопрос..." 
              disabled={loading}
            />
            <button type="submit" className="send-btn" disabled={loading || !input.trim()}>➤</button>
          </form>
        </div>
      )}
    </div>
  );
};

export default ChatWidget;