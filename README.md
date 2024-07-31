# extremexp-prototype
## System Architecture

The prototype is designed as a multi-server communication system, where users interact with the main application, which is hosted and executed by the **web_app server**.

Currently, **SQLite** functions as the database linked to the web_app server, handling user login information, datasets uploaded by users, and intent predictions received from the LLM server.

The **llm server** is accessed by the main app, which sends user-inputted text for processing. This text is classified by a specific LLM into an analytical intent, which is then presented to the user within the main app.

The **read-write-graphdb server** manages storage and retrieval of information from the **GraphDB**, which maintains the knowledge base.

Finally, the **automl server** processes requests from the main app, including the working dataset, intent predictions, and ML pipeline constraints. Based on this information, it generates ML pipelines using tools like TPOT or Hyperopt and returns the results to the main app.

![System Components](static/system-components.png)

## Project Setup

### Set up your virtual environment
 ```bash
  pip install virtualenv
  python3.11 -m venv prototype
  source prototype/bin/activate
```
### Install and Configure GraphDB
- Refer to https://graphdb.ontotext.com/documentation/10.7/how-to-install-graphdb.html for installation instructions.
- Once you install GraphDB, set the port to **8080** for the GraphDB instance.
- Start GraphDB server.

### Populate GraphDB repository with the KnowledgeBase.nt
- Install requests library :
```bash
pip install requests
```
- Create GraphDB repository (Default name is test-repo. Refer to the create_graphdb_repository.py to change settings):
```bash
python read-write-graphdb/utils/create_graphdb_repository.py
```
- Load data into created repository (local file path to GraphDB server directory is required):
```bash
python read-write-graphdb/utils/import_file_to_graphdb_repository.py <$user.home/graphdb-import/>
```

### Store your API keys
Make sure you have ```.env``` file in the **llm folder** with your API keys stored.
  ```
  OPENAI_API_KEY=<YOUR OPENAI_API_KEY>
  LlamaAPI_KEY=<LlamaAPI_KEY>
  ```
For more information on how to obtain API Keys, refer to : [OpenAI](https://platform.openai.com/docs/quickstart) and [LLama AI](https://docs.llama-api.com/api-token).


### Install OpenMP Library
  ```
brew install libomp
  ```

### Start servers
```bash
chmod +x start_servers.sh
./start_servers.sh
```
The **start_servers.sh** script will automatically install the necessary requirements and start the following servers:
- web_app
- llm
- read-write-graphdb
- automl

For detailed information about the API routes and functionality for each server, please refer to the specific **Markdown documentation** files located in their respective folders.

(**optional**) You can also **start one server at a time**, installing the necessary packages and running the main script.

As an example, the following commands will start llm server.
```bash
python3.11 -m pip install -r llm/requirements.txt
python3.11 llm/api_llm_interaction.py
```
### Navigate to the Main Application (web_app)
   In order to engage with application you should navigate your web browser to
`http://localhost:8000` or you can use `curl`.

```bash
curl -X GET http://localhost:8000
```bash

## Usage Guide
[[Watch Video]](https://drive.google.com/file/d/1hEKr7KGFvUbbweNEbMF8r9jD_QV_9tU4/view?usp=sharing)

