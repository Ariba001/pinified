from langgraph.graph import StateGraph

from agents import (
    understanding_agent,
    reconciliation_agent,
    qualification_agent,
    response_agent,
    sync_agent
)

def build_graph():

    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("understanding", understanding_agent)
    workflow.add_node("reconciliation", reconciliation_agent)
    workflow.add_node("qualification", qualification_agent)
    workflow.add_node("response", response_agent)
    workflow.add_node("sync", sync_agent)

    # Flow
    workflow.set_entry_point("understanding")

    workflow.add_edge("understanding", "reconciliation")
    workflow.add_edge("reconciliation", "qualification")
    workflow.add_edge("qualification", "response")
    workflow.add_edge("response", "sync")

    return workflow.compile()