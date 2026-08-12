import sys
import requests


def discover(peer_base_url: str) -> dict:
    """
    Discover another agent using its A2A Agent Card.
    """

    base_url = peer_base_url.rstrip("/")

    card_url = (
        f"{base_url}/.well-known/agent-card.json"
    )

    response = requests.get(
        card_url,
        timeout=10,
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
                    f"- {skill.get('name', skill)}"
                )

            else:
                print(
                    f"- {skill}"
                )

    else:
        print("Skills: none listed")

    return card


def delegate(
    card: dict,
    task: str,
) -> str:
    """
    Send a task to the discovered agent.
    """

    endpoint = card.get("url")

    if not endpoint:
        raise ValueError(
            "Agent card does not contain a URL."
        )

    response = requests.post(
        endpoint,
        json={
            "input": task
        },
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    try:
        text = (
            data["output"][0]
            ["content"][0]
            ["text"]
        )

    except (
        KeyError,
        IndexError,
        TypeError,
    ) as error:

        raise ValueError(
            "Invalid OpenResponses reply."
        ) from error

    return text


def main():

    if len(sys.argv) < 3:

        print(
            "Usage:"
        )

        print(
            "uv run python src/a2a_client.py "
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