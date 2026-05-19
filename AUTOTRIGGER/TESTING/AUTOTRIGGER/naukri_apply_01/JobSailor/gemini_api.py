"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""

import os

import google.generativeai as genai

genai.configure(api_key="add your api key here")

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 1000,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="remember all this when asked question you will answer from this data.\n"
                     "be concise only answer in max 5 words, average of 2 words, min of 1 word\n, "
                     "if it is a multi option question only give the index number of the answer",
)

chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": [
        "Use this example prompt and answer concisely."
      ],
    },
    {
      "role": "model",
      "parts": [
        "Understood. I will answer with short responses."
      ],
    },
  ]
)


def bard_flash_response(question) -> str:
    try:
      response = chat_session.send_message(question)
      return response.text
    except Exception as e:
      print(f"An error occurred: {e}")
      return 0

