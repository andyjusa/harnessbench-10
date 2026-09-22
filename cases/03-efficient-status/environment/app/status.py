import os

def status():
    return {"files": sum(len(files) for _, _, files in os.walk("."))}
