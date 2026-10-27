import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { API_ENDPOINTS } from '../config/api';

const ReportMissing = () => {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    lastSeenLocation: '',
    image: null
  });
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);

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
      reader.onload = (e) => {
        setImagePreview(e.target.result);
        setFormData(prev => ({
          ...prev,
          image: e.target.result
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(API_ENDPOINTS.REPORT_MISSING, formData);
      
      if (response.data.id) {
        toast.success('Missing person reported successfully!');
        // Reset form
        setFormData({
          name: '',
          age: '',
          gender: '',
          lastSeenLocation: '',
          image: null
        });
        setImagePreview(null);
        document.getElementById('imageInput').value = '';
      }
    } catch (error) {
      console.error('Error reporting missing person:', error);
      const msg =
        error?.response?.data?.error ||
        error?.response?.data?.message ||
        error?.message ||
        'Failed to report missing person. Please try again.';
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
            <div className="card-header bg-danger text-white">
              <h2 className="card-title mb-0">
                <i className="bi bi-person-x me-2"></i>
                Report Missing Person
              </h2>
            </div>
            <div className="card-body p-4">
              <form onSubmit={handleSubmit}>
                {/* Image Upload */}
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

                {/* Name */}
                <div className="mb-3">
                  <label className="form-label fw-bold">Name *</label>
                  <input
                    type="text"
                    className="form-control"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                {/* Age */}
                <div className="mb-3">
                  <label className="form-label fw-bold">Age *</label>
                  <input
                    type="number"
                    className="form-control"
                    name="age"
                    value={formData.age}
                    onChange={handleInputChange}
                    min="0"
                    max="120"
                    required
                  />
                </div>

                {/* Gender */}
                <div className="mb-3">
                  <label className="form-label fw-bold">Gender *</label>
                  <select
                    className="form-select"
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="">Select Gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                {/* Last Seen Location */}
                <div className="mb-4">
                  <label className="form-label fw-bold">Last Seen Location *</label>
                  <input
                    type="text"
                    className="form-control"
                    name="lastSeenLocation"
                    value={formData.lastSeenLocation}
                    onChange={handleInputChange}
                    placeholder="Enter address, city, or landmark"
                    required
                  />
                </div>

                {/* Submit Button */}
                <div className="d-grid">
                  <button
                    type="submit"
                    className="btn btn-danger btn-lg"
                    disabled={loading}
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

export default ReportMissing;
