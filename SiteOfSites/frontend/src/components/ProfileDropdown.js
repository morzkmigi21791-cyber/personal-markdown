import React, { useState, useRef, useEffect } from 'react';

const ProfileDropdown = ({ user, onLogout, onProfileClick, onSettingsClick }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = () => {
    onLogout();
    setIsOpen(false);
  };

  const handleProfileClick = () => {
    onProfileClick();
    setIsOpen(false);
  };

  const handleSettingsClick = () => {
    onSettingsClick();
    setIsOpen(false);
  };

  const getInitials = (nickname) => {
    return nickname ? nickname.charAt(0).toUpperCase() : 'U';
  };

  return (
    <div className="profile-dropdown" ref={dropdownRef}>
      <button 
        className="profile-button"
        onClick={() => setIsOpen(!isOpen)}
        title={user.nickname || user.email}
      >
        {getInitials(user.nickname)}
      </button>
      
      {isOpen && (
        <div className="profile-menu">
          <button className="profile-menu-item" onClick={handleProfileClick}>
            Мой профиль
          </button>
          <button className="profile-menu-item" onClick={handleSettingsClick}>
            Настройки
          </button>
          <button className="profile-menu-item" onClick={handleLogout}>
            Выйти
          </button>
        </div>
      )}
    </div>
  );
};

export default ProfileDropdown;

