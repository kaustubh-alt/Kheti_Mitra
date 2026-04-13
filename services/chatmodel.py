from google import genai
import asyncio

# The new version uses the 'Client' class for all interactions
client = genai.Client(api_key="")

async def get_gemini_response(prompt):
    # The new method is 'models.generate_content_stream'
    # We use 'await' for the initial call, which returns an async iterator
    response = await client.models.generate_content_stream(
        model='gemini-2.5-flash', # Updated to latest version 2.0
        contents=prompt
    )
    
    # Iterate through the async response chunks
    async for chunk in response:
        # The text is accessed directly via the .text attribute
        if chunk.text:
            yield chunk.text