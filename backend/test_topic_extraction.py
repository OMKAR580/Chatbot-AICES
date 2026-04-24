"""Focused smoke tests for topic extraction and prompt relevance."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.topic_utils import extract_topic


TEST_CASES = (
    ("explain hyperparameter", "Hyperparameter"),
    ("what is hyperparameter in ML", "Hyperparameter Machine Learning"),
    ("explain supervised learning", "Supervised Learning"),
    ("what is probability in math", "Probability"),
    ("explain static routing in Computer network", "Static Routing"),
    ("what is NLP in machine learning", "Natural Language Processing"),
    ("explain linear regression", "Linear Regression"),
    ("explain CNN with example", "Convolutional Neural Network"),
)





def main() -> None:
    for message, expected_topic in TEST_CASES:
        topic = extract_topic(message)
        assert topic == expected_topic, f"{message!r} -> {topic!r}, expected {expected_topic!r}"


    print("topic extraction tests passed")


if __name__ == "__main__":
    main()

