
import requests


def get_weather_data(city_name):
    """
    Calls the OpenWeatherMap API to get weather data for a specific city.
    This version has improved error handling.
    """
    if not city_name:
        return "You need to tell me a city name."
    
    API_KEY = "02ad06a3f97312999d200506c88ba8b5"  # Make sure your key is pasted here
    BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
    
    params = {'q': city_name, 'appid': API_KEY, 'units': 'metric'}
    
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        # --- DETAILED ERROR CHECKING ---
        # Check for 401 Unauthorized - a common API key issue
        if data.get("cod") == 401:
            print("ERROR: The API key is invalid or not activated yet.")
            return "Sorry, there seems to be a problem with my connection to the weather service. Please check the API key."
            
        # Check for 404 Not Found - city doesn't exist in their database
        if data.get("cod") == "404":
            print(f"ERROR: City '{city_name}' not found by the API.")
            return f"Sorry, I couldn't find the weather for {city_name}. Please double-check the city name."

        # Raise an exception for other bad status codes (like 5xx server errors)
        response.raise_for_status()

        # --- DATA EXTRACTION (if successful) ---
        main_weather = data["weather"][0]["main"]
        description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        
        response_string = (f"The weather in {city_name.capitalize()} is currently {temperature:.0f} degrees Celsius "
                           f"with {description}.")
        
        return response_string

    except requests.exceptions.RequestException as e:
        print(f"NETWORK ERROR: {e}")
        return "Sorry, I'm having trouble connecting to the weather service right now."


