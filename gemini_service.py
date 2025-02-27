# gemini_service.py
import os
import base64
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

# Initialize Gemini API with API key from environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not set. Image analysis will not work.")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def encode_image_to_base64(image_path):
    """
    Encode an image file to base64 string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path):
    """
    Analyze the image using Gemini AI API.
    Returns a dictionary with title and description.
    
    Args:
        image_path: Path to the local image file
    
    Returns:
        dict: {'title': '...', 'description': '...'}
    """
    if not GEMINI_API_KEY:
        return {
            "title": "API Key Missing",
            "description": "The Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable."
        }
    
    try:
        # Get a Gemini model that can process both text and images
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Read the image file as binary
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Create the prompt for title generation
        title_prompt = "Please generate a concise, descriptive title for this image. Keep it under 10 words."
        
        # Generate title using the model's generate_content method with the image
        title_response = model.generate_content([
            title_prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        # Create the prompt for description generation
        description_prompt = "Please provide a detailed description of what's in this image. Include key details about the subjects, setting, colors, and mood. Keep it under 200 words."
        
        # Generate description
        description_response = model.generate_content([
            description_prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        # Extract the text from the responses
        title = title_response.text.strip() if title_response.text else "Untitled Image"
        description = description_response.text.strip() if description_response.text else "No description available."
        
        return {
            "title": title,
            "description": description
        }
    
    except GoogleAPIError as e:
        print(f"Google API Error: {e}")
        return {
            "title": "Analysis Error",
            "description": f"An error occurred while analyzing the image: {str(e)}"
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "title": "Processing Error",
            "description": f"An unexpected error occurred while processing the image: {str(e)}"
        }