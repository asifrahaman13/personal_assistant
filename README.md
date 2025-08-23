## AI POWERED SECOND BRAIN

A production-ready, Personalized AI-powered second brain assistant.


## 🚀 Production Features

### Telegram auto reply as an AI AI-powered second brain. Capable of giving text as well as multimedia responses.

<img width="378" height="765" alt="Screenshot from 2025-08-21 10-18-14" src="https://github.com/user-attachments/assets/ed6eb565-173a-4353-9178-0db06279dac5" />
<img width="378" height="765" alt="Screenshot from 2025-08-21 10-18-51" src="https://github.com/user-attachments/assets/8bcc5f11-ae0f-4d49-89f2-451abd6f676b" />
<img width="378" height="765" alt="Screenshot from 2025-08-21 10-19-20" src="https://github.com/user-attachments/assets/6e1a96b1-734b-4860-af73-00202e4ad12f" />

### Email-based auto response. 

<img width="1526" height="810" alt="Screenshot from 2025-08-23 10-20-41" src="https://github.com/user-attachments/assets/013744f1-c940-47a8-9cfa-775ed1e3642b" />
<img width="1580" height="786" alt="Screenshot from 2025-08-23 10-22-32" src="https://github.com/user-attachments/assets/7b23811d-f07b-4a33-84e2-716948e7094a" />
<img width="1590" height="644" alt="Screenshot from 2025-08-21 10-21-57" src="https://github.com/user-attachments/assets/474c3d9c-399b-461c-8b89-f599520a3167" />

### Dashboard for data and visualization

<img width="1893" height="959" alt="Screenshot from 2025-08-21 16-46-24" src="https://github.com/user-attachments/assets/4ca5127b-ce3a-4e00-a9eb-3f8362cb0a86" />


## 🛠️ Production Setup

### 1. Environment Configuration

Copy the example environment file:
```bash
cp env.example .env
```

Edit `.env` with your credentials:

Start the production stack:
```bash
docker-compose up -d
```

This will start:
- MongoDB database
- Personal Assistant application

### 3. Local Development

Install dependencies:
```bash
uv sync
```

Run the production version:
```bash
uv run uvicorn src.main:app --reload 2>&1 | tee out.log
```

## 📈 MongoDB Collections

The application creates the following collections:

- **sessions**: Telegram session data
- **groups**: Group information and metadata
- **messages**: Cached message data
- **analyses**: Analysis results and reports

## 🔧 Production Configuration


### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f persona_ai 

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## 📊 Usage

### Batch Analysis Mode
1. **First Run**: The application will prompt for Telegram verification code
2. **Group Selection**: Choose from available groups
3. **Analysis**: View comprehensive analysis including:
   - Total messages and unique users
   - Sentiment distribution
   - Top active users
   - Average sentiment scores


**Features:**
- Real-time message reception
- Automatic sentiment analysis
- Custom message handlers per group
- MongoDB storage of real-time messages
- Event-driven architecture similar to WebSockets

## Formatting and tooling 

If precommit hook not installed 

```bash
pre-commit install
```
Before pushing any changes run the following code. However if you don't run run it it will run during commit messages.

```bash
uv run pre-commit run --all-files
```

## 🔒 Security

- Session data stored securely in MongoDB
- No local file storage
- Environment-based configuration
- Containerized deployment

## 📝 Logs

Application logs are stored in out.log when running locally.

## 🚀 Scaling

For high-volume production:

1. **MongoDB Replica Set**: Configure MongoDB replica set for high availability
2. **Load Balancer**: Use nginx or similar for multiple instances
3. **Redis Caching**: Add Redis for additional caching layer
4. **Monitoring**: Add Prometheus/Grafana for metrics

## 🔧 Troubleshooting

### No Messages Found
- Check group permissions
- Verify group has text messages
- Increase time period in code

### MongoDB Connection Issues
- Verify MongoDB is running: `docker-compose ps`
- Check connection string in `.env`
- View logs: `docker-compose logs mongodb`

### Session Issues
- Clear MongoDB sessions collection
- Re-authenticate with Telegram
