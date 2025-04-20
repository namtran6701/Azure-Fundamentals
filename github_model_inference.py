import os
from openai import OpenAI

# OpenAI SDK
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
    temperature=1.0,
    model=model
)

print(response.choices[0].message.content)


# Lang Graph 
import langchain_openai
import langgraph.graph
from langgraph.graph import MessagesState
from langgraph.graph import START, END

model = langchain_openai.ChatOpenAI(
  model="gpt-4o",
  api_key=os.environ["GITHUB_TOKEN"],
  base_url="https://models.inference.ai.azure.com", 
)

def call_model(state):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": response}

workflow = langgraph.graph.StateGraph(MessagesState)
workflow.add_node("agent", call_model)

workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)

graph = workflow.compile()

answer = graph.invoke({"messages": "Hello, how are you?"})

print(answer["messages"][-1].content)


