#!/usr/bin/env python
# coding: utf-8

# IMPORTS AND LLM INITIALIZATION

# In[ ]:


import os
import json
import gradio as gr # type: ignore
from gradio_pdf import PDF # type: ignore
from langchain_ollama import OllamaLLM, OllamaEmbeddings # type: ignore
from langchain_community.document_loaders import PyPDFLoader # type: ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
from langchain.chains import RetrievalQA # type: ignore
from langchain.memory import ConversationBufferMemory # type: ignore
from langchain_community.vectorstores import Chroma # type: ignore
from langchain.prompts import PromptTemplate # type: ignore

CHATS_DIR = "./chats"
#defines a directory to store chat history
os.makedirs(CHATS_DIR, exist_ok=True)

LLM_MODEL = "deepseek-r1:1.5b"
EMBED_MODEL = "granite-embedding:278m"

llm = OllamaLLM(model=LLM_MODEL, temperature=0.5)
embeddings = OllamaEmbeddings(model=EMBED_MODEL)


# LOADING PREVIOUS CHAT=> chat_dict -> checking everything in os.listdir(chats_dir) -> if ends with .json -> remove the .json and store in chat_id -> open the file as read only with open(chats_dir, filename) and store it in f -> json.load(f) and put it in data -> for chat[chat_id] = data put that data in and return the chats, create a flow diagram image for this please

# In[82]:


def load_chats():
    chat = {}
    #for every filename in listdir with CHATS_DIR
    for filename in os.listdir(CHATS_DIR):
        #if filename ends with .json, load the file and add it to chat dictionary
        if filename.endswith(".json"):
            #this remove the .json extension to use as chat_id
            chat_id = filename[:-5]
            #os.path.join combine the ./chats/chat_id.json and opens it as read only and
            #assigns it variable f 
            with open(os.path.join(CHATS_DIR, filename), 'r') as f:
                #loads the json file and assigns it into a python dictionary
                data = json.load(f)
            #adds the chat_id as key and data as value to the chat dictionary    
            chat[chat_id] = data
    return chat
#loading the chats on to the variable and making it available for the UI
chats = load_chats()


# Create New CHAT => flow  -> create a new chat_id by taking length +1 , Building a path using os.path.join(chats_dir, chatid) -> creating the path to to store using os.makedirs(chat_dir, exist_ok = True) -> then creating the chat with the id -> save_chat function returns chat_id

# In[83]:


def create_new_chat(chat_name = "New Chat"):
    #creating a new chat id by checking the length of existing chats +1
    chat_id = f"chat_{len(chats) + 1}"
    #Building a full path for a new sub-directory
    #chroma needs a unique folder for each chat 
    chat_dir = os.path.join(CHATS_DIR, chat_id)
    # creating a path with the chat_dir
    os.makedirs(chat_dir, exist_ok=True)
    #creating a new chat with the chat_id and chat_name
    chats[chat_id] = {
        "name":chat_name,
        "history": [],
        "vector_dir":chat_dir,
        "pdf_path":None,
        "memory": ConversationBufferMemory()
    }

    save_chat(chat_id)
    return chat_id



# SAVE_CHAT -> create a copy of the chat -> remove memory -> open the path using os.path.join of chats dir and id json -> Dump the data in Json format 

# In[84]:


def save_chat(chat_id):
    #grab the chats dict from global
    #access the chat via id
    #copy it into data to make modification and then store/replace
    data = chats[chat_id].copy()
    #so in memory we might store ConversationBufferMemory/ConversationSummaryMemory etc
    # Now these are langchain objects not python objects so you will get an error
    # to fight this error you remove it 
    data.pop("memory", None)
    #Open a file for writing the data
    #Join the chat dir and id with w 
    #B
    with open(os.path.join(CHATS_DIR, f"{chat_id}.json"), "w") as f:
        json.dump(data, f)


# DELETE CHAT -> os.remove(path) -> remove from vector db using shutil.rmtree -> del chats[chat_id]

# In[85]:


import shutil
def delete_chat(chat_id): 
    #build the json file path and remove it with os.remove
    os.remove(os.path.join(CHATS_DIR, f"{chat_id}.json"))
    #deleles the entire vector directory using shutil.rmtree
    shutil.rmtree(chats[chat_id]["vector_dir"], ignore_errors=True)
    #deletes entry from the global chat dic
    del chats[chat_id]


# Document loading -> Splitting -> Embeddings and storage  and Updating the chat path to realise pdf for later use 

# In[86]:


def upload_document(chat_id, file_path):
    try:
    #this is document loader to extract text/pages
     loader = PyPDFLoader(file_path)
     #loads the pdf into a list of documents, each representing a page or chunk
     #using REcurvsiveTextSplitter to split the text 
     doc = loader.load_and_split(text_splitter= RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 50))
     # create a chroma vector store from the chunked docs. from_documents embeds each doc using 
     # use global embeddings in store vectors in chroma 
     # persist_directory points to the chat's vector directory
     vectorstore = Chroma.from_documents(doc, embeddings, persist_directory=chats[chat_id]['vector_dir'])
     #save the vector store to disk in the specified directory as done above
     vectorstore.persist()
     #Update thr global dict for this ID , setting "PDf_path" to the file path
     #so we can view this pdf later on
     chats[chat_id]["pdf_path"] = file_path
     #saved the chat to presist
     save_chat(chat_id)
    except Exception as e:
        return f"Error uploading: {str(e)}"


# SETUP RAG CHAIN -> Load vector store, create a retriever and recreaes and load the memory with past history , set a prompt template and build retrievalQA chain -> Chain + Memory

# In[87]:


def get_rag_chain(chat_id):
    #load the existing chroma vector store from the chat's saved directory, no re-embedding 
    vectorstore = Chroma(persist_directory=chats[chat_id]["vector_dir"], embedding_function=embeddings)
    #turn the vector store into a retriever  so it can search for relevant chunks 
    retriever = vectorstore.as_retriever()
    #Create a memory object 
    memory = ConversationBufferMemory()
    #starts a for loop over the chat history list , to replay the entire conversation history into memory
    for msg in chats[chat_id]["history"]:
        memory.save_context({"input":msg["user"]}, {"output":msg["bot"]})
    prompt = PromptTemplate(input_variables=["context", "question"],template="""
    You are **sav.in**, a helpful assistant. That also means your identity and name is **sav.in**
    if you are prompted a question about your identity like what is your name? or who are you? or who am 
    i talking to your answer should be my identity is sav.in                        

    🔍 Step 1: Read the context below and answer based **only** on that.
    If the answer cannot be found in the context, proceed to Step 2.

    Step 2: Answer from your general knowledge, but clearly indicate you're using that knowledge.

    ---

    📄 Context:
    {context}

    ❓ User Question:
    {question}

    ---

    💬 Answer as sav.in:
    """)
    chain = RetrievalQA.from_chain_type(llm = llm, chain_type = "stuff", retriever = retriever, memory = memory, return_source_documents = True)
    return chain,memory


# QUERY_CHAT =>. get the  chain by get_rag_chain => executive the chain by sending a query => store the result from results['results'] in response and sources = results['source_documents']  => Append the new response into chat history by chats[chat_id]["history"].append({"user": query, "bot": response}) => save chat in disk => get the highlight text = [doc.page_content for doc in sources]

# In[88]:


def query_chat(chat_id, query):
    #check if chat exists in chat and has a PDF uploaded 
    #prevent queries without a document 
    if chat_id not in chats or not chats[chat_id]['pdf_path']:
        #for UI to render
        return "Upload a document first."
    #sets up rag pipeline with loaded data/memory
    chain, memory = get_rag_chain(chat_id)
    #sending query into the retrievalqa chain and storing the result in result
    result = chain({"query": query})
    #extracts the LLM generated answer from result in response
    response = result["result"]
    #for highlights it will return a list of chunks to highlight in PDF
    sources = result['source_documents']
    #append the query and response to history to record it and store it in disk
    chats[chat_id]["history"].append({"user":query, "bot":response})
    #save the chat for updated history
    save_chat(chat_id)
    #for each doc in sources get the chunk text which will be present in page_content
    #Prepares the string for PDF search / Highlight
    highlight_texts = [doc.page_content for doc in sources]
    #return the response and highlight texts
    return response, highlight_texts


# In[89]:


def render_lottie():
    return """
    <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
    <lottie-player src="assets/survey.json" background="transparent" speed="1" style="width: 300px; height: 300px;" loop autoplay></lottie-player>
    """


# In[90]:


def render_lottie():
    return """
    <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
    <lottie-player src="assets/chat_lottie.json" background="transparent" speed="1" style="width: 300px; height: 300px;" loop autoplay></lottie-player>
    """

theme = gr.themes.Monochrome(
    primary_hue="blue",
    secondary_hue="purple",
    neutral_hue="slate",
).set(
    body_background_fill="linear-gradient(to bottom, #0F172A, #1E293B)",
    body_background_fill_dark="linear-gradient(to bottom, #0F172A, #1E293B)",
    button_primary_background_fill="linear-gradient(90deg, #1E3A8A, #6D28D9)",
    button_primary_background_fill_hover="linear-gradient(90deg, #1D4ED8, #5B21B6)",
    block_radius="*radius_xl",
)

custom_css = """
body { 
    background: repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.05) 10px, rgba(255,255,255,0.05) 20px);
    background-color: #0F172A;
    animation: twinkle 3s infinite alternate;
}
@keyframes twinkle { 0% { opacity: 0.8; } 100% { opacity: 1; } }
.file { border: 2px dashed #6D28D9; transition: all 0.3s; animation: fadeIn 0.5s; }
.file:hover { border: 2px solid #A855F7; box-shadow: 0 0 15px #6D28D9; animation: pulse 1s infinite; }
@keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
.chatbot, .pdf { box-shadow: 0 4px 8px rgba(0,0,0,0.2); border-radius: 15px; background: linear-gradient(to bottom, #1E293B, #0F172A); animation: fadeIn 0.5s; }
.column:first-child { background: linear-gradient(to right, #0F172A, #1E293B); }
"""

with gr.Blocks(title="Sav.in Document Query", theme=theme, css=custom_css) as app:
    gr.Markdown("# Sav.in Query Chatbot", elem_classes="cosmic-header")
    current_chat = gr.State(None)
    chats_list = gr.State(chats)
    with gr.Row():
        with gr.Column(scale=1):
            chat_dropdown = gr.Dropdown(label="Select Chat", choices=list(chats.keys()))
            new_chat_btn = gr.Button("Spawn New Chat")
            delete_btn = gr.Button("Erase and Delete Chat")
        with gr.Column(scale=4):
            welcome = gr.HTML(render_lottie() + "<h2 style='text-align: center; color: #A855F7;'>Ignite your first cosmic query</h2>", visible=len(chats) == 0)
            with gr.Row(visible=False) as chat_row:
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(height=400)
                    msg = gr.Textbox(label="Ask your query", interactive=False)
                    upload = gr.File(label="Drag PDF on Here", type="filepath", interactive=True)
                    clear = gr.Button("Reset Chat")
                    save_note_btn = gr.Button("Capture Response as Note")
                pdf_viewer = PDF(label="Document View", interactive=True, height=400)
            notes = gr.TextArea(label="Notes", visible=False)

    def update_chats():
        return gr.update(choices=list(chats.keys())), chats  # Fixed typo: .ley() -> .keys()

    new_chat_btn.click(create_new_chat, outputs=[chat_dropdown, chats_list]).then(update_chats, outputs=[chat_dropdown, chats_list])

    def select_chat(chat_id):
        #processes selection
        if not chat_id:
            #if no id then returns the updates : show welcome and hide chat row, disable input and clear
            return gr.update(visible=True), gr.update(visible=False), gr.update(interactive=False), None, None
        #set states to current chat 
        current_chat.value = chat_id
        #Builds list of user/bot interactions from history
        history = [[(item["user"], item["bot"]) for item in chats[chat_id]["history"]]]
        #gets saved pdf path, loadds into viewer
        pdf_path = chats[chat_id]["pdf_path"]
        #Activate cht Ui
        return gr.update(visible=False), gr.update(visible=True), gr.update(interactive=True), history, pdf_path
    #Triggers on selection
    chat_dropdown.change(select_chat, inputs=chat_dropdown, outputs=[welcome, chat_row, msg, chatbot, pdf_viewer])

    def add_message(history, message):
        #Updates display, and takes current history list and user message 
        history.append((message, None))
        return history, ""

    def bot_response(history, chat_id):
        #extracts user query for rag call
        query = history[-1][0]
        # Calls query function. gets answer and chunks 
        response, highlights = query_chat(chat_id, query)
        # replaces placeholder with response
        history[-1] = (query, response)
        # returns history, updates PDF search with joined highlight
        return history, gr.update(search_text="|".join(highlights))
    #chat interaction loop, binds submit to add message , input si current history and message 
    msg.submit(add_message, [chatbot, msg], [chatbot, msg]).then(bot_response, [chatbot, current_chat], [chatbot, pdf_viewer])
    #Binds change to upload document 
    upload.change(upload_document, [current_chat, upload], None)
    # deltes chat 
    delete_btn.click(delete_chat, chat_dropdown).then(update_chats, outputs=[chat_dropdown, chats_list])

    def save_note(history):
        if history:
            #Gets last bot response , why and what to save 
            last_resp = history[-1][1]
            #
            with open("notes.txt", "a") as f:
                f.write(last_resp + "\n\n")
            return "Echo captured!"

    save_note_btn.click(save_note, chatbot, notes)

    clear.click(lambda: [], None, chatbot)

app.launch(inline=True, share=False)

