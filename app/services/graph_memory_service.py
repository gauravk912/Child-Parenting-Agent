from collections import Counter, defaultdict
from typing import List, Dict, Optional
from uuid import UUID

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
    trigger_labels: List[str],
    context_labels: List[str],
    behavior_labels: List[str],
    intervention_labels: List[str],
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

    FOREACH (item IN $trigger_labels |
        MERGE (t:TriggerTag {name: item})
        MERGE (i)-[:HAS_TRIGGER_TAG]->(t)
    )

    FOREACH (item IN $context_labels |
        MERGE (ct:ContextTag {name: item})
        MERGE (i)-[:HAS_CONTEXT_TAG]->(ct)
    )

    FOREACH (item IN $behavior_labels |
        MERGE (bt:BehaviorTag {name: item})
        MERGE (i)-[:HAS_BEHAVIOR_TAG]->(bt)
    )

    FOREACH (item IN $intervention_labels |
        MERGE (it:InterventionTag {name: item})
        MERGE (i)-[:HAS_INTERVENTION_TAG]->(it)
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
            interventions_tried=interventions_tried,
            location=location,
            trigger_labels=trigger_labels,
            context_labels=context_labels,
            behavior_labels=behavior_labels,
            intervention_labels=intervention_labels,
        )

    driver.close()


def get_similar_incidents_for_child(
    child_id: UUID,
    limit: int = 8,
) -> List[Dict]:
    driver = get_neo4j_driver()

    query = """
    MATCH (c:Child {id: $child_id})-[:HAD_INCIDENT]->(i:Incident)
    OPTIONAL MATCH (i)-[:USED_INTERVENTION]->(iv:Intervention)
    OPTIONAL MATCH (i)-[:HAS_CONTEXT_TAG]->(ct:ContextTag)
    OPTIONAL MATCH (i)-[:HAS_TRIGGER_TAG]->(tt:TriggerTag)
    RETURN
        i.id AS incident_id,
        i.antecedent AS antecedent,
        i.behavior AS behavior,
        i.consequence AS consequence,
        i.location AS location,
        collect(DISTINCT iv.name) AS interventions,
        collect(DISTINCT ct.name) AS context_tags,
        collect(DISTINCT tt.name) AS trigger_tags
    LIMIT $limit
    """

    rows = []
    with driver.session() as session:
        result = session.run(query, child_id=str(child_id), limit=limit)
        for record in result:
            rows.append(
                {
                    "incident_id": record.get("incident_id"),
                    "antecedent": record.get("antecedent"),
                    "behavior": record.get("behavior"),
                    "consequence": record.get("consequence"),
                    "location": record.get("location"),
                    "interventions": [x for x in (record.get("interventions") or []) if x],
                    "context_tags": [x for x in (record.get("context_tags") or []) if x],
                    "trigger_tags": [x for x in (record.get("trigger_tags") or []) if x],
                }
            )

    driver.close()
    return rows


def get_prior_helpful_interventions_for_child(
    child_id: UUID,
    limit: int = 8,
) -> List[str]:
    driver = get_neo4j_driver()

    query = """
    MATCH (c:Child {id: $child_id})-[:HAD_INCIDENT]->(:Incident)-[:USED_INTERVENTION]->(iv:Intervention)
    RETURN iv.name AS intervention_name, count(*) AS use_count
    ORDER BY use_count DESC, intervention_name ASC
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


def _infer_current_context_labels(parent_message: str) -> List[str]:
    msg = (parent_message or "").lower()
    labels = []

    if "after school" in msg:
        labels.append("after school transition")
    if "crowded" in msg:
        labels.append("crowded environment")
    if "store" in msg or "grocery" in msg or "shopping" in msg:
        labels.append("store outing")
    if "loud" in msg or "noise" in msg or "noisy" in msg:
        labels.append("loud environment")
    if "transition" in msg:
        labels.append("transition demand")
    if "throw" in msg:
        labels.append("throwing objects")
    if "scream" in msg or "yell" in msg:
        labels.append("screaming")

    return labels


def get_ranked_interventions_for_child(
    child_id: UUID,
    parent_message: Optional[str] = None,
    limit: int = 5,
) -> List[Dict]:
    driver = get_neo4j_driver()

    query = """
    MATCH (c:Child {id: $child_id})-[:HAD_INCIDENT]->(i:Incident)
    OPTIONAL MATCH (i)-[:USED_INTERVENTION]->(iv:Intervention)
    OPTIONAL MATCH (i)-[:HAS_CONTEXT_TAG]->(ct:ContextTag)
    OPTIONAL MATCH (i)-[:HAS_TRIGGER_TAG]->(tt:TriggerTag)
    OPTIONAL MATCH (i)-[:HAS_BEHAVIOR_TAG]->(bt:BehaviorTag)
    RETURN
        i.id AS incident_id,
        i.location AS location,
        i.antecedent AS antecedent,
        collect(DISTINCT iv.name) AS interventions,
        collect(DISTINCT ct.name) AS context_tags,
        collect(DISTINCT tt.name) AS trigger_tags,
        collect(DISTINCT bt.name) AS behavior_tags
    """

    current_labels = set(_infer_current_context_labels(parent_message or ""))
    intervention_scores = defaultdict(float)
    intervention_counts = defaultdict(int)

    with driver.session() as session:
        result = session.run(query, child_id=str(child_id))

        for record in result:
            interventions = [x for x in (record.get("interventions") or []) if x]
            location = (record.get("location") or "").lower()
            antecedent = (record.get("antecedent") or "").lower()

            incident_labels = set([x for x in (record.get("context_tags") or []) if x])
            incident_labels.update([x for x in (record.get("trigger_tags") or []) if x])
            incident_labels.update([x for x in (record.get("behavior_tags") or []) if x])

            match_count = len(current_labels.intersection(incident_labels))

            location_match = 0
            if "store" in (parent_message or "").lower() and "store" in location:
                location_match = 1
            if "grocery" in (parent_message or "").lower() and "grocery" in location:
                location_match = 1

            antecedent_match = 0
            if "after school" in (parent_message or "").lower() and "after school" in antecedent:
                antecedent_match = 1

            base_score = 1.0 + (2.5 * match_count) + (1.5 * location_match) + (1.5 * antecedent_match)

            for intervention in interventions:
                intervention_scores[intervention] += base_score
                intervention_counts[intervention] += 1

    driver.close()

    ranked = []
    for intervention, score in intervention_scores.items():
        ranked.append(
            {
                "intervention": intervention,
                "use_count": intervention_counts[intervention],
                "contextual_score": round(score, 2),
            }
        )

    ranked.sort(key=lambda x: (x["contextual_score"], x["use_count"], x["intervention"]), reverse=True)

    final = []
    for idx, item in enumerate(ranked[:limit], start=1):
        final.append(
            {
                "rank": idx,
                "intervention": item["intervention"],
                "use_count": item["use_count"],
                "contextual_score": item["contextual_score"],
            }
        )

    return final


def get_recurring_contexts_for_child(
    child_id: UUID,
    limit: int = 5,
) -> List[str]:
    driver = get_neo4j_driver()
    counter = Counter()

    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Child {id: $child_id})-[:HAD_INCIDENT]->(i:Incident)
            OPTIONAL MATCH (i)-[:HAS_CONTEXT_TAG]->(ct:ContextTag)
            OPTIONAL MATCH (i)-[:HAS_TRIGGER_TAG]->(tt:TriggerTag)
            RETURN i.location AS location, i.antecedent AS antecedent,
                   collect(DISTINCT ct.name) AS context_tags,
                   collect(DISTINCT tt.name) AS trigger_tags
            """,
            child_id=str(child_id),
        )

        for record in result:
            for item in record.get("context_tags") or []:
                if item:
                    counter[item] += 1
            for item in record.get("trigger_tags") or []:
                if item:
                    counter[item] += 1

            location = (record.get("location") or "").strip()
            antecedent = (record.get("antecedent") or "").strip()

            if location:
                counter[f"Location: {location}"] += 1

            lowered = antecedent.lower()
            if "after school" in lowered:
                counter["After school transition"] += 1
            if "crowded" in lowered:
                counter["Crowded environment"] += 1
            if "store" in lowered:
                counter["Store/errand outing"] += 1
            if "loud" in lowered:
                counter["Loud environment"] += 1

    driver.close()
    return [name for name, _ in counter.most_common(limit)]


def build_memory_summary(
    similar_incidents: List[Dict],
    prior_helpful_interventions: List[str],
    recurring_contexts: List[str],
) -> str:
    if not similar_incidents and not prior_helpful_interventions and not recurring_contexts:
        return "No prior incident memory available."

    parts = []

    if similar_incidents:
        first = similar_incidents[0]
        parts.append(
            "Recent similar incident memory: "
            f"antecedent={first.get('antecedent')}; "
            f"behavior={first.get('behavior')}; "
            f"consequence={first.get('consequence')}."
        )

    if recurring_contexts:
        parts.append("Recurring contexts: " + ", ".join(recurring_contexts) + ".")

    if prior_helpful_interventions:
        parts.append("Previously used interventions: " + ", ".join(prior_helpful_interventions) + ".")

    return " ".join(parts)