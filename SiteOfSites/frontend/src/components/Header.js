import React, { useState } from 'react';
import ProfileDropdown from './ProfileDropdown';
import SearchBar from './SearchBar';

const Header = ({ user, onLoginClick, onRegisterClick, onLogout, onProfileClick, onSettingsClick, onUserSelect }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="header">
      <div className="header-left">
        <a href="/" className="logo">Site of Sites</a>
        <button className="mobile-menu-toggle" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          {isMenuOpen ? '✕' : '☰'}
        </button>
      </div>
      
      <div className={`header-center ${isMenuOpen ? 'active' : ''}`}>
        <SearchBar onUserSelect={onUserSelect} />
      </div>
      
      <div className={`header-right ${isMenuOpen ? 'active' : ''}`}>
        {user ? (
          <ProfileDropdown 
            user={user} 
            onLogout={onLogout} 
            onProfileClick={onProfileClick}
            onSettingsClick={onSettingsClick}
          />
        ) : (
          <div className="auth-buttons">
            <button className="btn btn-secondary" onClick={onLoginClick}>
              Войти
            </button>
            <button className="btn btn-primary" onClick={onRegisterClick}>
              Регистрация
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
