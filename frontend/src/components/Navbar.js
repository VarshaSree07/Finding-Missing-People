import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
        <Link className="navbar-brand" to="/">
          <i className="bi bi-search-heart me-2"></i>
          AI Missing Person Finder
        </Link>
        
        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link className="nav-link" to="/">
                <i className="bi bi-house me-1"></i>Home
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/matches">
                <i className="bi bi-people me-1"></i>Matches
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/dashboard">
                <i className="bi bi-graph-up me-1"></i>Dashboard
              </Link>
            </li>
          </ul>
          
          <div className="d-flex">
            <Link className="btn btn-outline-light me-2" to="/report-missing">
              <i className="bi bi-plus-circle me-1"></i>Report Missing
            </Link>
            <Link className="btn btn-primary" to="/report-found">
              <i className="bi bi-check-circle me-1"></i>Report Found
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
