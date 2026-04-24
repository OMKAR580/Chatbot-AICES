"""AI integration service using OpenRouter for explanations, quizzes, and feedback."""

from __future__ import annotations

import json
import os
import re
import socket
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from dotenv import load_dotenv

try:
    import requests as _requests
except ModuleNotFoundError:
    _requests = None


load_dotenv()


OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "mistralai/mistral-7b-instruct"
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "8.0"))
SHORT_RESPONSE_WORDS = 100
NORMAL_RESPONSE_WORDS = 220
DETAILED_RESPONSE_WORDS = 300
MAX_RESPONSE_WORDS = 500
SHORT_MAX_TOKENS = 150
NORMAL_MAX_TOKENS = 280
DETAILED_MAX_TOKENS = 420
REGENERATION_TIMEOUT_SECONDS = min(3.0, DEFAULT_TIMEOUT_SECONDS)

EXPLANATION_SYSTEM_PROMPT = """You are a precise technical tutor.
Answer ONLY what the user asked.
Do NOT guess.
Do NOT change the topic.
Do NOT give generic definitions.
If the question is specific (like CNN), give a detailed explanation of THAT topic only.
If unsure, say "I am not fully sure" instead of hallucinating.

Adapt the answer to the question:
- If the user asks "in depth", give a detailed explanation.
- If the user asks "simple", keep it simple.
- If the user asks for code, include code.
- If the user does not ask for code, do NOT include code unnecessarily.

Always stay relevant to the question.
Use clear markdown only when it helps readability.
Do not force a fixed template.
Keep the response concise, technically correct, and within the requested level of detail.
"""

QUIZ_SYSTEM_PROMPT = """You are AICES, a computer science quiz generator.
Return only valid JSON that matches the requested schema.
Do not add markdown fences or commentary.
"""

FEEDBACK_SYSTEM_PROMPT = """You are AICES, a supportive computer science tutor.
Return one short study feedback message only.
Do not add markdown or JSON unless asked.
"""

LOW_QUALITY_PATTERNS = (
    r"\bis the idea you are trying to learn\b",
    r"\bthis topic is something\b",
    r"\bthis concept is important because it helps you learn\b",
    r"\breal-life analogy\b",
    r"\bdry run\b",
    r"\bgeneric definition\b",
)

SUPPORTED_LANGUAGES = {"English", "Hindi", "Hinglish"}
SUPPORTED_MODES = {"standard", "simpler", "example", "technical", "quiz"}
SUPPORTED_RESPONSE_DEPTHS = {"normal", "detailed"}
SUPPORTED_RESPONSE_MODES = {"auto", "short", "detailed", "notes", "code", "interview"}
SUPPORTED_CODE_LANGUAGES = {"Python", "Java", "C"}

CONCEPT_ALIASES = {
    "cnn": "cnn",
    "cnn / convolutional neural network": "cnn",
    "convolutional neural network": "cnn",
    "array": "array",
    "arrays": "array",
    "machine learning": "machine learning",
    "deep learning": "deep learning",
    "neural network": "neural network",
    "linked list": "linked list",
    "linked lists": "linked list",
    "linkedlist": "linked list",
    "linked-list": "linked list",
    "stack": "stack",
    "stacks": "stack",
    "queue": "queue",
    "queues": "queue",
    "queue data structure": "queue",
    "recursion": "recursion",
    "recursive function": "recursion",
    "binary search": "binary search",
    "binary-search": "binary search",
    "binarysearch": "binary search",
    "binary searching": "binary search",
    "tree": "tree",
    "graph": "graph",
    "dbms": "dbms",
    "os": "os",
    "cn": "cn",
    "oop": "oop",
    "dsa": "dsa",
}
TOPIC_VALIDATION_TERMS = {
    "cnn": ("cnn", "convolutional neural network", "convolution"),
    "machine learning": ("machine learning",),
    "deep learning": ("deep learning",),
    "neural network": ("neural network",),
    "linked list": ("linked list",),
    "binary search": ("binary search",),
    "array": ("array",),
    "stack": ("stack",),
    "queue": ("queue",),
    "tree": ("tree",),
    "graph": ("graph",),
    "dbms": ("dbms", "database management system"),
    "os": (" os ", "operating system"),
    "cn": (" cn ", "computer networks"),
    "oop": ("oop", "object oriented"),
    "dsa": ("dsa", "data structures and algorithms"),
    "recursion": ("recursion", "recursive"),
}

CONCEPT_LIBRARY: dict[str, dict[str, str]] = {
    "cnn": {
        "title": "CNN / Convolutional Neural Network",
        "definition": "A CNN, or Convolutional Neural Network, is a deep learning model designed to learn patterns from grid-like data such as images.",
        "simple_definition": "A CNN is a neural network that looks at small parts of an image, learns useful patterns, and then uses them to classify or detect things.",
        "simple": "Instead of reading every pixel independently, a CNN scans an image using filters. It first learns edges and shapes, then combines them into more complex features.",
        "standard": "A CNN processes image-like input through convolution layers, activation functions, pooling, flattening, and dense layers. This makes it strong at extracting spatial patterns while using far fewer parameters than a fully connected network on raw pixels.",
        "analogy": "Think of looking at an image through small windows. Each window checks for a pattern such as an edge, corner, or texture, and later layers combine those patterns into higher-level understanding.",
        "types": "Common CNN variants include simple image classifiers, LeNet-style networks, AlexNet, VGG, ResNet, and object-detection backbones.",
        "example": "A CNN can classify handwritten digits by learning stroke shapes, curves, and combinations of those local features.",
        "technical": "Convolution layers apply kernels or filters across the input to create feature maps. Pooling reduces spatial size, flattening converts feature maps into vectors, and dense layers perform the final prediction.",
        "operations": "- convolution with filters/kernels\n- activation such as ReLU\n- pooling to reduce feature-map size\n- flattening\n- dense layers for final prediction",
        "complexity": "The cost depends on image size, number of filters, kernel size, and network depth. CNNs trade more compute for strong feature extraction on image-like data.",
        "uses": "CNNs are widely used for image classification, object detection, face recognition, medical imaging, and other computer vision tasks in machine learning and deep learning.",
        "code_example": (
            "from tensorflow.keras import layers, models\n\n"
            "model = models.Sequential([\n"
            "    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),\n"
            "    layers.MaxPooling2D((2, 2)),\n"
            "    layers.Flatten(),\n"
            "    layers.Dense(64, activation='relu'),\n"
            "    layers.Dense(10, activation='softmax')\n"
            "])\n\n"
            "print(model.layers[0].__class__.__name__)"
        ),
        "code_output": "Conv2D",
        "code_walkthrough": (
            "1. `Conv2D` applies filters to the image and creates feature maps.\n"
            "2. `MaxPooling2D` reduces the spatial size while keeping important signals.\n"
            "3. `Flatten` turns feature maps into a single vector.\n"
            "4. Dense layers use those learned features to predict the final class."
        ),
        "interview_points": (
            "- CNN stands for Convolutional Neural Network.\n"
            "- Convolution layers learn local spatial patterns using filters.\n"
            "- Pooling reduces spatial size and helps with efficiency.\n"
            "- Flattening and dense layers turn learned features into final predictions."
        ),
        "common_mistakes": (
            "- Confusing convolution with a fully connected layer.\n"
            "- Ignoring the role of filters/kernels and feature maps.\n"
            "- Treating pooling, flattening, and dense layers as the same operation."
        ),
        "key_points": "- Great for image-like data\n- Learns local features first, then higher-level patterns\n- Uses convolution, pooling, flattening, and dense layers",
        "takeaway": "Use a CNN when the question is about learning spatial patterns from images or similar structured data.",
    },
    "machine learning": {
        "title": "Machine Learning",
        "definition": "Machine learning is a field of AI where systems learn patterns from data to make predictions or decisions.",
        "simple_definition": "Machine learning means teaching a system by showing it data instead of hardcoding every rule.",
        "simple": "The model studies examples, finds patterns, and then uses those patterns on new data.",
        "standard": "Machine learning builds models from data so that they can generalize to unseen examples. Common settings include supervised, unsupervised, and reinforcement learning.",
        "analogy": "It is like learning from practice problems instead of memorizing one fixed answer sheet.",
        "types": "Main types are supervised learning, unsupervised learning, reinforcement learning, classification, regression, and clustering.",
        "example": "Email spam detection is a classic machine learning problem where a model learns from labeled emails.",
        "technical": "A machine learning system usually includes data preprocessing, feature representation, model training, validation, and evaluation.",
        "operations": "- collect and clean data\n- train a model\n- validate the model\n- predict on new data",
        "complexity": "Complexity depends on the algorithm, dataset size, feature count, and training setup.",
        "uses": "Prediction, recommendation, classification, anomaly detection, and forecasting across many domains.",
        "code_example": (
            "from sklearn.linear_model import LogisticRegression\n\n"
            "model = LogisticRegression()\n"
            "print(type(model).__name__)"
        ),
        "code_output": "LogisticRegression",
        "code_walkthrough": (
            "1. We create a machine learning model object.\n"
            "2. In a real workflow, we would fit it on training data.\n"
            "3. Then we would use it to make predictions on new examples."
        ),
        "interview_points": (
            "- Machine learning learns patterns from data.\n"
            "- Generalization to unseen data is the main goal.\n"
            "- Data quality and evaluation matter as much as the model."
        ),
        "common_mistakes": (
            "- Assuming more data always fixes a bad problem setup.\n"
            "- Ignoring overfitting and evaluation quality.\n"
            "- Confusing training accuracy with real-world performance."
        ),
        "key_points": "- Learns from data\n- Used for prediction and pattern detection\n- Evaluation is critical",
        "takeaway": "Machine learning is about using data to build models that perform useful tasks on unseen inputs.",
    },
    "deep learning": {
        "title": "Deep Learning",
        "definition": "Deep learning is a branch of machine learning that uses multi-layer neural networks to learn complex patterns.",
        "simple_definition": "Deep learning is machine learning with many neural-network layers that learn increasingly complex features.",
        "simple": "Earlier layers learn simple patterns, and deeper layers combine them into more advanced understanding.",
        "standard": "Deep learning trains layered neural networks end to end, often on large datasets, to learn representations automatically instead of relying heavily on manual feature engineering.",
        "analogy": "It is like building understanding step by step: simple shapes first, then parts, then full objects.",
        "types": "Common deep learning models include feedforward neural networks, CNNs, RNNs, LSTMs, and transformers.",
        "example": "Image recognition and language modeling are classic deep learning applications.",
        "technical": "Deep learning relies on forward propagation, backpropagation, optimization, activation functions, and layered feature learning.",
        "operations": "- forward pass\n- loss computation\n- backpropagation\n- parameter update",
        "complexity": "Training can be computationally expensive and depends on model depth, parameter count, and dataset size.",
        "uses": "Computer vision, speech recognition, NLP, recommendation, and generative AI.",
        "code_example": (
            "from tensorflow.keras import layers, models\n\n"
            "model = models.Sequential([\n"
            "    layers.Dense(32, activation='relu', input_shape=(10,)),\n"
            "    layers.Dense(1)\n"
            "])\n"
            "print(len(model.layers))"
        ),
        "code_output": "2",
        "code_walkthrough": (
            "1. We create a neural network with stacked layers.\n"
            "2. The hidden layer learns features.\n"
            "3. The final layer produces the output."
        ),
        "interview_points": (
            "- Deep learning is a subset of machine learning.\n"
            "- It uses multiple neural-network layers.\n"
            "- It can learn features automatically from raw or lightly processed data."
        ),
        "common_mistakes": (
            "- Treating deep learning as separate from machine learning.\n"
            "- Ignoring data size, compute cost, and overfitting.\n"
            "- Using deep models when a simpler model is enough."
        ),
        "key_points": "- Multi-layer neural networks\n- Strong for complex pattern learning\n- Needs data and compute",
        "takeaway": "Deep learning is most useful when layered representation learning gives a clear advantage over simpler models.",
    },
    "neural network": {
        "title": "Neural Network",
        "definition": "A neural network is a model made of connected layers of neurons that transform input data into outputs.",
        "simple_definition": "A neural network is a layered model that takes input, passes it through hidden layers, and produces an output.",
        "simple": "Each layer learns part of the pattern, and the network improves by adjusting weights during training.",
        "standard": "Neural networks learn nonlinear relationships by combining weighted sums, activation functions, and stacked layers. They are the foundation of deep learning.",
        "analogy": "Think of information flowing through a sequence of checkpoints, where each checkpoint refines the signal.",
        "types": "Common types include feedforward networks, CNNs, RNNs, LSTMs, and transformers.",
        "example": "A neural network can classify images, predict values, or detect patterns in sequential data.",
        "technical": "Neural networks use weights, biases, activation functions, forward propagation, and backpropagation to learn from data.",
        "operations": "- input layer\n- hidden layers\n- activation functions\n- output layer\n- backpropagation during training",
        "complexity": "Complexity depends on the number of layers, neurons, parameters, and training iterations.",
        "uses": "Classification, regression, vision, NLP, time-series modeling, and recommendation systems.",
        "code_example": (
            "from tensorflow.keras import layers, models\n\n"
            "model = models.Sequential([\n"
            "    layers.Dense(16, activation='relu', input_shape=(4,)),\n"
            "    layers.Dense(3, activation='softmax')\n"
            "])\n"
            "print(model.layers[-1].__class__.__name__)"
        ),
        "code_output": "Dense",
        "code_walkthrough": (
            "1. The first dense layer learns hidden features.\n"
            "2. The final dense layer maps those features to class scores.\n"
            "3. Training adjusts the weights to reduce error."
        ),
        "interview_points": (
            "- Neural networks are made of layers, weights, and activations.\n"
            "- Hidden layers help learn complex patterns.\n"
            "- CNNs and transformers are specialized neural-network architectures."
        ),
        "common_mistakes": (
            "- Confusing a neural network with a specific architecture like CNN.\n"
            "- Ignoring activation functions and training dynamics.\n"
            "- Assuming deeper always means better."
        ),
        "key_points": "- Layered model\n- Learns nonlinear patterns\n- Core building block of deep learning",
        "takeaway": "A neural network is the general layered model; CNNs are one specialized type of neural network.",
    },
    "array": {
        "title": "Array",
        "definition": "An array is a linear data structure that stores multiple values in contiguous positions and lets us access elements by index.",
        "simple_definition": "An array is like a row of boxes where each box has a position number called an index.",
        "simple": "Each value sits at a fixed position, so if you know the index, you can reach that value quickly.",
        "standard": "Arrays keep related data together in order. Because each position is indexed, reading an element is very fast when you already know where to look.",
        "analogy": "Think of cinema seats in one row. Every seat has a number, so you can directly go to seat 5 without checking every other seat first.",
        "types": "Common forms include one-dimensional arrays, two-dimensional arrays, and dynamic-array-backed lists. The core idea is still indexed storage.",
        "example": "Marks of students, temperatures of a week, or prices of products can all be stored in an array when order matters.",
        "technical": "Arrays are usually stored in contiguous memory. That is why random access by index is O(1), but inserting in the middle can require shifting elements.",
        "operations": "- access `arr[i]`\n- update `arr[i] = value`\n- traverse each element\n- insert/delete may require shifting elements",
        "complexity": "Access is O(1), while searching is O(n) in an unsorted array and insertion/deletion in the middle is usually O(n). Space usage is O(n).",
        "uses": "Use arrays when you need ordered storage, fast index-based access, iteration, or a base structure for many algorithms.",
        "code_example": (
            "numbers = [10, 20, 30, 40]\n"
            "print('First element:', numbers[0])\n"
            "print('Third element:', numbers[2])\n"
            "numbers[1] = 25\n"
            "print('Updated array:', numbers)"
        ),
        "code_output": "First element: 10\nThird element: 30\nUpdated array: [10, 25, 30, 40]",
        "code_walkthrough": (
            "1. We create an array-like list with four values.\n"
            "2. `numbers[0]` reads the first position, so it prints `10`.\n"
            "3. `numbers[2]` reads the third position, so it prints `30`.\n"
            "4. `numbers[1] = 25` updates the second element.\n"
            "5. Printing the array shows the modified order `[10, 25, 30, 40]`."
        ),
        "interview_points": (
            "- Arrays support O(1) index access.\n"
            "- Elements are stored in contiguous memory in many languages.\n"
            "- Insertion or deletion in the middle is expensive because elements may need shifting."
        ),
        "common_mistakes": (
            "- Confusing an index with the stored value.\n"
            "- Accessing an index that is out of range.\n"
            "- Assuming insertion in the middle is always fast."
        ),
        "key_points": "- Elements are stored in order\n- Each element has an index\n- Great for fast direct access",
        "takeaway": "Use an array when you want ordered data and quick access by position.",
    },
    "linked list": {
        "title": "Linked List",
        "definition": "A linked list is a linear data structure made of nodes, where each node stores data and a reference to the next node.",
        "simple_definition": "A linked list is a chain of boxes where each box tells you where the next box is.",
        "simple": "Instead of keeping all values side by side like an array, a linked list connects one node to the next node using links.",
        "standard": "A linked list stores elements as separate nodes connected by pointers or references. This makes insertion and deletion easier at known positions, but direct index access is slower than an array.",
        "analogy": "Think of a treasure hunt where each clue points to the next clue. You cannot jump straight to the fifth clue until you follow the earlier ones.",
        "types": "Important types are singly linked list, doubly linked list, and circular linked list.",
        "example": "Music playlists and browser forward/backward navigation often use linked structures because moving between connected items is natural.",
        "technical": "Each node usually contains `data` and `next`. In doubly linked lists, nodes also keep a `prev` reference. Traversal is O(n), while insertion at the head can be O(1).",
        "operations": "- create a node\n- point one node to the next\n- traverse from head to end\n- insert/delete by changing links",
        "complexity": "Access by position is O(n), searching is O(n), and insertion or deletion at the head is O(1). Overall storage is O(n).",
        "uses": "Useful when frequent insertion and deletion matter more than random index access.",
        "code_example": (
            "class Node:\n"
            "    def __init__(self, data):\n"
            "        self.data = data\n"
            "        self.next = None\n\n"
            "head = Node(10)\n"
            "head.next = Node(20)\n"
            "head.next.next = Node(30)\n\n"
            "current = head\n"
            "while current:\n"
            "    print(current.data)\n"
            "    current = current.next"
        ),
        "code_output": "10\n20\n30",
        "code_walkthrough": (
            "1. We define a `Node` class that stores data and a link to the next node.\n"
            "2. `head` points to the first node containing `10`.\n"
            "3. The next two statements connect `10 -> 20 -> 30`.\n"
            "4. `current = head` starts traversal from the beginning.\n"
            "5. The loop prints each node's data and moves to the next node until it reaches `None`."
        ),
        "interview_points": (
            "- A linked list stores nodes, not contiguous elements like an array.\n"
            "- Direct access by index is O(n).\n"
            "- Insertion/deletion can be efficient because links are updated instead of shifting many elements."
        ),
        "common_mistakes": (
            "- Forgetting to update links during insertion or deletion.\n"
            "- Losing the head pointer.\n"
            "- Expecting O(1) index access like an array."
        ),
        "key_points": "- Nodes are connected through links\n- Traversal starts from the head\n- Good for flexible insertion and deletion",
        "takeaway": "A linked list trades fast indexed access for flexible node insertion and deletion.",
    },
    "stack": {
        "title": "Stack",
        "definition": "A stack is a linear data structure that follows LIFO: Last In, First Out.",
        "simple_definition": "A stack stores items so the last item added is removed first.",
        "simple": "Think of it like a pile. You add a new item on top, and when you remove something, you remove the top item first.",
        "standard": "A stack has one open end called the top. New elements are pushed onto the top, and removals happen from the same top position.",
        "analogy": "A pile of plates: the last plate placed on top is the first plate you pick up.",
        "types": "Stacks are often implemented using arrays/lists or linked lists. Variations include call stacks and monotonic stacks.",
        "example": "Browser Back works like a stack: every page you visit is pushed, and pressing Back pops the latest page.",
        "technical": "A stack maintains a top pointer or index. Push moves the top forward and inserts an item; pop returns the top item and moves the top backward.",
        "operations": "- `push(x)` adds `x` on top\n- `pop()` removes and returns the top item\n- `peek()` reads the top item\n- `isEmpty()` checks whether the stack has no items",
        "complexity": "Push, pop, and peek are usually O(1). Space usage is O(n).",
        "uses": "Function call stack, undo/redo, expression evaluation, DFS, and browser history.",
        "code_example": (
            "stack = []\n"
            "stack.append(10)\n"
            "stack.append(20)\n"
            "stack.append(30)\n\n"
            "print('Top element:', stack[-1])\n"
            "print('Removed:', stack.pop())\n"
            "print('Stack now:', stack)"
        ),
        "code_output": "Top element: 30\nRemoved: 30\nStack now: [10, 20]",
        "code_walkthrough": (
            "1. We start with an empty list and use it like a stack.\n"
            "2. `append()` pushes values on top, so the order becomes `[10, 20, 30]`.\n"
            "3. `stack[-1]` reads the current top element, which is `30`.\n"
            "4. `pop()` removes and returns that same top element.\n"
            "5. After removing `30`, the stack still keeps the older values `[10, 20]`."
        ),
        "interview_points": (
            "- Stack follows LIFO order.\n"
            "- Push, pop, and peek are usually O(1).\n"
            "- Common uses include function calls, undo/redo, DFS, and expression evaluation."
        ),
        "common_mistakes": (
            "- Popping from an empty stack without checking first.\n"
            "- Confusing stack order with queue order.\n"
            "- Forgetting that insertion and deletion both happen at the top."
        ),
        "key_points": "- LIFO order\n- Insertion and deletion happen at the top\n- Useful when the most recent item should be handled first",
        "takeaway": "If the newest item must come out first, a stack is a natural fit.",
    },
    "queue": {
        "title": "Queue",
        "definition": "A queue is a linear data structure that follows FIFO: First In, First Out.",
        "simple_definition": "A queue stores items so the first item added is removed first.",
        "simple": "Items join at the back and leave from the front, just like people waiting in line.",
        "standard": "A queue keeps order by adding new items at the rear and removing older items from the front.",
        "analogy": "A ticket counter line: the person who arrives first gets served first.",
        "types": "Common types are simple queue, circular queue, deque, and priority queue as a related specialized structure.",
        "example": "Print jobs use a queue: the first document sent to the printer is printed first.",
        "technical": "A queue tracks front and rear positions. Enqueue inserts at the rear; dequeue removes from the front.",
        "operations": "- `enqueue(x)` adds `x` at the rear\n- `dequeue()` removes the front item\n- `front()` reads the front item\n- `isEmpty()` checks whether the queue is empty",
        "complexity": "Enqueue and dequeue are usually O(1) with a proper implementation. Space usage is O(n).",
        "uses": "Scheduling, BFS, print queues, message queues, and buffering.",
        "code_example": (
            "from collections import deque\n\n"
            "queue = deque()\n"
            "queue.append('A')\n"
            "queue.append('B')\n"
            "queue.append('C')\n\n"
            "print('Front element:', queue[0])\n"
            "print('Removed:', queue.popleft())\n"
            "print('Queue now:', list(queue))"
        ),
        "code_output": "Front element: A\nRemoved: A\nQueue now: ['B', 'C']",
        "code_walkthrough": (
            "1. We create an empty deque and use it like a queue.\n"
            "2. `append()` adds items at the rear in the order `A`, `B`, `C`.\n"
            "3. `queue[0]` reads the front element, which is `A`.\n"
            "4. `popleft()` removes the front element first.\n"
            "5. The remaining queue becomes `['B', 'C']`."
        ),
        "interview_points": (
            "- Queue follows FIFO order.\n"
            "- Enqueue and dequeue should be O(1) with a good implementation.\n"
            "- Queues are common in BFS and scheduling systems."
        ),
        "common_mistakes": (
            "- Using a plain list inefficiently for front deletion.\n"
            "- Confusing queue order with stack order.\n"
            "- Forgetting to handle empty-queue cases."
        ),
        "key_points": "- FIFO order\n- Rear for insertion, front for deletion\n- Good for fair processing order",
        "takeaway": "Use a queue when the oldest item should be handled first.",
    },
    "recursion": {
        "title": "Recursion",
        "definition": "Recursion is a technique where a function solves a problem by calling itself on smaller inputs.",
        "simple_definition": "Recursion means a function repeats itself on a smaller version of the same problem.",
        "simple": "Each call does a small part of the work until it reaches a stopping point called the base case.",
        "standard": "A recursive solution needs a base case to stop and a recursive case that moves toward that base case.",
        "analogy": "Opening nested boxes: each box contains a smaller box until you reach the final empty box.",
        "types": "Common forms include direct recursion, indirect recursion, tail recursion, and head recursion.",
        "example": "factorial(4) = 4 * factorial(3), then 3 * factorial(2), until factorial(1) returns 1.",
        "technical": "Each recursive call is stored on the call stack. If the base case is missing, recursion can continue until stack overflow.",
        "operations": "- define a base case\n- reduce the input\n- call the same function\n- combine the returned result",
        "complexity": "Complexity depends on the recurrence. Factorial is O(n) time and O(n) stack space.",
        "uses": "Tree traversal, DFS, divide and conquer, and backtracking.",
        "code_example": (
            "def factorial(n):\n"
            "    if n == 1:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)\n\n"
            "print(factorial(4))"
        ),
        "code_output": "24",
        "code_walkthrough": (
            "1. `factorial(4)` is not the base case, so it becomes `4 * factorial(3)`.\n"
            "2. `factorial(3)` becomes `3 * factorial(2)`.\n"
            "3. `factorial(2)` becomes `2 * factorial(1)`.\n"
            "4. `factorial(1)` hits the base case and returns `1`.\n"
            "5. The answers return upward: `2 * 1 = 2`, `3 * 2 = 6`, and `4 * 6 = 24`."
        ),
        "interview_points": (
            "- Every recursive solution needs a base case.\n"
            "- Each call should move toward that base case.\n"
            "- Recursion uses call stack space, so space complexity matters too."
        ),
        "common_mistakes": (
            "- Forgetting the base case.\n"
            "- Reducing the problem incorrectly so recursion never ends.\n"
            "- Ignoring stack overflow risk on very deep inputs."
        ),
        "key_points": "- Must have a base case\n- Input should become smaller\n- Uses call stack memory",
        "takeaway": "Recursion is powerful when a problem naturally breaks into smaller similar problems.",
    },
    "binary search": {
        "title": "Binary Search",
        "definition": "Binary search finds an item in a sorted list by repeatedly halving the search range.",
        "simple_definition": "Binary search quickly finds a value by checking the middle and discarding half the list.",
        "simple": "Look at the middle. If the target is smaller, search left. If it is bigger, search right.",
        "standard": "Binary search works only when data is sorted. It compares the target with the middle element and narrows the range.",
        "analogy": "Guessing a number from 1 to 100: each guess cuts the possible range in half.",
        "types": "The main forms are iterative binary search and recursive binary search.",
        "example": "To find 7 in [1, 3, 5, 7, 9], check 5 first, then move to the right half and find 7.",
        "technical": "Maintain `low` and `high` pointers, compute `mid`, compare `arr[mid]`, and update the search boundary.",
        "operations": "- `low = 0`, `high = n - 1`\n- `mid = (low + high) // 2`\n- compare target with `arr[mid]`\n- move `low` or `high`",
        "complexity": "Binary search runs in O(log n) time and O(1) space in the iterative version.",
        "uses": "Searching sorted arrays, lower/upper bound problems, and optimization by answer.",
        "code_example": (
            "def binary_search(arr, target):\n"
            "    low = 0\n"
            "    high = len(arr) - 1\n\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        if arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n\n"
            "    return -1\n\n"
            "numbers = [1, 3, 5, 7, 9]\n"
            "print(binary_search(numbers, 7))"
        ),
        "code_output": "3",
        "code_walkthrough": (
            "1. `low` starts at index `0` and `high` starts at index `4`.\n"
            "2. `mid` becomes `2`, so we compare `arr[2]`, which is `5`, with the target `7`.\n"
            "3. Because `5` is smaller than `7`, the target must be on the right side, so `low` becomes `3`.\n"
            "4. Now `mid` becomes `3`, and `arr[3]` is `7`.\n"
            "5. The function returns index `3`, which is where the target was found."
        ),
        "interview_points": (
            "- Binary search works only on sorted data.\n"
            "- Time complexity is O(log n) because the search space is halved at each step.\n"
            "- Off-by-one handling with `low`, `high`, and `mid` is a common interview focus."
        ),
        "common_mistakes": (
            "- Using binary search on unsorted data.\n"
            "- Updating `low` and `high` incorrectly.\n"
            "- Forgetting the loop condition `low <= high`."
        ),
        "key_points": "- Requires sorted data\n- Discards half the search space each step\n- Much faster than linear search on large sorted arrays",
        "takeaway": "Binary search is the standard fast search technique when the data is sorted.",
    },
}

ALTERNATE_CODE_EXAMPLES: dict[tuple[str, str], dict[str, str]] = {
    ("array", "Java"): {
        "code_example": (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        int[] numbers = {10, 20, 30, 40};\n"
            "        System.out.println(\"First element: \" + numbers[0]);\n"
            "        System.out.println(\"Third element: \" + numbers[2]);\n"
            "        numbers[1] = 25;\n"
            "        System.out.println(\"Updated array: \" + java.util.Arrays.toString(numbers));\n"
            "    }\n"
            "}"
        ),
        "code_output": "First element: 10\nThird element: 30\nUpdated array: [10, 25, 30, 40]",
        "code_walkthrough": (
            "1. We create an integer array with four values.\n"
            "2. `numbers[0]` and `numbers[2]` access elements directly by index.\n"
            "3. `numbers[1] = 25` updates the second element.\n"
            "4. `Arrays.toString(numbers)` prints the whole array in a readable form."
        ),
    },
    ("array", "C"): {
        "code_example": (
            "#include <stdio.h>\n\n"
            "int main() {\n"
            "    int numbers[] = {10, 20, 30, 40};\n"
            "    numbers[1] = 25;\n\n"
            "    printf(\"First element: %d\\n\", numbers[0]);\n"
            "    printf(\"Third element: %d\\n\", numbers[2]);\n"
            "    printf(\"Updated array: [%d, %d, %d, %d]\\n\", numbers[0], numbers[1], numbers[2], numbers[3]);\n"
            "    return 0;\n"
            "}"
        ),
        "code_output": "First element: 10\nThird element: 30\nUpdated array: [10, 25, 30, 40]",
        "code_walkthrough": (
            "1. We declare an integer array with four values.\n"
            "2. Each element is accessed by its index, starting from `0`.\n"
            "3. `numbers[1] = 25` changes the second element.\n"
            "4. `printf` prints the values to show the updated array."
        ),
    },
    ("linked list", "Java"): {
        "code_example": (
            "class Node {\n"
            "    int data;\n"
            "    Node next;\n\n"
            "    Node(int data) {\n"
            "        this.data = data;\n"
            "    }\n"
            "}\n\n"
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        Node head = new Node(10);\n"
            "        head.next = new Node(20);\n"
            "        head.next.next = new Node(30);\n\n"
            "        Node current = head;\n"
            "        while (current != null) {\n"
            "            System.out.println(current.data);\n"
            "            current = current.next;\n"
            "        }\n"
            "    }\n"
            "}"
        ),
        "code_output": "10\n20\n30",
        "code_walkthrough": (
            "1. `Node` stores the data and the link to the next node.\n"
            "2. `head` points to the first node.\n"
            "3. The next assignments connect `10 -> 20 -> 30`.\n"
            "4. The loop starts at the head and keeps following `next` until it reaches `null`."
        ),
    },
    ("linked list", "C"): {
        "code_example": (
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n\n"
            "struct Node {\n"
            "    int data;\n"
            "    struct Node* next;\n"
            "};\n\n"
            "int main() {\n"
            "    struct Node* first = malloc(sizeof(struct Node));\n"
            "    struct Node* second = malloc(sizeof(struct Node));\n"
            "    struct Node* third = malloc(sizeof(struct Node));\n\n"
            "    first->data = 10; first->next = second;\n"
            "    second->data = 20; second->next = third;\n"
            "    third->data = 30; third->next = NULL;\n\n"
            "    struct Node* current = first;\n"
            "    while (current != NULL) {\n"
            "        printf(\"%d\\n\", current->data);\n"
            "        current = current->next;\n"
            "    }\n"
            "    return 0;\n"
            "}"
        ),
        "code_output": "10\n20\n30",
        "code_walkthrough": (
            "1. Each node stores a value and a pointer to the next node.\n"
            "2. We create three nodes and connect them in order.\n"
            "3. The loop starts from the first node and follows `next` until it reaches `NULL`."
        ),
    },
    ("recursion", "Java"): {
        "code_example": (
            "public class Main {\n"
            "    static int factorial(int n) {\n"
            "        if (n == 1) {\n"
            "            return 1;\n"
            "        }\n"
            "        return n * factorial(n - 1);\n"
            "    }\n\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(factorial(4));\n"
            "    }\n"
            "}"
        ),
        "code_output": "24",
        "code_walkthrough": (
            "1. `factorial(4)` calls `factorial(3)`.\n"
            "2. The calls continue until `factorial(1)` hits the base case.\n"
            "3. Then the answers return upward and multiply together to give `24`."
        ),
    },
    ("recursion", "C"): {
        "code_example": (
            "#include <stdio.h>\n\n"
            "int factorial(int n) {\n"
            "    if (n == 1) {\n"
            "        return 1;\n"
            "    }\n"
            "    return n * factorial(n - 1);\n"
            "}\n\n"
            "int main() {\n"
            "    printf(\"%d\\n\", factorial(4));\n"
            "    return 0;\n"
            "}"
        ),
        "code_output": "24",
        "code_walkthrough": (
            "1. Each function call waits for a smaller call to finish.\n"
            "2. `factorial(1)` is the base case and returns `1`.\n"
            "3. The earlier calls multiply their values on the way back, producing `24`."
        ),
    },
    ("binary search", "Java"): {
        "code_example": (
            "public class Main {\n"
            "    static int binarySearch(int[] arr, int target) {\n"
            "        int low = 0;\n"
            "        int high = arr.length - 1;\n\n"
            "        while (low <= high) {\n"
            "            int mid = (low + high) / 2;\n"
            "            if (arr[mid] == target) return mid;\n"
            "            if (arr[mid] < target) {\n"
            "                low = mid + 1;\n"
            "            } else {\n"
            "                high = mid - 1;\n"
            "            }\n"
            "        }\n"
            "        return -1;\n"
            "    }\n\n"
            "    public static void main(String[] args) {\n"
            "        int[] numbers = {1, 3, 5, 7, 9};\n"
            "        System.out.println(binarySearch(numbers, 7));\n"
            "    }\n"
            "}"
        ),
        "code_output": "3",
        "code_walkthrough": (
            "1. `low` and `high` mark the current search range.\n"
            "2. `mid` checks the middle position.\n"
            "3. If the middle value is too small, we move right; otherwise we move left.\n"
            "4. The function returns index `3` when it finds `7`."
        ),
    },
    ("binary search", "C"): {
        "code_example": (
            "#include <stdio.h>\n\n"
            "int binarySearch(int arr[], int size, int target) {\n"
            "    int low = 0;\n"
            "    int high = size - 1;\n\n"
            "    while (low <= high) {\n"
            "        int mid = (low + high) / 2;\n"
            "        if (arr[mid] == target) return mid;\n"
            "        if (arr[mid] < target) {\n"
            "            low = mid + 1;\n"
            "        } else {\n"
            "            high = mid - 1;\n"
            "        }\n"
            "    }\n"
            "    return -1;\n"
            "}\n\n"
            "int main() {\n"
            "    int numbers[] = {1, 3, 5, 7, 9};\n"
            "    printf(\"%d\\n\", binarySearch(numbers, 5, 7));\n"
            "    return 0;\n"
            "}"
        ),
        "code_output": "3",
        "code_walkthrough": (
            "1. `low` and `high` track the current search range.\n"
            "2. Each loop checks the middle element.\n"
            "3. The code removes half the range after each comparison.\n"
            "4. When `7` is found, the function returns index `3`."
        ),
    },
}


class _CompatRequestException(Exception):
    """Raised when the lightweight HTTP compatibility layer fails."""

    def __init__(self, message: str, *, timeout: bool = False) -> None:
        super().__init__(message)
        self.timeout = timeout


class _CompatResponse:
    """Small response wrapper that mimics the parts of requests.Response we use."""

    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text

    def json(self) -> Any:
        return json.loads(self.text)


class _RequestsCompat:
    """Minimal requests-like wrapper so the backend can run without extra deps."""

    RequestException = _CompatRequestException

    @staticmethod
    def post(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> _CompatResponse:
        payload = json.dumps(json_body or {}).encode("utf-8")
        request = urllib_request.Request(
            url,
            data=payload,
            headers=headers or {},
            method="POST",
        )

        try:
            with urllib_request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                return _CompatResponse(status_code=response.getcode(), text=body)
        except urllib_error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return _CompatResponse(status_code=exc.code, text=body)
        except urllib_error.URLError as exc:
            reason_text = str(exc.reason)
            is_timeout = isinstance(exc.reason, TimeoutError | socket.timeout) or "timed out" in reason_text.lower()
            raise _CompatRequestException(reason_text, timeout=is_timeout) from exc


def _http_post(
    url: str,
    *,
    headers: dict[str, str],
    json_body: dict[str, Any],
    timeout: float,
) -> Any:
    if _requests is not None:
        return _requests.post(url, headers=headers, json=json_body, timeout=timeout)

    return _RequestsCompat.post(url, headers=headers, json_body=json_body, timeout=timeout)


class AIServiceError(Exception):
    """Raised when the AI provider cannot generate a response."""


class MissingAPIKeyError(AIServiceError):
    """Raised when the OpenRouter API key is missing."""


class AIServiceTimeoutError(AIServiceError):
    """Raised when the OpenRouter call times out."""


def get_openai_model() -> str:
    """Backward-compatible accessor used by the existing routes."""
    return (
        os.getenv("OPENROUTER_MODEL")
        or os.getenv("OPENAI_MODEL")
        or DEFAULT_MODEL
    ).strip() or DEFAULT_MODEL


def _get_openrouter_api_key() -> str:
    """Return the configured OpenRouter API key."""
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def build_prompt(
    topic: str,
    user_message: str | None,
    level: str,
    language: str,
    mode: str = "standard",
    response_depth: str = "normal",
    response_mode: str = "auto",
    code_required: bool = False,
    code_language: str = "Python",
    weak_areas: list[str] | None = None,
) -> str:
    """Build the explanation prompt sent to OpenRouter."""
    details = _get_concept_details(topic)
    actual_question = (user_message or topic or details["title"]).strip()
    normalized_language = normalize_language(language)
    normalized_mode = mode if mode in SUPPORTED_MODES else "standard"
    normalized_response_mode = normalize_response_mode(response_mode)
    normalized_response_depth = _resolve_response_depth(
        response_depth=response_depth,
        response_mode=normalized_response_mode,
    )
    normalized_code_language = normalize_code_language(code_language)
    weak_area_text = ", ".join(weak_areas or []) or "none"
    target_words = _get_target_word_count(
        response_mode=normalized_response_mode,
        response_depth=normalized_response_depth,
    )
    include_code = _should_include_code(
        user_message=actual_question,
        code_required=code_required,
        response_mode=normalized_response_mode,
    )
    answer_style = _get_answer_style_instruction(
        mode=normalized_mode,
        response_mode=normalized_response_mode,
        response_depth=normalized_response_depth,
        include_code=include_code,
        code_language=normalized_code_language,
        target_words=target_words,
    )

    return (
        f"User question: {actual_question}\n"
        f"Detected topic: {details['title']}\n"
        f"Tutor mode: {normalized_mode}\n"
        f"Language: {normalized_language}\n"
        f"Learner level: {level}\n"
        f"Response mode: {normalized_response_mode}\n"
        f"Target prose length: about {target_words} words, never more than {MAX_RESPONSE_WORDS} words\n"
        f"Preferred code language: {normalized_code_language}\n"
        f"Weak areas to reinforce if relevant: {weak_area_text}\n\n"
        "Tutor requirements:\n"
        f"- {_get_level_guidance(level)}\n"
        f"- {_get_mode_guidance(normalized_mode)}\n"
        f"- {_get_language_guidance(normalized_language)}\n"
        f"- {_get_response_mode_guidance(normalized_response_mode)}\n"
        f"- {_get_code_guidance(include_code, normalized_code_language, normalized_response_depth, normalized_mode, normalized_response_mode)}\n"
        "- Answer the actual user question, not only the detected topic label.\n"
        "- If the user asks about a specific concept such as CNN, answer that exact concept.\n"
        "- If the topic is unclear, ask one short clarification question instead of guessing.\n"
        "- Do not reinterpret the topic as a different concept.\n"
        "- Do not force Definition/Example/Code sections if they are not relevant.\n"
        "- Prefer direct explanation over generic textbook wording.\n"
        f"- {answer_style}\n\n"
        "Reference context for this topic:\n"
        f"- Canonical title: {details['title']}\n"
        f"- Core definition: {details['definition']}\n"
        f"- One example: {details['example']}\n"
        f"- Complexity: {details['complexity']}\n"
        f"- Uses: {details['uses']}\n"
        f"- Common mistake: {_first_bullet(details['common_mistakes'])}\n"
        "Do not mention these instructions."
    )


def build_quiz_prompt(topic: str, level: str, language: str, count: int) -> str:
    """Build a JSON-only quiz prompt."""
    normalized_language = normalize_language(language)
    question_count = max(3, min(15, int(count or 5)))
    return (
        f"Generate exactly {question_count} multiple-choice questions about `{topic}`.\n"
        f"Learner level: {level}\n"
        f"Language: {normalized_language}\n"
        "Rules:\n"
        "- Cover different angles of the topic.\n"
        "- Each question must have exactly 4 options.\n"
        "- `correct_answer` must be the full option text, not a letter.\n"
        "- Keep wording concise and clear.\n"
        "Return valid JSON only with this exact shape:\n"
        "{\n"
        f'  "topic": "{topic}",\n'
        '  "questions": [\n'
        "    {\n"
        '      "question": "question text",\n'
        '      "options": ["option 1", "option 2", "option 3", "option 4"],\n'
        '      "correct_answer": "one of the option strings"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Do not wrap the JSON in markdown."
    )


def build_feedback_prompt(
    topic: str,
    score: int,
    weak_area: str,
    level: str,
    language: str = "Hinglish",
) -> str:
    """Build a short feedback prompt."""
    normalized_language = normalize_language(language)
    weak_area_text = weak_area or "none"
    return (
        f"A learner completed a quiz about `{topic}`.\n"
        f"Score: {score}%\n"
        f"Level after quiz: {level}\n"
        f"Weak area: {weak_area_text}\n"
        f"Reply in {normalized_language}.\n"
        "Write one short encouraging study message with the next focus area."
    )


def generate_explanation(
    topic: str,
    user_message: str | None,
    level: str,
    language: str,
    mode: str = "standard",
    response_depth: str = "normal",
    response_mode: str = "auto",
    code_required: bool = False,
    code_language: str = "Python",
    weak_areas: list[str] | None = None,
) -> str:
    """Generate an adaptive explanation using OpenRouter."""
    normalized_response_mode = normalize_response_mode(response_mode)
    normalized_response_depth = _resolve_response_depth(response_depth, normalized_response_mode)
    actual_question = (user_message or topic).strip()
    include_code = _should_include_code(
        user_message=actual_question,
        code_required=code_required,
        response_mode=normalized_response_mode,
    )
    prompt = build_prompt(
        topic=topic,
        user_message=user_message,
        level=level,
        language=language,
        mode=mode,
        response_depth=normalized_response_depth,
        response_mode=normalized_response_mode,
        code_required=code_required,
        code_language=code_language,
        weak_areas=weak_areas,
    )

    try:
        output_text = _call_openrouter(
            prompt,
            system_prompt=EXPLANATION_SYSTEM_PROMPT,
            max_tokens=_get_max_tokens_for_response(
                response_mode=normalized_response_mode,
                response_depth=normalized_response_depth,
            ),
            timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        )
    except AIServiceTimeoutError:
        return _fallback_explanation(
            topic=topic,
            user_message=actual_question,
            level=level,
            language=language,
            mode=mode,
            response_depth="normal",
            response_mode="short",
            code_required=code_required,
            code_language=code_language,
            weak_areas=weak_areas,
            timed_out=True,
        )
    except Exception:
        return _fallback_explanation(
            topic=topic,
            user_message=actual_question,
            level=level,
            language=language,
            mode=mode,
            response_depth=normalized_response_depth,
            response_mode=normalized_response_mode,
            code_required=code_required,
            code_language=code_language,
            weak_areas=weak_areas,
        )

    normalized_output = _normalize_explanation_markdown(output_text)
    if _should_regenerate_explanation(
        normalized_output,
        topic,
        user_message=actual_question,
        response_mode=normalized_response_mode,
        response_depth=normalized_response_depth,
        code_required=include_code,
    ):
        try:
            retry_output = _call_openrouter(
                _build_regeneration_prompt(
                    topic=topic,
                    user_message=actual_question,
                    previous_answer=normalized_output,
                    level=level,
                    language=language,
                    mode=mode,
                    response_depth=normalized_response_depth,
                    response_mode=normalized_response_mode,
                    code_required=include_code,
                    code_language=code_language,
                ),
                system_prompt=EXPLANATION_SYSTEM_PROMPT,
                max_tokens=_get_max_tokens_for_response(
                    response_mode=normalized_response_mode,
                    response_depth=normalized_response_depth,
                ),
                timeout_seconds=REGENERATION_TIMEOUT_SECONDS,
            )
            normalized_retry_output = _normalize_explanation_markdown(retry_output)
            if not _should_regenerate_explanation(
                normalized_retry_output,
                topic,
                user_message=actual_question,
                response_mode=normalized_response_mode,
                response_depth=normalized_response_depth,
                code_required=include_code,
            ):
                return normalized_retry_output
        except Exception:
            pass

        return _fallback_explanation(
            topic=topic,
            user_message=actual_question,
            level=level,
            language=language,
            mode=mode,
            response_depth=normalized_response_depth,
            response_mode=normalized_response_mode,
            code_required=include_code,
            code_language=code_language,
            weak_areas=weak_areas,
        )

    return normalized_output


def generate_quiz(topic: str, level: str, language: str, count: int = 5) -> dict[str, Any]:
    """Generate a quiz payload, with deterministic fallback on provider failure."""
    question_count = max(3, min(15, int(count or 5)))
    prompt = build_quiz_prompt(topic=topic, level=level, language=language, count=question_count)

    try:
        output_text = _call_openrouter(prompt, system_prompt=QUIZ_SYSTEM_PROMPT)
        raw_payload = _parse_json_value(output_text)
        return _normalize_quiz_payload(raw_payload, topic=topic, level=level, count=question_count)
    except Exception:
        return _fallback_quiz(topic=topic, level=level, count=question_count)


def generate_feedback(
    topic: str,
    score: int,
    weak_area: str,
    level: str,
    language: str = "Hinglish",
) -> str:
    """Generate short learner feedback with deterministic fallback."""
    fallback_feedback = _fallback_feedback(
        topic=topic,
        score=score,
        weak_area=weak_area,
        level=level,
        language=language,
    )
    prompt = build_feedback_prompt(
        topic=topic,
        score=score,
        weak_area=weak_area,
        level=level,
        language=language,
    )

    try:
        output_text = _call_openrouter(prompt, system_prompt=FEEDBACK_SYSTEM_PROMPT)
    except Exception:
        return fallback_feedback

    cleaned_output = output_text.strip()
    if not cleaned_output:
        return fallback_feedback

    try:
        parsed_value = _parse_json_value(cleaned_output)
    except ValueError:
        return cleaned_output

    if isinstance(parsed_value, dict):
        feedback = str(parsed_value.get("feedback", "")).strip()
        return feedback or fallback_feedback

    return cleaned_output


def normalize_language(language: str | None) -> str:
    """Normalize user-facing language choices to supported labels."""
    cleaned_language = (language or "Hinglish").strip().lower()
    language_map = {
        "english": "English",
        "hindi": "Hindi",
        "hinglish": "Hinglish",
    }
    return language_map.get(cleaned_language, "Hinglish")


def normalize_response_mode(response_mode: str | None) -> str:
    """Normalize response mode to supported labels."""
    cleaned_response_mode = (response_mode or "auto").strip().lower()
    response_mode_map = {
        "auto": "auto",
        "short": "short",
        "detailed": "detailed",
        "notes": "notes",
        "code": "code",
        "with_code": "code",
        "with code": "code",
        "interview": "interview",
    }
    normalized_response_mode = response_mode_map.get(cleaned_response_mode, "auto")
    return normalized_response_mode if normalized_response_mode in SUPPORTED_RESPONSE_MODES else "auto"


def normalize_code_language(code_language: str | None) -> str:
    """Normalize requested code language to supported labels."""
    cleaned_code_language = (code_language or "Python").strip().lower()
    code_language_map = {
        "python": "Python",
        "java": "Java",
        "c": "C",
    }
    normalized_code_language = code_language_map.get(cleaned_code_language, "Python")
    return normalized_code_language if normalized_code_language in SUPPORTED_CODE_LANGUAGES else "Python"


def _resolve_response_depth(response_depth: str, response_mode: str) -> str:
    normalized_response_mode = normalize_response_mode(response_mode)
    if normalized_response_mode in {"detailed", "notes", "code"}:
        return "detailed"

    if normalized_response_mode in {"short", "interview"}:
        return "normal"

    cleaned_response_depth = (response_depth or "normal").strip().lower()
    return cleaned_response_depth if cleaned_response_depth in SUPPORTED_RESPONSE_DEPTHS else "normal"


def _call_openrouter(
    user_message: str,
    *,
    system_prompt: str,
    max_tokens: int | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    api_key = _get_openrouter_api_key()
    if not api_key:
        raise MissingAPIKeyError("OPENROUTER_API_KEY is missing.")

    payload = {
        "model": get_openai_model(),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = _http_post(
            OPENROUTER_ENDPOINT,
            headers=headers,
            json_body=payload,
            timeout=timeout_seconds,
        )
    except Exception as exc:
        print("AI error:", type(exc).__name__)
        if _is_timeout_exception(exc):
            raise AIServiceTimeoutError("OpenRouter request timed out.") from exc
        raise AIServiceError("OpenRouter request failed.") from exc

    status_code = int(getattr(response, "status_code", 500))
    if status_code in {408, 504}:
        print("AI error:", f"HTTP {status_code}")
        raise AIServiceTimeoutError(f"OpenRouter timed out with HTTP {status_code}.")
    if status_code >= 400:
        print("AI error:", f"HTTP {status_code}")
        raise AIServiceError(_extract_error_message(response, status_code=status_code))

    try:
        content = str(response.json()["choices"][0]["message"]["content"]).strip()
    except Exception as exc:
        print("AI error:", type(exc).__name__)
        raise AIServiceError("OpenRouter returned an unexpected response shape.") from exc

    if not content:
        print("AI error:", "EmptyResponse")
        raise AIServiceError("OpenRouter returned an empty response.")

    print("AI response generated successfully")
    return content


def _extract_error_message(response: Any, *, status_code: int) -> str:
    try:
        payload = response.json()
    except Exception:
        payload = None

    if isinstance(payload, dict):
        error_value = payload.get("error")
        if isinstance(error_value, dict):
            message = str(error_value.get("message", "")).strip()
            if message:
                return f"OpenRouter returned HTTP {status_code}: {message}"

        message = str(payload.get("message", "")).strip()
        if message:
            return f"OpenRouter returned HTTP {status_code}: {message}"

    response_text = str(getattr(response, "text", "")).strip()
    if response_text:
        return f"OpenRouter returned HTTP {status_code}: {response_text}"

    return f"OpenRouter returned HTTP {status_code}."


def _should_regenerate_explanation(
    output_text: str,
    topic: str,
    *,
    user_message: str,
    response_mode: str,
    response_depth: str,
    code_required: bool,
) -> bool:
    normalized_output = _normalize_explanation_markdown(output_text)
    lowered_output = normalized_output.lower()
    normalized_topic = _normalize_topic_key(topic)
    validation_terms = _get_topic_validation_terms(normalized_topic)
    prose_words = _count_words_without_code(normalized_output)
    target_words = _get_target_word_count(response_mode=response_mode, response_depth=response_depth)
    minimum_words = _get_minimum_word_count(response_mode=response_mode, response_depth=response_depth)
    asked_terms = _get_query_validation_terms(user_message=user_message, normalized_topic=normalized_topic)

    if any(re.search(pattern, lowered_output, flags=re.IGNORECASE) for pattern in LOW_QUALITY_PATTERNS):
        return True

    if prose_words > min(MAX_RESPONSE_WORDS, target_words + 120):
        return True

    if prose_words < minimum_words:
        return True

    if asked_terms and not any(term in lowered_output for term in asked_terms):
        return True

    if normalized_topic in CONCEPT_LIBRARY:
        if validation_terms and not any(term in lowered_output for term in validation_terms):
            return True

    if code_required and "```" not in normalized_output and "`" not in normalized_output:
        return True

    return False


def _is_timeout_exception(exc: Exception) -> bool:
    if isinstance(exc, TimeoutError | socket.timeout):
        return True

    if getattr(exc, "timeout", False):
        return True

    requests_exceptions = getattr(_requests, "exceptions", None) if _requests is not None else None
    timeout_exception = getattr(requests_exceptions, "Timeout", None)
    if timeout_exception is not None and isinstance(exc, timeout_exception):
        return True

    return "timed out" in str(exc).lower()


def _get_target_word_count(response_mode: str, response_depth: str) -> int:
    normalized_response_mode = normalize_response_mode(response_mode)
    normalized_response_depth = _resolve_response_depth(response_depth, normalized_response_mode)

    if normalized_response_mode == "short":
        return SHORT_RESPONSE_WORDS

    if normalized_response_mode in {"detailed", "notes", "code"} or normalized_response_depth == "detailed":
        return DETAILED_RESPONSE_WORDS

    return NORMAL_RESPONSE_WORDS


def _get_minimum_word_count(response_mode: str, response_depth: str) -> int:
    target_words = _get_target_word_count(response_mode=response_mode, response_depth=response_depth)
    if target_words <= SHORT_RESPONSE_WORDS:
        return 35

    if target_words >= DETAILED_RESPONSE_WORDS:
        return 90

    return 60


def _get_topic_validation_terms(normalized_topic: str) -> tuple[str, ...]:
    explicit_terms = TOPIC_VALIDATION_TERMS.get(normalized_topic)
    if explicit_terms is not None:
        return explicit_terms

    return tuple(word for word in normalized_topic.split() if len(word) > 2)


def _get_query_validation_terms(user_message: str, normalized_topic: str) -> tuple[str, ...]:
    lowered_message = f" {user_message.strip().lower()} "
    terms: list[str] = []

    explicit_terms = TOPIC_VALIDATION_TERMS.get(normalized_topic)
    if explicit_terms is not None:
        terms.extend(explicit_terms)

    question_terms = (
        "cnn",
        "convolution",
        "kernel",
        "filter",
        "pooling",
        "flatten",
        "dense",
        "machine learning",
        "deep learning",
        "neural network",
        "binary search",
        "linked list",
        "recursion",
        "array",
        "stack",
        "queue",
        "tree",
        "graph",
        "dbms",
        "operating system",
        "oop",
        "dsa",
    )
    for term in question_terms:
        if term in lowered_message and term not in terms:
            terms.append(term)

    return tuple(terms)


def _should_include_code(user_message: str, code_required: bool, response_mode: str) -> bool:
    if code_required or response_mode == "code":
        return True

    lowered_message = f" {user_message.strip().lower()} "
    code_triggers = (
        " code ",
        " program ",
        " implementation ",
        " snippet ",
        " example in ",
        " with code",
        "show code",
        "write code",
    )
    return any(trigger in lowered_message for trigger in code_triggers)


def _get_answer_style_instruction(
    *,
    mode: str,
    response_mode: str,
    response_depth: str,
    include_code: bool,
    code_language: str,
    target_words: int,
) -> str:
    parts = [f"Aim for about {target_words} words of prose."]

    if response_mode == "short":
        parts.append("Keep the explanation crisp and high-signal.")
    elif response_mode in {"detailed", "notes"} or response_depth == "detailed":
        parts.append("Go deeper on the mechanism and important details.")

    if mode == "simpler":
        parts.append("Use simple language and short sentences.")
    elif mode == "technical":
        parts.append("Use precise technical language where helpful.")

    if include_code:
        parts.append(f"Include one short runnable {code_language} code snippet only if it directly helps.")
    else:
        parts.append("Do not include code unless the user explicitly asked for it.")

    parts.append("Use headings only when they improve clarity.")
    return " ".join(parts)


def _build_regeneration_prompt(
    *,
    topic: str,
    user_message: str,
    previous_answer: str,
    level: str,
    language: str,
    mode: str,
    response_depth: str,
    response_mode: str,
    code_required: bool,
    code_language: str,
) -> str:
    return (
        build_prompt(
            topic=topic,
            user_message=user_message,
            level=level,
            language=language,
            mode=mode,
            response_depth=response_depth,
            response_mode=response_mode,
            code_required=code_required,
            code_language=code_language,
            weak_areas=None,
        )
        + "\n\nThe previous answer was too generic, too short, or not specific enough.\n"
        + "Rewrite it once so it answers the exact question more precisely.\n"
        + "Do not repeat generic filler.\n"
        + "Previous answer:\n"
        + previous_answer
    )


def _get_max_tokens_for_response(response_mode: str, response_depth: str) -> int:
    target_words = _get_target_word_count(response_mode=response_mode, response_depth=response_depth)
    if target_words <= SHORT_RESPONSE_WORDS:
        return SHORT_MAX_TOKENS

    if target_words >= DETAILED_RESPONSE_WORDS:
        return DETAILED_MAX_TOKENS

    return NORMAL_MAX_TOKENS


def _count_words_without_code(text: str) -> int:
    text_without_code = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    return len(re.findall(r"\b\w+\b", text_without_code))


def _first_bullet(text: str) -> str:
    for line in (text or "").splitlines():
        cleaned_line = line.strip().lstrip("-").strip()
        if cleaned_line:
            return cleaned_line
    return ""


def _build_key_points(
    details: dict[str, str],
    *,
    mode: str,
    response_mode: str,
    weak_areas: list[str] | None,
) -> str:
    points = [
        details["complexity"],
        f"Best use: {details['uses']}",
        f"Watch out: {_first_bullet(details['common_mistakes']) or details['common_mistakes']}",
    ]

    if mode == "technical":
        points.append(f"Technical note: {details['technical']}")
    elif response_mode in {"detailed", "notes", "code", "interview"}:
        points.append(f"Interview tip: {_first_bullet(details['interview_points']) or details['interview_points']}")

    weak_area_text = ", ".join(weak_areas or [])
    if weak_area_text:
        points.append(f"Focus area: {weak_area_text}")

    max_points = 5 if response_mode in {"detailed", "notes", "code", "interview"} else 3
    return "\n".join(f"- {point}" for point in points[:max_points] if point)


def _normalize_explanation_markdown(output_text: str) -> str:
    cleaned_text = output_text.replace("\r\n", "\n").strip()
    if not cleaned_text:
        return cleaned_text

    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    cleaned_text = re.sub(r"(?m)^([A-Z][A-Za-z /-]{2,40}):\s*$", r"## \1", cleaned_text)
    return cleaned_text.strip()


def _parse_json_value(output_text: str) -> Any:
    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        start_index = min(
            [index for index in (output_text.find("{"), output_text.find("[")) if index != -1],
            default=-1,
        )
        end_index = max(output_text.rfind("}"), output_text.rfind("]"))
        if start_index == -1 or end_index == -1 or end_index <= start_index:
            raise ValueError("AI response did not contain JSON.")

        try:
            return json.loads(output_text[start_index : end_index + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("AI response contained malformed JSON.") from exc


def _normalize_quiz_payload(raw_payload: Any, topic: str, level: str, count: int) -> dict[str, Any]:
    if isinstance(raw_payload, list):
        raw_questions = raw_payload
        payload_topic = topic
    elif isinstance(raw_payload, dict):
        raw_questions = raw_payload.get("questions", [])
        payload_topic = str(raw_payload.get("topic") or topic).strip() or topic
    else:
        raise ValueError("Quiz payload must be a JSON object or list.")

    if not isinstance(raw_questions, list):
        raise ValueError("Quiz questions must be a list.")

    questions: list[dict[str, Any]] = []
    for raw_question in raw_questions:
        if not isinstance(raw_question, dict):
            continue

        question_text = str(raw_question.get("question", "")).strip()
        raw_options = raw_question.get("options", [])
        raw_correct_answer = str(
            raw_question.get("correct_answer") or raw_question.get("answer") or ""
        ).strip()

        if not question_text or not isinstance(raw_options, list):
            continue

        options = [str(option).strip() for option in raw_options if str(option).strip()]
        if len(options) < 4:
            continue

        options = options[:4]
        correct_answer = _normalize_correct_answer(raw_correct_answer, options)
        if not correct_answer:
            continue

        questions.append(
            {
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
            }
        )

        if len(questions) >= count:
            break

    if len(questions) < count:
        fallback_questions = _fallback_quiz(topic=topic, level=level, count=count)["questions"]
        for fallback_question in fallback_questions:
            if len(questions) >= count:
                break
            questions.append(fallback_question)

    return {
        "topic": payload_topic,
        "questions": questions[:count],
    }


def _normalize_correct_answer(raw_correct_answer: str, options: list[str]) -> str:
    if not raw_correct_answer:
        return ""

    cleaned_answer = raw_correct_answer.strip()
    normalized_answer = cleaned_answer.lower()
    letter_map = {"a": 0, "b": 1, "c": 2, "d": 3}
    if normalized_answer in letter_map and letter_map[normalized_answer] < len(options):
        return options[letter_map[normalized_answer]]

    if normalized_answer.isdigit():
        index = int(normalized_answer) - 1
        if 0 <= index < len(options):
            return options[index]

    for option in options:
        if _normalize_text(option) == _normalize_text(cleaned_answer):
            return option

    return ""


def _fallback_explanation(
    topic: str,
    user_message: str | None,
    level: str,
    language: str,
    mode: str = "standard",
    response_depth: str = "normal",
    response_mode: str = "auto",
    code_required: bool = False,
    code_language: str = "Python",
    weak_areas: list[str] | None = None,
    timed_out: bool = False,
) -> str:
    details = _get_concept_details(topic)
    actual_question = (user_message or topic or details["title"]).strip()
    normalized_language = normalize_language(language)
    normalized_mode = mode if mode in SUPPORTED_MODES else "standard"
    normalized_response_mode = normalize_response_mode(response_mode)
    normalized_code_language = normalize_code_language(code_language)
    include_code = _should_include_code(
        user_message=actual_question,
        code_required=code_required,
        response_mode=normalized_response_mode,
    )
    is_beginner = (level or "beginner").strip().lower() == "beginner" or normalized_mode == "simpler"
    wants_detailed = normalized_response_mode in {"detailed", "notes"} or response_depth == "detailed"
    wants_definition = bool(re.search(r"\b(what is|explain|teach|define)\b", actual_question, flags=re.IGNORECASE))
    wants_example = wants_detailed or normalized_mode == "example" or "example" in actual_question.lower()

    definition = details["simple_definition"] if is_beginner else details["definition"]
    explanation_parts = [details["simple"] if is_beginner else details["standard"]]
    if normalized_mode == "technical":
        explanation_parts.append(details["technical"])
    elif normalized_mode == "example":
        explanation_parts.append(f"Use case: {details['uses']}")
    elif normalized_response_mode in {"detailed", "notes", "code"}:
        explanation_parts.append(f"Use case: {details['uses']}")
    explanation = " ".join(part.strip() for part in explanation_parts if part.strip())
    example_text = details["example"]
    if normalized_response_mode in {"detailed", "notes", "code"}:
        compact_operations = re.sub(r"\s+", " ", details["operations"].replace("\n", "; ")).strip(" ;")
        explanation = f"{explanation} Core operations: {compact_operations}."
        example_text = f"{details['example']} Use it when: {details['uses']}"

    code_material = _get_code_material(details=details, code_language=normalized_code_language)
    code_block = "Choose a specific programming language variant if you want a runnable snippet."
    if code_material:
        code_block = f"```{code_material['fence_language']}\n{code_material['code_example']}\n```"

    sections: list[tuple[str, str]] = []
    if wants_definition:
        sections.append(("Definition", definition))
    sections.append(("Explanation", explanation))
    if wants_example:
        sections.append(("Example", example_text))
    if include_code:
        sections.append(("Code", code_block))
    sections.append(
        (
            "Key Points",
            _build_key_points(
                details,
                mode=normalized_mode,
                response_mode=normalized_response_mode,
                weak_areas=weak_areas,
            ),
        )
    )

    body = _compose_dynamic_study_note(details["title"], sections)
    if normalized_language == "Hindi":
        body = f"Chaliye is topic ko short notes me samajhte hain.\n\n{body}"
    elif normalized_language == "Hinglish":
        body = f"Chalo is topic ko short notes me samajhte hain.\n\n{body}"

    if timed_out:
        body = f"Quick fallback summary:\n\n{body}"

    return _normalize_explanation_markdown(body)


def _compose_dynamic_study_note(title: str, sections: list[tuple[str, str]]) -> str:
    blocks = [f"## {title}"]
    for label, content in sections:
        cleaned_content = (content or "").strip()
        if not cleaned_content:
            continue
        blocks.append(f"### {label}\n{cleaned_content}")

    return "\n\n".join(blocks)


def _compose_study_note(title: str, sections: list[tuple[str, str]]) -> str:
    blocks = [f"## {title}"]
    for label, content in sections:
        cleaned_content = (content or "").strip()
        if not cleaned_content:
            continue
        blocks.append(f"## {label}\n{cleaned_content}")

    return "\n\n".join(blocks)


def _get_code_material(details: dict[str, str], code_language: str) -> dict[str, str] | None:
    topic_key = details.get("concept_key", _normalize_topic_key(details.get("title", "")))
    normalized_code_language = normalize_code_language(code_language)
    fence_languages = {"Python": "python", "Java": "java", "C": "c"}

    if normalized_code_language == "Python" and details.get("code_example", "").strip():
        return {
            "language": "Python",
            "fence_language": "python",
            "code_example": details["code_example"],
            "code_output": details["code_output"],
            "code_walkthrough": details["code_walkthrough"],
        }

    alternate_material = ALTERNATE_CODE_EXAMPLES.get((topic_key, normalized_code_language))
    if alternate_material:
        return {
            "language": normalized_code_language,
            "fence_language": fence_languages.get(normalized_code_language, "text"),
            **alternate_material,
        }

    if details.get("code_example", "").strip():
        return {
            "language": "Python",
            "fence_language": "python",
            "code_example": details["code_example"],
            "code_output": details["code_output"],
            "code_walkthrough": details["code_walkthrough"],
        }

    return None


def _get_concept_details(topic: str) -> dict[str, str]:
    normalized_key = _normalize_topic_key(topic)
    details = CONCEPT_LIBRARY.get(normalized_key)
    if details is not None:
        return {"concept_key": normalized_key, **details}

    title = _title_case_topic(topic)
    cleaned_topic = title.lower()
    return {
        "concept_key": normalized_key,
        "title": title,
        "definition": f"{title} is a computer science concept that should be explained through its purpose, workflow, and a concrete example.",
        "simple_definition": f"{title} is a concept in computer science that becomes easier when you learn what it does and where it is used.",
        "simple": f"Start with the main purpose of {cleaned_topic}, then trace a very small example from start to finish.",
        "standard": f"Understand what problem {cleaned_topic} solves, how it works internally, and which tradeoffs it introduces.",
        "analogy": f"Relate {cleaned_topic} to a real-life workflow where each step has a clear role.",
        "types": "Types depend on the exact variant of this concept. If needed, clarify the specific subtype you want to study.",
        "example": f"Use one tiny example of {cleaned_topic} and trace each step carefully.",
        "technical": f"Focus on the internal workflow, data movement, control flow, and tradeoffs of {cleaned_topic}.",
        "operations": "- identify the goal\n- break the idea into steps\n- trace a small example\n- review edge cases",
        "complexity": "Time and space complexity depend on the exact algorithm or implementation of this concept.",
        "uses": f"Use {cleaned_topic} when it directly matches the problem constraints and desired behavior.",
        "code_example": (
            "def describe_concept(name):\n"
            "    print(f'Studying: {name}')\n\n"
            f"describe_concept('{title}')"
        ),
        "code_output": f"Studying: {title}",
        "code_walkthrough": (
            "1. The function receives the concept name.\n"
            "2. It prints a simple line showing which concept is being studied.\n"
            "3. Replace this with a topic-specific example when you want implementation details."
        ),
        "interview_points": (
            f"- Explain what {cleaned_topic} is in one or two lines.\n"
            "- Mention where it is used.\n"
            "- Call out the main tradeoff, limitation, or complexity concern."
        ),
        "common_mistakes": (
            "- Giving a definition without explaining the workflow.\n"
            "- Skipping edge cases.\n"
            "- Ignoring complexity or implementation tradeoffs."
        ),
        "key_points": "- Learn the purpose\n- Trace a tiny example\n- Review tradeoffs",
        "takeaway": f"Learn {cleaned_topic} by combining the definition, one small example, and the key tradeoffs.",
    }


def _normalize_topic_key(topic: str) -> str:
    normalized = re.sub(r"[_-]+", " ", (topic or "").strip().lower())
    normalized = re.sub(r"\s+", " ", normalized)
    return CONCEPT_ALIASES.get(normalized, normalized)


def _title_case_topic(topic: str) -> str:
    normalized_topic = _normalize_topic_key(topic)
    details = CONCEPT_LIBRARY.get(normalized_topic)
    if details is not None:
        return details["title"]

    cleaned_topic = re.sub(r"\s+", " ", (topic or "").strip())
    if not cleaned_topic:
        return "This Concept"

    return " ".join(part.capitalize() for part in cleaned_topic.split())


def _fallback_quiz(topic: str, level: str, count: int) -> dict[str, Any]:
    cleaned_topic = _title_case_topic(topic)
    question_bank = [
        {
            "question": f"What is the best first step when learning {cleaned_topic}?",
            "options": [
                "Understand the definition and purpose",
                "Memorize random edge cases first",
                "Ignore examples completely",
                "Skip the workflow",
            ],
            "correct_answer": "Understand the definition and purpose",
        },
        {
            "question": f"Which study method is most helpful for {cleaned_topic}?",
            "options": [
                "Trace a small example step by step",
                "Read only the heading",
                "Avoid practical inputs",
                "Memorize without understanding",
            ],
            "correct_answer": "Trace a small example step by step",
        },
        {
            "question": f"When revising {cleaned_topic}, what should you also check?",
            "options": [
                "Common mistakes and edge cases",
                "Only the topic name",
                "Unrelated formulas",
                "Nothing after the definition",
            ],
            "correct_answer": "Common mistakes and edge cases",
        },
        {
            "question": f"What usually improves understanding of {cleaned_topic} for a {level} learner?",
            "options": [
                "A worked example with explanation",
                "Skipping all examples",
                "Reading only one bullet",
                "Avoiding questions about the topic",
            ],
            "correct_answer": "A worked example with explanation",
        },
        {
            "question": f"What is a good way to confirm you understood {cleaned_topic}?",
            "options": [
                "Explain it in your own words",
                "Memorize one line only",
                "Ignore how it works",
                "Avoid practice questions",
            ],
            "correct_answer": "Explain it in your own words",
        },
        {
            "question": f"Why are examples useful while studying {cleaned_topic}?",
            "options": [
                "They connect the idea to an actual workflow",
                "They make the topic more confusing by default",
                "They replace the need to understand basics",
                "They are only useful after mastery",
            ],
            "correct_answer": "They connect the idea to an actual workflow",
        },
    ]

    questions = [question_bank[index % len(question_bank)] for index in range(max(3, min(15, count)))]
    return {
        "topic": cleaned_topic,
        "questions": questions,
    }


def _fallback_feedback(topic: str, score: int, weak_area: str, level: str, language: str) -> str:
    cleaned_topic = _title_case_topic(topic)
    normalized_language = normalize_language(language)

    if normalized_language == "Hindi":
        if weak_area and weak_area != "none":
            return (
                f"Aapne {cleaned_topic} me {score}% score kiya. Ab agla focus {weak_area} par rakhiye "
                f"aur {level} level ke chhote examples solve kijiye."
            )

        return (
            f"Aapne {cleaned_topic} me {score}% score kiya. Acchi progress hai. "
            f"Ab thoda aur {level} level practice kijiye."
        )

    if normalized_language == "Hinglish":
        if weak_area and weak_area != "none":
            return (
                f"You scored {score}% on {cleaned_topic}. Ab {weak_area} par focus karo "
                f"aur ek do small {level} examples practice karo."
            )

        return (
            f"You scored {score}% on {cleaned_topic}. Good progress. "
            f"Ab thoda aur {level} level practice karo."
        )

    if weak_area and weak_area != "none":
        return (
            f"You scored {score}% on {cleaned_topic}. Focus next on {weak_area} "
            f"and practice a few smaller {level} examples."
        )

    return (
        f"You scored {score}% on {cleaned_topic}. Good progress. "
        f"Keep practicing with slightly harder {level} examples."
    )


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _get_level_guidance(level: str) -> str:
    level_guidance = {
        "beginner": "Use simpler language first, but still explain the correct technical idea.",
        "intermediate": "Balance intuition with correct technical vocabulary and tradeoffs.",
        "advanced": "Include deeper detail, internal behavior, tradeoffs, and precise complexity discussion.",
    }
    return level_guidance.get((level or "").strip().lower(), level_guidance["beginner"])


def _get_mode_guidance(mode: str) -> str:
    mode_guidance = {
        "technical": "Lean into implementation details and meaningful complexity notes without becoming long-winded.",
        "simpler": "Keep the wording easy without losing correctness.",
        "example": "Use one practical example to make the concept stick.",
        "standard": "Balance clarity, structure, and speed.",
        "quiz": "Explain the concept in a way that helps the learner answer questions confidently.",
    }
    return mode_guidance.get(mode, mode_guidance["standard"])


def _get_language_guidance(language: str) -> str:
    language_guidance = {
        "English": "Write in clear English.",
        "Hindi": "Write in simple Hindi and keep technical terms in English when useful.",
        "Hinglish": "Write in natural Hinglish and keep technical terms in English.",
    }
    return language_guidance.get(language, language_guidance["English"])


def _get_response_mode_guidance(response_mode: str) -> str:
    response_mode_guidance = {
        "auto": "Prefer a compact, relevant answer without forcing a fixed layout.",
        "short": "Aim for about 100 words of prose.",
        "detailed": "Aim for about 300 words of prose.",
        "notes": "Keep it crisp and revision-friendly.",
        "code": "If code is requested, make it especially clear and practical.",
        "interview": "Keep the wording sharp and high-signal.",
    }
    return response_mode_guidance.get(response_mode, response_mode_guidance["auto"])


def _get_code_guidance(
    code_required: bool,
    code_language: str,
    response_depth: str,
    mode: str,
    response_mode: str,
) -> str:
    if code_required or response_mode == "code":
        return f"Include one short runnable {code_language} code example."

    return "Do not include code unless the user explicitly asked for it."
