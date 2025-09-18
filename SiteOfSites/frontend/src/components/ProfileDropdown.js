import React, { useState, useRef, useEffect } from 'react';

const ProfileDropdown = ({ user, onLogout }) => {
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
          <button className="profile-menu-item" onClick={() => setIsOpen(false)}>
            Личный кабинет
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

