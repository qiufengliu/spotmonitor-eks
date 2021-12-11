from kubernetes import config, client
import yaml
import json
import boto3

config.load_kube_config(config_file="./kubeconfig/fuwu-cluster-kube-config")
ec2 = boto3.client('ec2', region_name='cn-northwest-1')
coreApi = client.CoreV1Api()


def lambda_handler(event, context):
    body = yaml.safe_load(open('./k8s_event/event.yaml'))

    if event["detail-type"] == "EC2 Instance State-change Notification":
        if event["detail"]["state"] == "terminated":
            res = ec2.describe_instances(InstanceIds=[event['detail']['instance-id']])
            lifecycle = res['Reservations'][0]['Instances'][0]['InstanceLifecycle']
            if lifecycle == 'spot':
                body['reason'] = 'Terminated'
    elif event["detail-type"] == "EC2 Spot Instance Interruption Warning":
        body['reason'] = 'Interrupted'
    elif event["detail-type"] == "EC2 Spot Instance Request Fulfillment":
        body['metadata']['annotations']['request-id'] = event['detail']['spot-instance-request-id']
        body['reason'] = 'Fulfilled'
    if body['reason'] == 'empty':
        return {
            'statusCode': 200,
            'body': json.dumps('Nothing happened.')
        }
    else:

        body['metadata']['annotations']['instance-id'] = event['detail']['instance-id']
        body['metadata']['annotations']['action'] = body['reason']

        body['metadata']['name'] = "spot-notification-{}".format(event['id'])
        response = coreApi.create_namespaced_event("spot", body)

        return {
            'statusCode': 200,
            'body': json.dumps('Message Sent!')
        }
