from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from rag_core import DocumentProcessor, VectorStoreManager, RAGQueryEngine

app = Flask(__name__)
CORS(app) 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_PATH = os.path.join(BASE_DIR, '..', 'storage')
processor = DocumentProcessor(storage_path=STORAGE_PATH)
vector_manager = VectorStoreManager(db_path=processor.db_path)
query_engine = RAGQueryEngine()

WEB_FOLDER = os.path.join(BASE_DIR, '..', 'web')

@app.route('/')
def index():
    return send_from_directory(WEB_FOLDER, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(WEB_FOLDER, path)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('file')
    results = []
    
    for file in files:
        if file.filename == '':
            continue
            
        try:
            metadata = processor.save_file(file)
            
            documents = processor.load_document(metadata['file_path'], metadata['file_type'])
            chunks = processor.process_documents(documents, metadata)
            vector_manager.add_documents(chunks)
            
            results.append({
                'filename': metadata['filename'],
                'status': 'success'
            })
        except Exception as e:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'message': str(e)
            })
            
    return jsonify({'results': results})

@app.route('/api/documents', methods=['GET'])
def list_documents():
    docs = processor.get_all_metadata()
    return jsonify(docs)

@app.route('/api/documents/<file_hash>', methods=['DELETE'])
def delete_document(file_hash):
    success = processor.delete_document(file_hash)
    if success:
        vector_manager.delete_by_source(file_hash)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'Document not found'}), 404

@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    query_text = data.get('query')
    selected_files = data.get('selected_files', [])
    
    if not query_text:
        return jsonify({'error': 'No query provided'}), 400
        
    filter_dict = None
    if selected_files:
        filter_dict = {"file_hash": {"$in": selected_files}}
    
    relevant_docs = vector_manager.search(
        query_text,
        k=5,
        filter_dict=filter_dict
    )
    
    response = query_engine.generate_response(query_text, relevant_docs)
    
    return jsonify(response)

if __name__ == '__main__':
    if not os.path.exists(WEB_FOLDER):
        os.makedirs(WEB_FOLDER, exist_ok=True)
        
    app.run(host='0.0.0.0', debug=False, port=5000)
