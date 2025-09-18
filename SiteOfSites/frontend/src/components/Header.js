import React from 'react';
import ProfileDropdown from './ProfileDropdown';

const Header = ({ user, onLoginClick, onRegisterClick, onLogout }) => {
  return (
    <header className="header">
      <div className="header-left">
        Site of Sites
      </div>
      <div className="header-right">
        {user ? (
          <ProfileDropdown user={user} onLogout={onLogout} />
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

