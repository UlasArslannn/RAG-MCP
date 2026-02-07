from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever


model = OllamaLLM(model="llama3.2")


tamplate = """
You are an Pyschologist and you are helping to analyze and summarize people's reviews about a restaurant.

Here some relevent reviews: {reviews}

Here is the question to answer: {question}

"""

prompt = ChatPromptTemplate.from_template(tamplate)
chain = prompt | model

while True:
    question = input("Ask your question: ")
    if question == "q":
        break


    reviews = retriever.invoke(question)
    
    result  = chain.invoke({
        "reviews": reviews,
        "question": question
    })
    print(result)

