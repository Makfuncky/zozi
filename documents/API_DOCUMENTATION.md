# README for API Documentation Enhancement

## Zozi API OpenAPI Documentation

### Overview

The Zozi E-commerce platform includes comprehensive OpenAPI documentation for all backend APIs, generated automatically by FastAPI.

### Documentation Access

#### Interactive API Explorer
- **Swagger UI**: `http://localhost:8000/docs`
- **Redoc**: `http://localhost:8000/redoc`
- **Raw OpenAPI Schema**: `http://localhost:8000/openapi.json`

#### API Versioning

All API endpoints are versioned with `/api/v1/` prefix to support
backward compatibility for future updates.

- **Base Path**: `/api/v1/`
- **Example**: `/api/v1/auth/login`

#### Documentation Features

1. **Auto-Generated Documentation**
   - All endpoint parameters documented
   - Request/response models automatically included
   - Response examples and schemas
   - Error responses and status codes

2. **Enhanced Documentation**
   - Detailed parameter descriptions
   - Request/response examples
   - Tag organization for better navigation
   - Security scheme documentation

3. **Key API Endpoints**

   #### Authentication
   - `POST /api/v1/auth/login` - User authentication
   - `POST /api/v1/auth/register` - User registration
   - `POST /api/v1/auth/logout` - User logout

   #### Users
   - `GET /api/v1/users` - List users (admin)
   - `GET /api/v1/users/{id}` - Get user details
   - `PUT /api/v1/users/{id}` - Update user (admin)

   #### Orders
   - `GET /api/v1/orders` - List user orders
   - `POST /api/v1/orders` - Create new order
   - `GET /api/v1/orders/{id}` - Get order details

   #### Payments
   - `POST /api/v1/payments` - Process payment
   - `GET /api/v1/payments/{id}` - Get payment status
   - `POST /api/v1/payments/webhook` - Payment webhook handler

   #### Products
   - `GET /api/v1/products` - List products
   - `GET /api/v1/products/{id}` - Get product details
   - `GET /api/v1/products/search` - Search products

   #### Admin APIs
   - `GET /api/v1/admin/*` - Admin-only endpoints (authentication required)

3. **Security**

   - JWT-based authentication
   - Role-based access control
   - CORS configured for frontend applications
   - Rate limiting and security headers

4. **API Response Format**

   All API responses follow a consistent format:

   ```json
   {
     "success": true,
     "data": {...},
     "message": "Optional message",
     "error": null
   }
   ```

   Error responses:

   ```json
   {
     "success": false,
     "data": null,
     "message": "Error message",
     "error": {
       "code": "ERROR_CODE",
       "details": "Additional error information"
     }
   }
   ```

### Example API Usage

#### Get Products

```bash
curl -X GET "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### Create Order

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2, "price": 29.99}
    ],
    "shipping_address": {
      "street": "123 Main St",
      "city": "New York",
      "zip": "10001",
      "country": "US"
    }
  }'
```

### API Versioning Strategy

The platform uses URL-based API versioning:

```
Version 1 (current):
  GET /api/v1/products

Version 2 (future):
  GET /api/v2/products
```

This approach ensures backward compatibility for clients while allowing
for future API improvements and deprecations.

### Authentication

Most API endpoints require authentication:

1. **Login First**:

   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "user@example.com", "password": "password123"}'
   ```

2. **Use Token**: Include the JWT token in the Authorization header:

   ```
   Authorization: Bearer YOUR_JWT_TOKEN
   ```

### Error Handling

Common HTTP status codes:

- **200** - Success
- **400** - Bad Request (invalid input)
- **401** - Unauthorized (missing/invalid token)
- **403** - Forbidden (insufficient permissions)
- **404** - Not Found (resource doesn't exist)
- **500** - Internal Server Error

### Development

For API development:

1. Run the backend server:
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

2. Test API endpoints using the Swagger UI at `http://localhost:8000/docs`

3. Generate OpenAPI schema:
   ```bash
   curl http://localhost:8000/openapi.json > api-schema.json
   ```

### Contact

For API documentation questions or issues:
- Check the API documentation at `http://localhost:8000/docs`
- Contact the development team for additional documentation
- Review individual router files for specific endpoint details

---

*This documentation is auto-generated from the FastAPI OpenAPI schema.*
*For detailed endpoint information, refer to individual router files in `backend/routers/`.*
