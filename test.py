# import nltk
# import os

# os.environ['NLTK_DATA'] = 'C:/Users/Hi/AppData/Roaming/nltk_data'

# nltk.download('punkt')
# nltk.download('punkt_tab')

# from nltk.tokenize import word_tokenize
# sample_text = "This is a test sentence."
# tokens = word_tokenize(sample_text)
# print(tokens)


from gpt4all import GPT4All

# llm = GPT4All(model_name="DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf")
llm = GPT4All(model_name="DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf")

# import os
# from llama_index.core import ServiceContext, VectorStoreIndex, StorageContext
# from llama_index.core.node_parser import SentenceWindowNodeParser
# from llama_index.core.indices.postprocessor import MetadataReplacementPostProcessor
# from llama_index.core.indices.postprocessor import SentenceTransformerRerank
# from llama_index.core import load_index_from_storage
# # Instead of GPT4All, we're using Ollama:
# from llama_index.llms.ollama import Ollama
# from llama_index.core import Settings
# # Using OpenAI embeddings as an example for sentence transformers
# from llama_index.embeddings.openai import OpenAIEmbedding

# Set up the Ollama LLM to load the DeepSeek‑R1 model.
# Make sure your local Ollama server is running and that it supports "deepseek-r1".
# llm = Ollama(model="deepseek-r1", request_timeout=120.0)


prompt = "Answer this question: What is the financial capital of India?\nAnswer:"
answer = llm.generate(prompt, max_tokens=150)

print("Answer: ", answer)