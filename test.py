import google.generativeai as genai, os
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
print([m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods][:5])