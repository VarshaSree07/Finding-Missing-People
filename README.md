# AI Missing Person Finder

A full-stack web application that uses advanced facial recognition technology to help reunite missing persons with their families. The system automatically matches photos of found persons with reported missing persons using AI and sends notifications for high-confidence matches.

## 🌟 Features

### Core Functionality
- **Facial Recognition**: Uses DeepFace with Facenet model for accurate face matching
- **Geographic Filtering**: Only considers matches within 200km radius using Haversine distance
- **Real-time Matching**: Automatic matching when found persons are reported
- **High-Confidence Notifications**: Email and SMS alerts for matches >90% confidence

### User Interface
- **Modern React Frontend**: Built with React 18 and Bootstrap 5
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Interactive Maps**: Google Maps integration for location services
- **Image Upload**: Drag-and-drop image upload with preview
- **Real-time Feedback**: Toast notifications and loading states

### Admin Features
- **Dashboard**: Comprehensive admin view with statistics and maps
- **Match Management**: Verify or reject potential matches
- **Data Visualization**: Location heatmaps and match analytics
- **Report Management**: View all missing and found person reports

## 🏗️ Architecture

### Frontend (React + Vercel)
- **Framework**: React 18 with React Router
- **Styling**: Bootstrap 5 with custom CSS
- **State Management**: React Hooks
- **HTTP Client**: Axios for API calls
- **Maps**: Google Maps API integration
- **Deployment**: Vercel with automatic deployments

### Backend (Flask + Render)
- **Framework**: Flask with CORS enabled
- **AI/ML**: DeepFace for facial recognition
- **Image Processing**: PIL and OpenCV
- **Geocoding**: Google Maps API
- **Notifications**: Twilio (SMS) and SendGrid (Email)
- **Deployment**: Render with Docker support

### Database (MongoDB Atlas)
- **Database**: MongoDB with PyMongo driver
- **Collections**: missing_persons, found_persons, matches
- **Indexing**: Optimized for facial embedding queries
- **Geographic**: Location-based queries with 2dsphere indexes

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.9+
- MongoDB Atlas account
- Google Maps API key
- Twilio account (optional)
- SendGrid account (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-missing-person-finder.git
   cd ai-missing-person-finder
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your API keys
   python app.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp env.production .env.local
   # Edit .env.local with your API URL
   npm start
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## 📦 Deployment

### Production Deployment
The application is designed for easy deployment across multiple platforms:

- **Frontend**: Deploy to Vercel
- **Backend**: Deploy to Render
- **Database**: MongoDB Atlas

See [deployment-guide.md](deployment-guide.md) for detailed instructions.

### Environment Variables

#### Backend (Render)
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=noreply@missingpersonfinder.com
FROM_NAME=AI Missing Person Finder
HIGH_CONFIDENCE_THRESHOLD=0.9
NOTIFICATION_ENABLED=true
FLASK_ENV=production
```

#### Frontend (Vercel)
```env
REACT_APP_API_URL=https://your-backend.onrender.com
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## 🔧 API Documentation

### Endpoints

#### Missing Persons
- `POST /api/report-missing` - Report a missing person
- `GET /api/missing-persons` - Get all missing persons

#### Found Persons
- `POST /api/report-found` - Report a found person
- `GET /api/found-persons` - Get all found persons

#### Matches
- `GET /api/matches` - Get all potential matches
- `PUT /api/matches/:id` - Update match status

#### Reports
- `GET /api/reports` - Get all reports (missing + found)

#### Geocoding
- `POST /api/geocode` - Convert address to coordinates
- `POST /api/reverse-geocode` - Convert coordinates to address

### Request/Response Examples

#### Report Missing Person
```json
POST /api/report-missing
{
  "name": "John Doe",
  "age": 25,
  "gender": "male",
  "lastSeenLocation": "123 Main St, New York, NY",
  "contactInfo": "family@email.com",
  "image": "data:image/jpeg;base64,..."
}

Response:
{
  "id": "64a1b2c3d4e5f6789abcdef0",
  "message": "Missing person reported successfully",
  "face_detected": true
}
```

#### Report Found Person
```json
POST /api/report-found
{
  "image": "data:image/jpeg;base64,...",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "address": "456 Oak Ave, New York, NY",
  "description": "Found near Central Park"
}

Response:
{
  "id": "64a1b2c3d4e5f6789abcdef1",
  "message": "Found person reported successfully",
  "face_detected": true,
  "matches_found": 2,
  "matches": [...]
}
```

## 🧠 AI/ML Features

### Facial Recognition
- **Model**: Facenet (128-dimensional embeddings)
- **Similarity**: Cosine similarity for matching
- **Threshold**: 60% minimum for potential matches
- **High Confidence**: 90%+ triggers notifications

### Geographic Filtering
- **Algorithm**: Haversine distance formula
- **Radius**: 200km maximum distance
- **Accuracy**: Accounts for Earth's curvature
- **Performance**: Optimized for real-time matching

### Image Processing
- **Format Support**: JPEG, PNG, WebP
- **Face Detection**: OpenCV-based detection
- **Preprocessing**: Automatic image optimization
- **Storage**: Secure file storage with unique naming

## 📊 Database Schema

### Missing Persons Collection
```json
{
  "_id": "ObjectId",
  "name": "string",
  "age": "number",
  "gender": "string",
  "lastSeenLocation": "string",
  "latitude": "number",
  "longitude": "number",
  "formatted_address": "string",
  "contactInfo": "string",
  "image_path": "string",
  "face_embedding": [128 numbers],
  "created_at": "datetime",
  "status": "missing"
}
```

### Matches Collection
```json
{
  "_id": "ObjectId",
  "missing_person_id": "string",
  "found_person_id": "string",
  "similarity_score": "number",
  "distance_km": "number",
  "created_at": "datetime",
  "status": "pending|verified|rejected"
}
```

## 🔐 Security Features

- **CORS**: Configured for production domains
- **Environment Variables**: Sensitive data not committed
- **Input Validation**: Server-side validation for all inputs
- **Image Security**: Secure file upload and storage
- **Database**: MongoDB Atlas with IP whitelisting
- **HTTPS**: All production traffic encrypted

## 📈 Performance Optimizations

### Backend
- **Async Processing**: Non-blocking facial recognition
- **Database Indexing**: Optimized queries for embeddings
- **Caching**: Model caching for DeepFace
- **Error Handling**: Comprehensive error management

### Frontend
- **Code Splitting**: Lazy loading of components
- **Image Optimization**: Compressed image uploads
- **Caching**: API response caching
- **Bundle Optimization**: Minimized production builds

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm test
```

### Integration Testing
- API endpoint testing
- Database integration testing
- Facial recognition accuracy testing
- Notification system testing

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For support and questions:
- Create an issue on GitHub
- Check the [deployment guide](deployment-guide.md)
- Review the API documentation

## 🙏 Acknowledgments

- **DeepFace**: Facial recognition library
- **Google Maps**: Geocoding and mapping services
- **Twilio**: SMS notification service
- **SendGrid**: Email notification service
- **MongoDB Atlas**: Database hosting
- **Vercel**: Frontend hosting
- **Render**: Backend hosting

## 📊 Roadmap

### Phase 1 (Current)
- ✅ Basic facial recognition
- ✅ Geographic filtering
- ✅ Notification system
- ✅ Web interface

### Phase 2 (Planned)
- 🔄 Mobile app (React Native)
- 🔄 Advanced AI models
- 🔄 Real-time chat system
- 🔄 Police integration

### Phase 3 (Future)
- 🔄 Blockchain verification
- 🔄 Multi-language support
- 🔄 Advanced analytics
- 🔄 Global deployment

---

**Made with ❤️ to help reunite families**
