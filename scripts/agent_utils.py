"""
Agent utilities - LLM, MCP client, and agent setup
Both main.py and mcp_client.ipynb can import from here
"""

import os
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, ToolCall
from llama_index.core.workflow import Context


# -------------------- Configuration --------------------
SYSTEM_PROMPT = """\
You are an AI assistant for Tool Calling.

Before you help a user, you need to work with tools to interact with Our Database
"""

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/sse")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")


# -------------------- LLM Setup --------------------
def get_llm():
    """Get configured LLM instance"""
    llm = Ollama(model=LLM_MODEL, base_url=OLLAMA_HOST, request_timeout=120)
    Settings.llm = llm
    return llm


# -------------------- MCP Setup --------------------
def get_mcp_tools():
    """Get MCP client and tools spec"""
    mcp_client = BasicMCPClient(MCP_SERVER_URL)
    mcp_tools = McpToolSpec(client=mcp_client)
    return mcp_tools


# -------------------- Agent Setup --------------------
async def get_agent(mcp_tools: McpToolSpec = None, llm: Ollama = None):
    """
    Creates a FunctionAgent wired up with the MCP tool list and LLM.
    
    Args:
        mcp_tools: Optional McpToolSpec instance, creates new one if not provided
        llm: Optional LLM instance, creates new one if not provided
    
    Returns:
        FunctionAgent instance
    """
    if llm is None:
        llm = get_llm()
    
    if mcp_tools is None:
        mcp_tools = get_mcp_tools()
    
    tools = await mcp_tools.to_tool_list_async()
    
    agent = FunctionAgent(
        name='MyAgent',
        description='An agent that can work with our database',
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        tools=tools
    )
    
    return agent, tools


# -------------------- Message Handler --------------------
async def handle_user_message(
    message_content: str,
    agent: FunctionAgent,
    agent_context: Context,
    verbose: bool = False,
) -> tuple[str, list[dict]]:
    """
    Process user message and return response with tool calls.
    
    Args:
        message_content: The user's message
        agent: FunctionAgent instance
        agent_context: Context instance for the agent
        verbose: If True, logs and returns tool call details
    
    Returns:
        Tuple of (response_string, tool_calls_list)
    """
    tool_calls_log = []
    
    handler = agent.run(message_content, ctx=agent_context)
    
    async for event in handler.stream_events():
        if verbose and isinstance(event, ToolCall):
            tool_call_info = {
                "type": "call",
                "tool_name": event.tool_name,
                "tool_kwargs": event.tool_kwargs
            }
            tool_calls_log.append(tool_call_info)
            print(f"🔧 Calling tool {event.tool_name} with kwargs {event.tool_kwargs}")
            
        elif verbose and isinstance(event, ToolCallResult):
            tool_result_info = {
                "type": "result",
                "tool_name": event.tool_name,
                "tool_output": str(event.tool_output)
            }
            tool_calls_log.append(tool_result_info)
            print(f"📤 Tool {event.tool_name} returned {event.tool_output}")
    
    response = await handler
    return str(response), tool_calls_log
