import asyncio
import atexit
import logging
import threading
from typing import Awaitable, Coroutine, Optional, TypeVar

T = TypeVar("T")


class AsyncRunner:
    _instance: Optional["AsyncRunner"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure Singleton instance of AsyncRunner."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.loop: Optional[asyncio.AbstractEventLoop] = None
            self._thread: Optional[threading.Thread] = None
            self._shutdown_event = threading.Event()
            self._initialized = True

    def start(self):
        """Start the async runner."""
        if self._thread is not None:
            return
        logging.debug("Initiating async runner...")

        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                while not self._shutdown_event.is_set():  # Exit if shutting down
                    self.loop.run_forever()
            finally:
                try:
                    # Cancel all running tasks
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()

                    # Allow tasks to complete cancellation
                    self.loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                    self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                finally:
                    self.loop.close()
                    self._shutdown_event.set()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

        # Wait until loop is running
        while not (self.loop and self.loop.is_running()):
            pass

    def run_async(self, coro: Awaitable[T] | Coroutine) -> T:
        """Execute coroutine from sync context"""
        if not self.loop or not self.loop.is_running():
            raise RuntimeError("AsyncRunner not started")

        if self._shutdown_event.is_set():
            raise RuntimeError("AsyncRunner is shutting down")

        logging.debug("Executing coroutine - %s", coro.__name__)
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def shutdown(self):
        """Shutdown the async runner"""
        logging.debug("Shutting down async runner...")

        if self._shutdown_event.is_set():
            return

        if self.loop and self.loop.is_running():
            # Schedule loop stop
            self.loop.call_soon_threadsafe(self.loop.stop)

        # Wait for thread to finish if it's not the current thread
        if (
            self._thread
            and threading.current_thread() is not self._thread
            and self._thread.is_alive()
        ):
            self._thread.join(timeout=2)  # 2 seconds timeout

        self._shutdown_event.set()

    def __del__(self):
        self.shutdown()


async_runner = AsyncRunner()
async_runner.start()

atexit.register(async_runner.shutdown)


def run_async(coro: Awaitable[T] | Coroutine) -> T:
    """Execute coroutine from sync context"""
    return async_runner.run_async(coro)
