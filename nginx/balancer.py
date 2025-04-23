import requests
from collections import Counter


def test_load_balancing(url: str, n: int) -> dict[str, int]:
    results = Counter()

    for _ in range(n):
        try:
            response = requests.get(url, timeout=2)
            data = response.json()
            instance = data.get("instance", "unknown")
            results[instance] += 1
        except Exception:
            results["error"] += 1

    return results


if __name__ == "__main__":
    url = "http://localhost/api/auth/health"
    n = 1000
    stats = test_load_balancing(url, n)

    for instance, count in stats.items():
        print(f"{instance}: {count}")
