# ZOZI E-Commerce Platform 🚀

**Shop Smart, Live Luxe** - A premium marketplace connecting customers with trusted suppliers in the GCC region.

## 🎯 Overview

ZOZI is a comprehensive e-commerce platform built with modern technologies, featuring role-based access for customers, suppliers, and administrators. The platform offers a seamless shopping experience with advanced filtering, secure payments, and AI-powered features.

## 📚 Documentation

The canonical documentation lives under [documents/README.md](documents/README.md) (index). The two "source of truth" files for audit and implementation status are:

- [documents/CODEBASE_STATUS_MATRIX_DETAILED.md](documents/CODEBASE_STATUS_MATRIX_DETAILED.md)
- [documents/CODEBASE_FILE_INDEX.md](documents/CODEBASE_FILE_INDEX.md)
- [documents/PRODUCTION_DEPLOYMENT.md](documents/PRODUCTION_DEPLOYMENT.md)

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **Framework**: FastAPI for high-performance REST APIs
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT tokens with role-based access control
- **Payments**: Stripe card flow plus Tap hosted checkout for GCC-friendly payment coverage
- **Caching**: Redis for session management and performance

### Frontend (Next.js + React)
- **Framework**: Next.js 13+ with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS for responsive design
- **State Management**: Zustand for client-side state
- **UI Components**: Custom components with Lucide icons

### Key Features
- 🔐 **Role-Based Authentication**: Admin, Supplier, Customer roles
- 🛒 **Advanced E-Commerce**: Cart, wishlist, checkout, order tracking
- 🎨 **Modern UI/UX**: Responsive design with emerald green theme
- 🤖 **AI Chatbot**: Customer support and product recommendations
- 📊 **Analytics Dashboard**: Comprehensive reporting for admins
- 📱 **Mobile-First**: Optimized for all devices
- 🌍 **GCC Focus**: Localized for Middle East markets

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**: [Download from python.org](https://python.org)
- **Node.js 16+**: [Download from nodejs.org](https://nodejs.org)
- **Windows 10+**: (Batch file optimized for Windows)

### One-Click Setup & Launch

1. **Download/Clone** the project to your local machine
2. **Double-click** `run_zozi.bat` or run it from command prompt
3. **Wait** for the automated setup to complete
4. **Open** your browser to `http://localhost:3000`

The batch file will automatically:
- ✅ Set up Python virtual environment
- ✅ Install all backend dependencies
- ✅ Install all frontend dependencies
- ✅ Initialize and seed the database
- ✅ Start both backend and frontend servers
- ✅ Provide test account credentials

## 🔑 Test Accounts

After running the application, use these accounts to explore different features:

### 👑 Administrator
- **Email**: `admin@zozi.com`
- **Password**: `admin123`
- **Dashboard**: `http://localhost:3000/admin/dashboard`
- **Features**: User management, supplier approval, product moderation, analytics

### 🏪 Supplier
- **Email**: `supplier@zozi.com`
- **Password**: `supplier123`
- **Dashboard**: `http://localhost:3000/supplier/dashboard`
- **Features**: Product upload, inventory management, sales reports, payouts

### 🛒 Customer
- **Email**: `customer@zozi.com`
- **Password**: `customer123`
- **Dashboard**: `http://localhost:3000`
- **Features**: Browse products, add to cart/wishlist, checkout, order tracking

## 📱 Application URLs

- **🏠 Main Website**: `http://localhost:3000`
- **🔧 Backend API**: `http://localhost:8000`
- **📚 API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **🔄 API Alternative Docs**: `http://localhost:8000/redoc`

## 🎨 Brand Identity

### Primary Branding (ZOZI)
- **Colors**: Royal Blue (#1A4FFF), Gold (#CFAE70), Pearl White (#F8F8F8)
- **Typography**: Montserrat/Poppins (headings), Nunito/Lato (body)
- **Tagline**: "Shop Smart, Live Luxe"

### Alternative Branding (ZIP0)
- **Colors**: Midnight Blue (#1B2A49), Gold (#D4AF37), Silver Gray (#CCCCCC)
- **Tagline**: "Luxury at Zero Barriers"

## 🛍️ Customer Features

- **🏠 Home Page**: Featured products and promotional banners
- **📦 Product Catalog**: Advanced filtering by category, price, supplier
- **🔍 Search & Filter**: Real-time search with multiple filter options
- **❤️ Wishlist**: Save favorite products for later
- **🛒 Shopping Cart**: Persistent cart with quantity management
- **💳 Secure Checkout**: Stripe card payments and Tap hosted checkout
- **📋 Order Tracking**: Real-time order status updates
- **👤 Profile Management**: Account settings and preferences
- **🎁 Special Offers**: Promotional campaigns and discounts
- **🤖 AI Chatbot**: 24/7 customer support and recommendations

## 🏪 Supplier Features

- **📊 Dashboard**: Overview of sales, inventory, and performance
- **📤 Product Upload**: Easy product listing with image upload
- **📈 Inventory Management**: Stock control and product updates
- **💰 Sales Reports**: Detailed analytics and revenue tracking
- **💸 Payout Management**: Commission tracking and settlements
- **📞 Support**: Direct communication with platform admins

## 👑 Admin Features

- **👥 User Management**: Customer and supplier account oversight
- **✅ Supplier Approval**: Onboarding and verification process
- **🔧 Product Moderation**: Content review and quality control
- **📊 Analytics Dashboard**: Comprehensive business metrics
- **⚙️ Commission Setup**: Dynamic pricing and fee management
- **📈 Reports**: Sales, user, and performance analytics

## 🛠️ Development Setup (Manual)

If you prefer manual setup instead of the batch file:

### Backend Setup
```bash
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
python db/init_db.py --seed
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

On Windows, the batch launchers start the backend without `--reload` by default because uvicorn/watchfiles can emit a `KeyboardInterrupt` traceback during hot-reload shutdowns. Set `ZOZI_BACKEND_RELOAD=1` before running `start_zozi.bat` or `run_zozi.bat` if you explicitly want reload mode.

### Frontend Setup
```bash
cd frontend/shared
npm ci --legacy-peer-deps

cd ../web_app
npm ci --legacy-peer-deps
npm run dev
```

### Mobile App Setup
```bash
cd frontend/mobile_app
npm ci
npm run start
```

See `documents/RUNTIME_FILE_MAP.md` for the active env files, lockfiles, Docker files, and local database paths. The canonical local SQLite file is `backend/zozi.db`.

See `documents/FILE_ORGANIZATION_RULES.md` for the repository rules on where new files belong, which paths are canonical, and which generated files should never be committed.

### Admin Verification Sweep
```bash
python scripts/admin_verification.py
```

This runs the widened admin-panel regression sweep used for Section V validation: backend admin pytest suites, web admin-focused Jest coverage, mobile admin-focused Jest coverage, and web/mobile TypeScript checks. Use `--skip-backend`, `--skip-web`, `--skip-mobile`, or `--skip-typecheck` to narrow the run.

## 🗂️ Project Structure Rules

- Root is for orchestration only: Compose files, repo scripts, README, and deployment config.
- Backend runtime files belong under `backend/`; web runtime files belong under `frontend/web_app/`; mobile runtime files belong under `frontend/mobile_app/`.
- Keep one lockfile per real package and do not recreate a root `package-lock.json` without a root `package.json`.
- Keep generated output such as exports, logs, test results, caches, and local DB sidecars out of source folders and out of git.
- Use `documents/RUNTIME_FILE_MAP.md` as the source of truth for active runtime files and `documents/FILE_ORGANIZATION_RULES.md` as the source of truth for file placement rules.

## 🐳 Docker Deployment

For production deployment using Docker:

```bash
# Development with Docker Compose
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up --build
```

### Database Migrations During Deploy

- `scripts/deploy.sh` now runs `alembic upgrade head` automatically after Docker services are started (development and production Docker paths).
- `.github/workflows/ci-cd.yml` production deploy step also runs `alembic upgrade head` after `docker-compose ... up -d --build`.

If you deploy outside these flows, run migrations manually before serving traffic:

```bash
# Local backend virtualenv
cd backend
alembic upgrade head

# Docker development
docker-compose exec -T backend alembic upgrade head

# Docker production
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
DATABASE_URL=sqlite:///./zozi.db
SECRET_KEY=your-secret-key-here
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
TAP_SECRET_KEY=your_tap_secret_key
TAP_WEBHOOK_SECRET=your_tap_webhook_secret
TAP_WEBHOOK_URL=https://your-backend.example.com/payments/tap/webhook
CORS_ORIGINS=http://localhost:3000
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
RESEND_API_KEY=re_xxx_or_leave_blank_if_using_smtp
EMAIL_FROM=login@your-domain.example
SMTP_HOST=smtp.your-provider.example
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
CUSTOMER_EMAIL_VERIFICATION_MODE=auto
```

Local development uses SQLite by default. Docker Compose and production override `DATABASE_URL` to PostgreSQL.

Tap hosted checkout requires a public HTTPS webhook endpoint. For local development, expose `backend` with a tunnel such as `ngrok` or `cloudflared` and point `TAP_WEBHOOK_URL` to `/payments/tap/webhook` on that public URL.

### Customer Auth Setup

- Cheapest production-ready email delivery: use Resend with a low-cost domain and set `RESEND_API_KEY` plus `EMAIL_FROM`.
- Cheapest low-friction customer login: configure `GOOGLE_CLIENT_ID` and use the built-in Google Identity Services sign-in flow.
- Optional SMTP alternative: set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `EMAIL_FROM` instead of Resend.
- `CUSTOMER_EMAIL_VERIFICATION_MODE=auto` is the recommended default. It requires verification only when live email delivery is configured.
- Use `CUSTOMER_EMAIL_VERIFICATION_MODE=required` if you want strict email verification even for password login.
- Use `CUSTOMER_EMAIL_VERIFICATION_MODE=disabled` if you want to bypass customer email verification entirely for now.

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
# optional: external chatbot endpoint (can be an API route or third-party service)
NEXT_PUBLIC_CHATBOT_ENDPOINT=https://your-chatbot-service.example.com/ask
```

Tap hosted checkout does not need a frontend publishable key because payment collection happens on Tap's hosted page after the backend creates the charge.

`frontend/web_app/.env.local` is only for the web app. `frontend/mobile_app/.env` is the Expo mobile env file. The repo root `.env` is only for Docker Compose, and `backend/.env` is only for the FastAPI backend.

## 📊 Database Schema

- **Users**: Role-based authentication (admin/supplier/customer)
- **Products**: Catalog with supplier relationships
- **Orders**: Complete order management system
- **Order Items**: Individual order line items
- **Categories**: Product categorization system

## 🚀 Deployment Options

- **Railway**: `railway.toml` configured for easy deployment
- **Vercel**: Frontend deployment configuration
- **Docker**: Containerized deployment for any cloud provider
- **AWS/GCP/Azure**: Enterprise-grade cloud deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is proprietary software for ZOZI marketplace.

## 📞 Support

For technical support or questions:
- Check the API documentation at `/docs`
- Review the codebase comments
- Create an issue in the repository

---

**Built with ❤️ for the GCC e-commerce market**