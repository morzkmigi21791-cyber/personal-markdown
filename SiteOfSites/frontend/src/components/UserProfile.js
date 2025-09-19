import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './UserProfile.css';

const UserProfile = ({ userId, uniqueId, onClose }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (userId || uniqueId) {
      fetchUserProfile();
    }
  }, [userId, uniqueId]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      let response;
      if (uniqueId) {
        response = await axios.get(`/api/users/by-unique-id/${uniqueId}`);
      } else {
        response = await axios.get(`/api/users/${userId}`);
      }
      
      setUser(response.data);
    } catch (err) {
      setError('Пользователь не найден');
      console.error('Ошибка загрузки профиля:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="profile-modal-overlay" onClick={onClose}>
        <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
          <div className="profile-loading">
            <div className="loading-spinner"></div>
            <p>Загрузка профиля...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="profile-modal-overlay" onClick={onClose}>
        <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
          <div className="profile-error">
            <h3>Ошибка</h3>
            <p>{error || 'Пользователь не найден'}</p>
            <button className="btn btn-primary" onClick={onClose}>
              Закрыть
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-modal-overlay" onClick={onClose}>
      <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
        <div className="profile-header">
          <button className="profile-close" onClick={onClose}>
            ×
          </button>
          <h2>Профиль пользователя</h2>
        </div>
        
        <div className="profile-content">
          <div className="profile-main-info">
            <div className="profile-avatar">
              {user.avatar ? (
                <img src={user.avatar} alt={user.nickname} />
              ) : (
                <div className="default-avatar">
                  {user.nickname.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            
            <div className="profile-info">
              <h3 className="profile-nickname">{user.nickname}</h3>
              <p className="profile-id">ID: {user.unique_id}</p>
              <p className="profile-email">{user.email}</p>
              <p className="profile-join-date">
                На сайте с {formatDate(user.created_at)}
              </p>
            </div>
          </div>

          {user.description && (
            <div className="profile-description">
              <h4>О себе</h4>
              <p>{user.description}</p>
            </div>
          )}

          <div className="profile-projects">
            <h4>Проекты ({user.projects.length})</h4>
            {user.projects.length > 0 ? (
              <div className="projects-list">
                {user.projects.map((project) => (
                  <div key={project.id} className="project-item">
                    <h5 className="project-title">{project.title}</h5>
                    {project.description && (
                      <p className="project-description">{project.description}</p>
                    )}
                    <p className="project-date">
                      Создан {formatDate(project.created_at)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-projects">У пользователя пока нет проектов</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;

