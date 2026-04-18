# 🚙 DriveShare & Dock

**A premium mobile marketplace for RV rentals, land stays, and vehicle storage with a rugged forest-green aesthetic.**

<p align="center">
  <img src="https://img.shields.io/badge/React_Native-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Expo-000020?style=for-the-badge&logo=expo&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Stripe-008CDD?style=for-the-badge&logo=stripe&logoColor=white" />
</p>

---

## 📱 **What is DriveShare & Dock?**

DriveShare & Dock is a **mobile-first marketplace** that connects owners and renters across three premium categories:

- **🚐 RV Rentals** - Luxury motorhomes, adventure vans, and travel trailers
- **🏕️ Land Stays** - Private acreage with full utilities and hookups
- **🔒 Vehicle Storage** - Secure, gated storage facilities

### **Key Features:**

✅ **$25 User Verification Paywall** (Stripe integration)  
✅ **JWT Authentication** (Email/password)  
✅ **Category-Specific Listings** (RV, Land, Storage)  
✅ **Image Upload** (Camera + Gallery, up to 10 images)  
✅ **Booking System** (Date-based reservations)  
✅ **Direct Messaging** (In-app chat)  
✅ **Admin Panel** (User management, listing moderation, analytics)  
✅ **Social Proof Listings** (5 premium seed listings)  
✅ **Forest-Green Theme** (#1B4332 - Professional & Rugged)  

---

## 🛠️ **Tech Stack**

### **Frontend (Mobile App)**
- **Framework:** Expo / React Native
- **Language:** TypeScript
- **Navigation:** React Navigation (Tab + Stack)
- **State Management:** Zustand
- **HTTP Client:** Axios
- **Image Handling:** Expo Image Picker (base64)
- **Icons:** Expo Vector Icons

### **Backend (API)**
- **Framework:** FastAPI (Python 3.11)
- **Authentication:** JWT (python-jose)
- **Password Hashing:** Bcrypt (passlib)
- **Database Driver:** Motor (async MongoDB)
- **Payments:** Stripe via emergentintegrations
- **Environment:** Python dotenv

### **Database**
- **Database:** MongoDB
- **Collections:** users, listings, bookings, messages, payment_transactions

### **Payments**
- **Provider:** Stripe (LIVE keys)
- **Integration:** emergentintegrations library
- **Verification:** $25 one-time fee

---

## 📋 **Prerequisites**

Before you begin, ensure you have:

- **Node.js** (v18 or higher)
- **Python** (v3.11 or higher)
- **MongoDB** (local or Atlas cluster)
- **Expo CLI** (`npm install -g expo-cli`)
- **Stripe Account** (for payment processing)
- **iOS/Android device** or emulator for testing

---

## 🚀 **Quick Start**

### **1. Clone the Repository**

```bash
git clone https://github.com/yourusername/driveshare-dock.git
cd driveshare-dock
```

### **2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env and add your credentials:
# - MongoDB connection string
# - Stripe API keys
# - JWT secret

# Seed premium listings (optional)
python seed_listings.py

# Start the server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Backend will run at:** `http://localhost:8001`

### **3. Frontend Setup**

```bash
cd frontend

# Install dependencies
yarn install
# or
npm install

# Create .env file from example
cp .env.example .env

# Edit .env and update:
# EXPO_PUBLIC_BACKEND_URL=http://localhost:8001

# Start Expo
npx expo start
```

**Scan QR code** with Expo Go app (iOS/Android) or press:
- `i` for iOS simulator
- `a` for Android emulator
- `w` for web browser

---

## 🔐 **Environment Variables**

### **Backend (`/backend/.env`)**

| Variable | Description | Example |
|----------|-------------|----------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DB_NAME` | Database name | `driveshare_dock` |
| `STRIPE_API_KEY` | Stripe secret key | `sk_live_...` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | `pk_live_...` |
| `JWT_SECRET` | JWT signing secret | `your_random_secret` |

### **Frontend (`/frontend/.env`)**

| Variable | Description | Example |
|----------|-------------|----------|
| `EXPO_PUBLIC_BACKEND_URL` | Backend API URL | `https://your-api.com` |

**⚠️ NEVER commit `.env` files to GitHub!**

---

## 👤 **Default Credentials**

### **Admin Account**
- **Email:** `admin@driveshare.com`
- **Password:** `Admin123!`
- **Access:** Full admin panel (user management, listings, payments)

### **Test User**
- **Email:** `test@example.com`
- **Password:** `password123`
- **Status:** Unverified (requires $25 verification)

**🔒 Change these in production!**

---

## 📊 **Database Collections**

### **users**
```json
{
  "email": "user@example.com",
  "password": "hashed_password",
  "name": "John Doe",
  "phone": "555-1234",
  "is_verified": false,
  "is_admin": false,
  "is_banned": false,
  "created_at": "2025-07-15T10:30:00Z"
}
```

### **listings**
```json
{
  "owner_id": "user_id",
  "owner_name": "John Doe",
  "category": "rv_rental",
  "title": "Luxury Airstream",
  "description": "...",
  "price": 299.00,
  "location": "Moab, Utah",
  "images": ["base64_image_1", "base64_image_2"],
  "amenities": {},
  "status": "active",
  "created_at": "2025-07-15T10:30:00Z"
}
```

### **bookings**
```json
{
  "listing_id": "listing_id",
  "guest_id": "user_id",
  "host_id": "owner_id",
  "start_date": "2025-08-01T00:00:00Z",
  "end_date": "2025-08-05T00:00:00Z",
  "total_price": 1196.00,
  "status": "pending",
  "created_at": "2025-07-15T10:30:00Z"
}
```

---

## 🎨 **Design System**

### **Color Palette (Forest-Green)**

```javascript
Primary:    #1B4332  // Deep Forest
Secondary:  #2D6A4F  // Mid Forest
Accent:     #40916C  // Light Forest
Background: #F8F9FA  // Off-white
Text:       #212529  // Dark Gray
Error:      #D62828  // Deep Red
```

### **Typography**
- **Headings:** Bold, professional
- **Body:** 16px, readable
- **Buttons:** 16px, semi-bold

---

## 📦 **API Endpoints**

### **Authentication**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### **Payments**
- `POST /api/payments/verification/create-checkout` - Create $25 verification checkout
- `GET /api/payments/verification/status/{session_id}` - Check payment status
- `POST /api/webhook/stripe` - Stripe webhook handler

### **Listings**
- `GET /api/listings` - Get all listings (with filters)
- `POST /api/listings` - Create listing (verified users only)
- `GET /api/listings/{id}` - Get listing details
- `GET /api/listings/user/me` - Get my listings
- `DELETE /api/listings/{id}` - Delete listing

### **Bookings**
- `POST /api/bookings` - Create booking
- `GET /api/bookings/guest` - Get bookings as guest
- `GET /api/bookings/host` - Get bookings as host

### **Messages**
- `POST /api/messages` - Send message
- `GET /api/messages/conversations` - Get all conversations
- `GET /api/messages/{conversation_id}` - Get messages in conversation

### **Admin (Admin Only)**
- `GET /api/admin/stats` - Dashboard statistics
- `GET /api/admin/users` - All users
- `GET /api/admin/listings` - All listings
- `GET /api/admin/payments` - Payment transactions
- `PATCH /api/admin/users/{id}/verify` - Manually verify user
- `PATCH /api/admin/users/{id}/ban` - Ban/unban user
- `DELETE /api/admin/listings/{id}` - Delete any listing

**Full API docs:** `http://localhost:8001/docs` (FastAPI auto-generated)

---

## 🧪 **Testing**

### **Backend Tests**
```bash
cd backend
python -m pytest
```

### **Frontend Tests**
```bash
cd frontend
npm test
```

---

## 📱 **Building for Production**

### **Mobile App (iOS/Android)**

```bash
cd frontend

# Install EAS CLI
npm install -g eas-cli

# Configure EAS
eas build:configure

# Build for iOS
eas build --platform ios

# Build for Android
eas build --platform android

# Submit to App Store
eas submit --platform ios

# Submit to Play Store
eas submit --platform android
```

### **Backend Deployment**

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

---

## 🔒 **Security Considerations**

- ✅ **JWT tokens** expire after 30 days
- ✅ **Passwords** hashed with bcrypt
- ✅ **Stripe** payment processing (PCI compliant)
- ✅ **CORS** configured for production domains
- ✅ **Admin routes** protected with middleware
- ✅ **Input validation** on all endpoints
- ⚠️ **Change default admin password** before production!
- ⚠️ **Use environment variables** for all secrets
- ⚠️ **Enable HTTPS** in production

---

## 🐛 **Known Issues**

- Shadow props deprecated warnings (cosmetic, no impact)
- Expo package version warnings (app works correctly)

---

## 📄 **License**

MIT License - See [LICENSE](./LICENSE) file

---

## 🤝 **Contributing**

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 **Support**

For issues or questions:
- Open a [GitHub Issue](https://github.com/yourusername/driveshare-dock/issues)
- Email: support@driveshare.com

---

## 🙏 **Acknowledgments**

- Built with [Expo](https://expo.dev)
- Powered by [FastAPI](https://fastapi.tiangolo.com)
- Payments by [Stripe](https://stripe.com)
- Images from [Unsplash](https://unsplash.com)

---

<p align="center">
  Made with ❤️ by the DriveShare & Dock Team
</p>