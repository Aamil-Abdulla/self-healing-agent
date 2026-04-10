import code

from langgraph.graph import StateGraph , END
from typing import TypedDict
import os
from dotenv import load_dotenv
load_dotenv()
from groq import Groq
from  e2b_code_interpreter import Sandbox 
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class AgentState(TypedDict):
    original_code : str
    task_description : str
    current_code : str
    attempts : list[dict]
    attempts_count : int
    success : bool
    explanation : str
    analysis : str

def analyzer_node(state: AgentState):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"You are a code analyzer assistance that assists the code from the task description which user has given  : {state['task_description']} and the original code which the user has sent : {state['original_code']} .You need to first learn the task description then analyze the code and find the issue in it and give a detailed explanation about it"
            },
            {
                "role": "user",
                "content": f"Task Description : {state['task_description']} and the original code : {state['original_code']} ."
            }
        ]
    )

    
    
    return {"analysis": completion.choices[0].message.content}






def fix_node(state: AgentState):
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"You are a pro code fixer assistance that fixes that broken code using the task description which user has given .Return ONLY raw Python code. No backticks, no ```python, no markdown, no explanations. Just the code itself starting from the first import or def statement."
                },
            {
                "role": "user",
                "content": f"Task Description : {state['task_description']} and the original code : {state['original_code']} and the analysis : {state['analysis']} ."
            }
        ]
    )
    print("Fixing the code")
    
    return {
        "current_code": completion.choices[0].message.content,
        "attempts_count": state["attempts_count"] + 1
    }

def execute_node(state: AgentState):
    print("Executing the code")
    code = state["current_code"]
    if code.startswith("```"):
        code = code.split("\n", 1)[1]
    if code.endswith("```"):
        code = code.rsplit("\n", 1)[0]
    
    with Sandbox.create() as sandbox:
        execution = sandbox.run_code(code)
        if execution.error:
            return {
                "success": False,
                "explanation": f"Error: {execution.error}",
                "attempts": state["attempts"] + [{"code": code, "error": str(execution.error)}]
            }
        else:
            return {
                "success": True,
                "explanation": f"Output: {execution.logs.stdout}",
                "attempts": state["attempts"] + [{"code": code, "output": execution.logs.stdout}]
            }
def explain_node(state: AgentState):
    print("Explaining the results")
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"You are a pro code explainer assistance that explains the execution results of the code using the task description which user has given . Return ONLY the explanation. Do not include markdown code blocks, backticks, or any conversational text."
                },
                {
                "role": "user",
                "content": f" the original code : {state['original_code']} , the fixed code : {state['current_code']} and the analysis : {state['analysis']} and the attempts : {state['attempts']} ."
                }
        ]
        )
    return {"explanation": completion.choices[0].message.content}

def route_after_execute(state: AgentState):
    if state["success"]:
        return "explain"
    elif state["attempts_count"] < 5:
        return "fix"
    else:
        return END

graph = StateGraph(AgentState)
graph.add_node("analyzer" , analyzer_node)
graph.add_node("fix" , fix_node)
graph.add_node("execute" , execute_node)
graph.add_node("explain" , explain_node)    

graph.set_entry_point("analyzer")
graph.add_edge("analyzer", "fix")
graph.add_edge("fix", "execute")
graph.add_conditional_edges("execute", route_after_execute)
graph.add_edge("explain", END)

app = graph.compile()   