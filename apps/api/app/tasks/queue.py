import threading
from typing import Callable
from apps.api.app.core.config import settings

def dispatch_job(task_fn: Callable, *args, **kwargs):
    """
    Dispatches task to in-process background worker thread or Redis worker.
    """
    thread = threading.Thread(target=task_fn, args=args, kwargs=kwargs, daemon=True)
    thread.start()
