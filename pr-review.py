import os
import openai
from flask import Flask, request
from github import Github

app = Flask(__name__)

# Set up OpenAI API client
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Set up GitHub API client
gh = Github(os.environ.get("GITHUB_TOKEN"))


@app.route('/review_pr', methods=['POST'])
def review_pr():
    event = request.get_json()

    if event['action'] not in ['opened', 'synchronize', 'reopened']:
        return 'Ignoring non-PR opening/synchronize/reopening events', 200

    pr = event['pull_request']
    repo = event['repository']

    # Call GPT to get the review result
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can review pull requests."},
        {"role": "user",
            "content": f"Review the following Pull Request: {pr['title']} - {pr['body']}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=100,
        temperature=0.5,
    )

    review = response.choices[0]['message']['content'].strip()

    # Post the GPT result as a PR comment
    gh_repo = gh.get_repo(repo['full_name'])
    gh_pr = gh_repo.get_pull(pr['number'])
    gh_pr.create_issue_comment(review)

    return 'Review submitted', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
