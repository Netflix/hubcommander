"""
ADD WHATEVER CODE YOU NEED TO DO HERE TO DECRYPT CREDENTIALS FOR USE OF YOUR BOT!
"""


def get_credentials():
    # Here is a KMS example: (uncomment to make work)
    # return kms_decrypt()

    # For Docker, encryption is assumed to be happening outside of this, and the secrets
    # are instead being passed in as environment variables:
    import os
    return {
        # Minimum
        "SLACK": os.environ["SLACK_TOKEN"],

        # Optional:
        "GITHUB": os.environ.get("GITHUB_TOKEN"),
        "TRAVIS_PRO_USER": os.environ.get("TRAVIS_PRO_USER"),
        "TRAVIS_PRO_ID": os.environ.get("TRAVIS_PRO_ID"),
        "TRAVIS_PRO_TOKEN": os.environ.get("TRAVIS_PRO_TOKEN"),
        "TRAVIS_PUBLIC_USER": os.environ.get("TRAVIS_PUBLIC_USER"),
        "TRAVIS_PUBLIC_ID": os.environ.get("TRAVIS_PUBLIC_ID"),
        "TRAVIS_PUBLIC_TOKEN": os.environ.get("TRAVIS_PUBLIC_TOKEN"),
        "DUO_HOST": os.environ.get("DUO_HOST"),
        "DUO_IKEY": os.environ.get("DUO_IKEY"),
        "DUO_SKEY": os.environ.get("DUO_SKEY"),

        # ADD MORE HERE...
    }


# def kms_decrypt():
#     """
#     This is a method to decrypt credentials utilizing on-instance credentials
#     for AWS KMS. Please review AWS documentation for details.
#
#     The secret should be a JSON blob of the secrets that are required.
#     :return: A Dict with the secrets in them.
#     """
#     import boto3
#     import base64
#     import json
#     from config import KMS_REGION, KMS_CIPHERTEXT
#
#     kms_client = boto3.client("kms", region_name=KMS_REGION)
#     decrypt_res = kms_client.decrypt(CiphertextBlob=bytes(base64.b64decode(KMS_CIPHERTEXT)))
#     return json.loads(decrypt_res["Plaintext"].decode("utf-8"))


"""
Sample KMS encryption:
--------------------
import boto3
import json
import base64

kms_client = boto3.client("kms", region_name=KMS_REGION)
account_id = "YOUR ACCOUNT ID HERE"
key_id = "YOUR KEY ID HERE"
kms_arn = "arn:aws:kms:{region}:{account_id}:key/{key_id}".format(region=KMS_REGION, account_id=account_id, key_id=key_id)

secrets_to_encrypt = {
    "SLACK": "SLACK TOKEN HERE",
    "GITHUB": "GITHUB TOKEN HERE",
    "TRAVIS_PRO_USER": "GitHub ID of GitHub account with access to Travis Pro",
    "TRAVIS_PRO_ID": "The ID of the Travis user. Use the Travis API to get this (for Pro)",
    "TRAVIS_PRO_TOKEN": "Use the Travis API to get the Travis token (for the Travis Pro account)",
    "TRAVIS_PUBLIC_USER": "GitHub ID of GitHub account with access to Travis Public",
    "TRAVIS_PUBLIC_ID": "The ID of the Travis user. Use the Travis API to get this (for Public)",
    "TRAVIS_PUBLIC_TOKEN": Use the Travis API to get the Travis token (for the Travis Public account)",
    "DUO-HOST": "xxxxxxxx.duosecurity.com",
    "DUO-IKEY": "The IKEY for Duo",
    "DUO-SKEY": "The SKEY for Duo"
}

encrypt_res = kms_client.encrypt(KeyId=kms_arn, Plaintext=bytes(json.dumps(secrets_to_encrypt, indent=4), "utf-8"))

# Your results are:
print("The encrypted PTXT in B64:")
print(base64.b64encode(encrypt_res["CiphertextBlob"]).decode("utf-8"))
"""
