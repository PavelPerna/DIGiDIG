"""Run this model in Python

> pip install openai
"""
import os
from openai import OpenAI

# To authenticate with the model you will need to generate a personal access token (PAT) in your GitHub settings.
# Create your PAT token by following instructions here: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
client = OpenAI(api_key=os.environ["OPENAI_API_TOKEN"]) 

messages = [
    {
        "role": "developer",
        "content": "Reliable bussiness partner, general director of DIGiDIG company",
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Indroduce yourself",
            },
        ],
    },
]

while True:
    response = client.chat.completions.create(
        messages = messages,
        model = "gpt-5",
        max_completion_tokens = 8192,
        reasoning_effort = "high",
    )

    if response.choices[0].message.tool_calls:
        print(response.choices[0].message.tool_calls)
        messages.append(response.choices[0].message)
        for tool_call in response.choices[0].message.tool_calls:
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": [
                    {
                        "type": "text",
                        "text": locals()[tool_call.function.name](),
                    },
                ],
            })
    else:
        print("[Model Response] " + response.choices[0].message.content)
        break
