```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: initialize request
    Server->>Client: initialize response
    Client->>Server: initialized notification
    
    Note over Client,Server: Connection ready for use
    
    Client->>Client: Client
    Server->>Server: Server
``` 