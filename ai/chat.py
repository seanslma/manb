# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

import os
import json
import openai

# +
userpath = os.path.expanduser( '~' )
filepath = f'{userpath}/.config/chat.json'
with open(filepath, 'r') as f:
    api_key = json.load(f)['dev']
openai.api_key  = api_key

def get_ai_response(prompt, model='gpt-3.5-turbo', temperature=0):
    messages = [{'role': 'user', 'content': prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message['content']


# -

get_ai_response('hello')
