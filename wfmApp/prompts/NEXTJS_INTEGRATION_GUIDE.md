# Next.js Frontend-Backend Authentication Integration Guide

This document describes how the Next.js frontend application (`figmaDashboard` branch) integrates with the backend WFM microservices for authentication and authorization.

## Overview

The Next.js frontend application is now fully integrated with the backend microservices (`wfmv4/`) for authentication, user management, and role-based access control.

## Architecture

```
Next.js Frontend (App Router) ←→ Backend Microservices
     ↓                              ↓
- Authentication Service (Port 8001)
- API Gateway (Port 8000)
- Other Services (Ports 8002-8006)
```

## Backend Services

### Authentication Service (Port 8001)
- **Login Endpoint**: `POST /auth/login`
- **Token Verification**: `POST /auth/verify`
- **User Management**: CRUD operations for users, roles, and tenants

### API Gateway (Port 8000)
- Routes requests to appropriate microservices
- Handles CORS and request forwarding
- Provides unified API interface

## Frontend Integration

### Authentication Flow

1. **Login Process**:
   - User enters tenant ID, username, and password
   - Frontend sends credentials to `/auth/login` endpoint
   - Backend validates credentials and returns JWT token
   - Frontend stores token in localStorage
   - User is redirected to dashboard

2. **Token Management**:
   - JWT tokens are automatically included in all API requests
   - Token expiration is handled automatically
   - Unauthorized requests redirect to login page

3. **Role-Based Routing**:
   - SuperAdmin/Admin → `/dashboard`
   - Vendor → `/dashboard`
   - Technician → `/dashboard`
   - Demo → `/dashboard`

### Key Components

#### AuthService (`lib/auth-service.ts`)
- Handles all authentication API calls
- Manages JWT tokens
- Provides automatic token refresh and error handling

#### AuthContext (`contexts/auth-context.tsx`)
- Manages authentication state
- Provides login/logout functions
- Handles user session persistence

#### ProtectedRoute (`components/protected-route.tsx`)
- Guards routes based on authentication status
- Enforces role-based access control
- Redirects unauthorized users

#### LoginPage (`app/login/page.tsx`)
- Provides login form with tenant ID, username, and password
- Handles authentication errors
- Redirects to dashboard on success

## Configuration

### Environment Variables
Create a `.env.local` file in the frontend root:

```bash
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8000
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8000
NODE_ENV=development
```

### API Configuration (`lib/api.ts`)
- Centralized configuration for all API endpoints
- Environment-specific settings
- Timeout and header configurations

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/verify` - Token verification
- `POST /auth/refresh` - Token refresh (future)

### User Management
- `GET /users` - List users
- `POST /users` - Create user
- `GET /users/{id}` - Get user details
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

### Role Management
- `GET /roles` - List roles
- `POST /roles` - Create role
- `GET /roles/{id}` - Get role details
- `PUT /roles/{id}` - Update role
- `DELETE /roles/{id}` - Delete role

### Tenant Management
- `GET /tenants` - List tenants
- `POST /tenants` - Create tenant
- `GET /tenants/{id}` - Get tenant details
- `PUT /tenants/{id}` - Update tenant
- `DELETE /tenants/{id}` - Delete tenant

## Data Models

### User
```typescript
interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
  tenant_id: string;
  status: string;
  permissions: string[];
}
```

### Login Credentials
```typescript
interface LoginCredentials {
  username: string;
  password: string;
  tenant_id: string;
}
```

### Authentication Response
```typescript
interface AuthResponse {
  access_token: string;
  expires_in: number;
  user: User;
}
```

## Security Features

1. **JWT Authentication**: Secure token-based authentication
2. **Role-Based Access Control**: Routes and components protected by user roles
3. **Automatic Token Management**: Tokens are automatically included in requests
4. **Session Persistence**: User sessions persist across browser refreshes
5. **Secure Logout**: Proper cleanup of authentication state

## Error Handling

- **401 Unauthorized**: Invalid credentials or expired tokens
- **400 Bad Request**: Invalid input data
- **403 Forbidden**: Insufficient permissions
- **500 Internal Server Error**: Backend service issues

## Development Setup

1. **Start Backend Services**:
   ```bash
   cd wfmv4
   docker-compose up -d
   ```

2. **Start Frontend**:
   ```bash
   cd wfmApp
   npm run dev
   ```

3. **Test Authentication**:
   - Navigate to `http://localhost:3000/login`
   - Use valid credentials with tenant ID
   - Verify role-based routing works

## Testing

The integration includes comprehensive error handling and user feedback:
- Loading states during authentication
- Clear error messages for failed login attempts
- Automatic redirects based on user roles
- Proper handling of network errors

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run test-backend` - Test backend connectivity

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure backend CORS is properly configured
2. **Port Conflicts**: Verify backend services are running on correct ports
3. **Token Issues**: Check localStorage for valid tokens
4. **Role Mismatches**: Verify user has correct roles assigned

### Debug Mode

Enable debug logging in the browser console:
```typescript
// In AuthService constructor
console.log('API Config:', API_CONFIG);
console.log('Environment:', ENV_CONFIG);
```

## Support

For integration issues or questions:
1. Check the browser console for error messages
2. Verify backend services are running and accessible
3. Check network tab for failed API requests
4. Review authentication flow in React DevTools
5. Run `npm run test-backend` to verify connectivity

## Next Steps

1. **Test the integration** with the provided credentials
2. **Customize the dashboard** based on user roles
3. **Add more protected routes** as needed
4. **Implement token refresh** for better user experience
5. **Add audit logging** for security tracking
