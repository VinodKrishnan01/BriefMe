# Firestore Security Rules Guide

This guide explains the security rules for the Brief Generator application, covering both development and production scenarios.

## 📋 Overview

We have created two sets of security rules:
1. **Development Rules** (`firestore-rules-development.txt`) - For testing and development
2. **Production Rules** (`firestore-rules-production.txt`) - For production deployment

## 🔧 Development Rules Features

### Security Conditions Implemented:

1. **Data Validation**
   ```javascript
   function isValidBriefData(data) {
     return data.keys().hasAll(['client_session_id', 'source_text', 'summary', 'decisions', 'actions', 'questions', 'sha256', 'created_at']) &&
            data.source_text.size() > 0 &&
            data.source_text.size() <= 10000;
   }
   ```

2. **UUID Validation for Client Session ID**
   ```javascript
   function isValidClientSessionId(sessionId) {
     return sessionId is string && 
            sessionId.size() == 36 && 
            sessionId.matches('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}');
   }
   ```

3. **Action Items Structure Validation**
   ```javascript
   function isValidAction(action) {
     return action is map &&
            'text' in action &&
            action.text is string &&
            action.text.size() > 0;
   }
   ```

4. **Session Isolation**
   - Each client session can only access its own briefs
   - Prevents cross-session data leakage

5. **Data Constraints**
   - Source text: 1-10,000 characters
   - Arrays limited to 100 items each
   - Required fields validation
   - Proper data types enforcement

## 🚀 Production Rules Features

### Additional Security for Production:

1. **User Authentication Required**
   ```javascript
   allow read: if request.auth != null && isOwner(resource);
   ```

2. **User Ownership Validation**
   ```javascript
   function isOwner(resource) {
     return request.auth != null &&
            request.auth.uid == resource.data.user_id;
   }
   ```

3. **Enhanced Data Model**
   - Includes `user_id` field for ownership tracking
   - Links briefs to authenticated users

## 📝 How to Apply Rules

### For Development (Current):

1. **Copy the development rules** from `firestore-rules-development.txt`
2. **Go to Firebase Console** → Firestore → Rules
3. **Replace existing rules** with the development rules
4. **Click "Publish"**

### For Production (Later):

1. **Implement user authentication** in your app
2. **Update backend** to include `user_id` in brief documents
3. **Copy production rules** from `firestore-rules-production.txt`
4. **Replace development rules** with production rules
5. **Test thoroughly** before deploying

## 🔍 Rule Validation Examples

### Valid Operations:

```javascript
// Creating a brief with valid data
{
  "client_session_id": "123e4567-e89b-12d3-a456-426614174000",
  "source_text": "Meeting notes...",
  "summary": "Brief summary",
  "decisions": ["Decision 1"],
  "actions": [{"text": "Action item"}],
  "questions": ["Question 1"],
  "sha256": "abc123...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Invalid Operations (Will be Denied):

```javascript
// Missing required fields
{
  "source_text": "Some text"
  // Missing other required fields
}

// Invalid client session ID
{
  "client_session_id": "invalid-uuid",
  // ...other fields
}

// Text too long
{
  "source_text": "A".repeat(10001), // > 10,000 characters
  // ...other fields
}
```

## 🛡️ Security Benefits

### Data Integrity:
- Ensures all briefs have required structure
- Validates data types and constraints
- Prevents malformed data storage

### Session Security:
- Isolates data between different client sessions
- Prevents unauthorized access to other users' briefs
- Validates UUID format for session IDs

### Performance:
- Rules are evaluated efficiently
- No unnecessary database reads
- Proper indexing support

## 🧪 Testing Security Rules

### Firebase Console Simulator:
1. Go to Firestore → Rules
2. Click "Simulate" tab
3. Test different scenarios:
   - Valid brief creation
   - Invalid data attempts
   - Cross-session access attempts

### Local Testing:
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize project
firebase init firestore

# Run emulator with rules
firebase emulators:start --only firestore
```

## 📊 Monitoring and Logging

### What to Monitor:
- Rule denials in Firebase Console
- Failed operations in application logs
- Performance metrics

### Common Issues:
- Invalid UUID formats
- Missing required fields
- Cross-session access attempts
- Data type mismatches

## 🔄 Migration Path

### Development → Production:

1. **Add Authentication**
   - Implement Firebase Auth or Google Cloud Identity
   - Update frontend to handle authentication
   - Modify backend to use authenticated user IDs

2. **Update Data Model**
   - Add `user_id` field to all brief documents
   - Migrate existing data (if any)

3. **Switch Rules**
   - Replace development rules with production rules
   - Test thoroughly in staging environment

4. **Deploy**
   - Deploy new rules to production
   - Monitor for any issues

## ✅ Ready to Use

The **development rules** are ready to use immediately and provide:
- ✅ Data validation and integrity
- ✅ Session-based security
- ✅ Protection against malformed data
- ✅ Reasonable performance
- ✅ Clear error messages

**Apply the development rules now** and your Firestore database will be properly secured for development while maintaining all necessary functionality!
