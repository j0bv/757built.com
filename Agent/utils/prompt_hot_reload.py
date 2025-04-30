"""Prompt hot-reload helper.

Start a watchdog observer on Agent/prompts/* so that when any .md file is
updated we clear the LRU cache in Agent.enhanced_document_processor.load_prompt_template.

Set environment variable PROMPT_HOT_RELOAD=0 to disable.
"""
import os
from pathlib import Path
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class _PromptChangeHandler(FileSystemEventHandler):
    def __init__(self, invalidate_callback):
        super().__init__()
        self.invalidate_callback = invalidate_callback

    def on_modified(self, event):  # noqa: D401
        if event.is_directory:
            return
        if event.src_path.endswith('.md'):
            self.invalidate_callback()

    # Some editors replace files → treat created events, too.
    on_created = on_modified


def start(invalidate_callback, prompts_dir: str):
    """Run the watchdog observer in a daemon thread.

    Args:
        invalidate_callback: Function to call when templates change.
        prompts_dir: Directory path to watch.
    """
    if os.getenv('PROMPT_HOT_RELOAD', '1') != '1':
        return  # disabled

    watch_path = Path(prompts_dir).resolve()
    if not watch_path.exists():
        return

    handler = _PromptChangeHandler(invalidate_callback)
    observer = Observer()
    observer.schedule(handler, path=str(watch_path), recursive=False)
    observer.daemon = True

    # Run in separate thread so that observer.start() doesn't block main thread
    def _runner():
        observer.start()
        observer.join()

    Thread(target=_runner, name='PromptWatcher', daemon=True).start()
