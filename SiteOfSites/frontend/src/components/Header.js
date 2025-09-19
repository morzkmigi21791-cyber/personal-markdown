import React from 'react';
import ProfileDropdown from './ProfileDropdown';
import SearchBar from './SearchBar';

const Header = ({ user, onLoginClick, onRegisterClick, onLogout, onProfileClick, onSettingsClick, onUserSelect }) => {
  return (
    <header className="header">
      <div className="header-left">
        <a href="/" className="logo">Site of Sites</a>
      </div>
      
      <div className="header-center">
        <SearchBar onUserSelect={onUserSelect} />
      </div>
      
      <div className="header-right">
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

