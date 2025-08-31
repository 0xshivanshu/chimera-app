# Chimera: AI-Powered Security Automation Platform

Chimera is a security platform built to detect and investigate potential threats using real-world data from a mobile device. It has a backend with AI agent integration to provide real-time analysis of user location and incoming messages.

This repository contains the full monorepo for the project:

`mobile-app/`: A React Native client for user authentication and data collection.
`project-chimera/`: The core FastAPI backend that receives data and orchestrates analysis.


Implemented Features:

Secure User Authentication: Full registration and login system using a MongoDB backend, password hashing (`passlib`), and JWT for secure sessions.
Live GPS Location Onboarding: The mobile app collects the user's current GPS coordinates upon login and securely transmits them to the `/v1/onboard/location` endpoint for analysis (e.g., for "impossible travel" checks).
Real-time SMS Phishing Detection Pipeline:
-   The app is equipped with a service to listen for incoming SMS messages in real-time.
-   Upon receiving an SMS, the content is immediately sent to the `/v1/alert` endpoint.
-   The backend is configured to pass this SMS data to a fine-tuned "Inquisitor" AI agent for phishing analysis.


Tech Stack

| Area          | Technology                               |
| ------------- | ---------------------------------------- |
| **Backend**   | Python, FastAPI, MongoDB                 |
| **AI Agents** | Framework integrated with `pyautogen`    |
| **Frontend**  | React Native (with Expo), TypeScript     |
| **Database**  | MongoDB                                  |
| **Core Libs** | `axios`, `passlib`, `python-jose`        |

### Important Note on SMS Functionality

The real-time SMS analysis is a core feature of this project, but it requires a special permission (`RECEIVE_SMS`) that is not available in the standard Expo Go client app.
Therefore, the SMS feature will not work if you run the project in Expo Go.

### Alternative: How to Test the SMS Feature

To fully test the SMS functionality, you must build a custom development client of the app. This packages the necessary native code and allows the permission to be granted.

### Navigate to the mobile-app directory
cd mobile-app
### Run the EAS build command
eas build --profile development --platform android
_____________________________________________________________________________________________________________________________________________________________________________________________________________
# Getting Started (Local Setup)

Prerequisites:
  Node.js (LTS version)
  Python 3.10+
  MongoDB Community Server (running locally)
  Android Studio & Android SDK (for adb and device drivers)
  
1. Backend Setup

### Navigate to the backend directory
cd project-chimera
pip install -r requirements.txt

### Create a .env file and add your MONGO_DB_URI (No other keys needed for local testing)

### Run the backend server, listening on all interfaces
uvicorn api:app --reload --host 0.0.0.0
2. Mobile App Setup

### Navigate to the mobile app directory
cd mobile-app
npm install

## IMPORTANT: Configure the API address
Open src/api/chimeraApi.ts and set API_BASE_URL to your computer's local IP address.

### Start the Expo development server
npx expo start

You can now open the app in Expo Go to test the UI and location features, or connect your custom development client to test the SMS feature.
