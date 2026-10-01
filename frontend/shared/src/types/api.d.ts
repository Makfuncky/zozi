/**
 * Auto-generated TypeScript types from FastAPI OpenAPI schema
 * Run `npm run generate:api-types` to regenerate
 */

export interface paths {
  "/api/v1/auth/login": {
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["LoginRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["LoginResponse"];
          };
        };
        401: {
          content: {
            "application/json": components["schemas"]["ErrorResponse"];
          };
        };
      };
    };
  };
  "/api/v1/auth/register": {
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["RegisterRequest"];
        };
      };
      responses: {
        201: {
          content: {
            "application/json": components["schemas"]["UserResponse"];
          };
        };
        400: {
          content: {
            "application/json": components["schemas"]["ErrorResponse"];
          };
        };
      };
    };
  };
  "/api/v1/auth/me": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["UserResponse"];
          };
        };
        401: {
          content: {
            "application/json": components["schemas"]["ErrorResponse"];
          };
        };
      };
    };
  };
  "/api/v1/products": {
    get: {
      parameters: {
        query: {
          page?: number;
          limit?: number;
          category?: string;
          search?: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["ProductListResponse"];
          };
        };
      };
    };
  };
  "/api/v1/products/{id}": {
    get: {
      parameters: {
        path: {
          id: number;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Product"];
          };
        };
        404: {
          content: {
            "application/json": components["schemas"]["ErrorResponse"];
          };
        };
      };
    };
  };
  "/api/v1/orders": {
    get: {
      parameters: {
        query: {
          page?: number;
          limit?: number;
          status?: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["OrderListResponse"];
          };
        };
      };
    };
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["CreateOrderRequest"];
        };
      };
      responses: {
        201: {
          content: {
            "application/json": components["schemas"]["Order"];
          };
        };
      };
    };
  };
  "/api/v1/orders/{id}": {
    get: {
      parameters: {
        path: {
          id: number;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Order"];
          };
        };
      };
    };
  };
  "/api/v1/cart": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Cart"];
          };
        };
      };
    };
  };
  "/api/v1/cart/items": {
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["AddToCartRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Cart"];
          };
        };
      };
    };
  };
  "/api/v1/suppliers": {
    get: {
      parameters: {
        query: {
          page?: number;
          limit?: number;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["SupplierListResponse"];
          };
        };
      };
    };
  };
}

export interface components {
  schemas: {
    LoginRequest: {
      email: string;
      password: string;
    };
    LoginResponse: {
      access_token: string;
      refresh_token: string;
      token_type: string;
      user: components["schemas"]["User"];
    };
    RegisterRequest: {
      email: string;
      password: string;
      name: string;
      role?: "customer" | "supplier";
    };
    User: {
      id: number;
      email: string;
      name: string;
      role: string;
      is_verified: boolean;
      created_at: string;
    };
    UserResponse: {
      user: components["schemas"]["User"];
    };
    Product: {
      id: number;
      name: string;
      description: string;
      price: number;
      currency: string;
      images: string[];
      category: string;
      supplier_id: number;
      stock: number;
      is_active: boolean;
      created_at: string;
    };
    ProductListResponse: {
      items: components["schemas"]["Product"][];
      total: number;
      page: number;
      limit: number;
    };
    Order: {
      id: number;
      user_id: number;
      status: string;
      items: components["schemas"]["OrderItem"][];
      total: number;
      currency: string;
      created_at: string;
    };
    OrderItem: {
      id: number;
      product_id: number;
      quantity: number;
      price: number;
    };
    OrderListResponse: {
      items: components["schemas"]["Order"][];
      total: number;
      page: number;
      limit: number;
    };
    CreateOrderRequest: {
      items: {
        product_id: number;
        quantity: number;
      }[];
      shipping_address_id: number;
    };
    Cart: {
      id: number;
      items: components["schemas"]["CartItem"][];
      total: number;
      currency: string;
    };
    CartItem: {
      id: number;
      product_id: number;
      quantity: number;
      price: number;
      product?: components["schemas"]["Product"];
    };
    AddToCartRequest: {
      product_id: number;
      quantity: number;
    };
    Supplier: {
      id: number;
      name: string;
      description: string;
      is_verified: boolean;
      rating: number;
      created_at: string;
    };
    SupplierListResponse: {
      items: components["schemas"]["Supplier"][];
      total: number;
      page: number;
      limit: number;
    };
    ErrorResponse: {
      detail: string;
      code?: string;
    };
  };
}

export interface operations {}

export interface external {}
