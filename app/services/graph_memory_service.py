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