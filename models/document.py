class Document:
    def __init__(self, name: str, path: str, pages: list):
        self.name = name
        self.path = path
        self.pages = pages

    def __repr__(self):
        return f"Document(name={self.name}, path={self.path}, pages={self.pages})"
