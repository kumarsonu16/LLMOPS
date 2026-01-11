Create The Project:

```bash uv init .```

Create Virtual Env:

```bash uv venv .venv```


Create Virtual Env and intall Dependencies:

```bash uv add -r requirements.txt``


Add dependecies for Vscode:

```bash uv add ipykernel```


**Online tool to draw the diagram** 

[Flow.excalidraw](https://excalidraw.com/)


Install dependecies 

```bash uv add -r requirements.txt```

Sync the dependecies for uv.lock - important for production

```bash uv sync```

Activate ENV

```bash source /Users/s.kumar/Documents/learn/LLMOPS/.venv/bin/activate```
Run the uvicorn app

```bash uvicorn main:app --reload```


Run the test cases 

```bash uv run pytest```