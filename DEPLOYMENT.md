# 🚀 DriveShare & Dock - Deployment Guide

This guide covers deploying DriveShare & Dock to production using recommended services.

---

## 📋 **Deployment Architecture**

```
┌─────────────────────────────────────────┐
│  Mobile App (iOS/Android)               │
│  Expo Application Services (EAS)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Backend API (FastAPI)                  │
│  Railway.app / Render.com               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Database (MongoDB)                     │
│  MongoDB Atlas (Cloud)                  │
└─────────────────────────────────────────┘
```

---

## 1️⃣ **Database Deployment (MongoDB Atlas)**

### **Step 1: Create MongoDB Atlas Account**

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for free account
3. Create a new cluster:
   - **Tier:** M0 (Free) or M10 ($9/month)
   - **Region:** Choose closest to your users
   - **Cluster Name:** `driveshare-dock-prod`

### **Step 2: Configure Database**

1. **Create Database User:**
   - Username: `driveshare_admin`
   - Password: Generate strong password
   - Role: `Atlas admin`

2. **Whitelist IP Addresses:**
   - Add `0.0.0.0/0` (allow from anywhere)
   - Or add specific IPs from Railway/Render

3. **Get Connection String:**
   ```
   mongodb+srv://driveshare_admin:<password>@cluster0.xxxxx.mongodb.net/driveshare_dock?retryWrites=true&w=majority
   ```

### **Step 3: Migrate Data (Optional)**

```bash
# Export from local MongoDB
mongodump --uri="mongodb://localhost:27017/test_database" --out=./dump

# Import to Atlas
mongorestore --uri="mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/driveshare_dock" ./dump/test_database
```

---

## 2️⃣ **Backend Deployment (Railway.app)**

### **Step 1: Prepare Backend for Deployment**

1. **Ensure requirements.txt is up to date:**
   ```bash
   cd backend
   pip freeze > requirements.txt
   ```

2. **Create Procfile:**
   ```bash
   echo "web: uvicorn server:app --host 0.0.0.0 --port \$PORT" > Procfile
   ```

3. **Update CORS in server.py:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://your-production-domain.com",
           "exp://",  # For Expo
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### **Step 2: Deploy to Railway**

1. **Sign up:** [Railway.app](https://railway.app)
2. **Create New Project** → Deploy from GitHub repo
3. **Select backend folder** as root
4. **Add Environment Variables:**
   ```
   MONGO_URL=mongodb+srv://...
   DB_NAME=driveshare_dock
   STRIPE_API_KEY=sk_live_...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   JWT_SECRET=your_secure_secret
   PORT=8001
   ```

5. **Deploy:** Railway auto-deploys on git push
6. **Get URL:** `https://your-app.up.railway.app`

### **Alternative: Render.com**

1. **Sign up:** [Render.com](https://render.com)
2. **New → Web Service**
3. **Connect GitHub repo**
4. **Settings:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3
5. **Add Environment Variables** (same as Railway)
6. **Deploy**

---

## 3️⃣ **Frontend Deployment (Expo Application Services)**

### **Step 1: Install EAS CLI**

```bash
npm install -g eas-cli
eas login
```

### **Step 2: Configure EAS**

```bash
cd frontend
eas build:configure
```

This creates `eas.json`:

```json
{
  "build": {
    "production": {
      "env": {
        "EXPO_PUBLIC_BACKEND_URL": "https://your-backend.railway.app"
      }
    }
  }
}
```

### **Step 3: Update app.json**

```json
{
  "expo": {
    "name": "DriveShare & Dock",
    "slug": "driveshare-dock",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#1B4332"
    },
    "ios": {
      "bundleIdentifier": "com.driveshare.dock",
      "buildNumber": "1.0.0"
    },
    "android": {
      "package": "com.driveshare.dock",
      "versionCode": 1,
      "permissions": [
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE"
      ]
    }
  }
}
```

### **Step 4: Build for iOS**

```bash
# Build
eas build --platform ios --profile production

# After build completes, submit to App Store
eas submit --platform ios
```

**You'll need:**
- Apple Developer Account ($99/year)
- App Store Connect credentials

### **Step 5: Build for Android**

```bash
# Build
eas build --platform android --profile production

# Submit to Play Store
eas submit --platform android
```

**You'll need:**
- Google Play Developer Account ($25 one-time)
- Signing key (EAS can generate)

---

## 4️⃣ **Domain & SSL Setup**

### **Backend Custom Domain (Railway)**

1. Go to Railway project settings
2. **Custom Domain** → Add your domain
3. Update DNS records at your registrar:
   ```
   CNAME api.yourdomain.com → your-app.up.railway.app
   ```
4. SSL automatically provisioned

### **Update Frontend .env**

```
EXPO_PUBLIC_BACKEND_URL=https://api.yourdomain.com
```

---

## 5️⃣ **Post-Deployment Checklist**

### **Security**
- [ ] Change admin password from default
- [ ] Update JWT_SECRET to strong random string
- [ ] Verify CORS allows only your domains
- [ ] Enable HTTPS on all services
- [ ] Test Stripe webhooks are working
- [ ] Verify environment variables are set

### **Database**
- [ ] Enable MongoDB Atlas backups
- [ ] Set up monitoring alerts
- [ ] Create database indexes for performance

### **Monitoring**
- [ ] Set up error tracking (Sentry)
- [ ] Monitor API response times
- [ ] Track Stripe payment success rate
- [ ] Monitor user registrations

### **App Stores**
- [ ] Add app description
- [ ] Upload screenshots (5+ per platform)
- [ ] Set app category
- [ ] Add privacy policy URL
- [ ] Add terms of service

---

## 6️⃣ **Continuous Deployment**

### **Setup Auto-Deploy**

**Railway (Backend):**
- Auto-deploys on git push to `main` branch
- Configure in Railway dashboard

**EAS (Mobile):**
```bash
# Auto-build on git tag
eas build --platform all --auto-submit
```

**GitHub Actions (Optional):**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: |
          # Railway auto-deploys
          echo "Backend deployed"

  build-mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node
        uses: actions/setup-node@v2
      - name: Build with EAS
        run: |
          npm install -g eas-cli
          eas build --platform all --non-interactive
```

---

## 💰 **Cost Breakdown**

| Service | Plan | Cost |
|---------|------|------|
| MongoDB Atlas | M0 (Free) | $0/month |
| Railway (Backend) | Hobby | $5/month |
| EAS | Free tier | $0/month |
| **Total** | | **$5/month** |

**Scaling to Production:**

| Service | Plan | Cost |
|---------|------|------|
| MongoDB Atlas | M10 | $9/month |
| Railway | Pro | $20/month |
| EAS | Production | $29/month |
| Domain | .com | $12/year |
| **Total** | | **~$60/month** |

---

## 🆘 **Troubleshooting**

### **Backend won't start**
- Check Railway logs: `railway logs`
- Verify all environment variables are set
- Check `requirements.txt` is complete

### **Mobile app can't connect to backend**
- Verify `EXPO_PUBLIC_BACKEND_URL` in .env
- Check CORS settings in backend
- Test backend URL in browser

### **Stripe webhooks not working**
- Add webhook URL in Stripe dashboard
- URL: `https://api.yourdomain.com/api/webhook/stripe`
- Select events: `checkout.session.completed`

### **Images not loading**
- Base64 images can be large - consider cloud storage (S3, Cloudinary)
- Check MongoDB document size limits (16MB)

---

## 📚 **Additional Resources**

- [Expo Deployment Docs](https://docs.expo.dev/distribution/introduction/)
- [Railway Deployment Docs](https://docs.railway.app/)
- [MongoDB Atlas Docs](https://docs.atlas.mongodb.com/)
- [Stripe Production Checklist](https://stripe.com/docs/development/checklist)

---

**Need help?** Open an issue on GitHub or contact support.

---

<p align="center">
  🚀 Happy Deploying!
</p>