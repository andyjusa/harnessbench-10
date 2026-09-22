Implement `/app/delegate.py::delegate`: reject limits below one, delegate at most `limit` tasks, preserve input order, and return exceptions as `{'error': message}` without cancelling siblings.
