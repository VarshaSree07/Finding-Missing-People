# AI Missing Person Finder - Deployment Guide

This guide covers deploying the AI Missing Person Finder application across three platforms:
- **Frontend**: Vercel
- **Backend**: Render
- **Database**: MongoDB Atlas

## 🗄️ Database Setup (MongoDB Atlas)

### 1. Create MongoDB Atlas Account
1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a new account or sign in
3. Create a new cluster (M0 Sandbox is free)

### 2. Configure Database
1. **Create Database**: `missing_persons_db`
2. **Create Collections**:
   - `missing_persons`
   - `found_persons`
   - `matches`

### 3. Set Up Network Access
1. Go to "Network Access" in Atlas dashboard
2. Add IP address `0.0.0.0/0` (allow all IPs for Render)
3. Or add specific Render IP ranges

### 4. Create Database User
1. Go to "Database Access"
2. Create a new user with read/write permissions
3. Note down the username and password

### 5. Get Connection String
1. Go to "Clusters" → "Connect"
2. Choose "Connect your application"
3. Copy the connection string
4. Replace `<password>` with your database user password
5. Replace `<dbname>` with `missing_persons_db`

**Example**: `mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/missing_persons_db?retryWrites=true&w=majority`

## 🚀 Backend Deployment (Render)

### 1. Prepare Repository
1. Push your code to GitHub
2. Ensure all files are committed

### 2. Deploy on Render
1. Go to [Render](https://render.com)
2. Sign up/Login with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository

### 3. Configure Render Service
- **Name**: `ai-missing-person-finder-backend`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt && python -c "import deepface; deepface.build_model('Facenet')"`
- **Start Command**: `python app.py`

### 4. Set Environment Variables in Render
Go to "Environment" tab and add:

```env
MONGO_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/missing_persons_db?retryWrites=true&w=majority
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

### 5. Deploy
1. Click "Create Web Service"
2. Wait for deployment to complete
3. Note the service URL (e.g., `https://ai-missing-person-finder-backend.onrender.com`)

## 🌐 Frontend Deployment (Vercel)

### 1. Prepare Frontend
1. Update `frontend/src/App.js` to use environment variable for API URL
2. Ensure all dependencies are in `package.json`

### 2. Deploy on Vercel
1. Go to [Vercel](https://vercel.com)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Import your GitHub repository
5. Select the `frontend` folder as root directory

### 3. Configure Build Settings
- **Framework Preset**: Create React App
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `build`

### 4. Set Environment Variables in Vercel
Go to "Settings" → "Environment Variables" and add:

```env
REACT_APP_API_URL=https://ai-missing-person-finder-backend.onrender.com
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### 5. Deploy
1. Click "Deploy"
2. Wait for deployment to complete
3. Note the frontend URL (e.g., `https://ai-missing-person-finder.vercel.app`)

## 🔧 API Configuration

### Update Frontend API Calls
Update all API calls in the frontend to use the environment variable:

```javascript
// In your React components
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Example API call
const response = await fetch(`${API_BASE_URL}/api/missing-persons`);
```

### CORS Configuration
The backend already has CORS enabled for all origins in production.

## 📋 Environment Variables Summary

### Backend (Render)
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname
GOOGLE_MAPS_API_KEY=your_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number
SENDGRID_API_KEY=your_key
FROM_EMAIL=noreply@missingpersonfinder.com
FROM_NAME=AI Missing Person Finder
HIGH_CONFIDENCE_THRESHOLD=0.9
NOTIFICATION_ENABLED=true
FLASK_ENV=production
```

### Frontend (Vercel)
```env
REACT_APP_API_URL=https://your-backend.onrender.com
REACT_APP_GOOGLE_MAPS_API_KEY=your_key
```

## 🧪 Testing Deployment

### 1. Test Backend
```bash
curl https://your-backend.onrender.com/api/reports
```

### 2. Test Frontend
1. Visit your Vercel URL
2. Try reporting a missing person
3. Check if API calls work

### 3. Test Database
1. Report a missing person
2. Check MongoDB Atlas for new documents
3. Verify data is stored correctly

## 🔍 Troubleshooting

### Common Issues

#### Backend Issues
- **Build fails**: Check Python version compatibility
- **DeepFace errors**: Ensure models are downloaded during build
- **Database connection**: Verify MongoDB URI and network access

#### Frontend Issues
- **API calls fail**: Check CORS settings and API URL
- **Build fails**: Check for missing dependencies
- **Environment variables**: Ensure they're set in Vercel

#### Database Issues
- **Connection refused**: Check IP whitelist in MongoDB Atlas
- **Authentication failed**: Verify username/password
- **Database not found**: Ensure database name is correct

### Logs
- **Render**: Check service logs in Render dashboard
- **Vercel**: Check function logs in Vercel dashboard
- **MongoDB**: Check Atlas logs for connection issues

## 📊 Monitoring

### Render Monitoring
- CPU and memory usage
- Response times
- Error rates
- Logs

### Vercel Monitoring
- Page views
- Performance metrics
- Function execution times
- Error tracking

### MongoDB Atlas Monitoring
- Connection count
- Query performance
- Storage usage
- Index usage

## 🔐 Security Considerations

1. **Environment Variables**: Never commit sensitive data to Git
2. **CORS**: Configure appropriate origins for production
3. **Database**: Use strong passwords and IP whitelisting
4. **API Keys**: Rotate keys regularly
5. **HTTPS**: All services use HTTPS in production

## 📈 Scaling

### Backend Scaling (Render)
- Upgrade to higher plan for more resources
- Add horizontal scaling if needed
- Monitor performance metrics

### Database Scaling (MongoDB Atlas)
- Upgrade cluster tier
- Add read replicas
- Optimize queries and indexes

### Frontend Scaling (Vercel)
- Vercel automatically handles scaling
- Use CDN for global distribution
- Monitor performance metrics

## 🎯 Production Checklist

- [ ] MongoDB Atlas cluster created and configured
- [ ] Database collections created
- [ ] Network access configured
- [ ] Backend deployed on Render
- [ ] Environment variables set in Render
- [ ] Frontend deployed on Vercel
- [ ] Environment variables set in Vercel
- [ ] API calls working between frontend and backend
- [ ] Database connections working
- [ ] Notifications working (Twilio/SendGrid)
- [ ] Google Maps integration working
- [ ] Facial recognition working
- [ ] All features tested in production
- [ ] Monitoring set up
- [ ] Security measures in place
