import os
import hmac
import hashlib
import openai
import logging
import json
import uuid
from functools import wraps
from flask import Flask, request, abort
from github import Github

app = Flask(__name__)


# Custom JSON formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "asctime": self.formatTime(record, self.datefmt),
            "levelname": record.levelname,
            "event_id": getattr(record, "event_id", "not set"),
            "repo": getattr(record, "repo", "not set"),
            "pr": getattr(record, "pr", "not set"),
            "message": record.getMessage(),
        }
        return json.dumps(log_entry)


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logHandler = logging.StreamHandler()
formatter = JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Set up OpenAI API client
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Set up GitHub API client
gh = Github(os.environ.get("GITHUB_TOKEN"))

# Set up webhook secret
webhook_secret = os.environ.get("WEBHOOK_SECRET")


def validate_signature(request):
    signature = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        return False

    sha_name, signature = signature.split("=")
    if sha_name != "sha256":
        return False

    mac = hmac.new(webhook_secret.encode(), msg=request.data, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)


def attach_event_id_and_repo_pr(func):
    # Generate an event_id and attach it with repo name and pr number to the log record
    @wraps(func)
    def wrapper(*args, **kwargs):
        event_id = str(uuid.uuid4())
        event = request.get_json()
        pr = event["pull_request"]
        repo = event["repository"]

        logger = logging.getLogger()
        old_factory = logger.makeRecord

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.event_id = event_id
            record.repo = repo['full_name']
            record.pr = pr['number']
            return record

        logger.makeRecord = record_factory
        try:
            return func(*args, **kwargs)
        finally:
            logger.makeRecord = old_factory

    return wrapper


@app.route("/review_pr", methods=["POST"])
@attach_event_id_and_repo_pr
def review_pr():
    logger.info("Received user request")
    if not validate_signature(request):
        abort(401, "Invalid signature")
    logger.info("Webhook signature validated")

    event = request.get_json()

    logger.info(f"Webhook event type: {event['action']}")

    if event["action"] not in ["opened", "synchronize", "reopened"]:
        return "Ignoring non-PR opening/synchronize/reopening events", 200

    pr = event["pull_request"]
    repo = event["repository"]

    try:
        # Get the code changes from the PR
        logger.info(
            f"Fetching PR details from GitHub repo {repo['full_name']} #{pr['number']}"
        )
        gh_repo = gh.get_repo(repo["full_name"])
        gh_pr = gh_repo.get_pull(pr["number"])
        code_changes = gh_pr.get_files()
    except Exception as e:
        logger.error(f"Error while fetching PR details from GitHub API: {e}")
        return "Error while fetching PR details from GitHub API", 500

    # Concatenate the changes into a single string
    logger.info("Preparing GPT request with code changes")
    changes_str = "Title: " + gh_pr.title + "\n"
    if gh_pr.body is not None:
        changes_str += "Body: " + gh_pr.body + "\n"
    for change in code_changes:
        changes_str += f"File: {change.filename}\nPatch:\n{change.patch}\n\n"

    try:
        # Call GPT to get the review result
        logger.info("Sending request to OpenAI API")
        messages = [
            {
                "role": "system",
                "content": 
"""
As an AI assistant with expertise in programming, your primary task is to review the pull request provided by the user. The code changes are presented in the standard `diff` format.

When generating your review, adhere to the following template:
**[Changes]**: Summarize the main changes made in the pull request in less than 50 words.
**[Suggestions]**: Provide any suggestions or improvements for the code. Focus on code quality, logic, potential bugs and performance problems. Refrain from mentioning document-related suggestions such as "I suggest adding some comments", etc.
**[Clarifications]**: (Optional) If there are parts of the pull request that are unclear or lack sufficient context, ask for clarification here. If not, this section can be omitted.
**[Conclusion]**: Conclude the review with an overall assessment.
**[Other]**: (Optional) If there are additional observations or notes, mention them here. If not, this section can be omitted.

The user may also engage in further discussions about the review. It is not necessary to use the template when discussing with the user.
""",
            },
            {
                "role": "user",
                "content": f"Review the following pull request:\n{changes_str}\n",
            },
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0.6,
            n=2,
        )
        logger.info("Received responses from OpenAI API")
    except Exception as e:
        logger.error(f"Error while calling OpenAI API: {e}")
        return "Error while calling OpenAI API", 500

    reviews = [
        f"Review {i+1}:\n{response.choices[i]['message']['content'].strip()}\n"
        for i in range(len(response.choices))
    ]

    # Combine the reviews into a single string
    reviews_str = "\n".join(reviews)

    final_review = f"""**[AI Review]** This comment is generated by an AI model (gpt-4).\n\n{reviews_str}\n
    **[Note]** 
    The above AI review results are for reference only, please rely on human expert review results for the final conclusion.
    Usually, AI is better at enhancing the quality of code snippets. However, it's essential for human experts to pay close attention to whether the modifications meet the overall requirements. Providing detailed information in the PR description helps the AI generate more specific and useful review results.\n\n"""
    logger.info("Final review prepared")

    logger.info("Translating review to Chinese")
    translate_messages = [{"role": "user", "content": f"将下面内容翻译为中文:\n{final_review}"}]
    try:
        translated_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=translate_messages,
            max_tokens=2000,
            temperature=0.8,
            n=1,
        )
    except Exception as e:
        logger.error(f"Error while fetching PR details from GitHub API: {e}")
        return "Error while fetching PR details from GitHub API", 500
    logger.info("Translation completed")

    try:
        # Post the GPT result as a PR comment
        logger.info("Submitting PR review comment")
        gh_pr.create_issue_comment(
            final_review
            + "\n"
            + translated_response.choices[0]["message"]["content"].strip()
        )

        logger.info("PR review comment submitted")
    except Exception as e:
        logger.error(f"Error while submitting PR review comment: {e}")
        return "Error while submitting PR review comment", 500

    return "Review submitted", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
