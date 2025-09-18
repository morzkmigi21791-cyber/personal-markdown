import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Cookies from 'js-cookie';
import Header from './components/Header';
import Welcome from './components/Welcome';
import LoginModal from './components/LoginModal';
import RegisterModal from './components/RegisterModal';
import ProfileDropdown from './components/ProfileDropdown';
import './App.css';

// Настройка axios для работы с куки
axios.defaults.withCredentials = true;

function App() {
  const [user, setUser] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [loading, setLoading] = useState(true);

  // Проверяем аутентификацию при загрузке приложения
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Получаем токен из localStorage
      const token = localStorage.getItem('access_token');
      if (token) {
        // Устанавливаем токен в заголовок для этого запроса
        const response = await axios.get('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.data) {
          setUser(response.data);
        }
      }
    } catch (error) {
      console.log('Пользователь не аутентифицирован');
      // Удаляем недействительный токен
      localStorage.removeItem('access_token');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', {
        email,
        password
      });
      
      if (response.data.access_token) {
        // Сохраняем токен в localStorage
        localStorage.setItem('access_token', response.data.access_token);
        setUser(response.data.user);
        setShowLoginModal(false);
        return { success: true };
      }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Ошибка входа' 
      };
    }
  };

  const handleRegister = async (email, password, confirmPassword, nickname) => {
    try {
      const response = await axios.post('/api/auth/register', {
        email,
        password,
        confirm_password: confirmPassword,
        nickname
      });
      
      if (response.data.access_token) {
        // Сохраняем токен в localStorage
        localStorage.setItem('access_token', response.data.access_token);
        setUser(response.data.user);
        setShowRegisterModal(false);
        return { success: true };
      }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Ошибка регистрации' 
      };
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post('/api/auth/logout');
    } catch (error) {
      console.error('Ошибка при выходе:', error);
    } finally {
      // Удаляем токен из localStorage
      localStorage.removeItem('access_token');
      setUser(null);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header 
        user={user}
        onLoginClick={() => setShowLoginModal(true)}
        onRegisterClick={() => setShowRegisterModal(true)}
        onLogout={handleLogout}
      />
      
      <main className="main-content">
        <Welcome />
      </main>

      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLogin={handleLogin}
          onSwitchToRegister={() => {
            setShowLoginModal(false);
            setShowRegisterModal(true);
          }}
        />
      )}

      {showRegisterModal && (
        <RegisterModal
          onClose={() => setShowRegisterModal(false)}
          onRegister={handleRegister}
          onSwitchToLogin={() => {
            setShowRegisterModal(false);
            setShowLoginModal(true);
          }}
        />
      )}
    </div>
  );
}

export default App;

