import json
import yaml
import pandas as pd
from typing import List
from langchain_core.documents.base import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def load_vector_store(path):
    return FAISS.load_local(path, OpenAIEmbeddings(model="text-embedding-3-small"), allow_dangerous_deserialization=True)

def save_vector_store(vector_store, path):
    vector_store.save_local(path)

def load_config(yaml_path):
    with open(yaml_path, "r") as stream:
        return yaml.safe_load(stream) or {}

def save_progress(last_index, filename="progress.json"):
    with open(filename, "w") as f:
        json.dump({"last_index": last_index}, f)

def load_progress(filename="progress.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f).get("last_index", 0)
    except FileNotFoundError:
        return 0

def create_documents(df, start_idx, end_idx) -> List[Document]:
    documents = []
    for i in range(start_idx, min(end_idx, len(df))):
        metadata = {"asin": df['asin'][i]}
        for j in range(1, 6):  # Bullet points 1 to 5
            metadata[f'bullet_point{j}'] = df.get(f'bullet_point{j}', {}).get(i, "")
        metadata['product_title'] = df['item_name'][i]
        metadata['question_text'] = df['question_text'][i]
        metadata['answers'] = df['answers'][i]
        
        doc2 = Document(page_content=df['product_description'][i], id=df.iloc[i]['question_id'], metadata=metadata)
        metadata['product_description'] = df['product_description'][i]
        metadata.pop('question_text')
        doc1 = Document(page_content=df['question_text'][i], id=df.iloc[i]['question_id'], metadata=metadata)
        documents.append((doc1, doc2))
    return documents

def create_vector_store(config, batch_size=1000):
    config = config['data']
    with open(config['full_pqa'], 'r') as f:
        df = pd.DataFrame([json.loads(line) for line in f])
    
    last_index = load_progress()
    total_len = len(df)
    print(f"Starting from index: {last_index}/{total_len}")
    
    if last_index == 0:
        q_db = FAISS.from_documents([Document('...')], OpenAIEmbeddings(model="text-embedding-3-small"))
        d_db = FAISS.from_documents([Document('...')], OpenAIEmbeddings(model="text-embedding-3-small"))
    else:
        q_db = FAISS.load_local("data/q_faiss_index", OpenAIEmbeddings(model="text-embedding-3-small"), allow_dangerous_deserialization=True)
        d_db = FAISS.load_local("data/d_faiss_index", OpenAIEmbeddings(model="text-embedding-3-small"), allow_dangerous_deserialization=True)
    
    batch_end = min(last_index + batch_size, total_len)
    if last_index < total_len:
        docs = create_documents(df, last_index, batch_end)
        
        q_docs = [d[0] for d in docs]
        d_docs = [d[1] for d in docs]
        
        q_db.add_documents(q_docs)
        d_db.add_documents(d_docs)
        
        q_db.save_local("data/q_faiss_index")
        d_db.save_local("data/d_faiss_index")
        
        save_progress(batch_end)
        print(f"Processed up to index: {batch_end}/{total_len}")

def main():
    config = load_config('path_config.yaml')
    create_vector_store(config, batch_size=7604)  # Chia nhỏ mỗi lần xử lý 1000 dòng

if __name__ == "__main__":
    main()
