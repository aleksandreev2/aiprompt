from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.app.knowledge import KnowledgeBase


ROOT = Path(__file__).parents[1]


def test_fts_retrieval_can_run_from_gradio_worker_threads():
    """KnowledgeBase is created during module import, then Gradio calls it from workers."""
    kb = KnowledgeBase(ROOT / "knowledge")
    intent = "девушка прижимается руками к окну, за окном размыто школьный двор"

    def retrieve_once():
        pack = kb.retrieve(intent, limit=8)
        return {item.canonical for item in pack.candidates}

    # Use several worker threads so the test catches both sqlite's thread-affinity
    # error and accidental concurrent use of the shared FTS connection.
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: retrieve_once(), range(12)))

    assert all("hands pressed against window" in result for result in results)
    assert all("schoolyard" in result for result in results)
