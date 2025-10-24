# DIGiDIG Make Install Fix - October 2025

## 🎯 **Problem**
After reorganizing the project structure to move services from root directories to `services/`, the `make install` command was failing because the Dockerfiles contained hardcoded paths to the old structure.

## ❌ **Error**
```bash
failed to solve: failed to compute cache key: failed to calculate checksum of ref 04b20531-c06a-4e8c-b5a1-6be3358a2af3::13fd32orpoat8rkmq9mnlsxys: "/storage/src/storage.py": not found
```

## 🔧 **Root Cause**
Dockerfiles were still referencing the old paths:
- `COPY storage/requirements.txt .` → Should be `COPY services/storage/requirements.txt .`
- `COPY storage/src/storage.py .` → Should be `COPY services/storage/src/storage.py .`

## ✅ **Solution**
Updated all Dockerfiles to use the new `services/` directory structure:

### Files Fixed:
1. **`services/storage/Dockerfile`**
   ```dockerfile
   # OLD
   COPY storage/requirements.txt .
   COPY storage/src/storage.py .
   
   # NEW
   COPY services/storage/requirements.txt .
   COPY services/storage/src/storage.py .
   ```

2. **`services/identity/Dockerfile`**
   ```dockerfile
   # OLD
   COPY identity/requirements.txt .
   COPY identity/src/ ./src/
   COPY identity/scripts/ ./scripts/
   
   # NEW
   COPY services/identity/requirements.txt .
   COPY services/identity/src/ ./src/
   COPY services/identity/scripts/ ./scripts/
   ```

3. **`services/smtp/Dockerfile`**
   ```dockerfile
   # OLD
   COPY smtp/requirements.txt .
   COPY smtp/src/ .
   
   # NEW
   COPY services/smtp/requirements.txt .
   COPY services/smtp/src/ .
   ```

4. **`services/imap/Dockerfile`**
   ```dockerfile
   # OLD
   COPY imap/requirements.txt .
   COPY imap/src/imap.py .
   
   # NEW
   COPY services/imap/requirements.txt .
   COPY services/imap/src/imap.py .
   ```

5. **`services/client/Dockerfile`**
   ```dockerfile
   # OLD
   COPY client/requirements.txt .
   COPY client/src/ .
   
   # NEW
   COPY services/client/requirements.txt .
   COPY services/client/src/ .
   ```

6. **`services/admin/Dockerfile`**
   ```dockerfile
   # OLD
   COPY admin/requirements.txt .
   COPY admin/src/ .
   
   # NEW
   COPY services/admin/requirements.txt .
   COPY services/admin/src/ .
   ```

7. **`services/apidocs/Dockerfile`**
   ```dockerfile
   # OLD
   COPY apidocs/requirements.txt .
   COPY apidocs/src/ ./src/
   
   # NEW
   COPY services/apidocs/requirements.txt .
   COPY services/apidocs/src/ ./src/
   ```

## 🎉 **Result**
```bash
$ make install
Installing and initializing services...
[+] Building 57.9s (78/78) FINISHED
✔ admin     Built
✔ apidocs   Built  
✔ client    Built
✔ identity  Built
✔ imap      Built
✔ smtp      Built
✔ storage   Built

[+] Running 18/18
✔ Container digidig-postgres-1    Healthy
✔ Container digidig-mongo-1       Healthy
✔ Container digidig-identity-1    Started
✔ Container digidig-storage-1     Started
✔ Container digidig-admin-1       Started
✔ Container digidig-smtp-1        Started
✔ Container digidig-imap-1        Started
✔ Container digidig-client-1      Started
✔ Container digidig-apidocs-1     Started

Installation complete. Default admin user (admin@example.com/admin) is auto-created if needed.
```

## 🔍 **Key Insights**
1. **Docker Context**: Dockerfiles use the project root as build context, so paths must be relative to the root directory
2. **Consistency**: All 7 services needed the same path update pattern
3. **Build Dependencies**: The `common/` and `config/` directories remained at the root, so those paths didn't need changes

## ✅ **Verification**
- All 7 service containers build successfully
- Database containers (postgres, mongo) start correctly
- Full microservices stack deploys without errors
- Default admin user creation works

The project restructure is now fully functional with Docker builds! 🎯