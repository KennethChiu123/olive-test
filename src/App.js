import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const API_BASE = '/api/dogs';

function App() {
  const [dogs, setDogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('/api/stats');
      if (response.ok) {
        const data = await response.json();
        setTotalPages(data.total_pages || 1);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  const fetchDogs = useCallback(async (page) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}?page=${page}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.length === 0 && page > 1) {
        setError(`No data available for page ${page}. Try page 1.`);
        return;
      }
      
      setDogs(data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching dogs:', err);
      setError(`Failed to fetch dogs: ${err.message}`);
      setLoading(false);
      setDogs([]);
    }
  }, []);

  useEffect(() => {
    fetchDogs(currentPage);
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Generate page numbers with ellipsis (Google/GitHub style)
  const generatePageNumbers = () => {
    const pages = [];
    const delta = 2; // Show 2 pages on each side of current
    
    for (let i = 1; i <= totalPages; i++) {
      if (
        i === 1 || // First page
        i === totalPages || // Last page
        (i >= currentPage - delta && i <= currentPage + delta) // Near current
      ) {
        pages.push(i);
      } else if (pages[pages.length - 1] !== '...') {
        pages.push('...');
      }
    }
    
    return pages;
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Dog Breeds</h1>
        <p className="subtitle">Browse our collection of dog breeds</p>
      </header>

      <div className="container">
        {/* Error Display */}
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading dogs...</p>
          </div>
        )}

        {/* Dogs Grid */}
        {!loading && dogs.length > 0 && (
          <div className="dogs-grid">
            {dogs.map((dog, index) => (
              <div key={index} className="dog-card">
                <img
                  src={dog.image || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2UyZThmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjQ4IiBmaWxsPSIjNjQ3NDhiIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj7wn5CVPC90ZXh0Pjwvc3ZnPg=='}
                  alt={dog.breed}
                  className="dog-image"
                  onError={(e) => {
                    // Use inline SVG as fallback for broken images
                    e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2UyZThmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjQ4IiBmaWxsPSIjNjQ3NDhiIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj7wn5CVPC90ZXh0Pjwvc3ZnPg==';
                    e.target.style.objectFit = 'contain';
                  }}
                />
                <h3 className="dog-breed">{dog.breed}</h3>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && dogs.length === 0 && !error && (
          <div className="empty-state">
            <p>No dogs found for this page.</p>
            <button
              onClick={() => handlePageChange(1)}
              className="back-to-start-button"
            >
              Go to Page 1
            </button>
          </div>
        )}

        {/* Pagination Controls at Bottom - Modern numbered style */}
        {!loading && totalPages > 0 && (
          <div className="pagination-wrapper">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="pagination-arrow"
              aria-label="Previous page"
            >
              ←
            </button>

            <div className="pagination-numbers">
              {generatePageNumbers().map((pageNum, index) => (
                pageNum === '...' ? (
                  <span key={`ellipsis-${index}`} className="pagination-ellipsis">
                    ...
                  </span>
                ) : (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    className={`pagination-number ${currentPage === pageNum ? 'active' : ''}`}
                    aria-label={`Go to page ${pageNum}`}
                    aria-current={currentPage === pageNum ? 'page' : undefined}
                  >
                    {pageNum}
                  </button>
                )
              ))}
            </div>

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="pagination-arrow"
              aria-label="Next page"
            >
              →
            </button>
          </div>
        )}

        {/* Info Display */}
        <div className="info-bar">
          {dogs.length > 0 && (
            <span className="item-count">
              Showing {dogs.length} dogs on page {currentPage} of {totalPages}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
