import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './SearchBar.css';

const SearchBar = ({ onUserSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const searchRef = useRef(null);
  const resultsRef = useRef(null);

  // Обработка поиска с задержкой
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (query.length >= 2) {
        performSearch(query);
      } else {
        setResults([]);
        setShowResults(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query]);

  // Закрытие результатов при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const performSearch = async (searchQuery) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/users/search?q=${encodeURIComponent(searchQuery)}`);
      setResults(response.data);
      setShowResults(true);
    } catch (error) {
      console.error('Ошибка поиска:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUserClick = (user) => {
    setQuery('');
    setShowResults(false);
    if (onUserSelect) {
      onUserSelect(user);
    }
  };

  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  const handleInputFocus = () => {
    if (results.length > 0) {
      setShowResults(true);
    }
  };

  return (
    <div className="search-container" ref={searchRef}>
      <div className="search-input-wrapper">
        <input
          type="text"
          className="search-input"
          placeholder="Поиск пользователей по имени или ID..."
          value={query}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
        />
        {loading && <div className="search-loading">⟳</div>}
      </div>
      
      {showResults && (
        <div className="search-results" ref={resultsRef}>
          {results.length > 0 ? (
            results.map((user) => (
              <div
                key={user.id}
                className="search-result-item"
                onClick={() => handleUserClick(user)}
              >
                <div className="search-result-avatar">
                  {user.avatar ? (
                    <img src={user.avatar} alt={user.nickname} />
                  ) : (
                    <div className="default-avatar">
                      {user.nickname.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>
                <div className="search-result-info">
                  <div className="search-result-nickname">{user.nickname}</div>
                  <div className="search-result-id">ID: {user.unique_id}</div>
                </div>
              </div>
            ))
          ) : (
            <div className="search-no-results">
              {query.length >= 2 ? 'Пользователи не найдены' : 'Введите минимум 2 символа'}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;

