import re
from pydantic import BaseModel, Field
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.extractors import BaseExtractor
from llama_index.llms.ollama import Ollama
from llama_index.core.ingestion import IngestionPipeline

# ---------------------------------------------------------
# 1. Clean the Markdown Text
# ---------------------------------------------------------
def clean_markdown(md_text: str) -> str:
    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', md_text)
    # Example: Remove NCERT recurring page footers/watermarks if they exist in your MD
    # text = re.sub(r'Rationalised 2023-24.*?\n', '', text, flags=re.IGNORECASE)
    # text = re.sub(r'Chapter \d+ Exercises.*?(?=#|\Z)', '', text, flags=re.DOTALL)
    
    return text.strip()

# Read your parsed markdown file
with open("ncert_chapter.md", "r", encoding="utf-8") as f:
    raw_md = f.read()

cleaned_text = clean_markdown(raw_md)
document = Document(text=cleaned_text)

# ---------------------------------------------------------
# 2. Define the Metadata Schema
# ---------------------------------------------------------
class NCERTMetadata(BaseModel):
    chapter_name: str = Field(description="The main chapter name this text belongs to.")
    topic: str = Field(description="The primary topic being discussed.")
    subtopic: str = Field(description="The specific subtopic or concept.")
    image_referenced: bool = Field(description="True if an image like ![alt](path) is in the text.")

# ---------------------------------------------------------
# 3. Custom Metadata Extractor using Ollama
# ---------------------------------------------------------
class LocalOllamaExtractor(BaseExtractor):
    def __init__(self, llm):
        self.llm = llm
        super().__init__()

    async def aextract(self, nodes):
        for node in nodes:
            # We use the LLM to structure the output as JSON matching our Pydantic model
            prompt = (
                f"Analyze this textbook section and extract the chapter name, topic, and subtopic.\n"
                f"Text: {node.text[:1000]}...\n\n"
                f"Return ONLY valid JSON matching this schema: "
                f"{{'chapter_name': '...', 'topic': '...', 'subtopic': '...', 'image_referenced': true/false}}"
            )
            
            # Call local Ollama
            response = self.llm.complete(prompt)
            
            try:
                # Basic string cleaning to grab the JSON dictionary from the LLM output
                import json
                json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
                metadata_dict = json.loads(json_str)
                
                # Inject the LLM's findings into the node's metadata
                node.metadata.update(metadata_dict)
            except Exception as e:
                print(f"Failed to parse LLM JSON for a node: {e}")
                
        return nodes

# ---------------------------------------------------------
# 4. Run the Pipeline
# ---------------------------------------------------------
# Assuming Ollama is running and you pulled a model like Qwen2.5 (ollama run qwen2.5)
llm = Ollama(model="qwen2.5", request_timeout=120.0)

# The Markdown parser respects the # and ## headers for logical chunks
node_parser = MarkdownNodeParser()
metadata_extractor = LocalOllamaExtractor(llm=llm)

# The pipeline processes the document sequentially
pipeline = IngestionPipeline(
    transformations=[
        node_parser,
        metadata_extractor
    ]
)

print("Running chunking and metadata extraction via local LLM...")
nodes = pipeline.run(documents=[document])

# Verify the output
for idx, node in enumerate(nodes[:3]):
    print(f"\n--- Node {idx+1} ---")
    print(f"Metadata: {node.metadata}")
    print(f"Text Snippet: {node.text[:100]}...\n")