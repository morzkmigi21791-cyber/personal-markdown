import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import ProjectFileModal from '../components/ProjectFileModal';
import './UserProfilePage.css';

const PieChart = ({ data }) => {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  if (total === 0) return <div className="no-data">Нет данных для графика</div>;

  let cumulativePercent = 0;

  const getCoordinatesForPercent = (percent) => {
    const x = Math.cos(2 * Math.PI * percent);
    const y = Math.sin(2 * Math.PI * percent);
    return [x, y];
  };

  const slices = data.map((item, index) => {
    const startPercent = cumulativePercent;
    const percent = item.value / total;
    cumulativePercent += percent;
    const endPercent = cumulativePercent;

    const [startX, startY] = getCoordinatesForPercent(startPercent);
    const [endX, endY] = getCoordinatesForPercent(endPercent);
    
    const largeArcFlag = percent > 0.5 ? 1 : 0;
    
    const pathData = percent === 1 
      ? `M 1 0 A 1 1 0 1 1 -1 0 A 1 1 0 1 1 1 0`
      : `M 0 0 L ${startX} ${startY} A 1 1 0 ${largeArcFlag} 1 ${endX} ${endY} Z`;

    return { ...item, path: pathData, percent, index };
  });

  return (
    <div className="pie-chart-container">
      <div className="pie-chart-wrapper">
        <svg viewBox="-1.1 -1.1 2.2 2.2" className="pie-chart-svg">
           <g transform="rotate(-90)">
            {slices.map((slice, i) => (
              <path
                key={i}
                d={slice.path}
                fill={slice.color}
                className={`pie-slice ${hoveredIndex === i ? 'active' : ''}`}
                onMouseEnter={() => setHoveredIndex(i)}
                onMouseLeave={() => setHoveredIndex(null)}
              />
            ))}
           </g>
        </svg>
        {hoveredIndex !== null && (
          <div className="chart-tooltip">
            <div className="tooltip-title">{data[hoveredIndex].label}</div>
            <div className="tooltip-value">
              {data[hoveredIndex].value} ({Math.round(data[hoveredIndex].value / total * 100)}%)
            </div>
          </div>
        )}
      </div>
      <div className="chart-legend">
        {data.map((item, i) => (
          <div 
            key={i} 
            className={`legend-item ${hoveredIndex === i ? 'active' : ''}`}
            onMouseEnter={() => setHoveredIndex(i)}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <span className="legend-color" style={{ backgroundColor: item.color }}></span>
            <span className="legend-label">{item.label}</span>
            <span className="legend-percent">{Math.round(item.value / total * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const UserProfilePage = ({ user: currentUser, siteConfig }) => {
  const { uniqueId } = useParams();
  const navigate = useNavigate();
  const [profileUser, setProfileUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showFileModal, setShowFileModal] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [projectStats, setProjectStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [projectForm, setProjectForm] = useState({
    title: '',
    description: ''
  });
  const [projectLoading, setProjectLoading] = useState(false);
  const [projectError, setProjectError] = useState('');
  const [projectSuccess, setProjectSuccess] = useState('');
  const [showGeneralStats, setShowGeneralStats] = useState(false);
  const [generalStats, setGeneralStats] = useState([]);
  const [loadingGeneralStats, setLoadingGeneralStats] = useState(false);

  useEffect(() => {
    fetchUserProfile();
  }, [uniqueId]);

  // Применяем фон страницы при загрузке профиля
  useEffect(() => {
    if (profileUser && profileUser.page_background) {
      document.body.style.backgroundImage = `url(${profileUser.page_background})`;
      document.body.style.backgroundSize = 'cover';
      document.body.style.backgroundAttachment = 'fixed';
    } else {
      // Сброс на дефолтный градиент
      document.body.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    }
    
    return () => {
      // Очистка при уходе со страницы
      document.body.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    };
  }, [profileUser]);

  // Загрузка общей статистики
  useEffect(() => {
    if (showGeneralStats) {
      fetchGeneralStats();
    }
  }, [showGeneralStats]);

  const fetchGeneralStats = async () => {
    setLoadingGeneralStats(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await api.get('/api/user/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setGeneralStats(response.data);
    } catch (error) {
      console.error("Ошибка загрузки общей статистики:", error);
    } finally {
      setLoadingGeneralStats(false);
    }
  };

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

  const handleStatsClick = async (e, project) => {
    e.stopPropagation();
    setSelectedProject(project);
    setShowStatsModal(true);
    setLoadingStats(true);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await api.get(`/api/projects/${project.id}/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setProjectStats(response.data);
    } catch (error) {
      console.error("Ошибка загрузки статистики:", error);
    } finally {
      setLoadingStats(false);
    }
  };

  const handleProjectUpdate = () => {
    // Обновляем список проектов после изменений в файлах
    fetchUserProfile();
  };

  return (
    <div className="user-profile-page">
      <div className="profile-container">
        <div 
          className="profile-header"
          style={profileUser.profile_cover ? { 
            backgroundImage: `url(${profileUser.profile_cover})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            color: 'white',
            textShadow: '0 2px 4px rgba(0,0,0,0.7)'
          } : {}}
        >
          {isOwnProfile && (
            <>
              <button 
                className="edit-profile-btn"
                onClick={() => navigate('/settings')}
                title="Настроить оформление"
              >
                🖌️
              </button>
              <button 
                className="general-stats-btn"
                onClick={() => setShowGeneralStats(true)}
                title="Общая статистика"
              >
                📈
              </button>
            </>
          )}
          <div className="profile-avatar">
            {profileUser.avatar ? (
              <img src={profileUser.avatar} alt="Аватар" />
            ) : (
              profileUser.nickname ? profileUser.nickname.charAt(0).toUpperCase() : 'U'
            )}
          </div>
          <div className="profile-info">
            <h1 className="profile-name">
              {profileUser.nickname}
            </h1>
            {profileUser.description && (
              <p className="profile-bio">{profileUser.description}</p>
            )}
          </div>
        </div>

        <div className="profile-content">
          <div 
            className="profile-section"
            style={profileUser.projects_background ? {
              backgroundImage: `url(${profileUser.projects_background})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              padding: '24px',
              minHeight: '500px', /* Минимальная высота, чтобы фон был виден */
              /* borderRadius убран, чтобы фон прилегал к краям, если нужно */
            } : {}}
          >
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
                    maxLength={30}
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
                      style={{ backgroundColor: profileUser.card_color || '#ffffff' }}
                      onClick={() => handleProjectClick(project)}
                    >
                      <div className="project-header">
                        <h3>{project.title}</h3>
                        {isOwnProfile && (
                          <div className="project-actions">
                            <button
                              className="btn btn-info btn-sm"
                              onClick={(e) => handleStatsClick(e, project)}
                              title="Статистика посещений"
                            >
                              📊
                            </button>
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
                            📍 /sites/{project.subdomain}
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
                            href={`${siteConfig?.protocol || 'http'}://${siteConfig?.domain || 'localhost'}/sites/${project.subdomain}/`}
                            target="_blank"
                            rel="noopener"
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

      {showStatsModal && selectedProject && (
        <div className="modal-overlay" onClick={() => setShowStatsModal(false)}>
          <div className="modal-content stats-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Статистика: {selectedProject.title}</h2>
              <button className="modal-close" onClick={() => setShowStatsModal(false)}>×</button>
            </div>
            <div className="modal-body">
              {loadingStats ? (
                <div className="loading">Загрузка статистики...</div>
              ) : projectStats ? (
                <div className="stats-container">
                  <div className="stats-summary">
                    <div className="stat-card">
                      <span className="stat-value">{projectStats.visits_today}</span>
                      <span className="stat-label">За сегодня</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-value">{projectStats.visits_week}</span>
                      <span className="stat-label">За неделю</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-value">{projectStats.visits_month}</span>
                      <span className="stat-label">За месяц</span>
                    </div>
                    <div className="stat-card total">
                      <span className="stat-value">{projectStats.total_visits}</span>
                      <span className="stat-label">Всего</span>
                    </div>
                  </div>

                  <div className="stats-details">
                    <div className="stats-column">
                      <h3>🌍 Страны</h3>
                      <ul className="stats-list">
                        {Object.entries(projectStats.countries).length > 0 ? (
                          Object.entries(projectStats.countries).map(([country, count]) => (
                            <li key={country}>
                              <span className="country-code">{country === 'Unknown' ? 'Неизвестно' : country}</span>
                              <span className="count">{count}</span>
                            </li>
                          ))
                        ) : <li className="empty">Нет данных</li>}
                      </ul>
                    </div>
                    <div className="stats-column">
                      <h3>🔗 Источники</h3>
                      <ul className="stats-list">
                        {Object.entries(projectStats.sources).map(([source, count]) => (
                          <li key={source}>
                            <span className="source-name">
                              {source === 'direct' ? 'Прямой переход' : 
                               source === 'profile' ? 'Профиль пользователя' : 'Внешний сайт'}
                            </span>
                            <span className="count">{count}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <p>Не удалось загрузить статистику</p>
              )}
            </div>
          </div>
        </div>
      )}

      {showGeneralStats && (
        <div className="modal-overlay" onClick={() => setShowGeneralStats(false)}>
          <div className="modal-content stats-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Общая статистика</h2>
              <button className="modal-close" onClick={() => setShowGeneralStats(false)}>×</button>
            </div>
            <div className="modal-body">
              {loadingGeneralStats ? (
                <div className="loading">Загрузка...</div>
              ) : (
                <div className="general-stats-container">
                  {generalStats.length > 0 && (
                    <PieChart data={(() => {
                      // Подготовка данных для графика
                      const sorted = [...generalStats].sort((a, b) => b.total_visits - a.total_visits);
                      const top5 = sorted.slice(0, 5);
                      const others = sorted.slice(5);
                      const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];
                      
                      const chartData = top5.map((item, index) => ({
                        label: item.project_title,
                        value: item.total_visits,
                        color: colors[index % colors.length]
                      }));
                      
                      if (others.length > 0) {
                        const othersCount = others.reduce((sum, item) => sum + item.total_visits, 0);
                        if (othersCount > 0) {
                          chartData.push({
                            label: 'Остальные',
                            value: othersCount,
                            color: '#C9CBCF'
                          });
                        }
                      }
                      return chartData.filter(d => d.value > 0);
                    })()} />
                  )}
                  <div className="general-stats-header">
                    <span className="col-name">Проект</span>
                    <span className="col-stat">Сегодня</span>
                    <span className="col-stat">Всего</span>
                  </div>
                  <div className="general-stats-list">
                    {generalStats.map(stat => (
                      <div 
                        key={stat.project_id} 
                        className="general-stats-item"
                        onClick={(e) => {
                          const project = profileUser.projects.find(p => p.id === stat.project_id);
                          if (project) {
                            setShowGeneralStats(false);
                            handleStatsClick(e, project);
                          }
                        }}
                      >
                        <span className="col-name">{stat.project_title}</span>
                        <span className="col-stat">{stat.visits_today}</span>
                        <span className="col-stat">{stat.total_visits}</span>
                      </div>
                    ))}
                    {generalStats.length === 0 && <p className="no-data">Нет данных</p>}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfilePage;