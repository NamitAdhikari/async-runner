
# Async Runner
**Async Runner** is a minimal Python utility designed to run asynchronous tasks from synchronous code — **without worrying about event loop conflicts or lifecycle issues**.

## Why Async Runner?
In many real-world projects, especially when integrating third-party libraries or legacy synchronous code, you may need to **invoke `async` functions inside a `sync` context**. However, common approaches come with challenges:

- `asyncio.run()` creates a new event loop, which fails if one already exists.
- Some libraries **require an existing event loop**, others **fail if one already exists**.
- Solutions like `greenlet` can be overly complex or unsuitable for certain use cases.

After struggling with these limitations across different projects, this package was built to offer a clean, lightweight, and **thread-safe** solution by:

✅ Delegating async tasks to a background thread <br>
✅ Maintaining a **single, long-running event loop** <br>
✅ Making async-in-sync calls as easy as a regular function call

## Installation
```bash
pip install async-runner
```

## ✅ Features
- Simple, one-line usage
- Thread-safe and reusable
- Works in environments with or without existing event loops
- Avoids `RuntimeError: Event loop is closed` or `This event loop is already running issues`

## How It Works
`async_runner` creates and manages an **event loop inside a dedicated background thread**. This allows your sync code to safely schedule and await asynchronous tasks, without interfering with the main thread’s context.

## Example Usage
```python
import asyncio
from async_runner import run_async

async def async_task():
    await asyncio.sleep(1)
    return "Async task completed"

def sync_task():
    result = run_async(async_task())
    print(result)

sync_task()
```

#### Output:
```
Async task completed
```

## Use Cases
- Calling async APIs from FastAPI views or Python Scripts
- Wrapping async logic inside a sync SDK
- Integrating with libraries that inconsistently depend on event loop presence
