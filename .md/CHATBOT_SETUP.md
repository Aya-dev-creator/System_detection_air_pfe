# Weather Chatbot Setup Guide

## Overview
The weather chatbot is powered by **Mistral AI** and integrated with your AirWatch weather monitoring system. It provides intelligent weather-related conversations and recommendations based on real-time weather data.

## Features
✅ Real-time weather conversations
✅ Health and safety recommendations
✅ Outdoor activity suggestions
✅ Air quality integration
✅ Beautiful responsive UI
✅ Conversation history management

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs the Mistral AI client (`mistralai==0.4.2`).

### 2. Get Mistral API Key
1. Visit: https://console.mistral.ai/
2. Sign up for a free account
3. Generate an API key
4. Keep it safe (never commit to git)

### 3. Configure Environment Variable
Add to your `.env` file:
```
MISTRAL_API_KEY=your_api_key_here
```

Example `.env` file:
```
# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_api_key_here

# OpenWeather API (existing)
OPENWEATHER_API_KEY=your_openweather_key

# Other existing configurations...
```

## Usage

### Starting the Server
```bash
python web_server.py
```

Then navigate to:
- **Chatbot**: http://localhost:5000/chatbot
- **Dashboard**: http://localhost:5000/
- **Map**: http://localhost:5000/map

### API Endpoints

#### 1. Send Message to Chatbot
```bash
POST /api/chatbot/message
Content-Type: application/json

{
    "message": "What should I wear today?"
}
```

Response:
```json
{
    "message": "Based on the current weather conditions...",
    "status": "success",
    "timestamp": "2026-05-26T10:30:00"
}
```

#### 2. Get Weather Advice
```bash
GET /api/chatbot/advice
```

Response:
```json
{
    "message": "Based on current weather conditions: Temperature 22°C, Humidity 65%...",
    "status": "success",
    "timestamp": "2026-05-26T10:30:00"
}
```

#### 3. Reset Conversation
```bash
POST /api/chatbot/reset
```

Response:
```json
{
    "message": "Conversation reset",
    "status": "success",
    "timestamp": "2026-05-26T10:30:00"
}
```

## File Structure

```
versel/
├── weather_chatbot.py          # Main chatbot module
├── web_server.py               # Flask app with chatbot endpoints
├── requirements.txt            # Updated with Mistral dependency
├── templates/
│   └── chatbot.html           # Beautiful chatbot UI
└── CHATBOT_SETUP.md           # This file
```

## Code Architecture

### WeatherChatbot Class
Located in `weather_chatbot.py`:

```python
from weather_chatbot import WeatherChatbot, get_chatbot

# Initialize
chatbot = WeatherChatbot(api_key="your_key")

# Send message
response = chatbot.chat("What's the weather like?")

# Get specific advice
advice = chatbot.get_weather_advice(
    temperature=22,
    humidity=65,
    weather_type="sunny",
    air_quality="Good"
)

# Reset conversation
chatbot.reset_conversation()
```

## Example Chatbot Interactions

### Question 1: General Weather
```
User: "What's the weather like today?"
Bot: "Based on current data, it's sunny with a temperature of 22°C and humidity at 65%. Perfect for outdoor activities! I'd recommend staying hydrated and using sunscreen if you're going outside."
```

### Question 2: Health Recommendation
```
User: "Is it safe to exercise outside?"
Bot: "With current conditions (22°C, 65% humidity, good air quality), it's excellent for exercising outside. I recommend light to moderate exercise. Make sure to drink plenty of water and take breaks every 30 minutes."
```

### Question 3: Activity Suggestion
```
User: "What can I do today?"
Bot: "Perfect day for outdoor activities! I suggest: jogging, cycling, hiking, or picnicking. Avoid peak heat hours (12-4 PM). Remember to wear sunscreen and bring water."
```

## Troubleshooting

### Issue: "Mistral API key not found"
**Solution**: Make sure you've set `MISTRAL_API_KEY` in your `.env` file.

### Issue: "Error: 401 Unauthorized"
**Solution**: Check that your API key is correct. Visit https://console.mistral.ai/ to verify.

### Issue: "Connection timeout"
**Solution**: Check your internet connection and Mistral API status at https://status.mistral.ai/

### Issue: "Empty responses"
**Solution**: Restart the Flask server. The chatbot caches conversation history for performance.

## Performance Notes

- **Response Time**: Usually 1-3 seconds (depends on Mistral API)
- **Conversation Memory**: Keeps last 10 messages for context
- **Rate Limiting**: Mistral Free tier has rate limits - consider upgrading for production
- **Temperature**: Set to 0.7 for balanced creativity and consistency

## Security Best Practices

1. ✅ Never commit API keys to git
2. ✅ Use `.env` file with `.gitignore`
3. ✅ Validate user input on the server side
4. ✅ Add CORS headers if needed for API calls from other domains
5. ✅ Consider rate limiting for production deployment

## Next Steps

1. ✅ Get your Mistral API key
2. ✅ Add it to `.env`
3. ✅ Run `pip install -r requirements.txt`
4. ✅ Start the server: `python web_server.py`
5. ✅ Open http://localhost:5000/chatbot
6. ✅ Chat with your weather chatbot!

## Support & Documentation

- **Mistral AI Docs**: https://docs.mistral.ai/
- **Weather Chatbot Code**: See `weather_chatbot.py`
- **Flask Integration**: See routes in `web_server.py` (lines ~1757-1857)

---

**Enjoy your weather chatbot! 🤖🌤️**
