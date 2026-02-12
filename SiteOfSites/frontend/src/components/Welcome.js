import React from 'react';

const Welcome = () => {
  return (
    <div className="welcome">
      <h1>Site of Sites</h1>
      <p className="subtitle">
        Ваше пространство для творчества. Создавайте, кастомизируйте и делитесь своими веб-проектами с миром.
      </p>

      <div className="features-grid">
        <div className="feature-card">
          <span className="feature-icon">🚀</span>
          <h3>Мгновенный хостинг</h3>
          <p>Загружайте HTML, CSS и JS файлы, и ваш сайт сразу станет доступен онлайн. Никаких сложных настроек серверов.</p>
        </div>
        <div className="feature-card">
          <span className="feature-icon">🎨</span>
          <h3>Полная кастомизация</h3>
          <p>Настройте профиль под себя: меняйте фоны, цвета карточек и аватарку. Сделайте свою страницу уникальной.</p>
        </div>
        <div className="feature-card">
          <span className="feature-icon">🌐</span>
          <h3>Личные поддомены</h3>
          <p>Каждый проект получает свой уникальный адрес (например, <code>project.localhost</code>), которым легко поделиться.</p>
        </div>
        <div className="feature-card">
          <span className="feature-icon">🔒</span>
          <h3>Приватность</h3>
          <p>Вы сами решаете, кто видит ваши проекты: только вы, пользователи с ссылкой или весь мир.</p>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
