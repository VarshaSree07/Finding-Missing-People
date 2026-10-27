import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { API_ENDPOINTS } from '../config/api';

const MODES = {
  IMAGE: 'IMAGE',
  VIDEO: 'VIDEO',
};

const ReportFound = () => {
  const [mode, setMode] = useState(MODES.IMAGE);
  const [formData, setFormData] = useState({
    image: null,      // base64 string for IMAGE mode
    latitude: null,
    longitude: null,
    address: '',
    description: ''
  });
  const [imagePreview, setImagePreview] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState('');

  // Auto-fetch geolocation on component mount
  useEffect(() => {
    getCurrentLocation();
  }, []);

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by this browser.');
      return;
    }

    setLocationLoading(true);
    setLocationError('');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setFormData(prev => ({
          ...prev,
          latitude,
          longitude
        }));
        setLocationLoading(false);
        toast.success('Location detected successfully!');
        
        // Optionally reverse geocode to get address
        reverseGeocode(latitude, longitude);
      },
      (error) => {
        setLocationLoading(false);
        let errorMessage = 'Unable to retrieve your location.';
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location access denied by user.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information is unavailable.';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out.';
            break;
        }
        
        setLocationError(errorMessage);
        toast.error(errorMessage);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  };

  const reverseGeocode = async (lat, lng) => {
    try {
      const response = await axios.post(API_ENDPOINTS.REVERSE_GEOCODE, {
        lat: lat,
        lng: lng
      });
      
      if (response.data.formatted_address) {
        setFormData(prev => ({
          ...prev,
          address: response.data.formatted_address
        }));
      }
    } catch (error) {
      console.error('Reverse geocoding failed:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setImagePreview(ev.target.result);
        setFormData(prev => ({
          ...prev,
          image: ev.target.result
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleVideoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoFile(file);
    } else {
      setVideoFile(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (mode === MODES.IMAGE) {
        const response = await axios.post(API_ENDPOINTS.REPORT_FOUND, formData);
        if (response.data.id) {
          toast.success('Found person reported successfully (image)!');
          setFormData({
            image: null,
            latitude: null,
            longitude: null,
            address: '',
            description: ''
          });
          setImagePreview(null);
          setVideoFile(null);
          const imgInput = document.getElementById('imageInput');
          if (imgInput) imgInput.value = '';
          setLocationError('');
        }
      } else if (mode === MODES.VIDEO) {
        if (!videoFile) {
          toast.error('Please select a video file.');
          return;
        }

        const form = new FormData();
        form.append('video', videoFile);
        if (formData.latitude != null) form.append('latitude', formData.latitude);
        if (formData.longitude != null) form.append('longitude', formData.longitude);
        if (formData.address) form.append('address', formData.address);
        if (formData.description) form.append('description', formData.description);

        const response = await axios.post(API_ENDPOINTS.UPLOAD_VIDEO, form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        if (response.data && response.data.faces_detected >= 0) {
          toast.success('Video processed successfully!');
          setVideoFile(null);
        }
      }
    } catch (error) {
      console.error('Error reporting found person:', error);
      const msg =
        error?.response?.data?.error ||
        error?.response?.data?.message ||
        error?.message ||
        'Failed to report found person. Please try again.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-lg-6">
          <div className="card shadow">
            <div className="card-header bg-success text-white">
              <h2 className="card-title mb-0">
                <i className="bi bi-person-check me-2"></i>
                Report Found Person
              </h2>
            </div>
            <div className="card-body p-4">
              <form onSubmit={handleSubmit}>
                {/* Mode selector */}
                <div className="mb-3">
                  <label className="form-label fw-bold">Report Type</label>
                  <div className="btn-group w-100" role="group">
                    <button
                      type="button"
                      className={`btn ${mode === MODES.IMAGE ? 'btn-outline-success active' : 'btn-outline-success'}`}
                      onClick={() => setMode(MODES.IMAGE)}
                    >
                      Image
                    </button>
                    <button
                      type="button"
                      className={`btn ${mode === MODES.VIDEO ? 'btn-outline-success active' : 'btn-outline-success'}`}
                      onClick={() => setMode(MODES.VIDEO)}
                    >
                      Video
                    </button>
                  </div>
                </div>

                {/* Image Upload (IMAGE mode) */}
                {mode === MODES.IMAGE && (
                  <div className="mb-4">
                    <label className="form-label fw-bold">Upload Photo *</label>
                    <div className="border rounded p-3 text-center">
                      {imagePreview ? (
                        <div>
                          <img 
                            src={imagePreview} 
                            alt="Preview" 
                            className="img-fluid rounded mb-3"
                            style={{ maxHeight: '200px' }}
                          />
                          <input
                            id="imageInput"
                            type="file"
                            className="form-control"
                            accept="image/*"
                            onChange={handleImageChange}
                            required
                          />
                        </div>
                      ) : (
                        <div>
                          <i className="bi bi-camera text-muted" style={{ fontSize: '3rem' }}></i>
                          <p className="text-muted mt-2">Click to upload photo</p>
                          <input
                            id="imageInput"
                            type="file"
                            className="form-control"
                            accept="image/*"
                            onChange={handleImageChange}
                            required
                          />
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Video Upload (VIDEO mode) */}
                {mode === MODES.VIDEO && (
                  <div className="mb-4">
                    <label className="form-label fw-bold">Upload Video *</label>
                    <input
                      type="file"
                      className="form-control"
                      accept="video/*"
                      onChange={handleVideoChange}
                      required
                    />
                    <small className="text-muted">
                      Supported formats: mp4, avi, etc. Only key frames are processed for performance.
                    </small>
                  </div>
                )}

                {/* Location Information */}
                <div className="mb-4">
                  <label className="form-label fw-bold">Location Information</label>
                  
                  {locationLoading ? (
                    <div className="alert alert-info d-flex align-items-center">
                      <div className="spinner-border spinner-border-sm me-2" role="status"></div>
                      Detecting your location...
                    </div>
                  ) : locationError ? (
                    <div className="alert alert-warning">
                      <i className="bi bi-exclamation-triangle me-2"></i>
                      {locationError}
                      <button 
                        type="button" 
                        className="btn btn-sm btn-outline-warning ms-2"
                        onClick={getCurrentLocation}
                      >
                        Try Again
                      </button>
                    </div>
                  ) : formData.latitude && formData.longitude ? (
                    <div className="alert alert-success">
                      <i className="bi bi-geo-alt me-2"></i>
                      Location detected successfully!
                    </div>
                  ) : null}

                  {/* Coordinates Display */}
                  {formData.latitude && formData.longitude && (
                    <div className="row mb-3">
                      <div className="col-md-6">
                        <label className="form-label">Latitude</label>
                        <input
                          type="text"
                          className="form-control"
                          value={formData.latitude}
                          readOnly
                        />
                      </div>
                      <div className="col-md-6">
                        <label className="form-label">Longitude</label>
                        <input
                          type="text"
                          className="form-control"
                          value={formData.longitude}
                          readOnly
                        />
                      </div>
                    </div>
                  )}

                  {/* Address */}
                  <div className="mb-3">
                    <label className="form-label">Address</label>
                    <input
                      type="text"
                      className="form-control"
                      name="address"
                      value={formData.address}
                      onChange={handleInputChange}
                      placeholder="Detected address will appear here"
                    />
                  </div>
                </div>

                {/* Description */}
                <div className="mb-4">
                  <label className="form-label fw-bold">Additional Information</label>
                  <textarea
                    className="form-control"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    rows="3"
                    placeholder="Any additional details about the found person..."
                  />
                </div>

                {/* Submit Button */}
                <div className="d-grid">
                  <button
                    type="submit"
                    className="btn btn-success btn-lg"
                    disabled={
                      loading ||
                      (mode === MODES.IMAGE && !formData.image) ||
                      (mode === MODES.VIDEO && !videoFile)
                    }
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                        Submitting...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-send me-2"></i>
                        Submit Report
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportFound;
