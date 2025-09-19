import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './UserProfilePage.css';

const UserProfilePage = ({ user }) => {
  const { uniqueId } = useParams();
  const navigate = useNavigate();
  const [profileUser, setProfileUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUserProfile();
  }, [uniqueId]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`/api/users/by-unique-id/${uniqueId}`);
      setProfileUser(response.data);
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

  const isOwnProfile = user && profileUser && user.id === profileUser.id;

  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-loading">
          <div className="loading-spinner"></div>
          <p>Загрузка профиля...</p>
        </div>
      </div>
    );
  }

  if (error || !profileUser) {
    return (
      <div className="profile-page">
        <div className="profile-error">
          <h2>Пользователь не найден</h2>
          <p>Возможно, пользователь с таким ID не существует или был удален.</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            Вернуться на главную
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="profile-header">
          <button className="back-btn" onClick={() => navigate('/')}>
            ← Назад
          </button>
          <h1>Профиль пользователя</h1>
          {isOwnProfile && (
            <button 
              className="btn btn-secondary"
              onClick={() => navigate('/settings')}
            >
              Настройки профиля
            </button>
          )}
        </div>
        
        <div className="profile-content">
          <div className="profile-main-info">
            <div className="profile-avatar">
              {profileUser.avatar ? (
                <img src={profileUser.avatar} alt={profileUser.nickname} />
              ) : (
                <div className="default-avatar">
                  {profileUser.nickname.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            
            <div className="profile-info">
              <h2 className="profile-nickname">{profileUser.nickname}</h2>
              <p className="profile-id">ID: {profileUser.unique_id}</p>
              <p className="profile-email">{profileUser.email}</p>
              <p className="profile-join-date">
                На сайте с {formatDate(profileUser.created_at)}
              </p>
            </div>
          </div>

          {profileUser.description && (
            <div className="profile-description">
              <h3>О себе</h3>
              <p>{profileUser.description}</p>
            </div>
          )}

          <div className="profile-projects">
            <h3>Проекты ({profileUser.projects.length})</h3>
            {profileUser.projects.length > 0 ? (
              <div className="projects-list">
                {profileUser.projects.map((project) => (
                  <div key={project.id} className="project-item">
                    <h4 className="project-title">{project.title}</h4>
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

export default UserProfilePage;

