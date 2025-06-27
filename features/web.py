# features/web.py
import webbrowser
import urllib.parse

def play_on_youtube(search_query):
    """
    Opens a YouTube search results page for the given query.
    This method is very fast as it does not scrape any data.
    """
    if not search_query:
        return "You need to tell me what to play."

    try:
        # Format the search query for a URL
        formatted_query = urllib.parse.quote_plus(search_query)
        search_url = f"https://www.youtube.com/results?search_query={formatted_query}"
        
        # Open the search results in the default web browser
        webbrowser.open(search_url)
        
        return f"Showing results for '{search_query}' on YouTube."
    except Exception as e:
        print(f"An error occurred in play_on_youtube: {e}")
        return "Sorry, an unexpected error occurred."