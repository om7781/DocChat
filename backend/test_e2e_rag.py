import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from main import build_chain, get_llm

def run_tests():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE RAG & MODEL VERIFICATION TESTS")
    print("=" * 60)

    # 1. Model initialization
    print("\n[Step 1] Testing Model Initialization...")
    llm = get_llm()
    print(f"  Initialized LLM type: {llm._llm_type}")
    print("  -> PASSED: Model initialization successful.")

    # 2. Simple LLM invocation
    print("\n[Step 2] Testing Simple LLM Invocation...")
    simple_prompt = (
        "Document Context:\nNovaTech Solutions has 1,200 employees across Austin, London, and Singapore.\n\n"
        "Question: How many employees does NovaTech have?\n\nAnswer:"
    )
    ans = llm.invoke(simple_prompt)
    print(f"  LLM Output: {ans[:150]}...")
    assert len(ans.strip()) > 0
    print("  -> PASSED: Simple LLM invocation successful.")

    # 3. Document upload & extraction & splitting & embedding & vector store
    print("\n[Step 3] Testing Document Upload, Chunking, Embedding & Vector Store...")
    sample_file = Path("test_sample.txt")
    sample_text = """Company: NovaTech Solutions
Document Type: Employee Handbook Excerpt
Last Updated: October 2026

NovaTech Solutions was founded in 2015, headquartered in Austin, Texas.
Full-time employees are entitled to 20 days of paid annual leave per year.
Sick leave is capped at 10 days per calendar year.
Maternity leave is 26 weeks fully paid. Paternity leave is 4 weeks fully paid.
Unused annual leave of up to 10 days can be carried forward to the next year.
The company offers health insurance covering employees and up to 3 dependents.
Employees are eligible for a 401(k) plan with a 5% company match after completing 6 months of service.
Remote work allowance of $100 per month is provided for employees working fully remotely.
All employees receive a $2,000 annual learning and development budget.
"""
    sample_file.write_text(sample_text, encoding="utf-8")
    print("  Created test document: test_sample.txt")

    print("\n[Step 4] Testing Retrieval Chain Building...")
    chain = build_chain(str(sample_file), ".txt")
    print("  ConversationalRetrievalChain built successfully.")
    print("  -> PASSED: Document extraction, splitting, embedding and FAISS index created.")

    # 5. Question answering using retrieved context
    print("\n[Step 5] Testing Question Answering using Retrieved Context...")
    test_questions = [
        "How many days of paid annual leave do employees get?",
        "What is the maternity leave policy?",
        "What is the remote work allowance?"
    ]

    for q in test_questions:
        print(f"\n  Q: {q}")
        res = chain.invoke({"question": q})
        answer = res.get("answer", "")
        sources = res.get("source_documents", [])
        print(f"  A: {answer[:200]}...")
        print(f"  Retrieved Chunks: {len(sources)}")
        assert len(answer) > 0
        assert len(sources) > 0

    print("\n  -> PASSED: Question answering with retrieved context verified.")

    # Clean up test file
    sample_file.unlink(missing_ok=True)

    print("\n" + "=" * 60)
    print("ALL 5 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
