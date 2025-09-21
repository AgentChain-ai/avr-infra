# 🧪 Phase 1 API Testing Guide - Akash Institute Outreach System

## 🚀 Quick Start

### Prerequisites
1. **Server Running**: Make sure the FastAPI server is running:
   ```bash
   cd akash-outreach
   uvicorn app.main:app --port 8000
   ```

2. **Base URL**: All API requests use: `http://localhost:8000`

3. **API Documentation**: Interactive docs available at: `http://localhost:8000/docs`

---

## 🔐 Authentication API Testing

### 1. Admin Login (Get JWT Token)
```bash
curl -X POST "{{backend_url}}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_info": {
    "username": "admin",
    "is_admin": true,
    "permissions": ["read", "write", "admin"]
  }
}
```

### 2. Get Current User Info
```bash
# Replace YOUR_TOKEN with the access_token from login
curl -X GET "{{backend_url}}/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Logout
```bash
curl -X POST "{{backend_url}}/auth/logout" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 👥 Students API Testing

### 1. List All Students
```bash
curl -X GET "{{backend_url}}/students" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Create New Student
```bash
curl -X POST "{{backend_url}}/students" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "student_data": {
      "student_name": "Rahul Sharma",
      "parent_name": "Suresh Sharma",
      "scholarship_amount": 50000,
      "rank": 145,
      "course": "Engineering"
    },
    "priority": 1
  }'
```

### 3. Get Student by ID
```bash
curl -X GET "{{backend_url}}/students/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Update Student
```bash
curl -X PUT "{{backend_url}}/students/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_data": {
      "student_name": "Rahul Sharma Updated",
      "call_notes": "Parent very interested in course details"
    },
    "call_status": "completed"
  }'
```

### 5. Search Students
```bash
curl -X GET "{{backend_url}}/students/search?q=Rahul" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Get Students by Status
```bash
curl -X GET "{{backend_url}}/students?call_status=pending&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. Delete Student
```bash
curl -X DELETE "{{backend_url}}/students/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ⚙️ Field Configuration API Testing

### 1. List All Field Configurations
```bash
curl -X GET "{{backend_url}}/fields" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Create New Field Configuration
```bash
curl -X POST "{{backend_url}}/fields" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "scholarship_type",
    "field_type": "select",
    "field_label": "Scholarship Type",
    "is_required": true,
    "field_options": {
      "options": ["Full Scholarship", "Partial Scholarship", "Merit Based", "Need Based"]
    },
    "display_order": 5
  }'
```

### 3. Get Active Fields Only
```bash
curl -X GET "{{backend_url}}/fields/active" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Update Field Configuration
```bash
curl -X PUT "{{backend_url}}/fields/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "field_label": "Student Full Name (Updated)",
    "is_required": true,
    "validation_rules": {
      "min_length": 2,
      "max_length": 100
    }
  }'
```

---

## 📞 Calls API Testing

### 1. List All Calls
```bash
curl -X GET "{{backend_url}}/calls" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Create New Call Log
```bash
curl -X POST "{{backend_url}}/calls" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "phone_number": "9876543210",
    "call_status": "completed",
    "call_duration": 180,
    "conversation_data": {
      "questions_asked": ["What is the course curriculum?", "What are the fees?"],
      "answers_provided": {
        "curriculum": "Comprehensive 4-year engineering program",
        "fees": "₹2,50,000 per year"
      },
      "satisfaction_level": "high"
    },
    "ai_summary": "Parent satisfied with course details and fee structure"
  }'
```

### 3. Get Calls for Specific Student
```bash
curl -X GET "{{backend_url}}/calls/student/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Get Recent Calls
```bash
curl -X GET "{{backend_url}}/calls/recent?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Update Call Log
```bash
curl -X PUT "{{backend_url}}/calls/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "follow_up_required": true,
    "conversation_data": {
      "follow_up_notes": "Parent wants to visit campus next week"
    }
  }'
```

---

## 📚 Context Information API Testing

### 1. List All Context Information
```bash
curl -X GET "{{backend_url}}/context" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Create New Context Information
```bash
curl -X POST "{{backend_url}}/context" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Admission Process",
    "information": "Students need to complete online application, submit documents, and attend counseling session. Merit-based admission with entrance test scores.",
    "priority": 3,
    "tags": ["admission", "process", "requirements"]
  }'
```

### 3. Search Context Information
```bash
curl -X GET "{{backend_url}}/context/search?q=fees" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. AI Context Chat (Get AI Response for Admin)
```bash
curl -X POST "{{backend_url}}/context/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I tell parents about the fee structure?"
  }'
```

### 5. Get Active Context for Voice Agent
```bash
curl -X GET "{{backend_url}}/context/active?priority_min=2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 Analytics API Testing

### 1. Get Complete Dashboard Metrics
```bash
curl -X GET "{{backend_url}}/analytics/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response Structure:**
```json
{
  "total_students": 150,
  "total_calls": 45,
  "calls_completed": 30,
  "calls_pending": 15,
  "success_rate": 66.67,
  "avg_call_duration": 165,
  "students_by_status": {
    "pending": 120,
    "completed": 25,
    "failed": 5
  },
  "calls_by_status": {
    "completed": 30,
    "no_answer": 10,
    "failed": 5
  },
  "recent_activity": [...]
}
```

### 2. Get Student Statistics
```bash
curl -X GET "{{backend_url}}/analytics/students" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Get Call Analytics
```bash
curl -X GET "{{backend_url}}/analytics/calls?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Get System Performance Metrics
```bash
curl -X GET "{{backend_url}}/analytics/performance" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 Health Check & System Status

### 1. Basic Health Check
```bash
curl -X GET "{{backend_url}}/health"
```

### 2. Detailed System Status
```bash
curl -X GET "{{backend_url}}/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📁 CSV Import Testing

### 1. Test CSV Upload and Field Mapping
```bash
# Create a test CSV file first
echo "Student Name,Phone,Parent Name,Scholarship Amount,Rank
Rahul Sharma,9876543210,Suresh Sharma,50000,145
Priya Patel,9876543211,Rajesh Patel,75000,89
Arjun Kumar,9876543212,Vikash Kumar,60000,67" > test_students.csv

# Upload CSV for processing
curl -X POST "{{backend_url}}/students/bulk-import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_students.csv"
```

---

## 🧪 Complete Testing Workflow

### Step-by-Step API Testing
1. **Start Server**: `uvicorn akash-outreach.app.main:app --port 8000`
2. **Get Token**: Login to get JWT token
3. **Test Each Endpoint**: Use the curl commands above
4. **Verify Data**: Check that data is created/updated correctly
5. **Test Error Cases**: Try invalid data to test validation

### Automated Testing Script
```bash
#!/bin/bash
# save as test_api.sh

# 1. Login and get token
TOKEN=$(curl -s -X POST "{{backend_url}}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

echo "Got token: ${TOKEN:0:20}..."

# 2. Test students API
echo "Testing Students API..."
curl -s -X GET "{{backend_url}}/students" \
  -H "Authorization: Bearer $TOKEN" | jq '.total'

# 3. Test analytics API  
echo "Testing Analytics API..."
curl -s -X GET "{{backend_url}}/analytics/dashboard" \
  -H "Authorization: Bearer $TOKEN" | jq '.total_students'

echo "✅ API testing complete!"
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Authentication Errors
```
{"detail": "Not authenticated"}
```
**Solution**: Make sure to include the Bearer token in all protected endpoints

### Issue 2: Database Not Found
```
{"detail": "Database connection failed"}
```
**Solution**: Run `python init_database.py` first to create the database

### Issue 3: Permission Errors
```
PermissionError: Permission denied (os error 13)
```
**Solution**: Run server from akash-outreach directory: `cd akash-outreach && uvicorn app.main:app --port 8000`

### Issue 4: Import Errors
```
ImportError: cannot import name ...
```
**Solution**: Make sure you're in the virtual environment: `source venv/bin/activate`

---

## ✅ Expected Test Results

After running all tests, you should have:
- ✅ JWT authentication working
- ✅ Students created, updated, and searchable
- ✅ Field configurations managing schema
- ✅ Call logs tracking conversations
- ✅ Context information for AI agent
- ✅ Analytics showing real metrics
- ✅ CSV import processing files correctly

## 🎯 Next Steps

Once Phase 1 testing is complete:
1. **Phase 2**: Build Streamlit admin dashboard
2. **Phase 3**: Integrate with AVR voice system
3. **Phase 4**: Add advanced AI features
4. **Phase 5**: Production deployment

---

*Generated for Akash Institute Outreach System - Phase 1 Complete ✅*
