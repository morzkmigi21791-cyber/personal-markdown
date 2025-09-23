import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import ProjectFileModal from '../components/ProjectFileModal';
import './UserProfilePage.css';

const UserProfilePage = ({ user: currentUser }) => {
  const { uniqueId } = useParams();
  const [profileUser, setProfileUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showFileModal, setShowFileModal] = useState(false);

  useEffect(() => {
    fetchUserProfile();
  }, [uniqueId]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/users/by-unique-id/${uniqueId}`);
      setProfileUser(response.data);
    } catch (error) {
      setError('Пользователь не найден');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="user-profile-page">
        <div className="loading">Загрузка профиля...</div>
      </div>
    );
  }

  if (error || !profileUser) {
    return (
      <div className="user-profile-page">
        <div className="error">
          <h2>Пользователь не найден</h2>
          <p>Профиль с таким ID не существует или был удален.</p>
        </div>
      </div>
    );
  }

  const isOwnProfile = currentUser && currentUser.unique_id === uniqueId;

  const handleProjectClick = (project) => {
    if (isOwnProfile) {
      setSelectedProject(project);
      setShowFileModal(true);
    }
  };

  const handleFileModalClose = () => {
    setShowFileModal(false);
    setSelectedProject(null);
  };

  const handleProjectUpdate = () => {
    // Обновляем список проектов после изменений в файлах
    fetchUserProfile();
  };

  return (
    <div className="user-profile-page">
      <div className="profile-container">
        <div className="profile-header">
          <div className="profile-avatar">
            {profileUser.nickname ? profileUser.nickname.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="profile-info">
            <h1 className="profile-name">
              {profileUser.nickname || 'Без имени'}
            </h1>
            <p className="profile-email">{profileUser.email}</p>
            {profileUser.bio && (
              <p className="profile-bio">{profileUser.bio}</p>
            )}
          </div>
        </div>

        <div className="profile-content">
          <div className="profile-section">
            <h2>Проекты</h2>
            {profileUser.projects && profileUser.projects.length > 0 ? (
              <div className="projects-grid">
                {profileUser.projects.map((project) => (
                  <div 
                    key={project.id} 
                    className={`project-card ${isOwnProfile ? 'clickable' : ''}`}
                    onClick={() => handleProjectClick(project)}
                  >
                    <h3>{project.title}</h3>
                    <p>{project.description || 'Без описания'}</p>
                    <div className="project-meta">
                      <span className="project-status">
                        {project.is_public ? 'Публичный' : 'Приватный'}
                      </span>
                      <span className="project-date">
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {isOwnProfile && (
                      <div className="project-files-count">
                        Файлов: {project.files ? project.files.length : 0}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-projects">
                {isOwnProfile ? 'У вас пока нет проектов' : 'У пользователя нет проектов'}
              </p>
            )}
          </div>

          {isOwnProfile && (
            <div className="profile-actions">
              <button 
                className="btn btn-primary"
                onClick={() => window.location.href = '/settings'}
              >
                Настройки профиля
              </button>
            </div>
          )}
        </div>
      </div>

      {showFileModal && selectedProject && (
        <ProjectFileModal
          project={selectedProject}
          isOpen={showFileModal}
          onClose={handleFileModalClose}
          onUpdate={handleProjectUpdate}
        />
      )}
    </div>
  );
};

export default UserProfilePage;
