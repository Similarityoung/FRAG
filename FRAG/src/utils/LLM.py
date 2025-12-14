from langchain_community.llms.ollama import Ollama
from config import reasoning_model, commercial_models, ollama_models
import config
from langchain_openai import OpenAI
from langchain_community.llms.moonshot import Moonshot


class LLM:
    def __init__(self, model: str = None):
        if model is None:
            model = str(reasoning_model)
        self.model = model
        
        if model in ollama_models:
            self.llm = Ollama(
                model=model,
                temperature=config.temperature,
                num_predict=config.max_tokens
            )

        elif model in commercial_models:
            if model.startswith("gpt"):
                self.llm = OpenAI(model_name=model, temperature=0)
            else:
                self.llm = Moonshot(model_name=model, temperature=0)

        else:
            raise ValueError(f"Model '{model}' not supported. Available models: {ollama_models + commercial_models}")

    def batch_invoke(self, queries):
        answers = [self.llm.invoke(query) for query in queries]
        return answers

    def invoke(self, query):
        answer = self.llm.invoke(query)
        return answer


if __name__ == "__main__":
    llm = LLM(model="llama3")

    answer = llm.invoke("Tell me a joke")
    print(answer)
