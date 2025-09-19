import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ProfileSettingsPage.css';

const ProfileSettingsPage = ({ user, onUpdate }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nickname: '',
    description: '',
    avatar: ''
  });
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [projectForm, setProjectForm] = useState({
    title: '',
    description: ''
  });

  useEffect(() => {
    if (user) {
      setFormData({
        nickname: user.nickname || '',
        description: user.description || '',
        avatar: user.avatar || ''
      });
      fetchProjects();
    }
  }, [user]);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get('/api/projects', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setProjects(response.data);
    } catch (error) {
      console.error('Ошибка загрузки проектов:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleProjectFormChange = (e) => {
    const { name, value } = e.target;
    setProjectForm(prev => ({
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
      const response = await axios.put('/api/users/profile', formData, {
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

  const handleCreateProject = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      await axios.post('/api/projects', projectForm, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setProjectForm({ title: '', description: '' });
      setShowProjectForm(false);
      fetchProjects();
      setSuccess('Проект создан');
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка создания проекта');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот проект?')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`/api/projects/${projectId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      fetchProjects();
      setSuccess('Проект удален');
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка удаления проекта');
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
              />
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
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Сохранение...' : 'Сохранить изменения'}
            </button>
          </form>

          <div className="projects-section">
            <div className="projects-header">
              <h2>Мои проекты ({projects.length})</h2>
              <button 
                className="btn btn-secondary"
                onClick={() => setShowProjectForm(!showProjectForm)}
              >
                {showProjectForm ? 'Отмена' : 'Добавить проект'}
              </button>
            </div>

            {showProjectForm && (
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
                  />
                </div>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  Создать проект
                </button>
              </form>
            )}

            <div className="projects-list">
              {projects.map((project) => (
                <div key={project.id} className="project-item">
                  <div className="project-info">
                    <h3>{project.title}</h3>
                    {project.description && <p>{project.description}</p>}
                    <small>Создан {new Date(project.created_at).toLocaleDateString('ru-RU')}</small>
                  </div>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDeleteProject(project.id)}
                  >
                    Удалить
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileSettingsPage;

