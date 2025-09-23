import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ProjectFileModal.css';

const ProjectFileModal = ({ project, isOpen, onClose, onUpdate }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [folders, setFolders] = useState([]);
  const [currentFolderId, setCurrentFolderId] = useState(null);
  const [showMoveDialog, setShowMoveDialog] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState(null);

  useEffect(() => {
    if (isOpen && project) {
      fetchFiles();
      fetchFolders();
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
      setFiles(response.data);
    } catch (error) {
      setError('Ошибка загрузки файлов');
    } finally {
      setLoading(false);
    }
  };

  const fetchFolders = async () => {
    try {
      const response = await axios.get(`/api/projects/${project.id}/folders`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      setFolders(response.data);
    } catch (error) {
      setError('Ошибка загрузки папок');
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

        await axios.post(`/api/projects/${project.id}/files`, formData, {
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

  const handleFileDelete = async (fileId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот файл?')) return;

    try {
      await axios.delete(`/api/projects/${project.id}/files/${fileId}`, {
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
      const response = await axios.get(`/api/projects/${project.id}/files/${file.id}/download`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.original_filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError('Ошибка скачивания файла');
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      await axios.post(`/api/projects/${project.id}/folders`, {
        name: newFolderName.trim(),
        parent_folder_id: currentFolderId
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      setNewFolderName('');
      setShowCreateFolder(false);
      await fetchFolders();
      if (onUpdate) onUpdate();
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка создания папки');
    }
  };

  const handleDeleteFolder = async (folderId, folderName) => {
    if (!window.confirm(`Вы уверены, что хотите удалить папку "${folderName}"? Все файлы в ней также будут удалены.`)) return;

    try {
      await axios.delete(`/api/projects/${project.id}/folders/${folderId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      await fetchFolders();
      await fetchFiles();
      if (onUpdate) onUpdate();
    } catch (error) {
      setError('Ошибка удаления папки');
    }
  };

  const handleMoveFile = async (fileId, targetFolderId) => {
    try {
      await axios.put(`/api/projects/${project.id}/files/${fileId}/move`, {
        folder_id: targetFolderId
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      await fetchFiles();
      if (onUpdate) onUpdate();
    } catch (error) {
      setError('Ошибка перемещения файла');
    }
  };

  const openMoveDialog = (fileId) => {
    setSelectedFileId(fileId);
    setShowMoveDialog(true);
  };

  const closeMoveDialog = () => {
    setShowMoveDialog(false);
    setSelectedFileId(null);
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
    <div className="modal-overlay" onClick={onClose}>
      <div className="project-file-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Файлы проекта: {project.title}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-content">
          <div className="file-actions">
            <div className="upload-section">
              <label className="upload-btn">
                <input
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  disabled={uploading}
                />
                {uploading ? 'Загрузка...' : 'Добавить файлы'}
              </label>
            </div>

            <div className="folder-actions">
              <button 
                className="create-folder-btn"
                onClick={() => setShowCreateFolder(!showCreateFolder)}
              >
                📁 Создать папку
              </button>
            </div>
          </div>

          {showCreateFolder && (
            <div className="create-folder-form">
              <div className="form-row">
                <input
                  type="text"
                  placeholder="Название папки"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleCreateFolder()}
                />
                <div className="form-buttons">
                  <button 
                    onClick={handleCreateFolder}
                    disabled={!newFolderName.trim()}
                    className="create-btn"
                  >
                    Создать
                  </button>
                  <button 
                    onClick={() => {
                      setNewFolderName('');
                      setShowCreateFolder(false);
                    }}
                    className="cancel-btn-small"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="error-message">{error}</div>
          )}

          <div className="files-section">
            <h3>Файлы и папки проекта</h3>
            
            {loading ? (
              <div className="loading">Загрузка файлов...</div>
            ) : (files.length === 0 && folders.length === 0) ? (
              <div className="no-files">Файлы и папки не найдены</div>
            ) : (
              <div className="items-list">
                {/* Папки */}
                {folders.map((folder) => (
                  <div key={`folder-${folder.id}`} className="folder-item">
                    <div className="folder-info">
                      <span className="folder-icon">📁</span>
                      <div className="folder-details">
                        <div className="folder-name">{folder.name}</div>
                        <div className="folder-meta">
                          Папка • {new Date(folder.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    <div className="folder-actions">
                      <button 
                        className="delete-btn"
                        onClick={() => handleDeleteFolder(folder.id, folder.name)}
                        title="Удалить папку"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}

                {/* Файлы */}
                {files.map((file) => (
                  <div key={`file-${file.id}`} className="file-item">
                    <div className="file-info">
                      <span className="file-icon">{getFileIcon(file.original_filename)}</span>
                      <div className="file-details">
                        <div className="file-name">{file.original_filename}</div>
                        <div className="file-meta">
                          {formatFileSize(file.file_size)} • 
                          {new Date(file.created_at).toLocaleDateString()}
                          {file.folder_id && (
                            <span className="file-folder"> • В папке</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="file-actions">
                      <button 
                        className="move-btn"
                        onClick={() => openMoveDialog(file.id)}
                        title="Переместить в папку"
                      >
                        📁
                      </button>
                      <button 
                        className="download-btn"
                        onClick={() => handleDownload(file)}
                        title="Скачать"
                      >
                        ⬇️
                      </button>
                      <button 
                        className="delete-btn"
                        onClick={() => handleFileDelete(file.id)}
                        title="Удалить"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Диалог перемещения файла */}
          {showMoveDialog && (
            <div className="move-dialog-overlay" onClick={closeMoveDialog}>
              <div className="move-dialog" onClick={(e) => e.stopPropagation()}>
                <h3>Переместить файл в папку</h3>
                <div className="folder-options">
                  <button 
                    className="folder-option"
                    onClick={() => {
                      handleMoveFile(selectedFileId, null);
                      closeMoveDialog();
                    }}
                  >
                    📁 Корневая папка
                  </button>
                  {folders.map((folder) => (
                    <button 
                      key={folder.id}
                      className="folder-option"
                      onClick={() => {
                        handleMoveFile(selectedFileId, folder.id);
                        closeMoveDialog();
                      }}
                    >
                      📁 {folder.name}
                    </button>
                  ))}
                </div>
                <button className="cancel-btn" onClick={closeMoveDialog}>
                  Отмена
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectFileModal;
