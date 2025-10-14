import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import './ProfileSettingsPage.css';

const ProfileSettingsPage = ({ user, onUpdate }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nickname: '',
    description: '',
    avatar: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (user) {
      setFormData({
        nickname: user.nickname || '',
        description: user.description || '',
        avatar: user.avatar || ''
      });
    }
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await api.put('/api/users/profile', formData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setSuccess('Профиль успешно обновлен');
      if (onUpdate) {
        onUpdate(response.data);
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка обновления профиля');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setFormData(prev => ({
          ...prev,
          avatar: event.target.result
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  if (!user) {
    return (
      <div className="settings-page">
        <div className="settings-error">
          <h2>Доступ запрещен</h2>
          <p>Для доступа к настройкам необходимо войти в систему.</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            На главную
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <div className="settings-container">
        <div className="settings-header">
          <button className="back-btn" onClick={() => navigate(`/profile/${user.unique_id}`)}>
            ← К профилю
          </button>
          <h1>Настройки профиля</h1>
        </div>

        <div className="settings-content">
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form onSubmit={handleSubmit} className="profile-form">
            <h2>Основная информация</h2>
            
            <div className="form-group">
              <label>Никнейм</label>
              <input
                type="text"
                name="nickname"
                value={formData.nickname}
                onChange={handleInputChange}
                required
                maxLength={20}
                placeholder="Введите ваш никнейм"
              />
            </div>

            <div className="form-group">
              <label>Описание</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                placeholder="Расскажите о себе..."
                maxLength={500}
              />
              <small className="char-count">
                {formData.description.length}/500 символов
              </small>
            </div>

            <div className="form-group">
              <label>Аватарка</label>
              <div className="avatar-upload">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarUpload}
                  id="avatar-upload"
                  style={{ display: 'none' }}
                />
                <label htmlFor="avatar-upload" className="avatar-upload-btn">
                  {formData.avatar ? (
                    <img src={formData.avatar} alt="Аватар" />
                  ) : (
                    <div className="default-avatar">
                      {formData.nickname.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <span>Изменить аватар</span>
                </label>
              </div>
              <small className="upload-hint">
                Рекомендуемый размер: 200x200 пикселей
              </small>
            </div>

            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => navigate(`/profile/${user.unique_id}`)}
              >
                Отмена
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Сохранение...' : 'Сохранить изменения'}
              </button>
            </div>
          </form>

          <div className="settings-info">
            <h3>Управление проектами</h3>
            <p>
              Для создания и управления проектами перейдите в ваш профиль.
              Там вы сможете создавать новые проекты, загружать файлы и настраивать хостинг.
            </p>
            <button 
              className="btn btn-primary"
              onClick={() => navigate(`/profile/${user.unique_id}`)}
            >
              Перейти к проектам
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileSettingsPage;