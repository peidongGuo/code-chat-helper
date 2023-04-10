import openai
import time

openai.api_key = "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"


def tokens_of_string(s):
    return len(s.split())


def program_a(input_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": input_text},
        ],
        max_tokens=300,
        n=1,
        temperature=0.8,
    )
    return response.choices[0].message['content'].strip()


def program_b(input_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": input_text},
        ],
        max_tokens=300,
        n=1,
        temperature=0.8,
    )
    return response.choices[0].message['content'].strip()


def truncate_history(history, max_tokens):
    while tokens_of_string(history) > max_tokens:
        history = history.split('\n', 2)[-1]
    return history


initial_prompt = "你好！我是个AI。"
turns = 50
max_history_tokens = 4096 - 500  # GPT-3.5-turbo的最大token限制减去预留的回应token数量和统计误差

current_prompt = initial_prompt
for i in range(turns):
    if i % 2 == 0:
        response = program_a(current_prompt)
        print(f"AI A: {response}")
    else:
        response = program_b(current_prompt)
        print(f"AI B: {response}")

    current_prompt += f"\n{response}"
    current_prompt = truncate_history(current_prompt, max_history_tokens)
    time.sleep(1)
