
############################################
# region os env
import os
with open('.env', 'r') as f:
    for line in f:
        try:
            key, value = line.strip().split('=')
            os.environ[key] = value
        except:
            break
# endregion

############################################
# region LLM config
ollama_models = [
    "llama2:7b-chat-q5_K_M",
    "llama3:70b-instruct-q5_K_M",
    "llama3:8b-instruct-q5_K_M",
    "llama2:70b-chat-q5_K_M"
]

commercial_models = [
    "gpt-3.5-turbo-0125",
    "gpt-4o-mini-2024-07-18",
]

reasoning_model = "llama3:8b-instruct-q5_K_M"
hop_pred_model = reasoning_model
max_reasoning_paths = 64
temperature = 0.01
max_tokens = 256
stop_tokens = ["\n", "<|eot_id|>", "</s>"]
# endregion

############################################
# region Datasets config
supported_datasets = ["CWQ", "webqsp",]

reasoning_dataset = "CWQ"
reasoning_type = "PPR2"  # PPR4
experiment_type = "MainExperiment"

dataset_dir = f"/back-up/gzy/dataset/AAAI/{experiment_type}/{reasoning_dataset}/{reasoning_type}/"
test_file = dataset_dir + "test_name.jsonl"
# endregion

############################################
# region SentenceModel config
emb_model_dir = "sentence-transformers/all-MiniLM-L6-v2"
rerank_model_dir = "BAAI/bge-reranker-v2-m3"

# endregion

############################################
# region Evaluation config
hr_top_k = 10
# endregion
