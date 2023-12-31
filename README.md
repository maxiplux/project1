# Project 1 - Linux Servers on AWS

## Warning :warning:
**IMPORTANT: THE CODE IN THIS REPOSITORY CAN DELETE ALL YOUR RESOURCES IN YOUR ENVIRONMENT. PLEASE ENSURE YOU READ AND UNDERSTAND THE CODE BEFORE EXECUTING.**

:exclamation: **DO NOT EXECUTE THESE SCRIPTS IN A PRODUCTION ENVIRONMENT WITHOUT A THOROUGH UNDERSTANDING OF HOW BOTO3 WORKS.**

## Prerequisites

Before you begin, ensure you have met the following requirements:
- You have installed the AWS CLI.
- You have configured your AWS credentials (`~/.aws/config`).
- Python3


## How to Execute

### Setting up the Environment

To create all the requirements for the project:
- python3  -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt

### EXECUTING CODE 

To delete all resources associated with a specific VPC ID:
- python main.py


### Deleting Resources

To delete all resources associated with a specific VPC ID:
- python delete-all.py  VPCID
- EXAMPLE: python delete-all.py  vpc-0f0595cb02601764f


