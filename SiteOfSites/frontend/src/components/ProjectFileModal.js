import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ProjectFileModal.css';

const ProjectFileModal = ({ project, isOpen, onClose, onUpdate }) => {
  const [files, setFiles] = useState([]);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState('root');
  const [viewMode, setViewMode] = useState('grid'); // grid или list

  useEffect(() => {
    if (isOpen && project) {
      fetchFiles();
    }
  }, [isOpen, project]);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`/api/projects/${project.id}/files`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      setFiles(response.data.files || []);
      setFolders(response.data.folders || []);
    } catch (error) {
      setError('Ошибка загрузки файлов');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const filesToUpload = Array.from(event.target.files);
    if (filesToUpload.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      for (const file of filesToUpload) {
        const formData = new FormData();
        formData.append('file', file);

        await axios.post(`/api/projects/${project.id}/files?folder=${selectedFolder}`, formData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'multipart/form-data'
          }
        });
      }
      
      await fetchFiles();
      if (onUpdate) onUpdate();
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка загрузки файлов');
    } finally {
      setUploading(false);
    }
  };

  const handleFileDelete = async (filename, folder) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот файл?')) return;

    try {
      await axios.delete(`/api/projects/${project.id}/files?filename=${encodeURIComponent(filename)}&folder=${folder}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      await fetchFiles();
      if (onUpdate) onUpdate();
    } catch (error) {
      setError('Ошибка удаления файла');
    }
  };

  const handleDownload = async (file) => {
    try {
      const response = await axios.get(`/api/projects/${project.id}/files/download?filename=${encodeURIComponent(file.original_name)}&folder=${file.folder}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.original_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError('Ошибка скачивания файла');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (filename) => {
    const extension = filename.split('.').pop().toLowerCase();
    switch (extension) {
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'webp':
        return '🖼️';
      case 'pdf':
        return '📄';
      case 'doc':
      case 'docx':
        return '📝';
      case 'xls':
      case 'xlsx':
        return '📊';
      case 'zip':
      case 'rar':
        return '📦';
      case 'mp4':
      case 'avi':
      case 'mov':
        return '🎥';
      case 'mp3':
      case 'wav':
        return '🎵';
      case 'html':
      case 'htm':
        return '🌐';
      case 'css':
        return '🎨';
      case 'js':
        return '⚡';
      default:
        return '📄';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="file-panel-overlay" onClick={onClose}>
      <div className="file-panel" onClick={(e) => e.stopPropagation()}>
        {/* Заголовок панели */}
        <div className="file-panel-header">
          <div className="header-left">
            <h1 className="panel-title">Файлы проекта</h1>
            <span className="project-name">{project.title}</span>
          </div>
          <div className="header-right">
            <div className="view-controls">
              <button 
                className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
                title="Сетка"
              >
                ⊞
              </button>
              <button 
                className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => setViewMode('list')}
                title="Список"
              >
                ☰
              </button>
            </div>
            <button className="close-btn" onClick={onClose}>×</button>
          </div>
        </div>

        {/* Панель инструментов */}
        <div className="file-panel-toolbar">
          <div className="toolbar-left">
            <div className="upload-section">
              <div className="folder-selector">
                <label>Папка:</label>
                <select 
                  value={selectedFolder} 
                  onChange={(e) => setSelectedFolder(e.target.value)}
                >
                  <option value="root">📁 Корневая папка</option>
                  <option value="images">🖼️ Images</option>
                </select>
              </div>
              <label className="upload-btn">
                <input
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  disabled={uploading}
                />
                {uploading ? '⏳ Загрузка...' : '📤 Добавить файлы'}
              </label>
            </div>
          </div>
          <div className="toolbar-right">
            <div className="file-stats">
              {files.length > 0 && (
                <span className="stats-text">
                  {files.length} файл{files.length === 1 ? '' : files.length < 5 ? 'а' : 'ов'}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Сообщения об ошибках */}
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{error}</span>
            <button className="error-close" onClick={() => setError(null)}>×</button>
          </div>
        )}

        {/* Основное содержимое */}
        <div className="file-panel-content">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <span>Загрузка файлов...</span>
            </div>
          ) : files.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📁</div>
              <h3>Папка пуста</h3>
              <p>Добавьте файлы, чтобы начать работу с проектом</p>
            </div>
          ) : (
            <div className={`files-container ${viewMode}`}>
              {folders.map((folder) => {
                const folderFiles = files.filter(file => file.folder === folder);
                if (folderFiles.length === 0) return null;
                
                return (
                  <div key={folder} className="folder-group">
                    <div className="folder-header">
                      <h3 className="folder-title">
                        {folder === 'root' ? '📁 Корневая папка' : '🖼️ Images'}
                      </h3>
                      <span className="folder-count">{folderFiles.length} файл{folderFiles.length === 1 ? '' : folderFiles.length < 5 ? 'а' : 'ов'}</span>
                    </div>
                    <div className={`files-grid ${viewMode}`}>
                      {folderFiles.map((file, index) => (
                        <div key={`file-${index}`} className="file-card">
                          <div className="file-preview">
                            <div className="file-icon">{getFileIcon(file.original_name)}</div>
                          </div>
                          <div className="file-info">
                            <div className="file-name" title={file.original_name}>
                              {file.original_name}
                            </div>
                            <div className="file-meta">
                              <span className="file-size">{formatFileSize(file.size)}</span>
                              <span className="file-date">
                                {new Date(file.last_modified).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                          <div className="file-actions">
                            <button 
                              className="action-btn download-btn"
                              onClick={() => handleDownload(file)}
                              title="Скачать"
                            >
                              ⬇️
                            </button>
                            <button 
                              className="action-btn delete-btn"
                              onClick={() => handleFileDelete(file.original_name, file.folder)}
                              title="Удалить"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectFileModal;
