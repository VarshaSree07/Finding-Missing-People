import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const Dashboard = () => {
  const [reports, setReports] = useState([]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [map, setMap] = useState(null);
  const mapRef = useRef(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [reportsRes, matchesRes] = await Promise.all([
        axios.get('/api/reports'),
        axios.get('/api/matches')
      ]);

      setReports(reportsRes.data);
      setMatches(matchesRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Initialize map when reports are loaded
  useEffect(() => {
    if (reports.length > 0 && !map) {
      initializeMap();
    }
  }, [reports, map]);

  const initializeMap = () => {
    if (mapRef.current && !map) {
      const newMap = L.map(mapRef.current).setView([40.7128, -74.0060], 10);
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(newMap);

      // Add markers for each report
      reports.forEach(report => {
        if (report.latitude && report.longitude) {
          const markerColor = report.type === 'missing' ? 'red' : 'green';
          const icon = L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color: ${markerColor}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          });

          const marker = L.marker([report.latitude, report.longitude], { icon })
            .addTo(newMap);

          marker.bindPopup(`
            <div>
              <h6>${report.name}</h6>
              <p><strong>Type:</strong> ${report.type}</p>
              <p><strong>Age:</strong> ${report.age}</p>
              <p><strong>Gender:</strong> ${report.gender}</p>
              <p><strong>Location:</strong> ${report.lastSeenLocation || report.address}</p>
              <p><strong>Date:</strong> ${new Date(report.created_at).toLocaleDateString()}</p>
            </div>
          `);
        }
      });

      setMap(newMap);
    }
  };

  const handleVerifyMatch = async (matchId) => {
    try {
      await axios.put(`/api/matches/${matchId}`, { status: 'verified' });
      toast.success('Match verified successfully!');
      fetchDashboardData();
    } catch (error) {
      console.error('Error verifying match:', error);
      toast.error('Failed to verify match');
    }
  };

  const handleRejectMatch = async (matchId) => {
    try {
      await axios.put(`/api/matches/${matchId}`, { status: 'rejected' });
      toast.success('Match rejected');
      fetchDashboardData();
    } catch (error) {
      console.error('Error rejecting match:', error);
      toast.error('Failed to reject match');
    }
  };

  const getStatusBadge = (type) => {
    return type === 'missing' ? 
      <span className="badge bg-danger">Missing</span> : 
      <span className="badge bg-success">Found</span>;
  };

  const getMatchStatusBadge = (status) => {
    const statusConfig = {
      pending: { class: 'bg-warning', text: 'Pending' },
      verified: { class: 'bg-success', text: 'Verified' },
      rejected: { class: 'bg-danger', text: 'Rejected' }
    };
    
    const config = statusConfig[status] || statusConfig.pending;
    return (
      <span className={`badge ${config.class} text-white`}>
        {config.text}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="container py-5">
        <div className="loading-spinner">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid py-4">
      {/* Header */}
      <div className="row mb-4">
        <div className="col-12">
          <h2>
            <i className="bi bi-graph-up me-2"></i>
            Admin Dashboard
          </h2>
          <p className="text-muted">Overview of all reports and potential matches</p>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="row g-4 mb-4">
        <div className="col-md-3">
          <div className="card bg-danger text-white">
            <div className="card-body">
              <div className="d-flex justify-content-between">
                <div>
                  <h4 className="card-title">{reports.filter(r => r.type === 'missing').length}</h4>
                  <p className="card-text">Missing Persons</p>
                </div>
                <div className="align-self-center">
                  <i className="bi bi-person-x" style={{ fontSize: '2rem' }}></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-md-3">
          <div className="card bg-success text-white">
            <div className="card-body">
              <div className="d-flex justify-content-between">
                <div>
                  <h4 className="card-title">{reports.filter(r => r.type === 'found').length}</h4>
                  <p className="card-text">Found Persons</p>
                </div>
                <div className="align-self-center">
                  <i className="bi bi-person-check" style={{ fontSize: '2rem' }}></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-md-3">
          <div className="card bg-warning text-white">
            <div className="card-body">
              <div className="d-flex justify-content-between">
                <div>
                  <h4 className="card-title">{matches.filter(m => m.status === 'pending').length}</h4>
                  <p className="card-text">Pending Matches</p>
                </div>
                <div className="align-self-center">
                  <i className="bi bi-clock" style={{ fontSize: '2rem' }}></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-md-3">
          <div className="card bg-primary text-white">
            <div className="card-body">
              <div className="d-flex justify-content-between">
                <div>
                  <h4 className="card-title">{matches.filter(m => m.status === 'verified').length}</h4>
                  <p className="card-text">Verified Matches</p>
                </div>
                <div className="align-self-center">
                  <i className="bi bi-check-circle" style={{ fontSize: '2rem' }}></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="row g-4">
        {/* Reports Table */}
        <div className="col-lg-8">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="card-title mb-0">
                <i className="bi bi-table me-2"></i>
                All Reports
              </h5>
              <button 
                className="btn btn-outline-primary btn-sm"
                onClick={fetchDashboardData}
              >
                <i className="bi bi-arrow-clockwise me-1"></i>
                Refresh
              </button>
            </div>
            <div className="card-body">
              {reports.length === 0 ? (
                <div className="text-center py-4">
                  <i className="bi bi-inbox text-muted" style={{ fontSize: '3rem' }}></i>
                  <p className="text-muted mt-2">No reports available</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>Gender</th>
                        <th>Location</th>
                        <th>Date</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reports.map((report, index) => (
                        <tr key={index}>
                          <td>{getStatusBadge(report.type)}</td>
                          <td>{report.name}</td>
                          <td>{report.age}</td>
                          <td className="text-capitalize">{report.gender}</td>
                          <td>
                            {report.type === 'missing' ? 
                              report.lastSeenLocation : 
                              report.address || 'Not specified'
                            }
                          </td>
                          <td>{new Date(report.created_at).toLocaleDateString()}</td>
                          <td>
                            <button className="btn btn-sm btn-outline-primary">
                              <i className="bi bi-eye"></i>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Map */}
        <div className="col-lg-4">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="bi bi-geo-alt me-2"></i>
                Location Map
              </h5>
            </div>
            <div className="card-body p-0">
              <div 
                ref={mapRef} 
                style={{ height: '400px', width: '100%' }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Matches Section */}
      {matches.length > 0 && (
        <div className="row mt-4">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h5 className="card-title mb-0">
                  <i className="bi bi-people me-2"></i>
                  Potential Matches
                </h5>
              </div>
              <div className="card-body">
                <div className="row g-3">
                  {matches.map((match) => {
                    const missingPerson = reports.find(r => r._id === match.missing_person_id && r.type === 'missing');
                    const foundPerson = reports.find(r => r._id === match.found_person_id && r.type === 'found');
                    
                    if (!missingPerson || !foundPerson) return null;

                    const confidencePercentage = Math.round(match.similarity_score * 100);

                    return (
                      <div key={match._id} className="col-md-6">
                        <div className="card border">
                          <div className="card-body">
                            <div className="d-flex justify-content-between align-items-start mb-3">
                              <h6 className="card-title">Match #{match._id.slice(-6)}</h6>
                              {getMatchStatusBadge(match.status)}
                            </div>
                            
                            <div className="row">
                              <div className="col-6">
                                <h6 className="text-danger small">Missing: {missingPerson.name}</h6>
                                <p className="small text-muted mb-1">Age: {missingPerson.age}</p>
                                <p className="small text-muted">Location: {missingPerson.lastSeenLocation}</p>
                              </div>
                              <div className="col-6">
                                <h6 className="text-success small">Found: Person</h6>
                                <p className="small text-muted mb-1">Found at: {foundPerson.address}</p>
                                <p className="small text-muted">Date: {new Date(foundPerson.created_at).toLocaleDateString()}</p>
                              </div>
                            </div>

                            <div className="alert alert-info py-2 mb-3">
                              <small>
                                <i className="bi bi-percent me-1"></i>
                                Confidence: {confidencePercentage}%
                              </small>
                            </div>

                            {match.status === 'pending' && (
                              <div className="d-flex gap-2">
                                <button
                                  className="btn btn-success btn-sm"
                                  onClick={() => handleVerifyMatch(match._id)}
                                >
                                  <i className="bi bi-check-circle me-1"></i>
                                  Verify
                                </button>
                                <button
                                  className="btn btn-danger btn-sm"
                                  onClick={() => handleRejectMatch(match._id)}
                                >
                                  <i className="bi bi-x-circle me-1"></i>
                                  Reject
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
