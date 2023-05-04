import os
import hmac
import hashlib
import openai
from flask import Flask, request, abort
from github import Github

app = Flask(__name__)

# Set up OpenAI API client
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Set up GitHub API client
gh = Github(os.environ.get("GITHUB_TOKEN"))

# Set up webhook secret
webhook_secret = os.environ.get("WEBHOOK_SECRET")


def validate_signature(request):
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        return False

    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        return False

    mac = hmac.new(webhook_secret.encode(), msg=request.data,
                   digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)


@app.route('/review_pr', methods=['POST'])
def review_pr():
    if not validate_signature(request):
        abort(401, 'Invalid signature')

    event = request.get_json()

    if event['action'] not in ['opened', 'synchronize', 'reopened']:
        return 'Ignoring non-PR opening/synchronize/reopening events', 200

    pr = event['pull_request']
    repo = event['repository']

    # Get the code changes from the PR
    gh_repo = gh.get_repo(repo['full_name'])
    gh_pr = gh_repo.get_pull(pr['number'])
    code_changes = gh_pr.get_files()

    # Concatenate the changes into a single string
    changes_str = "Title: " + gh_pr.title + "\n"
    if gh_pr.body is not None:
        changes_str += "Body: " + gh_pr.body + "\n"
    for change in code_changes:
        changes_str += f"File: {change.filename}\nPatch:\n{change.patch}\n\n"

    # Call GPT to get the review result
    messages = [
    {
        "role": "system",
        "content": "As an AI assistant with programming expertise, you are a meticulous code reviewer."},
    {"role": "user",
        "content": f"Review the following pull request:\n{changes_str}\n\nThe '+' means the line is added, and the '-' means the line is removed. Please provide a review result for the PR."}
]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=600,
        temperature=0.5,
        n=5,
    )

    reviews = [
    f"Review {i+1}:\n{response.choices[i]['message']['content'].strip()}\n" for i in range(len(response.choices))]

    # Combine the reviews into a single string
    reviews_str = "\n".join(reviews)

    # Call GPT to generate the summary of the reviews
    summary_messages = [
        {"role": "system",
        "content": f"Here are some review results for reference:\n{reviews_str}"},
        {"role": "user",
         "content":"These reviews results are merely surface-level. Please remeber you are an expert, provide a more detailed review result."},
        {"role": "user",
         "content": "NOTE THAT YOU ARE AN EXPERT. Please summarize the review results. Ensure that the output follows the template:'\n\n**[Changes]**\n\n**[Suggestions]**\n\n**[Conclusion]**\n\n**[Action]**\n\n**[Other]**\n\n'."},
    ]

    summary_response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=summary_messages,
    max_tokens=600,
    temperature=0.5,
    n=1
    )

    final_review = f"""**[AI Review]** This comment is generated by an AI model (gpt-3.5-turbo).\n\n{summary_response.choices[0]['message']['content'].strip()}\n
    **[Note]** 
    The above AI review results are for reference only, please rely on human expert review results for the final conclusion.
    Usually, AI is better at enhancing the quality of code snippets. However, it's essential for human experts to pay close attention to whether the modifications meet the overall requirements. Providing detailed information in the PR description helps the AI generate more specific and useful review results.\n\n"""

    translate_messages = [
    {"role": "user",
     "content": f"将下面内容翻译为中文{final_review}"
     }
]
    translated_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=translate_messages,
        max_tokens=2000,
        temperature=0.8,
        n=1
    )

    # Post the GPT result as a PR comment
    gh_pr.create_issue_comment(translated_response.choices[0]['message']['content'].strip())

    return 'Review submitted', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
