import os
import asyncio
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

async def check_groq():
    api_key = os.getenv("GROQ_API_KEY")
    print(f"Checking Groq API KEY: {api_key[:5] if api_key else 'None'}...")
    if not api_key:
        print("GROQ_API_KEY is not set!")
        return

    client = Groq(api_key=api_key)
    try:
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say hello world"}]
        )
        print(f"Response: {completion.choices[0].message.content}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_groq())
