# Google Cloud Platform Setup Guide

## Step-by-Step GCP Project Creation and Firestore Setup

### 1. Create Google Cloud Account and Project

#### Prerequisites
- Google account
- Credit card for GCP billing (Google provides $300 free credits for new users)

#### Steps:
1. **Visit Google Cloud Console**: Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. **Sign in** with your Google account
3. **Accept terms** and set up billing if it's your first time
4. **Create a new project**:
   - Click "Select a project" → "New Project"
   - Project name: `brief-generator` (or your preferred name)
   - Leave organization as "No organization"
   - Click "Create"
   - Note down your **Project ID** (it will be something like `brief-generator-123456`)

### 2. Enable Required APIs

1. **Navigate to APIs & Services** → **Library**
2. **Enable the following APIs**:
   - **Firestore API**: Search for "Cloud Firestore API" → Enable
   - **Cloud Resource Manager API**: Search for "Cloud Resource Manager API" → Enable

### 3. Set up Firestore Database

1. **Navigate to Firestore**:
   - In the left sidebar, go to "Firestore" → "Database"
2. **Create database**:
   - Click "Create database"
   - Choose "Start in test mode" (for development)
   - Select a location (choose closest to you, e.g., `us-central1`)
   - Click "Create"

### 4. Create Service Account for Authentication

1. **Navigate to IAM & Admin** → **Service Accounts**
2. **Create Service Account**:
   - Click "Create Service Account"
   - Service account name: `brief-generator-service`
   - Service account ID: `brief-generator-service` (auto-filled)
   - Description: `Service account for brief generator app`
   - Click "Create and Continue"

3. **Grant Roles**:
   - Add role: `Cloud Datastore User` (for Firestore read/write)
   - Click "Continue" → "Done"

4. **Generate Key**:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON" format
   - Click "Create"
   - **Save the downloaded JSON file** as `service-account-key.json` in a secure location

### 5. Get Gemini API Key

1. **Visit AI Studio**: Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. **Create API Key**:
   - Click "Create API Key"
   - Select your GCP project from dropdown
   - Click "Create API Key in existing project"
   - **Copy and save the API key**

### 6. Configure Firestore Security Rules (Development)

1. **Go to Firestore** → **Rules**
2. **Replace the rules** with the following for development:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write access to briefs collection
    match /briefs/{document} {
      allow read, write: if true;
    }
  }
}
```
3. **Click "Publish"**

**Important**: These rules allow unrestricted access for development. In production, you'd implement proper security rules.

### 7. Important Information to Note Down

After completing the above steps, you should have:

1. **GCP Project ID**: `your-project-id-123456`
2. **Service Account JSON file**: Downloaded to your computer
3. **Gemini API Key**: The API key string
4. **Firestore Database**: Created and ready

### 8. Environment Setup

You'll need these values for your application:

```bash
# For Backend (.env file)
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
GCP_PROJECT_ID=your-project-id-123456
FLASK_ENV=development
```

### Security Best Practices

1. **Never commit credentials to git**:
   - Add `service-account-key.json` to `.gitignore`
   - Add `.env` files to `.gitignore`

2. **Service Account Key Storage**:
   - Store the JSON file in your project root (but not in git)
   - Or set the full path in `GOOGLE_APPLICATION_CREDENTIALS`

3. **API Key Security**:
   - Don't hardcode API keys in your code
   - Use environment variables

### Cost Considerations

**Free Tier Limits** (as of 2024):
- **Firestore**: 1 GB storage, 50,000 reads, 20,000 writes per day
- **Gemini API**: Has usage limits (check current pricing)

For this project scope, you should stay well within free limits.

### Troubleshooting Common Issues

1. **"Permission denied" errors**:
   - Ensure service account has correct roles
   - Check that APIs are enabled

2. **"Project not found"**:
   - Verify PROJECT_ID in environment variables
   - Ensure you're using the correct project ID (not project name)

3. **Authentication errors**:
   - Check service account JSON file path
   - Ensure GOOGLE_APPLICATION_CREDENTIALS points to correct file

### Next Steps

Once you have completed this setup:
1. Note down your Project ID, API key location, and service account file location
2. We'll use these in our application configuration
3. We can start building the Flask backend with Firestore integration

Are you ready to proceed with the GCP setup, or do you have any questions about these steps?
