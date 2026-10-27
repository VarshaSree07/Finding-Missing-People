import React from 'react';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="container">
        <div className="row">
          <div className="col-md-6">
            <h5>AI Missing Person Finder</h5>
            <p className="mb-0">
              Using advanced facial recognition technology to help reunite families.
            </p>
          </div>
          <div className="col-md-6 text-md-end">
            <h6>Quick Links</h6>
            <div className="d-flex flex-column flex-md-row justify-content-md-end">
              <a href="/" className="text-light me-3 mb-1">Home</a>
              <a href="/report-missing" className="text-light me-3 mb-1">Report Missing</a>
              <a href="/report-found" className="text-light me-3 mb-1">Report Found</a>
              <a href="/matches" className="text-light mb-1">Matches</a>
            </div>
          </div>
        </div>
        <hr className="my-4" />
        <div className="row">
          <div className="col-12 text-center">
            <p className="mb-0">
              &copy; 2024 AI Missing Person Finder. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
