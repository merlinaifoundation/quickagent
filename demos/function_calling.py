import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def should_respond(prompt):
    """
    Function to determine if the prompt requires a response.
    """
    print("LLM Response")

def process_prompt(prompt):
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that determines if a prompt requires a response. If it does, call the should_respond function."},
                {"role": "user", "content": prompt}
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "should_respond",
                    "description": "Call this function if the prompt requires a response",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }],
            tool_choice="auto"
        )
        
        if response.choices[0].message.tool_calls:
            should_respond(prompt)
        else:
            print("No response needed.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    end_time = time.time()
    elapsed_time = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"Processing time: {elapsed_time:.2f} ms")

def main():
    print("Welcome to the Interactive ChatGPT Response Script!")
    print("Enter your prompts one at a time. Type 'exit' to quit.")
    
    while True:
        prompt = input("\nEnter your prompt: ").strip()
        
        if prompt.lower() == 'exit':
            print("Thank you for using the Interactive ChatGPT Response Script. Goodbye!")
            break
        
        if prompt:
            print(f"\nProcessing prompt: '{prompt}'")
            process_prompt(prompt)
        else:
            print("Empty prompt. Please try again.")

if __name__ == "__main__":
    main()