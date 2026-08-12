import sys
import httpx


def discover(peer_base_url: str) -> dict:
    """
    Discover another agent using its A2A Agent Card.
    """

    base_url = peer_base_url.rstrip("/")

    card_url = (
        f"{base_url}/.well-known/agent-card.json"
    )

    response = httpx.get(
        card_url,
        timeout=10.0,
    )

    response.raise_for_status()

    card = response.json()

    print(
        f"Agent name: {card.get('name', 'Unknown')}"
    )

    skills = card.get(
        "skills",
        [],
    )

    if skills:
        print("Skills:")

        for skill in skills:
            if isinstance(skill, dict):
                print(
                    f"- {skill.get('name', 'Unnamed skill')}"
                )
            else:
                print(
                    f"- {skill}"
                )

    else:
        print("Skills: none listed")

    return card


def extract_output_text(data: dict) -> str:
    """
    Extract output_text from an OpenResponses-shaped response.
    """

    for output_item in data.get("output", []):

        if output_item.get("type") != "message":
            continue

        for content_item in output_item.get(
            "content",
            [],
        ):

            if content_item.get("type") == "output_text":
                return content_item.get(
                    "text",
                    "",
                )

    raise ValueError(
        "No output_text found in the response."
    )


def delegate(
    card: dict,
    task: str,
) -> str:
    """
    Delegate a task using the endpoint provided by the Agent Card.
    """

    endpoint = card.get("url")

    if not endpoint:
        raise ValueError(
            "Agent Card does not contain a URL."
        )

    response = httpx.post(
        endpoint,
        json={
            "input": task,
        },
        timeout=60.0,
    )

    response.raise_for_status()

    data = response.json()

    return extract_output_text(
        data
    )


def main():

    if len(sys.argv) < 3:

        print(
            "Usage: uv run python src/a2a_client.py "
            'http://<peer> "task for their agent"'
        )

        sys.exit(1)

    peer_url = sys.argv[1]

    task = " ".join(
        sys.argv[2:]
    )

    card = discover(
        peer_url
    )

    result = delegate(
        card,
        task,
    )

    print()
    print("Delegated result:")
    print(result)


if __name__ == "__main__":
    main()