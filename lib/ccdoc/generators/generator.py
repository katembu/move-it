import tempfile

class NotRenderedError(Exception):
    pass

class Generator(object):
    def __init__(self, title, subtitle, contents):
        self.handle = tempfile.NamedTemporaryFile()

        self.title = title
        self.subtitle = subtitle
        self.contents = contents
        self.rendered = False

    def render_document(self):
        self.start_document()
        self.render_contents()
        self.end_document()
        self.rendered = True

    def get_filename(self):
        if not self.rendered:
            raise NotRenderedError("Document not yet rendered")
        return self.handle.name

    def get_contents(self):
        if not self.rendered:
            raise NotRenderedError("Document not yet rendered")
        self.handle.rewind()
        return self.handle.read()

    def destroy_file(self):
        return self.handle.close()

    def start_document(self):
        pass

    def self.render_contents(self):
        pass

    def end_document(self):
        pass

        
