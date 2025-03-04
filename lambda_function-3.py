import boto3
import json
import csv
import os 
from datetime import date

TAG_NAME = "<TAG_NAME>"
TAG_VALUE = "<TAG_VALUE>"

reports_bucket="<BUCKET_NAME>"
directory = '/tmp/reports/'
date_format = date.today().strftime("/%Y/%m/%d/")

####################
# Boto3 Objects
####################
ec2 = boto3.client("ec2")
elb = boto3.client('elbv2')
autoscaling = boto3.client('autoscaling')
rds = boto3.client("rds")
ecr = boto3.client('ecr')
sns = boto3.client('sns')
s3 = boto3.client('s3')
apigateway = boto3.client('apigateway')
lambda_function = boto3.client('lambda')
wafv2 = boto3.client('wafv2')
firehose = boto3.client('firehose')
kinesis = boto3.client('kinesis')
ecs = boto3.client('ecs')
glue = boto3.client('glue')
cognito = boto3.client('cognito-idp')

def create_report(filename, header, datas):
    csvFile = open(directory + filename, 'w', newline='', encoding='utf8')
    writer = csv.writer(csvFile)
    writer.writerow(header)
    for data in datas:
        writer.writerow(data)
    csvFile.close()

    s3.upload_file(directory + filename, reports_bucket, 'reports' + date_format + filename)

def get_ec2_instances():
    print("*********** EC2 Instance List ***********")
    header = ['Instance_ID', 'Instance_State', 'Tag_Status']
    data = []

    response = ec2.describe_instances()["Reservations"]
    for reservation in response:
        for instance in reservation["Instances"]:
            if 'Tags' not in instance:
                data.append([instance['InstanceId'], instance['State']['Name'], "Resource_Not_Tagged"])

            else:
                list = []
                for tag in instance['Tags']:
                    print(instance['Tags'])
                    list.append(tag['Key'])
                    if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                        data.append([instance['InstanceId'], instance['State']['Name'], "Match_Found"])

                if TAG_NAME not in list:
                    data.append([instance['InstanceId'], instance['State']['Name'], TAG_NAME + "_Tag_Missing"])

    create_report('ec2.csv', header, data)

def get_sg():
    print("*********** EC2 Security Group ***********")
    header = ['SecurityGroup_ID', 'Tag_Status']
    data = []

    response = ec2.describe_security_groups()['SecurityGroups']
    for security_group in response:
        if 'Tags' not in security_group:
            data.append([security_group['GroupId'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in security_group['Tags']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([security_group['GroupId'], "Match_Found"])
            
            if TAG_NAME not in list:
                data.append([security_group['GroupId'], TAG_NAME + "_Tag_Missing"])

    create_report('security_group.csv', header, data)

def get_elb():
    print("*********** ELB List ***********")
    header = ['Load_Balancer_Name', 'Load_Balancer_Status', 'Tag_Status']
    data = []

    response = elb.describe_load_balancers()["LoadBalancers"]
    for loadBalancer in response:
        lb = elb.describe_tags(ResourceArns=[loadBalancer['LoadBalancerArn']])['TagDescriptions'][0]

        if not lb['Tags']:
            data.append([loadBalancer['LoadBalancerName'], loadBalancer['State']['Code'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in lb['Tags']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([loadBalancer['LoadBalancerName'], loadBalancer['State']['Code'], "Match_Found"])
            
            if TAG_NAME not in list:
                data.append([loadBalancer['LoadBalancerName'], loadBalancer['State']['Code'], TAG_NAME + "_Tag_Missing"])
    
    create_report('elb.csv', header, data)

def get_target_groups():
    print("*********** ELB Target Group List ***********")
    header = ['Target_GroupName', 'LoadBalancer_Arns', 'Tag_Status']
    data = []

    response = elb.describe_target_groups()["TargetGroups"]
    for targetGroup in response:
        lb_tg = elb.describe_tags(ResourceArns=[targetGroup['TargetGroupArn']])['TagDescriptions'][0]

        if not lb_tg['Tags']:
            data.append([targetGroup['TargetGroupName'],targetGroup['LoadBalancerArns'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in lb_tg['Tags']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([targetGroup['TargetGroupName'],targetGroup['LoadBalancerArns'], "Match_Found"])

            if TAG_NAME not in list:
                data.append([targetGroup['TargetGroupName'],targetGroup['LoadBalancerArns'], TAG_NAME + "_Tag_Missing"])

    create_report('target_group.csv', header, data)

def get_auto_scaling_groups():
    print("*********** AutoScaling Group List ***********")
    header = ['ASG_Name', 'Tag_Status']
    data = []

    response = autoscaling.describe_auto_scaling_groups()["AutoScalingGroups"]
    for autoScalingGroup in response:
        if not autoScalingGroup['Tags']:
            data.append([autoScalingGroup['AutoScalingGroupName'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in autoScalingGroup['Tags']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([autoScalingGroup['AutoScalingGroupName'], "Match_Found"])
            if TAG_NAME not in list:
                data.append([autoScalingGroup['AutoScalingGroupName'], TAG_NAME + "_Tag_Missing"])

    create_report('asg.csv', header, data)

def get_rds():
    print("*********** RDS Instance List ***********")
    header = ['RDS_Instance_Identifier', 'RDS_Instance_Status', 'Tag_Status']
    data = []

    response = rds.describe_db_instances()["DBInstances"]
    for dbInstance in response:
        if not dbInstance['TagList']:
            data.append([dbInstance['DBInstanceIdentifier'],dbInstance['DBInstanceStatus'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in dbInstance['TagList']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([dbInstance['DBInstanceIdentifier'],dbInstance['DBInstanceStatus'], "Match_Found"])
            if TAG_NAME not in list:
                data.append([dbInstance['DBInstanceIdentifier'],dbInstance['DBInstanceStatus'], TAG_NAME + "_Tag_Missing"])

    create_report('rds.csv', header, data)

def get_sns():
    print("*********** SNS Topic List ***********")
    header = ['SNS_Topic', 'Tag_Status']
    data = []

    response = sns.list_topics()['Topics']
    for topic in response:
        tags = sns.list_tags_for_resource(ResourceArn=topic['TopicArn'])

        if not tags['Tags']:
            data.append([topic['TopicArn'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in tags['Tags']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([topic['TopicArn'], "Match_Found"])
            if TAG_NAME not in list:
                data.append([topic['TopicArn'], TAG_NAME + "_Tag_Missing"])

    create_report('sns.csv', header, data)

def get_ecr():
    print("*********** ECR List ***********")
    header = ['ECR_Repository_Name', 'Tag_Status']
    data = []

    response = ecr.describe_repositories()['repositories']
    for repositorie in response:
        tags =  ecr.list_tags_for_resource(resourceArn=repositorie['repositoryArn'])

        if not tags['tags']:
                data.append([repositorie['repositoryName'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in tags['tags']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([repositorie['repositoryName'], "Match_Found"])

            if TAG_NAME not in list:
                data.append([repositorie['repositoryName'], TAG_NAME + "_Tag_Missing"])

    create_report('ecr.csv', header, data)

def get_apigateway():
    print("*********** API Gateway List ***********")
    header = ['API_Gateway_Name', 'Tag_Status']
    data = []

    response = apigateway.get_rest_apis()['items']
    for restApi in response:
        if 'tags' not in restApi:
            data.append([restApi['name'], "Resource_Not_Tagged"])

        else:
            if TAG_NAME not in restApi['tags']:
                data.append([restApi['name'], TAG_NAME + "_Tag_Missing"])
            elif TAG_NAME in restApi['tags'] and restApi['tags'][TAG_NAME] == TAG_VALUE:
                data.append([restApi['name'], "Match_Found"])

    create_report('api_gateway.csv', header, data)

def get_lambda_function():
    print("*********** Lambda Functions List ***********")
    header = ['Lambda_Name', 'Tag_Status']
    data = []

    response = lambda_function.list_functions()['Functions']

    for function in response:
        tags = lambda_function.list_tags(Resource=function['FunctionArn'])
        
        if not tags['Tags']:
            data.append([function['FunctionName'], "Resource_Not_Tagged"])

        else:
            if TAG_NAME not in tags['Tags']:
                data.append([function['FunctionName'], TAG_NAME + "_Tag_Missing"])
            elif TAG_NAME in tags['Tags'] and tags['Tags'][TAG_NAME] == TAG_VALUE:
                data.append([function['FunctionName'], "Match_Found"])

    create_report('lambda_function.csv', header, data)

def get_waf_acl():
    print("*********** WAF V2 ACL List ***********")
    header = ['WAF_ACL_Name', 'Tag_Status']
    data = []

    response = wafv2.list_web_acls(Scope='REGIONAL')['WebACLs']

    for web_acl in response:
        tags = wafv2.list_tags_for_resource(ResourceARN=web_acl['ARN'])['TagInfoForResource']

        if not tags['TagList']:
                data.append([web_acl['Name'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in tags['TagList']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([web_acl['Name'], "Match_Found"])

            if TAG_NAME not in list:
                data.append([web_acl['Name'], TAG_NAME + "_Tag_Missing"])

    create_report('waf.csv', header, data)

def get_delivery_streams():
    print("*********** Firehouse Delivery Streams List ***********")
    header = ['Delivery_Stream_Name', 'Tag_Status']
    data = []

    response = firehose.list_delivery_streams()['DeliveryStreamNames']

    for stream_name in response:
        tags = firehose.list_tags_for_delivery_stream(DeliveryStreamName=stream_name)

        if not tags['Tags']:
                data.append([stream_name, "Resource_Not_Tagged"])
        else:
            list = []
            for tag in tags['Tags']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([stream_name, "Match_Found"])

            if TAG_NAME not in list:
                data.append([stream_name, TAG_NAME + "_Tag_Missing"])

    create_report('firehose.csv', header, data)

def get_kinesis_streams():
    print("*********** Kinesis Streams List ***********")
    header = ['Kinesis_Stream_Name', 'Tag_Status']
    data = []

    response = kinesis.list_streams()['StreamNames']

    for stream in response:
        tags = kinesis.list_tags_for_stream(StreamName=stream)
        data.append(tags)

    create_report('kinesis.csv', header, data)

def get_ecs_cluster():
    print("*********** ECS Cluster List ***********")
    header = ['ECS_Cluster_Name', 'Tag_Status']
    data = []

    response = ecs.list_clusters()['clusterArns']

    for cluster_arn in response:
        cluster = ecs.describe_clusters(clusters=[cluster_arn], include=['TAGS'])['clusters']
        data.append([cluster['clusterName'], cluster['tags']])

        if not cluster['tags']:
                data.append([cluster['clusterName'], "Resource_Not_Tagged"])

        else:
            list = []
            for tag in cluster['tags']:
                list.append(tag['key'])

                if tag['key'] == TAG_NAME and tag['value'] == TAG_VALUE:
                    data.append([cluster['clusterName'], "Match_Found"])

            if TAG_NAME not in list:
                data.append([cluster['clusterName'], TAG_NAME + "_Tag_Missing"])

    create_report('ecs.csv', header, data)


def lambda_handler(event, context):
    if not os.path.exists(directory):
        os.mkdir(directory)

    get_ec2_instances()
    get_sg()
    get_elb()
    get_target_groups()
    get_auto_scaling_groups()
    get_rds()
    get_sns()
    get_ecr()
    get_apigateway()
    get_lambda_function()
    get_waf_acl()
    get_delivery_streams()
    get_kinesis_streams()
    get_ecs_cluster()

    return {
        'statusCode': 200,
        'body': json.dumps('Report generated successfully')
    }
