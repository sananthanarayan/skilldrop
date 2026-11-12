# Mermaid sequence diagram starter

Use for: showing the **order** of messages between participants. Best when "who calls whom in what order" is the question.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as Web app
    participant API as API gateway
    participant Auth as Auth service
    participant DB as Database

    User->>Web: Click "sign in"
    Web->>API: POST /login {email, pwd}
    API->>Auth: Validate credentials
    Auth->>DB: SELECT user WHERE email=?
    DB-->>Auth: User row
    Auth-->>API: JWT (15 min) + refresh
    API-->>Web: Set-Cookie, 200 OK
    Web-->>User: Dashboard

    Note over API,Auth: All hops over mTLS
```

## Tips

- `->>` solid arrow (call) · `-->>` dashed arrow (return/async) · `-x` lost message
- `autonumber` adds 1, 2, 3 to each step — great for design reviews
- `Note over A,B: text` annotates a span; `Note left of A: text` annotates one side
- `loop`, `alt`/`else`, `par` for control flow:
  ```
  alt token valid
      API-->>Web: 200
  else token expired
      API-->>Web: 401
  end
  ```
- Don't overuse — past ~12 messages it becomes a wall. Split into "happy path" and "error path" diagrams.
