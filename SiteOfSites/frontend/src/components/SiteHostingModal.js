import React, { useState, useEffect } from 'react';
import axios from 'axios';
import api from '../api';
import './SiteHostingModal.css';

const SiteHostingModal = ({ project, isOpen, onClose, onUpdate }) => {
  const [hostingConfig, setHostingConfig] = useState({
    subdomain: '',
    visibility: 'PRIVATE',
    is_active: false,
    index_file: 'index.html'
  });
  const [siteFiles, setSiteFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [subdomainCheck, setSubdomainCheck] = useState(null);
  const [checkingSubdomain, setCheckingSubdomain] = useState(false);
  const [siteConfig, setSiteConfig] = useState({ domain: 'localhost', protocol: 'http' });

  useEffect(() => {
    if (isOpen && project) {
      fetchHostingInfo();
      fetchConfig();
    }
  }, [isOpen, project]);

  const fetchConfig = async () => {
    try {
      const response = await api.get('/api/config');
      setSiteConfig(response.data);
    } catch (error) {
      console.error('Не удалось загрузить конфигурацию сайта', error);
    }
  };

  const fetchHostingInfo = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`/api/projects/${project.id}/hosting`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const hostingData = response.data;
      
      setHostingConfig({
        subdomain: hostingData.project.subdomain || '',
        visibility: hostingData.project.visibility || 'PRIVATE',
        is_active: hostingData.project.is_active || false,
        index_file: hostingData.project.index_file || 'index.html'
      });
      
      setSiteFiles(hostingData.site_files || []);
    } catch (error) {
      console.error('Error fetching hosting info:', error);
      if (error.response?.status === 401) {
        setError('Ошибка авторизации. Пожалуйста, войдите в систему заново.');
      } else {
        setError('Ошибка загрузки информации о хостинге: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const checkSubdomainAvailability = async (subdomain) => {
    if (!subdomain || subdomain.length < 3) {
      setSubdomainCheck(null);
      return;
    }

    try {
      setCheckingSubdomain(true);
      const response = await axios.get(`/api/hosting/check-subdomain/${subdomain}`);
      setSubdomainCheck(response.data);
    } catch (error) {
      console.error('Error checking subdomain:', error);
      setSubdomainCheck({ available: false, message: 'Ошибка проверки поддомена' });
    } finally {
      setCheckingSubdomain(false);
    }
  };

  const handleSubdomainChange = (e) => {
    const value = e.target.value;
    setHostingConfig(prev => ({ ...prev, subdomain: value }));
    
    // Проверяем доступность поддомена с задержкой
    clearTimeout(window.subdomainCheckTimeout);
    window.subdomainCheckTimeout = setTimeout(() => {
      checkSubdomainAvailability(value);
    }, 500);
  };

  const handleSave = async () => {
    try {
      // Проверка наличия главного файла перед активацией
      if (hostingConfig.is_active) {
        const indexFileExists = siteFiles.some(f => f.filename === hostingConfig.index_file);
        if (!indexFileExists) {
          setError(`Ошибка: Главный файл "${hostingConfig.index_file}" не найден. Загрузите его перед активацией.`);
          return;
        }
      }

      setLoading(true);
      setError('');
      setSuccessMessage('');
      
      const token = localStorage.getItem('access_token');
      const response = await axios.put(`/api/projects/${project.id}/hosting`, hostingConfig, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (onUpdate) {
        onUpdate();
      }
      
      setSuccessMessage('Настройки успешно сохранены');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Error saving hosting config:', error);
      setError(error.response?.data?.detail || 'Ошибка сохранения настроек');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setHostingConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content site-hosting-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Настройки хостинга</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          {loading && <div className="loading">Загрузка...</div>}
          
          {error && <div className="error-message">{error}</div>}
          {successMessage && <div className="success-message" style={{backgroundColor: '#d4edda', color: '#155724', padding: '12px', borderRadius: '6px', marginBottom: '20px', border: '1px solid #c3e6cb'}}>{successMessage}</div>}
          
          <div className="hosting-form">
            <div className="form-group">
              <label htmlFor="subdomain">Поддомен</label>
              <div className="subdomain-input">
                <input
                  type="text"
                  id="subdomain"
                  name="subdomain"
                  value={hostingConfig.subdomain}
                  onChange={handleSubdomainChange}
                  placeholder="mysite"
                  className={subdomainCheck && !subdomainCheck.available ? 'error' : ''}
                />
                {/* <span className="subdomain-suffix">.localhost</span> - убрали суффикс, так как теперь это часть пути */}
              </div>
              {checkingSubdomain && <div className="checking">Проверка...</div>}
              {subdomainCheck && (
                <div className={`subdomain-status ${subdomainCheck.available ? 'available' : 'unavailable'}`}>
                  {subdomainCheck.message}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="visibility">Видимость сайта</label>
              <select
                id="visibility"
                name="visibility"
                value={hostingConfig.visibility}
                onChange={handleInputChange}
              >
                <option value="PRIVATE">Приватный (только для вас)</option>
                <option value="PUBLIC">Публичный (доступен всем)</option>
                <option value="LINK_ONLY">По ссылке (только по прямой ссылке)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="index_file">Главный файл</label>
              <input
                type="text"
                id="index_file"
                name="index_file"
                value={hostingConfig.index_file}
                onChange={handleInputChange}
                placeholder="index.html"
              />
            </div>

            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={hostingConfig.is_active}
                  onChange={handleInputChange}
                />
                <span className="checkmark"></span>
                Активировать сайт
              </label>
              <p className="help-text">
                Сайт будет доступен по адресу: {hostingConfig.subdomain ? `${siteConfig.protocol}://${siteConfig.domain}/sites/${hostingConfig.subdomain}` : 'укажите поддомен'}
              </p>
            </div>

            {siteFiles.length > 0 && (
              <div className="site-files">
                <h3>Файлы сайта</h3>
                <div className="files-list">
                  {siteFiles.map((file, index) => (
                    <div key={index} className="file-item">
                      <span className="file-name">{file.filename}</span>
                      <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {hostingConfig.subdomain && hostingConfig.is_active && (
              <div className="site-preview">
                <h3>Просмотр сайта</h3>
                <p>Ваш сайт доступен по адресу:</p>
                <div className="site-url">
                  <code>{siteConfig.protocol}://{siteConfig.domain}/sites/{hostingConfig.subdomain}/</code>
                  <a 
                    href={`${siteConfig.protocol}://${siteConfig.domain}/sites/${hostingConfig.subdomain}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="preview-site-btn"
                  >
                    👁️ Открыть сайт
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Отмена
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleSave}
            disabled={loading || (subdomainCheck && !subdomainCheck.available)}
          >
            {loading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SiteHostingModal;
