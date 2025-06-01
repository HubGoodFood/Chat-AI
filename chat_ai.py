def chat():
    print("Hello! I am a simple chat AI. How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        # In a real AI, you would process user_input and generate a response here.
        print("AI: I received your message: " + user_input)

if __name__ == "__main__":
    chat()
