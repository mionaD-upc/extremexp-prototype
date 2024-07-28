import shutil
import os
import requests
import json

# GraphDB REST API
## https://graphdb.ontotext.com/documentation/10.1/using-the-graphdb-rest-api.html

def import_server_files(source_file, destination_directory, base_url, repo_id):
    os.makedirs(destination_directory, exist_ok=True)
    
    filename = os.path.basename(source_file)
    destination_path = os.path.join(destination_directory, filename)
    shutil.copy(source_file, destination_path)
    
    print(f"File '{filename}' copied to server directory '{destination_directory}'.")
    
    # Prepare the data for POST request
    data_url = filename  # Assuming filename is sufficient if server can directly access it
    payload = {
        "fileNames": [data_url]
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    # Make POST request to import files to repository
    url = f"{base_url}/rest/repositories/{repo_id}/import/server"
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 202:
        print(f"File '{filename}' imported to repository {repo_id} successfully.")
    else:
        print(f"Failed to import files to repository {repo_id}. Status Code: {response.status_code}, Error: {response.text}")

# Example usage:
if __name__ == "__main__":
    source_file = "/Users/miona.dimic/Desktop/Project_IntentDetect/prototype/pro/graphdb-import/KnowledgeBase.nt"
    destination_directory = "/Users/miona.dimic/graphdb-import"
    base_url = "http://localhost:8080"
    repo_id = "test-repo"
    
    import_server_files(source_file, destination_directory, base_url, repo_id)
