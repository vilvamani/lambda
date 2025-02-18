import boto3
import json
import csv
import os   
from datetime import date

ec2 = boto3.client("ec2", "ap-northeast-1")
rds = boto3.client("rds", "ap-northeast-1")
elb = boto3.client('elbv2')
ecr = boto3.client('ecr')
autoscaling = boto3.client('autoscaling')
s3 = boto3.client('s3')

directory = '/tmp/reports/'
reports_bucket='<BucketName>'
filters = [{'Name':'tag:Environment', 'Values':['staging']}]
date_format = date.today().strftime("%Y/%m/%d/")

def creadte_report(filename, header, datas):
    csvFile = open(directory + filename, 'w', newline='', encoding='utf8')
    writer = csv.writer(csvFile)
    writer.writerow(header)
    for data in datas:
        writer.writerow(data)
    csvFile.close()

    s3.upload_file(directory + filename, reports_bucket, 'reports' + date_format + filename)


def get_ec2_instances():
    print("*********** EC2 Instance List ***********")
    header = ['Instance_ID', 'Instance_State']
    data = []

    #response = ec2.describe_instances(Filters=filters)
    response = ec2.describe_instances()
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            # print(instance['InstanceId'],instance['State']['Name'])
            data.append([instance['InstanceId'],instance['State']['Name']])

    creadte_report('ec2.csv', header, data)

def get_rds():
    print("*********** RDS Instance List ***********")
    header = ['RDS_Instance_Identifier', 'RDS_Instance_Status']
    data = []

    response = rds.describe_db_instances()
    for dbInstance in response["DBInstances"]:
        for tag in dbInstance['TagList']:
            if tag['Key'] == 'Environment' and tag['Value'] == 'staging':
               #print(dbInstance['DBInstanceIdentifier'],dbInstance['DBInstanceStatus'])
               data.append([dbInstance['DBInstanceIdentifier'],dbInstance['DBInstanceStatus']])

    creadte_report('rds.csv', header, data)


def get_elb():
    print("*********** ELB List ***********")
    header = ['Load_Balancer_Name', 'Load_Balancer_Status']
    data = []

    response = elb.describe_load_balancers()
    for loadBalancer in response["LoadBalancers"]:
        tagDescriptions = elb.describe_tags(ResourceArns=[loadBalancer['LoadBalancerArn']])
        for tag in tagDescriptions['TagDescriptions'][0]['Tags']:
            if tag['Key'] == 'Environment' and tag['Value'] == 'staging':
                #print(loadBalancer['LoadBalancerName'], loadBalancer['State']['Code'])
                data.append([loadBalancer['LoadBalancerName'], loadBalancer['State']['Code']])
    
    creadte_report('elb.csv', header, data)


def get_target_groups():
    print("*********** ELB Target Group List ***********")
    header = ['Target_GroupName', 'LoadBalancer_Arns']
    data = []

    response = elb.describe_target_groups()
    for targetGroup in response["TargetGroups"]:
        tagDescriptions = elb.describe_tags(ResourceArns=[targetGroup['TargetGroupArn']])
        for tag in tagDescriptions['TagDescriptions'][0]['Tags']:
            if tag['Key'] == 'Environment' and tag['Value'] == 'staging':
                #print(targetGroup['TargetGroupName'],targetGroup['LoadBalancerArns'])
                data.append([targetGroup['TargetGroupName'],targetGroup['LoadBalancerArns']])

    creadte_report('target_group.csv', header, data)

def get_auto_scaling_groups():
    print("*********** AutoScaling Group List ***********")
    header = ['ASG_Name']
    data = []

    response = autoscaling.describe_auto_scaling_groups(Filters=filters)
    for autoScalingGroup in response["AutoScalingGroups"]:
        #print(autoScalingGroup['AutoScalingGroupName'])
        data.append([autoScalingGroup['AutoScalingGroupName']])

    creadte_report('asg.csv', header, data)

def get_ecr():
    print("*********** ECR List ***********")
    header = ['ECR_Repository_Name']
    data = []

    response = ecr.describe_repositories()
    for repositorie in response["repositories"]:
        tagDescriptions =  ecr.list_tags_for_resource(resourceArn=repositorie['repositoryArn'])
        for tag in tagDescriptions['tags']:
            if tag['Key'] == 'Environment' and tag['Value'] == 'staging':
                #print(repositorie['repositoryName'])
                data.append([repositorie['repositoryName']])

    creadte_report('ecr.csv', header, data)  


def lambda_handler(event, context):
    if not os.path.exists(directory):
        os.mkdir(directory)

    get_ec2_instances()
    get_elb()
    get_target_groups()
    get_auto_scaling_groups()
    get_ecr()
    get_rds()

    return {
        'statusCode': 200,
        'body': json.dumps('Report generated successfully')
    }
