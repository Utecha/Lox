class Writer:
    def __init__(self, output):
        self.output = output
        self.data = ""

    def add(self, data):
        self.data += str(data)

    def addln(self, data = ""):
        self.data += str(data) + '\n'

    def write(self):
        with open(self.output, "w+") as f:
            f.write(self.data)
