from langgraph.graph import START, END, StateGraph

from app.graph.state import (
    CrisisGraphState,
    DebriefGraphState,
    PredictionGraphState,
    ReportGraphState,
)

from app.graph.nodes.context_fetch import context_fetch
from app.graph.nodes.router import router
from app.graph.nodes.intervention_planner import intervention_planner
from app.graph.nodes.memory_retrieval import memory_retrieval
from app.graph.nodes.evidence_search import evidence_search
from app.graph.nodes.response_generator import response_generator
from app.graph.nodes.safety_guard import safety_guard

from app.graph.nodes.transcribe_audio import transcribe_audio
from app.graph.nodes.abc_extractor import abc_extractor
from app.graph.nodes.memory_normalizer import memory_normalizer
from app.graph.nodes.sql_persist import sql_persist
from app.graph.nodes.graph_updater import graph_updater

from app.graph.nodes.risk_model import risk_model
from app.graph.nodes.prevention_planner import prevention_planner

from app.graph.nodes.report_generator import report_generator


def build_crisis_graph():
    graph = StateGraph(CrisisGraphState)

    graph.add_node("context_fetch", context_fetch)
    graph.add_node("router", router)
    graph.add_node("intervention_planner", intervention_planner)
    graph.add_node("memory_retrieval", memory_retrieval)
    graph.add_node("evidence_search", evidence_search)
    graph.add_node("response_generator", response_generator)
    graph.add_node("safety_guard", safety_guard)

    graph.add_edge(START, "context_fetch")
    graph.add_edge("context_fetch", "router")
    graph.add_edge("router", "intervention_planner")
    graph.add_edge("intervention_planner", "memory_retrieval")
    graph.add_edge("memory_retrieval", "evidence_search")
    graph.add_edge("evidence_search", "response_generator")
    graph.add_edge("response_generator", "safety_guard")
    graph.add_edge("safety_guard", END)

    return graph.compile()


def build_debrief_graph():
    graph = StateGraph(DebriefGraphState)

    graph.add_node("transcribe_audio", transcribe_audio)
    graph.add_node("abc_extractor", abc_extractor)
    graph.add_node("memory_normalizer", memory_normalizer)
    graph.add_node("sql_persist", sql_persist)
    graph.add_node("graph_updater", graph_updater)

    graph.add_edge(START, "transcribe_audio")
    graph.add_edge("transcribe_audio", "abc_extractor")
    graph.add_edge("abc_extractor", "memory_normalizer")
    graph.add_edge("memory_normalizer", "sql_persist")
    graph.add_edge("sql_persist", "graph_updater")
    graph.add_edge("graph_updater", END)

    return graph.compile()


def build_prediction_graph():
    graph = StateGraph(PredictionGraphState)

    graph.add_node("risk_model", risk_model)
    graph.add_node("prevention_planner", prevention_planner)

    graph.add_edge(START, "risk_model")
    graph.add_edge("risk_model", "prevention_planner")
    graph.add_edge("prevention_planner", END)

    return graph.compile()


def build_report_graph():
    graph = StateGraph(ReportGraphState)

    graph.add_node("report_generator", report_generator)

    graph.add_edge(START, "report_generator")
    graph.add_edge("report_generator", END)

    return graph.compile()