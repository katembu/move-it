from generator import Generator

class HTMLGenerator(Generator):
    def start_document(self):
        self.handle.write('Start')

    def self.render_contents(self):
        self.handle.write('Middle')

    def end_document(self):
        self.handle.write('End')

        
