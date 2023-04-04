#! /bin/bash
curl -X POST -H "Content-Type: application/json" -d '{
        "action": "opened",
        "pull_request": {
          "number": 2,
          "title": "Sample Pull Request",
          "body": "This is a sample pull request."
        },
        "repository": {
          "full_name": "LI-Mingyu/cndev-tutorial"
        }
      }' http://8.210.136.172:36831/review_pr