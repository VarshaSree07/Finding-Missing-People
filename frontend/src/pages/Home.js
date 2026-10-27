import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div className="container-fluid">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-lg-8 text-center">
              <h1 className="display-3 fw-bold mb-4">
                AI Missing Person Finder
              </h1>
              <p className="lead mb-5">
                Our advanced facial recognition technology helps reunite families by matching 
                missing persons with found individuals. Upload photos and let our AI do the work 
                to help bring loved ones home.
              </p>
              
              {/* Action Buttons */}
              <div className="d-flex flex-column flex-md-row justify-content-center gap-4">
                <Link 
                  className="btn btn-danger btn-lg px-5 py-3" 
                  to="/report-missing"
                  style={{ fontSize: '1.2rem', minWidth: '200px' }}
                >
                  <i className="bi bi-person-x me-2"></i>
                  Report Missing
                </Link>
                <Link 
                  className="btn btn-success btn-lg px-5 py-3" 
                  to="/report-found"
                  style={{ fontSize: '1.2rem', minWidth: '200px' }}
                >
                  <i className="bi bi-person-check me-2"></i>
                  Report Found
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
