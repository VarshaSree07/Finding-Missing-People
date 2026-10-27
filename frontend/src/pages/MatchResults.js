import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

const MatchResults = () => {
  const [matches, setMatches] = useState([]);
  const [missingPersons, setMissingPersons] = useState([]);
  const [foundPersons, setFoundPersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingMatch, setProcessingMatch] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [matchesRes, missingRes, foundRes] = await Promise.all([
        axios.get('/api/matches'),
        axios.get('/api/missing-persons'),
        axios.get('/api/found-persons')
      ]);

      setMatches(matchesRes.data);
      setMissingPersons(missingRes.data);
      setFoundPersons(foundRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load match data');
    } finally {
      setLoading(false);
    }
  };

  const getPersonById = (id, type) => {
    const persons = type === 'missing' ? missingPersons : foundPersons;
    return persons.find(person => person._id === id);
  };

  const handleVerifyMatch = async (matchId) => {
    setProcessingMatch(matchId);
    try {
      // Update match status to verified
      await axios.put(`/api/matches/${matchId}`, { status: 'verified' });
      toast.success('Match verified successfully!');
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error verifying match:', error);
      toast.error('Failed to verify match');
    } finally {
      setProcessingMatch(null);
    }
  };

  const handleRejectMatch = async (matchId) => {
    setProcessingMatch(matchId);
    try {
      // Update match status to rejected
      await axios.put(`/api/matches/${matchId}`, { status: 'rejected' });
      toast.success('Match rejected');
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error rejecting match:', error);
      toast.error('Failed to reject match');
    } finally {
      setProcessingMatch(null);
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'danger';
  };

  const getStatusBadge = (status) => {
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
    <div className="container py-5">
      <div className="row">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2>
              <i className="bi bi-people me-2"></i>
              Match Results
            </h2>
            <button 
              className="btn btn-outline-primary"
              onClick={fetchData}
            >
              <i className="bi bi-arrow-clockwise me-1"></i>
              Refresh
            </button>
          </div>

          {matches.length === 0 ? (
            <div className="text-center py-5">
              <i className="bi bi-search text-muted" style={{ fontSize: '4rem' }}></i>
              <h4 className="text-muted mt-3">No matches found</h4>
              <p className="text-muted">Potential matches will appear here when found.</p>
            </div>
          ) : (
            <div className="row g-4">
              {matches.map((match) => {
                const missingPerson = getPersonById(match.missing_person_id, 'missing');
                const foundPerson = getPersonById(match.found_person_id, 'found');
                
                if (!missingPerson || !foundPerson) return null;

                const confidencePercentage = Math.round(match.similarity_score * 100);
                const confidenceColor = getConfidenceColor(match.similarity_score);

                return (
                  <div key={match._id} className="col-lg-6">
                    <div className="card h-100 shadow-sm">
                      <div className="card-header d-flex justify-content-between align-items-center">
                        <h5 className="mb-0">Potential Match</h5>
                        {getStatusBadge(match.status)}
                      </div>
                      
                      <div className="card-body">
                        <div className="row">
                          {/* Missing Person */}
                          <div className="col-md-6">
                            <div className="text-center">
                              <h6 className="text-danger mb-3">
                                <i className="bi bi-person-x me-1"></i>
                                Missing Person
                              </h6>
                              {missingPerson.image_path ? (
                                <img
                                  src={`/uploads/${missingPerson.image_path.split('/').pop()}`}
                                  alt="Missing person"
                                  className="img-fluid rounded mb-2"
                                  style={{ maxHeight: '200px', width: '100%', objectFit: 'cover' }}
                                  onError={(e) => {
                                    e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
                                  }}
                                />
                              ) : (
                                <div className="bg-light rounded d-flex align-items-center justify-content-center mb-2" style={{ height: '200px' }}>
                                  <i className="bi bi-person text-muted" style={{ fontSize: '3rem' }}></i>
                                </div>
                              )}
                              <h6 className="mb-1">{missingPerson.name}</h6>
                              <p className="text-muted small mb-0">
                                Age: {missingPerson.age} | {missingPerson.gender}
                              </p>
                              <p className="text-muted small">
                                Last seen: {missingPerson.lastSeenLocation}
                              </p>
                            </div>
                          </div>

                          {/* Found Person */}
                          <div className="col-md-6">
                            <div className="text-center">
                              <h6 className="text-success mb-3">
                                <i className="bi bi-person-check me-1"></i>
                                Found Person
                              </h6>
                              {foundPerson.image_path ? (
                                <img
                                  src={`/uploads/${foundPerson.image_path.split('/').pop()}`}
                                  alt="Found person"
                                  className="img-fluid rounded mb-2"
                                  style={{ maxHeight: '200px', width: '100%', objectFit: 'cover' }}
                                  onError={(e) => {
                                    e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg==';
                                  }}
                                />
                              ) : (
                                <div className="bg-light rounded d-flex align-items-center justify-content-center mb-2" style={{ height: '200px' }}>
                                  <i className="bi bi-person text-muted" style={{ fontSize: '3rem' }}></i>
                                </div>
                              )}
                              <h6 className="mb-1">Found Person</h6>
                              <p className="text-muted small mb-0">
                                Found at: {foundPerson.address || 'Location not specified'}
                              </p>
                              <p className="text-muted small">
                                Reported: {new Date(foundPerson.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Confidence Score */}
                        <div className="text-center mt-3">
                          <div className={`alert alert-${confidenceColor} mb-3`}>
                            <h5 className="mb-0">
                              <i className="bi bi-percent me-1"></i>
                              Confidence: {confidencePercentage}%
                            </h5>
                            <small>
                              {confidencePercentage >= 80 ? 'High confidence match' : 
                               confidencePercentage >= 60 ? 'Medium confidence match' : 
                               'Low confidence match'}
                            </small>
                          </div>
                        </div>

                        {/* Admin Actions */}
                        {match.status === 'pending' && (
                          <div className="d-grid gap-2 d-md-flex justify-content-md-center">
                            <button
                              className="btn btn-success"
                              onClick={() => handleVerifyMatch(match._id)}
                              disabled={processingMatch === match._id}
                            >
                              {processingMatch === match._id ? (
                                <>
                                  <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                                  Processing...
                                </>
                              ) : (
                                <>
                                  <i className="bi bi-check-circle me-1"></i>
                                  Verify Match
                                </>
                              )}
                            </button>
                            <button
                              className="btn btn-danger"
                              onClick={() => handleRejectMatch(match._id)}
                              disabled={processingMatch === match._id}
                            >
                              <i className="bi bi-x-circle me-1"></i>
                              Reject Match
                            </button>
                          </div>
                        )}

                        {/* Match Details */}
                        <div className="mt-3 pt-3 border-top">
                          <small className="text-muted">
                            <i className="bi bi-clock me-1"></i>
                            Match found: {new Date(match.created_at).toLocaleString()}
                          </small>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MatchResults;
