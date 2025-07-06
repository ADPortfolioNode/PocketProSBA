class FileAgent:
    def __init__(self):
        pass
    
    def handle_message(self, message):
        return {"response": "File agent response"}
    
    def list_files(self):
        return {"files": []}
    
    def upload_file(self, file):
        return {"success": True, "filename": file.filename if hasattr(file, 'filename') else 'unknown'}
