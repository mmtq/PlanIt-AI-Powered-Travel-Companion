"""
LLM interface functionality for DocuBuddy.
Handles language model operations and conversation management.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_ollama import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TravelAgent:
    def __init__(self):
        self.llm = Ollama(model="llama2")
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are PlanIT, an expert AI travel companion. "
                "Help users plan their trips by providing detailed, "
                "personalized travel recommendations and itineraries. "
                "Focus on understanding the user's travel preferences, "
                "budget constraints, and specific interests."
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def chat(self, user_input: str) -> str:
        chat_history = self.memory.load_memory_variables({})["chat_history"]
        response = self.chain.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        self.memory.save_context(
            {"input": user_input},
            {"output": response}
        )
        return response

    def clear_history(self):
        self.memory.clear()

# Example usage:
if __name__ == "__main__":
    agent = TravelAgent()
    
    # Example conversation
    print("Agent: Hello! I'm PlanIT, your AI travel companion. How can I help plan your next adventure?")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Agent: Goodbye! Have a great trip!")
            break
            
        response = agent.chat(user_input)
        print(f"Agent: {response}")
