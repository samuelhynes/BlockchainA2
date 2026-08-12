#!/bin/bash

# Check if the user provided a commit message as an argument


# Add all changes
git add main.py
git add README.md
git add blockchain.py
git add consensus.py
git add values.py
git add transaction.py
git add Run.sh


# Commit changes with the provided commit message
git commit -m "New code"

# Push the changes to the remote repository (assuming the default 'origin' and 'main' branch)
git push 

echo "Changes pushed to the remote repository successfully!"