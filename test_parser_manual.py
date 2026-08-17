from orchestration import OrchestrationService

service = OrchestrationService()

queries = [
    "What is V Kohli's batting average?",
    "What is Virat Kohli's strike rate?",
    "How has Virat Kohli performed against Jasprit Bumrah?",
    "Kohli vs Bumrah",
]

for q in queries:
    print("=" * 80)
    print("QUESTION:", q)

    try:
        response = service.ask(q)
        print("SUCCESS:", response.success)
        print("ANSWER:", response.answer)
    except Exception as e:
        print("ERROR:", type(e).__name__)
        print("MESSAGE:", e)