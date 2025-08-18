# API Docs


### Login into your telegram session (request for the code)

```bash
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{"phone": "invalid"}'
```

### Enter the code for login

```bash
curl -X POST "http://localhost:8000/api/v1/code" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+9999999999",
    "code": "12345"
  }'
```


### Logout of the session

```bash
curl -X GET "http://localhost:8000/api/v1/logout/+1234567890"
```