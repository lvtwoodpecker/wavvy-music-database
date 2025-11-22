
# Wavvy

Full-stack music streaming & events platform

This repo contains:
1. Backend – Flask API
2. Frontend – React app (music player UI, auth, dashboards, etc.)

This guide walks you through:

1. Setting up your environment
2. Running the backend
3. Running the frontend
4. Useful scripts & troubleshooting

--------
## Repository Structure

```bash
app/  # Flask API
frontend/ # react app
scripts/
tests/
```

---------

## Packages

```bash
python3 -m venv venv
cd venv/bin/activate
pip3 install -r requirements.txt
```

---------

## ENV

```.env
# Flask
FLASK_ENV=development
SECRET_KEY=dev-secret-key

# Frontend
FRONTEND_URL=http://localhost:5173

# Backend 
BACKEND_URL=http://localhost:5000

# Payments
PAYMENTS_PROVIDER=stripe
STRIPE_API_KEY=YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_dummy_for_now   # can be fake for now

# SUPABASE
SUPABASE_URL=https://pghgrbyvivxbgarhqadv.supabase.co
SUPABASE_SERVICE_KEY=YOUR_KEY
```

---------
## Frontend set up 
### Install dependencies and Run server
```bash
cd frontend
npm install
npm run dev
```

---------
## Run Backend API server
``bash
python3 -m app.main.py 
```
