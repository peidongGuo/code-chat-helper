import openai
import os

# Set up OpenAI API client
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Get the test results
with open("test_results.txt", "r") as f:
    lines = f.readlines()
    test_results = ''.join(lines)

# Split test_results using empty lines as separators
test_cases = test_results.split("\n\n")

# Combine test cases until the token limit is reached
combined_test_cases = []
current_batch = ""
for test_case in test_cases:
    if len(current_batch + test_case) < 3300:
        current_batch += test_case + "\n\n"
    else:
        combined_test_cases.append(current_batch.strip())
        current_batch = test_case + "\n\n"
combined_test_cases.append(current_batch.strip())

# Initialize an empty list to store the analysis results
analysis_results = []

# Create a prompt for GPT and analyze each batch of test cases
for i, batch in enumerate(combined_test_cases):
    if not batch.strip():
        continue

    print(f"Batch {i + 1}: \n{batch}")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that specialized in analyzing software test results."},
        {"role": "user",
            "content": f"Please provide a detailed analysis of the following batch of test results (Batch {i + 1}): \n\n{batch}\n\nPlease include:\n1. A summary of the overall test results\n2. A list of failed test cases, if any\n3. Possible causes for the failures"}
    ]

    # Call the OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=400,
        temperature=0.5,
    )

    # Get the analysis text
    analysis_text = response.choices[0]['message']['content'].strip()

    print(analysis_text)

    # Add the analysis text to the analysis_results list
    analysis_results.append(analysis_text)

# Join the analysis results
final_analysis = "\n".join(analysis_results)

# Print the final analysis text to the console
print("GPT Test Analysis:")
print(final_analysis)
