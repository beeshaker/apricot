from groq import Groq

def generate_daily_trivia():
    prompt = (
        "Generate a fun and interesting trivia question related to real estate or property management in Kenya. The question should be about the property management service in Kenya."
        "Provide both the trivia question, the hint, and the correct answer in the following format: "
        "Question: [Trivia Question] "
        "Hint: [Hint Text] "
        "Answer: [Trivia Answer] "
    )
    try:
        # Import ChatGroq and initialize the client (ensure you have installed the ChatGroq library)
        

        client = Groq()

        # Use the Qwen2.5 model
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Updated model name
            messages=[
                {"role": "system", "content": "You are an assistant that generates trivia questions about real estate and property management services in Kenya."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150,
        )

        # Extract the content correctly
        trivia_text = response.choices[0].message.content.strip()

        # Initialize default values
        question = "Trivia question not available."
        hint = "Hint not available."
        answer = "Answer not available."

        # Parse the response into question, hint, and answer
        if "Hint:" in trivia_text and "Answer:" in trivia_text:
            parts = trivia_text.split("Hint:")
            question = parts[0].replace("Question:", "").strip()
            hint_answer = parts[1].split("Answer:")
            hint = hint_answer[0].strip()
            answer = hint_answer[1].strip()

        return question, hint, answer
       

    except Exception as e:
        return "Trivia question not available.", "Hint not available.", f"Error: {str(e)}"