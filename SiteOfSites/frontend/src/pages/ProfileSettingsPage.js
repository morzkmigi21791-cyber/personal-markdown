import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import './ProfileSettingsPage.css';

// Компонент для обрезки изображения
const ImageCropper = ({ imageSrc, onCrop, onCancel, circular = false }) => {
  const canvasRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [minScale, setMinScale] = useState(0.1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const imgRef = useRef(new Image());

  useEffect(() => {
    imgRef.current.src = imageSrc;
    imgRef.current.onload = () => {
      // Центрируем изображение
      const canvas = canvasRef.current;
      if (!canvas) return;
      const aspect = imgRef.current.width / imgRef.current.height;
      let drawWidth, drawHeight;
      
      if (aspect > 1) {
        drawHeight = canvas.height;
        drawWidth = canvas.height * aspect;
      } else {
        drawWidth = canvas.width;
        drawHeight = canvas.width / aspect;
      }
      
      // Вычисляем минимальный масштаб, чтобы картинка перекрывала область кропа (200x200)
      // Область кропа по центру: 200x200. Канвас: 300x300.
      const minScaleVal = Math.max(200 / imgRef.current.width, 200 / imgRef.current.height);
      setMinScale(minScaleVal);
      
      setScale(Math.max(1, minScaleVal)); // Начальный масштаб
      setPos({
        x: (canvas.width - drawWidth) / 2, 
        y: (canvas.height - drawHeight) / 2 
      });
      draw();
    };
  }, [imageSrc]);

  useEffect(() => {
    draw();
  }, [scale, pos]);

  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // 1. Очищаем канвас
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 2. Рисуем изображение (с учетом масштаба и позиции)
    const img = imgRef.current;
    const width = img.width * scale;
    const height = img.height * scale;
    
    ctx.drawImage(img, pos.x, pos.y, width, height);
    
    // 3. Рисуем затемнение с "дыркой"
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.beginPath();
    // Внешний прямоугольник (весь канвас)
    ctx.rect(0, 0, canvas.width, canvas.height);
    
    // Внутренняя область (дырка), рисуем в обратную сторону для создания выреза
    // Центр канваса: 150, 150. Размер кропа: 200x200 (радиус 100 или отступ 50)
    if (circular) {
      ctx.arc(canvas.width / 2, canvas.height / 2, 100, 0, Math.PI * 2, true);
    } else {
      ctx.rect(250, 50, -200, 200); // Рисуем против часовой стрелки
    }
    ctx.fill('evenodd'); // Используем правило evenodd для создания дырки
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartPos({ x: e.clientX - pos.x, y: e.clientY - pos.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPos({ x: e.clientX - startPos.x, y: e.clientY - startPos.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleSave = () => {
    const canvas = document.createElement('canvas');
    const size = 400;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');

    // Вычисляем координаты выреза относительно исходного изображения
    // Центр кропа на канвасе (150, 150) минус позиция картинки (pos.x, pos.y)
    // дает смещение центра кропа относительно левого верхнего угла картинки (в масштабированных пикселях)
    const cropCenterX = (300 / 2) - pos.x;
    const cropCenterY = (300 / 2) - pos.y;
    
    // Переводим в координаты исходного изображения (делим на scale)
    const imgCropX = (cropCenterX - 100) / scale;
    const imgCropY = (cropCenterY - 100) / scale;
    const imgCropSize = 200 / scale;

    // Рисуем вырезанную часть чистого изображения
    ctx.drawImage(imgRef.current, imgCropX, imgCropY, imgCropSize, imgCropSize, 0, 0, size, size);
    
    onCrop(canvas.toDataURL('image/jpeg', 0.8));
  };

  return (
    <div className="cropper-modal">
      <div className="cropper-content">
        <h3>Настройка изображения</h3>
        <div className="canvas-container">
          <canvas 
            ref={canvasRef} 
            width={300} 
            height={300}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
        </div>
        <div className="cropper-controls">
          <label>Масштаб:
            <input 
              type="range" 
              min={minScale} 
              max="3" 
              step="0.01" 
              value={scale} 
              onChange={(e) => setScale(parseFloat(e.target.value))} 
            />
            <span style={{ marginLeft: '10px', minWidth: '40px', display: 'inline-block' }}>
              {Math.round(scale * 100)}%
            </span>
          </label>
        </div>
        <div className="cropper-actions">
          <button className="btn btn-secondary" onClick={onCancel}>Отмена</button>
          <button className="btn btn-primary" onClick={handleSave}>Применить</button>
        </div>
      </div>
    </div>
  );
};

const ProfileSettingsPage = ({ user, onUpdate }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nickname: '',
    description: '',
    avatar: '',
    profile_cover: '',
    page_background: '',
    projects_background: '',
    card_color: '#ffffff'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Состояния для кроппера
  const [cropperImage, setCropperImage] = useState(null);
  const [cropperField, setCropperField] = useState(null);

  useEffect(() => {
    if (user) {
      setFormData({
        nickname: user.nickname || '',
        description: user.description || '',
        avatar: user.avatar || '',
        profile_cover: user.profile_cover || '',
        page_background: user.page_background || '',
        projects_background: user.projects_background || '',
        card_color: user.card_color || '#ffffff'
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

  const handleFileSelect = (e, field) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Файл слишком большой (макс 5МБ)');
        return;
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        // Если это аватарка - открываем кроппер
        if (field === 'avatar') {
          setCropperImage(event.target.result);
          setCropperField(field);
        } else {
          // Для остальных полей сохраняем сразу
          setFormData(prev => ({ ...prev, [field]: event.target.result }));
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleCropComplete = (croppedDataUrl) => {
    setFormData(prev => ({ ...prev, [cropperField]: croppedDataUrl }));
    setCropperImage(null);
    setCropperField(null);
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
            
            {/* Секция изображений */}
            <div className="images-section">
              <h2>Оформление</h2>
              
              <div className="form-group">
                <label>Аватарка</label>
                <div className="image-upload-row">
                  <div className="preview-circle">
                    {formData.avatar ? <img src={formData.avatar} alt="Avatar" /> : <div className="placeholder">?</div>}
                  </div>
                  <input type="file" accept=".png, .jpg, .jpeg, .webp" onChange={(e) => handleFileSelect(e, 'avatar')} />
                </div>
              </div>

              <div className="form-group">
                <label>Обложка профиля</label>
                <div className="image-upload-row">
                  <div className="preview-rect">
                    {formData.profile_cover ? <img src={formData.profile_cover} alt="Cover" /> : <div className="placeholder">Нет обложки</div>}
                  </div>
                  <input type="file" accept=".png, .jpg, .jpeg, .webp" onChange={(e) => handleFileSelect(e, 'profile_cover')} />
                </div>
                <small className="upload-hint">Рекомендуемый размер: 1400x300 px</small>
              </div>

              <div className="form-group">
                <label>Общий фон страницы</label>
                <div className="image-upload-row">
                  <div className="preview-rect">
                    {formData.page_background ? <img src={formData.page_background} alt="Page BG" /> : <div className="placeholder">Стандартный</div>}
                  </div>
                  <input type="file" accept=".png, .jpg, .jpeg, .webp" onChange={(e) => handleFileSelect(e, 'page_background')} />
                </div>
                <small className="upload-hint">Рекомендуемый размер: 1920x1080 px (или бесшовная текстура)</small>
              </div>

              <div className="form-group">
                <label>Фон блока проектов</label>
                <div className="image-upload-row">
                  <div className="preview-rect">
                    {formData.projects_background ? <img src={formData.projects_background} alt="Projects BG" /> : <div className="placeholder">Стандартный</div>}
                  </div>
                  <input type="file" accept=".png, .jpg, .jpeg, .webp" onChange={(e) => handleFileSelect(e, 'projects_background')} />
                </div>
                <small className="upload-hint">Рекомендуемый размер: 1400x800 px</small>
              </div>

              <div className="form-group">
                <label>Цвет карточек проектов</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input 
                    type="color" 
                    name="card_color" 
                    value={formData.card_color} 
                    onChange={handleInputChange} 
                    style={{ width: '50px', height: '40px', padding: '0', border: 'none' }}
                  />
                  <span>{formData.card_color}</span>
                </div>
              </div>
            </div>

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

      {/* Модальное окно кроппера */}
      {cropperImage && (
        <ImageCropper 
          imageSrc={cropperImage} 
          onCrop={handleCropComplete} 
          onCancel={() => setCropperImage(null)}
          circular={cropperField === 'avatar'}
        />
      )}
    </div>
  );
};

export default ProfileSettingsPage;