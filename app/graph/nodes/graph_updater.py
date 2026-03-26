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
    )

    return {
        **state,
        "graph_updated": True,
    }