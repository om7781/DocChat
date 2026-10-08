import os
from typing import Any, List, Optional
from pydantic import Field
from dotenv import load_dotenv
from langchain_core.language_models.llms import LLM
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

load_dotenv()
token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")

class HuggingFaceChatLLM(LLM):
    """
    LangChain LLM wrapper for Hugging Face chat completion models.
    Uses InferenceClient with provider="auto" so Hugging Face automatically
    routes to a supported live provider (such as Novita, SambaNova, etc.).
    """
    model_id: str = Field(default="meta-llama/Llama-3.1-8B-Instruct")
    provider: str = Field(default="auto")
    api_token: str = Field(default="")
    max_new_tokens: int = Field(default=512)
    temperature: float = Field(default=0.3)

    @property
    def _llm_type(self) -> str:
        return "huggingface_chat_llm"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        client = InferenceClient(provider=self.provider, token=self.api_token)
        try:
            response = client.chat_completion(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_new_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content
        except HfHubHTTPError as e:
            err_str = str(e)
            if "402" in err_str or "Payment Required" in err_str:
                # User's Hugging Face account has 0 remaining inference credits
                fallback_answer = self._extract_context_answer(prompt)
                return (
                    f"[Hugging Face Notice: Monthly inference credits exhausted on this account]\n\n"
                    f"**Answer based on document context:**\n{fallback_answer}"
                )
            raise e

    def _extract_context_answer(self, prompt: str) -> str:
        """Extract relevant sentences from document context when remote quota is 0."""
        if "Document Context:" in prompt and "Question:" in prompt:
            parts = prompt.split("Document Context:")
            if len(parts) > 1:
                ctx_and_q = parts[1].split("Question:")
                context = ctx_and_q[0].strip()
                question = ctx_and_q[1].split("Answer:")[0].strip() if len(ctx_and_q) > 1 else ""
                
                # Find most relevant lines matching question words
                q_words = set(w.lower() for w in question.split() if len(w) > 3)
                lines = [l.strip() for l in context.split("\n") if l.strip()]
                scored = []
                for line in lines:
                    score = sum(1 for w in q_words if w in line.lower())
                    if score > 0:
                        scored.append((score, line))
                if scored:
                    scored.sort(key=lambda x: x[0], reverse=True)
                    return "\n".join(item[1] for item in scored[:3])
                return context[:500]
        return "Information found in document."

if __name__ == "__main__":
    print("Testing HuggingFaceChatLLM...")
    llm = HuggingFaceChatLLM(api_token=token)
    print(f"Model ID: {llm.model_id}")
    print(f"Provider: {llm.provider}")
    test_prompt = (
        "Document Context:\nNovaTech Solutions was founded in 2015 in Austin, Texas. "
        "It employs over 1,200 people.\n\n"
        "Question: When was NovaTech founded?\n\nAnswer:"
    )
    ans = llm.invoke(test_prompt)
    print("\nLLM Response:\n" + ans)
    print("\nStandalone LLM test completed successfully!")
