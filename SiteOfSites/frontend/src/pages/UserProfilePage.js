import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';
import ProjectFileModal from '../components/ProjectFileModal';
import './UserProfilePage.css';

const UserProfilePage = ({ user: currentUser }) => {
  const { uniqueId } = useParams();
  const [profileUser, setProfileUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showFileModal, setShowFileModal] = useState(false);
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [projectForm, setProjectForm] = useState({
    title: '',
    description: ''
  });
  const [projectLoading, setProjectLoading] = useState(false);
  const [projectError, setProjectError] = useState('');
  const [projectSuccess, setProjectSuccess] = useState('');

  useEffect(() => {
    fetchUserProfile();
  }, [uniqueId]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/users/by-unique-id/${uniqueId}`);
      setProfileUser(response.data);
    } catch (error) {
      setError('Пользователь не найден');
    } finally {
      setLoading(false);
    }
  };

  const handleProjectFormChange = (e) => {
    const { name, value } = e.target;
    setProjectForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    setProjectLoading(true);
    setProjectError('');
    setProjectSuccess('');

    try {
      const token = localStorage.getItem('access_token');
      await api.post('/api/projects', projectForm, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setProjectForm({ title: '', description: '' });
      setShowProjectForm(false);
      await fetchUserProfile();
      setProjectSuccess('Проект создан');
    } catch (error) {
      setProjectError(error.response?.data?.detail || 'Ошибка создания проекта');
    } finally {
      setProjectLoading(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот проект?')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      await api.delete(`/api/projects/${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      await fetchUserProfile();
      setProjectSuccess('Проект удален');
    } catch (error) {
      setProjectError(error.response?.data?.detail || 'Ошибка удаления проекта');
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
            {profileUser.avatar ? (
              <img src={profileUser.avatar} alt="Аватар" />
            ) : (
              profileUser.nickname ? profileUser.nickname.charAt(0).toUpperCase() : 'U'
            )}
          </div>
          <div className="profile-info">
            <h1 className="profile-name">
              {profileUser.nickname || 'Без имени'}
            </h1>
            <p className="profile-email">{profileUser.email}</p>
            {profileUser.description && (
              <p className="profile-bio">{profileUser.description}</p>
            )}
          </div>
        </div>

        <div className="profile-content">
          <div className="profile-section">
            <div className="projects-header">
              <h2>Проекты</h2>
              {isOwnProfile && (
                <button 
                  className="btn btn-primary"
                  onClick={() => setShowProjectForm(!showProjectForm)}
                >
                  {showProjectForm ? 'Отмена' : 'Создать проект'}
                </button>
              )}
            </div>

            {projectError && <div className="alert alert-error">{projectError}</div>}
            {projectSuccess && <div className="alert alert-success">{projectSuccess}</div>}

            {isOwnProfile && showProjectForm && (
              <form onSubmit={handleCreateProject} className="project-form">
                <div className="form-group">
                  <label>Название проекта</label>
                  <input
                    type="text"
                    name="title"
                    value={projectForm.title}
                    onChange={handleProjectFormChange}
                    required
                    maxLength={100}
                    placeholder="Введите название проекта"
                  />
                </div>
                <div className="form-group">
                  <label>Описание</label>
                  <textarea
                    name="description"
                    value={projectForm.description}
                    onChange={handleProjectFormChange}
                    rows={3}
                    placeholder="Описание проекта..."
                    maxLength={500}
                  />
                </div>
                <div className="form-actions">
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={() => setShowProjectForm(false)}
                  >
                    Отмена
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={projectLoading}>
                    {projectLoading ? 'Создание...' : 'Создать проект'}
                  </button>
                </div>
              </form>
            )}

            {(() => {
              // Фильтруем проекты в зависимости от того, свой ли это профиль
              const visibleProjects = isOwnProfile 
                ? profileUser.projects 
                : profileUser.projects?.filter(project => project.visibility === 'PUBLIC' && project.is_active);
              
              return visibleProjects && visibleProjects.length > 0 ? (
                <div className="projects-grid">
                  {visibleProjects.map((project) => (
                    <div 
                      key={project.id} 
                      className={`project-card ${isOwnProfile ? 'clickable' : ''}`}
                      onClick={() => handleProjectClick(project)}
                    >
                      <div className="project-header">
                        <h3>{project.title}</h3>
                        {isOwnProfile && (
                          <div className="project-actions">
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteProject(project.id);
                              }}
                            >
                              Удалить
                            </button>
                          </div>
                        )}
                      </div>
                      <p>{project.description || 'Без описания'}</p>
                      <div className="project-meta">
                        <span className="project-status">
                          {project.is_active ? '🌐 Активен' : '⏸️ Неактивен'}
                        </span>
                        <span className="project-visibility">
                          {project.visibility === 'PUBLIC' ? '🌍 Публичный' : 
                           project.visibility === 'LINK_ONLY' ? '🔗 По ссылке' : '🔒 Приватный'}
                        </span>
                        {project.subdomain && project.is_active && (
                          <span className="project-subdomain">
                            📍 {project.subdomain}.localhost
                          </span>
                        )}
                        <span className="project-date">
                          {new Date(project.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      {/* Кнопка для просмотра сайта */}
                      {project.subdomain && project.is_active && (
                        <div className="project-site-actions">
                          <a 
                            href={`http://${project.subdomain}.localhost`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="view-site-btn"
                            onClick={(e) => e.stopPropagation()}
                          >
                            👁️ Посмотреть сайт
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-projects">
                  {isOwnProfile 
                    ? 'У вас пока нет проектов' 
                    : profileUser.projects && profileUser.projects.length > 0
                      ? 'У пользователя нет публичных активных сайтов'
                      : 'У пользователя нет проектов'
                  }
                </p>
              );
            })()}
          </div>

          {isOwnProfile && (
            <div className="profile-actions">
              <button 
                className="btn btn-secondary"
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