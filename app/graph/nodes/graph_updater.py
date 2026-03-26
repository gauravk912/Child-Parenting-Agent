from app.services.graph_memory_service import create_incident_memory_node


def graph_updater(state):
    create_incident_memory_node(
        child_id=state["child_id"],
        incident_id=state["incident_id"],
        antecedent=state.get("antecedent"),
        behavior=state.get("behavior"),
        consequence=state.get("consequence"),
        interventions_tried=state.get("interventions_tried", []),
        location=state.get("location"),
        trigger_labels=state.get("trigger_labels", []),
        context_labels=state.get("context_labels", []),
        behavior_labels=state.get("behavior_labels", []),
        intervention_labels=state.get("intervention_labels", []),
    )

    return {
        **state,
        "graph_updated": True,
    }