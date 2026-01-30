from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jarvis_core.sync.manager import SyncQueueManager


def register_default_handlers(manager: "SyncQueueManager") -> None:
    # Avoid circular imports by importing here
    # Implementation depends on what we want to sync.
    # Instructions example:
    # manager.register_handler("search", lambda query, **kwargs: client.search(query, **kwargs))

    # But checking 'client.search' availability.
    # We might need to instantiate clients or use global ones.

    # Placeholder for now until we identify specific clients clearly.
    # Or define simple wrappers.

    def handle_search(args, kwargs):
        # This is a bit tricky because we don't know the client instance.
        # The 'queue' assumes we can replay the operation.
        # For 'search', we likely use unified search.
        from jarvis_core.sources import UnifiedSourceClient

        client = UnifiedSourceClient()
        client.search(*args, **kwargs)

    manager.register_handler("search", handle_search)

    # Add more handlers as needed
