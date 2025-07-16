graph TD
    A[Client Request] --> B[Token Expired?]
    B -->|No| C[✅ Success]
    B -->|Yes| D[🚫 401 Unauthorized]
    D --> E[Has refresh_token?]
    E -->|Yes| F[Try Token Refresh]
    E -->|No| G[Full OAuth Flow]
    F -->|Success| H[Retry Original Request]
    F -->|Failed| G
    G --> I[New Tokens]
    H --> C
    I --> J[Retry Original Request]
    J --> C