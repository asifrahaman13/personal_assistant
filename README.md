# Telegram Group Analyzer - Production Ready

A production-ready Telegram group message analyzer with MongoDB storage, sentiment analysis, and user activity tracking.


<img width="1905" height="964" alt="Screenshot from 2025-07-30 10-22-32" src="https://github.com/user-attachments/assets/8ad73723-b3ba-4c6a-9bc8-a98469648925" />

<img width="1905" height="964" alt="Screenshot from 2025-07-30 10-22-47" src="https://github.com/user-attachments/assets/dba7ad46-30b1-4c58-9425-786d4dfb80a9" />

<img width="1905" height="964" alt="Screenshot from 2025-07-30 10-41-18" src="https://github.com/user-attachments/assets/702625fd-59a6-4d6c-9a9d-60ad37045ead" />

<img width="1905" height="964" alt="Screenshot from 2025-07-30 10-21-56" src="https://github.com/user-attachments/assets/63eb9e92-f894-48c2-98b7-b6b97a8c0ce4" />


## 🚀 Production Features

- **MongoDB Storage**: Session data, messages, and analysis results stored in MongoDB
- **Caching**: Intelligent message caching to reduce API calls
- **Docker Support**: Complete containerized deployment
- **Scalable**: Designed for production workloads
- **Session Management**: Secure session storage in database
- **Real-Time Messaging**: WebSocket-like functionality for live message reception

## 📊 Analysis Features

- **Unique User Tracking**: Count and analyze unique users in groups
- **Sentiment Analysis**: Analyze message sentiment (positive/negative/neutral)
- **User Activity**: Track most active users
- **Message Statistics**: Comprehensive message analytics
- **Chunked Processing**: Efficient handling of large message volumes with configurable chunk sizes
- **Multiple LLM Support**: OpenAI GPT-4 and Google Gemini Pro integration for AI-powered analysis

## 🔄 Real-Time Capabilities

**Telegram does NOT provide native WebSocket APIs**, but offers several real-time options:

### 1. **Telethon Event System** (Implemented)
- Uses long polling with event handlers
- Provides WebSocket-like functionality
- Messages received as they arrive
- Automatic sentiment analysis
- Custom handlers per group

### 2. **Telegram Bot API Webhooks**
- HTTP POST requests for bot updates
- Requires public HTTPS endpoint
- Limited to bot functionality

### 3. **MTProto Protocol**
- Telegram's native protocol
- Used by Telethon library
- Provides real-time updates
- Most reliable for user accounts

## 🛠️ Production Setup

### 1. Environment Configuration

Copy the example environment file:
```bash
cp env.example .env
```

Edit `.env` with your credentials:

```bash
# Required for OpenAI integration
OPENAI_API_KEY=your_openai_api_key_here

# Required for Gemini integration  
GEMINI_API_KEY=your_gemini_api_key_here

# Other required variables...
```

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
docker-compose logs -f telegram-analyzer

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
