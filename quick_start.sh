#!/bin/bash
# quick_start.sh - Start and test DevDeploy

echo "=========================================="
echo "DevDeploy Quick Start"
echo "=========================================="

echo ""
echo "1. Stopping any running containers..."
docker-compose down

echo ""
echo "2. Starting containers..."
docker-compose up -d --build

echo ""
echo "3. Waiting for API to start..."
sleep 10

echo ""
echo "4. Testing API..."
curl -s http://localhost:8000 | grep -q "Welcome"
if [ $? -eq 0 ]; then
    echo "   API is running!"
else
    echo "   API failed to start"
    exit 1
fi

echo ""
echo "5. Creating test user..."
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","username":"admin","password":"AdminPass123!"}' \
     -s | grep -q "id"
if [ $? -eq 0 ]; then
    echo "   Test user created"
else
    echo "   User may already exist"
fi

echo ""
echo "6. Getting access token..."
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login?username=admin@example.com&password=AdminPass123!" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
if [ $? -eq 0 ]; then
    echo "   Token obtained: ${TOKEN:0:20}..."
else
    echo "   Failed to get token"
    exit 1
fi

echo ""
echo "=========================================="
echo "READY TO USE!"
echo "=========================================="
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Test credentials:"
echo "  Email: admin@example.com"
echo "  Password: AdminPass123!"
echo ""
echo "To test with curl:"
echo "  curl -H \"Authorization: Bearer $TOKEN\" http://localhost:8000/auth/me"
echo ""
echo "To run full test:"
echo "  python test_all_endpoints.py"
echo ""
echo "=========================================="