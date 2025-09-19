import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Cookies from 'js-cookie';
import Header from './components/Header';
import Welcome from './components/Welcome';
import LoginModal from './components/LoginModal';
import RegisterModal from './components/RegisterModal';
import ProfileDropdown from './components/ProfileDropdown';
import SearchBar from './components/SearchBar';
import UserProfilePage from './pages/UserProfilePage';
import ProfileSettingsPage from './pages/ProfileSettingsPage';
import './App.css';

// Настройка axios для работы с куки
axios.defaults.withCredentials = true;

function AppContent() {
  const [user, setUser] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

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

  const handleUserSelect = (selectedUser) => {
    navigate(`/profile/${selectedUser.unique_id}`);
  };

  const handleProfileUpdate = (updatedUser) => {
    setUser(updatedUser);
  };

  const handleProfileClick = () => {
    if (user) {
      navigate(`/profile/${user.unique_id}`);
    }
  };

  const handleSettingsClick = () => {
    navigate('/settings');
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
        onProfileClick={handleProfileClick}
        onSettingsClick={handleSettingsClick}
        onUserSelect={handleUserSelect}
      />
      
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="/profile/:uniqueId" element={<UserProfilePage user={user} />} />
          <Route path="/settings" element={<ProfileSettingsPage user={user} onUpdate={handleProfileUpdate} />} />
        </Routes>
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

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;

