# Authentication Flow Testing Guide

## Quick Test Script

```bash
#!/bin/bash

echo "=== DIGiDIG Authentication Flow Test ==="
echo ""

# 1. Test unauthenticated access to admin (should redirect)
echo "1. Testing unauthenticated access to admin..."
curl -sI http://10.1.1.26:9105/ | grep -E "HTTP|Location"
echo ""

# 2. Test unauthenticated access to client (should redirect)
echo "2. Testing unauthenticated access to client..."
curl -sI http://10.1.1.26:9104/ | grep -E "HTTP|Location"
echo ""

# 3. Test unauthenticated access to mail (should redirect)
echo "3. Testing unauthenticated access to mail..."
curl -sI http://10.1.1.26:9107/ | grep -E "HTTP|Location"
echo ""

# 4. Test SSO login page
echo "4. Testing SSO login page..."
curl -s http://10.1.1.26:9106/?app=admin | grep -o "<h2>.*</h2>"
echo ""

# 5. Perform login
echo "5. Performing login as admin@example.com..."
curl -X POST http://10.1.1.26:9106/login?app=admin \
  -d "email=admin@example.com" \
  -d "password=admin" \
  -c /tmp/auth_cookies.txt \
  -sI | grep -E "HTTP|Location|Set-Cookie"
echo ""

# 6. Test session verification
echo "6. Testing session verification endpoint..."
curl -b /tmp/auth_cookies.txt \
  http://10.1.1.26:9101/api/session/verify \
  -s | python3 -m json.tool 2>/dev/null || echo "Failed to parse JSON"
echo ""

# 7. Test authenticated access to admin
echo "7. Testing authenticated access to admin..."
curl -b /tmp/auth_cookies.txt \
  http://10.1.1.26:9105/ \
  -sI | grep -E "HTTP|Location"
echo ""

# 8. Test authenticated access to client
echo "8. Testing authenticated access to client..."
curl -b /tmp/auth_cookies.txt \
  http://10.1.1.26:9104/ \
  -sI | grep -E "HTTP|Location"
echo ""

# 9. Test authenticated access to mail
echo "9. Testing authenticated access to mail..."
curl -b /tmp/auth_cookies.txt \
  http://10.1.1.26:9107/ \
  -sI | grep -E "HTTP|Location"
echo ""

# Cleanup
rm -f /tmp/auth_cookies.txt

echo "=== Test Complete ==="
```

## Expected Results

### 1. Unauthenticated Access
```
HTTP/1.1 303 See Other
Location: http://10.1.1.26:9106/?app=admin
```

### 2. SSO Login Page
```
<h2>DIGiDIG Login</h2>
```

### 3. Successful Login
```
HTTP/1.1 303 See Other
Location: http://10.1.1.26:9105
Set-Cookie: access_token=eyJ...; Path=/; HttpOnly; SameSite=Lax
```

### 4. Session Verification
```json
{
  "authenticated": true,
  "username": "admin",
  "roles": ["admin", "user"],
  "is_admin": true
}
```

### 5. Authenticated Access
```
HTTP/1.1 200 OK
```

## Manual Browser Testing

### Test 1: Admin Access Flow
1. Open browser in private/incognito mode
2. Navigate to `http://10.1.1.26:9105/`
3. **Expected:** Redirect to SSO login page showing "Signing in to: admin"
4. Enter credentials: `admin@example.com` / `admin`
5. Click "Login"
6. **Expected:** Redirect back to admin dashboard at `http://10.1.1.26:9105/`

### Test 2: Client Access Flow
1. In same browser session (already authenticated)
2. Navigate to `http://10.1.1.26:9104/`
3. **Expected:** Immediately see client home page (no redirect, session still valid)

### Test 3: Mail Access Flow
1. In same browser session
2. Navigate to `http://10.1.1.26:9107/`
3. **Expected:** Immediately see mail interface (no redirect, session still valid)

### Test 4: New Session
1. Clear cookies or open new private window
2. Navigate to `http://10.1.1.26:9104/`
3. **Expected:** Redirect to SSO showing "Signing in to: client"
4. Login and verify redirect to client home

### Test 5: Non-Admin Access to Admin
1. Create a regular user (not admin role)
2. Login via SSO
3. Try to access `http://10.1.1.26:9105/`
4. **Expected:** See "Access Denied" page

## API Testing with curl

### Complete Flow Example
```bash
# Step 1: Try to access admin without auth
curl -c cookies.txt -b cookies.txt -L http://10.1.1.26:9105/

# Step 2: Login via SSO
curl -c cookies.txt -X POST "http://10.1.1.26:9106/login?app=admin" \
  -d "email=admin@example.com" \
  -d "password=admin"

# Step 3: Access admin with cookie
curl -b cookies.txt http://10.1.1.26:9105/

# Step 4: Verify session
curl -b cookies.txt http://10.1.1.26:9101/api/session/verify

# Step 5: Access other apps with same cookie
curl -b cookies.txt http://10.1.1.26:9104/  # client
curl -b cookies.txt http://10.1.1.26:9107/  # mail
```

## Debugging

### Check Service Health
```bash
curl http://10.1.1.26:9101/api/health  # identity
curl http://10.1.1.26:9106/health      # sso
curl http://10.1.1.26:9105/health      # admin
curl http://10.1.1.26:9104/health      # client
curl http://10.1.1.26:9107/            # mail (no health endpoint)
```

### Check Logs
```bash
# Identity service logs
docker logs digidig-identity

# SSO service logs
docker logs digidig-sso

# Admin service logs
docker logs digidig-admin

# Client service logs
docker logs digidig-client

# Mail service logs
docker logs digidig-mail
```

### Common Issues

#### 1. Cookie Not Set
- **Symptom:** Always redirected to login even after successful authentication
- **Check:** Look for `Set-Cookie` header in SSO response
- **Fix:** Verify SSO `/login` endpoint sets cookie correctly

#### 2. Session Verification Fails
- **Symptom:** 401 errors from `/api/session/verify`
- **Check:** Token expiration, revocation status
- **Fix:** Login again to get fresh token

#### 3. Redirect Loop
- **Symptom:** Continuous redirects between app and SSO
- **Check:** Cookie domain/path settings
- **Fix:** Ensure cookie is accessible across all services

#### 4. Access Denied for Admin
- **Symptom:** Regular user can't access admin
- **Check:** User roles in database
- **Fix:** Grant admin role: `UPDATE user_roles SET role_id=2 WHERE user_id=X`

## Database Verification

```sql
-- Check user roles
SELECT u.username, r.name as role
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.username = 'admin';

-- Check active tokens (should see refresh tokens)
SELECT username, expires_at 
FROM refresh_tokens 
ORDER BY expires_at DESC;

-- Check revoked tokens
SELECT jti, expires_at 
FROM revoked_tokens 
ORDER BY expires_at DESC;
```

## Performance Testing

```bash
# Test 100 concurrent logins
for i in {1..100}; do
  curl -X POST http://10.1.1.26:9106/login?app=client \
    -d "email=admin@example.com" \
    -d "password=admin" \
    -s -o /dev/null -w "%{http_code}\n" &
done
wait

# Test session verification throughput
ab -n 1000 -c 10 -C "access_token=YOUR_TOKEN" \
  http://10.1.1.26:9101/api/session/verify
```

## Security Testing

### 1. Test Invalid Credentials
```bash
curl -X POST "http://10.1.1.26:9106/login?app=admin" \
  -d "email=admin@example.com" \
  -d "password=wrongpassword" \
  -L
# Expected: Redirect to login with error message
```

### 2. Test Expired Token
```bash
# Set access_token cookie with expired JWT
curl -b "access_token=expired.jwt.token" \
  http://10.1.1.26:9105/
# Expected: Redirect to SSO login
```

### 3. Test XSS Protection
```bash
# Try to access cookie from JavaScript (should fail)
# In browser console:
document.cookie
# Expected: access_token should not be visible (HttpOnly)
```

### 4. Test CSRF Protection
```bash
# Try to submit login from different origin
curl -X POST "http://10.1.1.26:9106/login?app=admin" \
  -H "Origin: http://evil.com" \
  -d "email=admin@example.com" \
  -d "password=admin"
# Expected: Should still work (form POST), but cookie SameSite prevents CSRF
```
