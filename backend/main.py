from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, TypedDict, Sequence
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain_groq import ChatGroq
import os
from backend.config import GROQ_API_KEY, TAVILY_API_KEY

app = FastAPI(title="LangGraph Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
MODEL_NAMES = [
    "llama3-70b-8192",
    "mixtral-8x7b-32768"
]

class ChatRequest(BaseModel):
    messages: List[str]
    model_name: str
    system_prompt: str

# Define state schema
class AgentState(TypedDict):
    messages: Sequence[BaseMessage]

def initialize_agent(model_name: str, system_prompt: str):
    """Initialize the LangGraph agent"""
    # Set up LLM
    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name=model_name,
        temperature=0.7,
        max_tokens=1000
    )
    
    # Set up tools
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
    tools = [TavilySearchResults(max_results=3)]
    tool_executor = ToolExecutor(tools)
    
    # Create workflow with state schema
    workflow = StateGraph(AgentState)
    
    # Define agent state
    def agent_step(state: AgentState) -> AgentState:
        messages = list(state["messages"])
        # Add system prompt to the first message
        if messages and isinstance(messages[0], HumanMessage):
            messages[0] = HumanMessage(content=f"{system_prompt}\n\n{messages[0].content}")
        
        response = llm.invoke(messages)
        return {"messages": messages + [response]}
    
    # Add node to the graph
    workflow.add_node("agent", agent_step)
    
    # Define entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edge to END
    workflow.add_edge("agent", END)
    
    # Compile workflow
    chain = workflow.compile()
    
    return chain

@app.get("/")
async def root():
    return {"status": "online", "message": "LangGraph Agent API is running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    """Process chat messages"""
    try:
        if request.model_name not in MODEL_NAMES:
            return {"error": "Invalid model name"}
            
        # Initialize agent
        agent = initialize_agent(request.model_name, request.system_prompt)
        
        # Process messages
        messages = [HumanMessage(content=msg) for msg in request.messages]
        state = {"messages": messages}
        result = agent.invoke(state)
        
        # Extract the last message from the result
        last_message = result["messages"][-1]
        response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
        return {
            "messages": [
                {"type": "ai", "content": response}
            ]
        }
        
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}"}