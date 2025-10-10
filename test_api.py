#!/usr/bin/env python3
"""PPTist AI Backend API smoke tests."""

import json
import time
from typing import Any

import requests

BASE_URL = "http://localhost:8000"


def test_health() -> bool:
    """Test the health endpoint."""

    print("🔍 Checking health endpoint…")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        print(f"❌ Health check failed: {response.status_code}")
        return False
    except Exception as exc:  # pragma: no cover - CLI helper
        print(f"❌ Request failed: {exc}")
        return False


def iter_stream(response: requests.Response) -> None:
    """Pretty-print streamed JSON chunks."""

    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if not chunk:
            continue
        text = chunk.strip()
        if not text:
            continue
        try:
            payload: Any = json.loads(text)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(text)


def test_ppt_outline() -> None:
    """Test outline generation."""

    print("\n📝 Testing PPT outline generation…")

    data = {
        "model": "openrouter/auto",
        "language": "English",
        "content": "How AI accelerates climate research",
        "stream": True,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/tools/aippt_outline",
            json=data,
            stream=True,
            timeout=30,
        )
        if response.status_code == 200:
            print("✅ Outline request succeeded")
            iter_stream(response)
        else:
            print(f"❌ Outline request failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as exc:  # pragma: no cover - CLI helper
        print(f"❌ Request failed: {exc}")


def test_ppt_content() -> None:
    """Test PPT content generation."""

    print("\n🎨 Testing PPT content generation…")

    sample_outline = """# AI for Climate Research
## Data Foundations
### Data Quality
- Harmonise satellite and sensor data
- Maintain provenance tracking
### Storage Strategy
- Scalable data lakes
- Tiered cold storage
## Modelling Approaches
### Forecasting Models
- Hybrid physical and ML approaches
- Ensemble predictions
### Scenario Planning
- Generative simulations
- Policy stress tests"""

    data = {
        "model": "openrouter/auto",
        "language": "English",
        "content": sample_outline,
        "stream": True,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/tools/aippt",
            json=data,
            stream=True,
            timeout=60,
        )
        if response.status_code == 200:
            print("✅ Content request succeeded")
            iter_stream(response)
        else:
            print(f"❌ Content request failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as exc:  # pragma: no cover - CLI helper
        print(f"❌ Request failed: {exc}")


def main() -> None:
    """Run the smoke tests sequentially."""

    print("🧪 PPTist AI Backend API Tests")
    print("=" * 50)

    if not test_health():
        print("❌ Server is not reachable. Start it with: uv run main.py")
        return

    test_ppt_outline()
    time.sleep(2)
    test_ppt_content()

    print("\n🎉 Tests completed!")


if __name__ == "__main__":
    main()
