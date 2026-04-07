from langgraph.graph import StateGraph , END
from typing import TypedDict
import os

class AgentState(TypedDict):
    original_code : str
    task_description : str
    current_code : str
    attempts : list[dict]
    attempts_count : int
    success : bool
    explanation : str

def analyzer_node(state: AgentState):
    print("Analyzing the code")
    return {"current_code": state["original_code"]}
def fix_node(state: AgentState):
    print("Fixing the code")
    pass
def execute_node(state: AgentState):
    print("Executing the code")
    return {"current_code": state["current_code"]}  

def explain_node(state: AgentState):
    print("Explaining the results")
    return {"explanation": state["explanation"]}

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
graph.add_conditional_edge("execute", route_after_execute)
graph.add_edge("explain", END)
