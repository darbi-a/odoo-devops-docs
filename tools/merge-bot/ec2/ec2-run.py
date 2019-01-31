import json
import boto3
from subprocess import Popen
import requests


def main():
    region_name = requests.get('http://169.254.169.254/latest/meta-data/placement/availability-zone').text[:-1]
    ssm_client = boto3.client('ssm', region_name=region_name)

    queue_name = ssm_client.get_parameter(Name='QUEUE_NAME', WithDecryption=True)['Parameter']['Value']
    shutdown_time = ssm_client.get_parameter(Name='SHUTDOWN_TIME', WithDecryption=True)['Parameter']['Value']
    github_token = ssm_client.get_parameter(Name='GITHUB_TOKEN_FOR_BOT', WithDecryption=True)['Parameter']['Value']

    sqs = boto3.resource('sqs', region_name=region_name)
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    messages = []
    response = queue.get_messages(10)
    while len(response) > 0:
        messages.extend(response)
        response = queue.get_messages(10)

    if len(messages) > 0 and shutdown_time != 0:
        Popen(['sudo', 'shutdown', '-c'])
        Popen(['sudo', 'shutdown', '-h', '+{}'.format(shutdown_time)])

    for message in messages:
        body = json.loads(message[0].body)
        if body['action']:
            print('python', 'odoo-devops/tools/merge-bot/review-bot.py',
                  body['repository']['full_name'], str(body['number']), '--github_token', github_token)
            Popen(['python', 'odoo-devops/tools/merge-bot/review-bot.py',
                   body['repository']['full_name'], str(body['number']), '--github_token', github_token])

        queue.delete_messages(Entries=[{
            'Id': message.message_id,
            'ReceiptHandle': message.receipt_handle
        }])


if __name__ == "__main__":
    main()
