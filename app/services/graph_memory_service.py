from uuid import UUID
from typing import List,Dict, Optional
from app.db.neo4j import get_neo4j_driver


def create_child_profile_node(
    child_id: UUID,
    child_name: str,
    parent_id: UUID,
) -> None:
    driver = get_neo4j_driver()

    query = """
    MERGE (c:Child {id: $child_id})
    SET c.name = $child_name,
        c.parent_id = $parent_id

    MERGE (p:Parent {id: $parent_id})
    MERGE (p)-[:CARES_FOR]->(c)
    """

    with driver.session() as session:
        session.run(
            query,
            child_id=str(child_id),
            child_name=child_name,
            parent_id=str(parent_id),
        )

    driver.close()


def update_child_profile_node(
    child_id: UUID,
    child_name: str,
) -> None:
    driver = get_neo4j_driver()

    query = """
    MATCH (c:Child {id: $child_id})
    SET c.name = $child_name
    """

    with driver.session() as session:
        session.run(
            query,
            child_id=str(child_id),
            child_name=child_name,
        )

    driver.close()
    
def delete_child_profile_node(
    child_id: UUID,
) -> None:
    driver = get_neo4j_driver()

    query = """
    MATCH (c:Child {id: $child_id})
    DETACH DELETE c
    """

    with driver.session() as session:
        session.run(
            query,
            child_id=str(child_id),
        )

    driver.close()

def create_incident_memory_node(
    child_id: UUID,
    incident_id: UUID,
    antecedent: Optional[str],
    behavior: Optional[str],
    consequence: Optional[str],
    interventions_tried: List[str],
    location: Optional[str],
) -> None:
    driver = get_neo4j_driver()

    query = """
    MERGE (c:Child {id: $child_id})
    MERGE (i:Incident {id: $incident_id})
    SET i.antecedent = $antecedent,
        i.behavior = $behavior,
        i.consequence = $consequence,
        i.location = $location

    MERGE (c)-[:HAD_INCIDENT]->(i)

    FOREACH (item IN $interventions_tried |
        MERGE (iv:Intervention {name: item})
        MERGE (i)-[:USED_INTERVENTION]->(iv)
    )
    """

    with driver.session() as session:
        session.run(
            query,
            child_id=str(child_id),
            incident_id=str(incident_id),
            antecedent=antecedent,
            behavior=behavior,
            consequence=consequence,
            location=location,
            interventions_tried=interventions_tried,
        )

    driver.close()
    

def get_similar_incidents_for_child(
    child_id: UUID,
    limit: int = 5,
) -> List[Dict]:
    driver = get_neo4j_driver()

    query = """
    MATCH (c:Child {id: $child_id})-[:HAD_INCIDENT]->(i:Incident)
    OPTIONAL MATCH (i)-[:USED_INTERVENTION]->(iv:Intervention)
    RETURN
        i.id AS incident_id,
        i.antecedent AS antecedent,
        i.behavior AS behavior,
        i.consequence AS consequence,
        i.location AS location,
        collect(DISTINCT iv.name) AS interventions
    ORDER BY incident_id DESC
    LIMIT $limit
    """

    records_out = []
    with driver.session() as session:
        result = session.run(query, child_id=str(child_id), limit=limit)
        for record in result:
            records_out.append(
                {
                    "incident_id": record.get("incident_id"),
                    "antecedent": record.get("antecedent"),
                    "behavior": record.get("behavior"),
                    "consequence": record.get("consequence"),
                    "location": record.get("location"),
                    "interventions": [x for x in (record.get("interventions") or []) if x],
                }
            )

    driver.close()
    return records_out


def get_prior_helpful_interventions_for_child(
    child_id: UUID,
    limit: int = 5,
) -> List[str]:
    driver = get_neo4j_driver()

    query = """
    MATCH (c:Child {id: $child_id})-[:HAD_INCIDENT]->(:Incident)-[:USED_INTERVENTION]->(iv:Intervention)
    RETURN iv.name AS intervention_name, count(*) AS use_count
    ORDER BY use_count DESC
    LIMIT $limit
    """

    interventions = []
    with driver.session() as session:
        result = session.run(query, child_id=str(child_id), limit=limit)
        for record in result:
            name = record.get("intervention_name")
            if name:
                interventions.append(name)

    driver.close()
    return interventions


def build_memory_summary(
    similar_incidents: List[Dict],
    prior_helpful_interventions: List[str],
) -> str:
    if not similar_incidents and not prior_helpful_interventions:
        return "No prior incident memory available."

    summary_parts = []

    if similar_incidents:
        first = similar_incidents[0]
        summary_parts.append(
            "Recent similar incident memory: "
            f"antecedent={first.get('antecedent')}; "
            f"behavior={first.get('behavior')}; "
            f"consequence={first.get('consequence')}."
        )

    if prior_helpful_interventions:
        summary_parts.append(
            "Previously used interventions: " + ", ".join(prior_helpful_interventions) + "."
        )

    return " ".join(summary_parts)