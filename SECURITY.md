# 🔒 ARK Security Documentation

## Security Fixes Implemented

### Path Traversal Vulnerability (CRITICAL) - FIXED ✅

**Issue:** Uncontrolled user data used in file path operations allowed directory traversal attacks.

**Attack Vector:**
```python
# Before fix - VULNERABLE
filepath = "../../../etc/passwd"  # Attacker input
full_path = os.path.join("/app/files", filepath)
# Result: /etc/passwd (escapes container!)
```

**Solution:** Implemented comprehensive path validation function

```python
def validate_file_path(user_path: str) -> Path:
    """
    Validate and sanitize file paths to prevent path traversal attacks.
    
    Security measures:
    1. Blocks empty paths
    2. Strips leading/trailing whitespace and separators
    3. Detects ".." traversal attempts
    4. Prevents absolute paths
    5. Resolves symlinks and relative paths
    6. Validates resolved path is within BASE_FILES_DIR
    """
```

### Protected Endpoints

All file operation endpoints now use path validation:

#### ✅ POST `/api/files` - Create/Write File
- Validates user-provided path before file creation
- Creates directories only within allowed base
- Prevents writing outside `/app/files`

#### ✅ GET `/api/files/{file_path:path}` - Read File
- Validates path before reading
- Checks file exists and is actually a file (not directory)
- Returns 403 if path escapes base directory

#### ✅ DELETE `/api/files/{file_path:path}` - Delete File
- Validates path before deletion
- Ensures only files can be deleted (not directories)
- Prevents deletion outside allowed base

## Security Best Practices Implemented

### 1. Input Validation
- All user-provided file paths are validated
- Empty paths are rejected
- Paths are sanitized before use

### 2. Path Canonicalization
- Uses `Path.resolve()` to eliminate symlinks
- Resolves relative path components (`.`, `..`)
- Normalizes path separators

### 3. Boundary Checking
- All resolved paths verified against `BASE_FILES_DIR`
- String prefix checking prevents escapes: `str(full_path).startswith(str(BASE_FILES_DIR))`
- Rejects paths outside allowed directory with 403 Forbidden

### 4. Type Safety
- Uses `pathlib.Path` for type-safe path operations
- Avoids string concatenation for paths
- Explicit file vs directory checks

### 5. Error Handling
- HTTPException raised with specific status codes
- 400 Bad Request for invalid paths
- 403 Forbidden for access violations
- 404 Not Found for missing files
- Detailed error messages for debugging (safe for production)

## Additional Security Measures

### CORS Configuration
Currently set to allow all origins for development:
```python
allow_origins=["*"]  # TODO: Restrict in production
```

**Production Recommendation:**
```python
allow_origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

### Redis Security
- Redis accessible only within Docker network
- No external port exposure recommended
- Use Redis password in production: `REDIS_PASSWORD=strong_password`

### Database Security
- SQLite database stored in `/app/data` volume
- File permissions should be restricted: `chmod 600 ark.db`
- Regular backups recommended

### Container Security
- Services run within Docker containers
- Network isolation between services
- Volume mounts restricted to necessary directories

## Threat Model

### Protected Against
✅ Path Traversal (Directory Traversal)  
✅ Arbitrary File Read  
✅ Arbitrary File Write  
✅ Arbitrary File Deletion  
✅ Symlink Attacks  

### Additional Considerations

#### File Upload Size Limits
```python
# Recommended: Add to FastAPI configuration
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_request_size=10_000_000  # 10MB
)
```

#### Rate Limiting
```python
# Recommended: Add rate limiting for file operations
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/files")
@limiter.limit("10/minute")  # Max 10 file operations per minute
async def create_file(request: Request, file_data: dict):
    ...
```

#### Authentication & Authorization
```python
# Recommended: Add authentication
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/api/files")
async def create_file(
    file_data: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Validate JWT token
    token = credentials.credentials
    user = verify_token(token)
    ...
```

## Security Testing

### Test Cases for Path Validation

```python
# Test path traversal attempts
assert_rejects("../../../etc/passwd")
assert_rejects("../../secrets.txt")
assert_rejects("....//....//etc/passwd")
assert_rejects("/etc/passwd")
assert_rejects("~/sensitive_file")

# Test valid paths
assert_accepts("documents/report.txt")
assert_accepts("projects/ark/data.json")
assert_accepts("subfolder/nested/file.md")

# Test edge cases
assert_rejects("")
assert_rejects("   ")
assert_rejects("./")
assert_rejects("../")
```

### Manual Testing

```bash
# Test path traversal protection
curl -X POST http://localhost:8000/api/files \
  -H "Content-Type: application/json" \
  -d '{"path": "../../../etc/passwd", "content": "test"}'
# Expected: 400 Bad Request - "Invalid path: Directory traversal detected"

# Test valid file creation
curl -X POST http://localhost:8000/api/files \
  -H "Content-Type: application/json" \
  -d '{"path": "test/valid.txt", "content": "Hello ARK"}'
# Expected: 200 OK - {"success": true, "path": "test/valid.txt"}

# Test reading with traversal
curl http://localhost:8000/api/files/../../../etc/passwd
# Expected: 400 Bad Request - "Invalid path: Directory traversal detected"
```

## Deployment Security Checklist

### Production Deployment
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Restrict CORS to specific origins
- [ ] Set Redis password: `REDIS_URL=redis://:password@redis:6379`
- [ ] Use environment variables for secrets (never hardcode)
- [ ] Set up firewall rules (only expose necessary ports)
- [ ] Enable Docker security features (AppArmor, SELinux)
- [ ] Implement rate limiting on all endpoints
- [ ] Add authentication and authorization
- [ ] Set up logging and monitoring
- [ ] Regular security updates: `docker-compose pull`
- [ ] Database backups: `cp data/ark.db backups/ark_$(date +%Y%m%d).db`
- [ ] File upload size limits
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (use parameterized queries)
- [ ] XSS protection in frontend
- [ ] CSRF token validation
- [ ] Security headers (CSP, HSTS, X-Frame-Options)

### Container Security
```yaml
# docker-compose.yml security enhancements
services:
  ark-core:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## Incident Response

If you suspect a security breach:

1. **Isolate**: `docker-compose down`
2. **Investigate**: Check logs `docker-compose logs`
3. **Backup**: Save current state for forensics
4. **Patch**: Apply security updates
5. **Restore**: From clean backup if compromised
6. **Monitor**: Watch for suspicious activity

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email security concerns to: security@ark-project.org (if applicable)
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

## Security Changelog

### 2024-11-06 - Path Traversal Fix
- **Severity**: CRITICAL
- **Issue**: Uncontrolled user data in file paths
- **Fix**: Added `validate_file_path()` function
- **Endpoints**: POST/GET/DELETE `/api/files`
- **Status**: ✅ FIXED

---

**Last Updated**: 2024-11-06  
**Security Review**: Recommended every 90 days  
**Next Review**: 2025-02-06

*ARK - Security through sovereignty and vigilance*
