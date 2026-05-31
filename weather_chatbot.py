"""
Weather Chatbot using Mistral AI API
Provides intelligent weather-related conversations and recommendations
"""
import os
import logging
from datetime import datetime
from mistralai.client import Mistral

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeatherChatbot:
    """Weather chatbot powered by Mistral AI"""
    
    def __init__(self, api_key=None):
        """
        Initialize the Weather Chatbot
        
        Args:
            api_key (str): Mistral API key. If None, uses MISTRAL_API_KEY env var
        """
        self.api_key = api_key or os.getenv('MISTRAL_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Mistral API key not found. Set MISTRAL_API_KEY environment variable "
                "or pass it to WeatherChatbot()"
            )
        
        self.client = Mistral(api_key=self.api_key)
        self.model = "mistral-small-latest"  # Using Mistral Small for faster responses
        
        # System prompt for the weather chatbot (French + HTML format)
        self.system_prompt = """Vous êtes l'assistant IA météo et qualité de l'air d'AirWatch.
Votre rôle est de répondre aux questions des utilisateurs en français de manière claire, chaleureuse et structurée.

Consignes obligatoires de formatage et de style :
1. Répondez TOUJOURS en français.
2. Structurez votre réponse avec des sections courtes et distinctes.
3. Utilisez des émojis appropriés au début des points clés pour rendre la lecture agréable.
4. IMPORTANT : Formatez votre réponse DIRECTEMENT en HTML brut. Utilisez uniquement les balises suivantes :
   - <p>...</p> pour les paragraphes ordinaires.
   - <strong>...</strong> pour mettre en valeur les mots importants.
   - <br> pour les retours à la ligne simples.
   - <h3>...</h3> pour les titres de section/rubriques.
   - <ul>...</ul> et <li>...</li> pour les listes à puces.
5. Ne mettez AUCUN bloc de code Markdown ou enveloppe de code comme ```html ou ```. Retournez directement le HTML brut.
6. Restez focalisé sur la météo, la qualité de l'air, la santé et les conseils associés. Ne proposez rien qui sorte de ce cadre."""

        # System prompt for the enterprise chatbot
        self.enterprise_system_prompt = """Vous êtes l'assistant IA industriel et environnemental d'AirWatch Entreprise.
Votre rôle est d'analyser les émissions de CO2 des usines industrielles, d'évaluer l'efficacité des systèmes de lavage de CO2 (CO2 Wash) et de proposer des solutions d'optimisation énergétique pour réduire l'empreinte carbone.

Consignes obligatoires de formatage et de style :
1. Répondez TOUJOURS en français dans un ton professionnel, analytique et orienté solution B2B.
2. Formatez DIRECTEMENT en HTML brut (sans bloc markdown ```html). Utilisez <p>, <strong>, <br>, <h3>, <ul>, <li>.
3. Résumez les émissions de manière claire, et proposez toujours 2 ou 3 pistes d'optimisation technique.
4. Restez concentré sur l'industrie, le CO2, l'efficacité énergétique et la qualité de l'air industriel."""
        
        self.conversation_history = []
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
    
    def chat(self, user_message, weather_context=None, mode='standard'):
        """
        Send a message to the chatbot and get a response
        
        Args:
            user_message (str): User's message
            weather_context (dict): Optional weather data to include in context
        
        Returns:
            dict: Response with 'message' and metadata
        """
        try:
            # Build context from weather data if provided
            context_str = ""
            if weather_context:
                context_str = self._build_weather_context(weather_context)
            
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Select appropriate system prompt based on mode
            active_prompt = self.enterprise_system_prompt if mode == 'enterprise' else self.system_prompt
            
            # Prepare messages for API (dict format for mistralai 2.x)
            messages = [
                {"role": "system", "content": active_prompt}
            ]
            
            # Add weather context if available
            if context_str:
                messages.append({
                    "role": "system",
                    "content": f"Current weather context:\n{context_str}"
                })
            
            # Add conversation history (keep last 10 messages)
            for msg in self.conversation_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Call Mistral API
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=512
            )
            
            # Extract response text
            assistant_message = response.choices[0].message.content
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return {
                "message": assistant_message,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Chatbot error: {str(e)}")
            return {
                "message": f"Error: {str(e)}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_weather_advice(self, temperature, humidity, weather_type, air_quality=None):
        """
        Get specific weather advice based on current conditions
        
        Args:
            temperature (float): Temperature in Celsius
            humidity (float): Humidity percentage
            weather_type (str): Type of weather (sunny, rainy, cloudy, etc.)
            air_quality (dict): Optional air quality data
        
        Returns:
            dict: Weather advice from the chatbot
        """
        context = {
            "temperature": temperature,
            "humidity": humidity,
            "weather_type": weather_type,
            "air_quality": air_quality
        }
        
        prompt = f"""Based on the current weather conditions:
- Temperature: {temperature}°C
- Humidity: {humidity}%
- Weather type: {weather_type}
{"- Air quality: " + str(air_quality) if air_quality else ""}

Please provide:
1. Health recommendations for these conditions
2. Suggested outdoor activities (if appropriate)
3. Any safety warnings or precautions"""
        
        return self.chat(prompt, weather_context=context)
    
    def _build_weather_context(self, weather_data):
        """Build a readable weather context string"""
        context = []
        
        if "temperature" in weather_data:
            context.append(f"Temperature: {weather_data['temperature']}°C")
        
        if "humidity" in weather_data:
            context.append(f"Humidity: {weather_data['humidity']}%")
        
        if "weather_type" in weather_data:
            context.append(f"Weather type: {weather_data['weather_type']}")
        
        if "wind_speed" in weather_data:
            context.append(f"Wind speed: {weather_data['wind_speed']} km/h")
        
        if "air_quality" in weather_data:
            context.append(f"Air quality: {weather_data['air_quality']}")
        
        return "\n".join(context)


# Singleton instance
_chatbot_instance = None


def get_chatbot(api_key=None):
    """Get or create the chatbot instance"""
    global _chatbot_instance
    
    if _chatbot_instance is None:
        _chatbot_instance = WeatherChatbot(api_key)
    
    return _chatbot_instance
