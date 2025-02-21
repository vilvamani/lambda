import boto3
import json
import csv
import os   
from datetime import date

ec2 = boto3.client("ec2")
elb = boto3.client('elbv2')
autoscaling = boto3.client('autoscaling')
rds = boto3.client("rds")
ecr = boto3.client('ecr')
sns = boto3.client('sns')
s3 = boto3.client('s3')

TAG_NAME = "<TAG_NAME>"
TAG_VALUE = "<TAG_VALUE>"

reports_bucket="<BUCKET_NAME>"
directory = '/tmp/reports/'
date_format = date.today().strftime("/%Y/%m/%d/")

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
                    list.append(tag['Key'])
                    if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                        data.append([instance['InstanceId'], instance['State']['Name'], "Match_Found"])

                if TAG_NAME not in list:
                    data.append([instance['InstanceId'], instance['State']['Name'], TAG_NAME + "_Tag_Missing"])

    creadte_report('ec2.csv', header, data)

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

    creadte_report('security_group.csv', header, data)

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
    
    creadte_report('elb.csv', header, data)

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

    creadte_report('target_group.csv', header, data)

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

    creadte_report('asg.csv', header, data)

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

    creadte_report('rds.csv', header, data)

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

    creadte_report('sns.csv', header, data)

def get_ecr():
    print("*********** ECR List ***********")
    header = ['ECR_Repository_Name', 'Tag_Status']
    data = []

    response = ecr.describe_repositories()["repositories"]
    for repositorie in response:
        tags =  ecr.list_tags_for_resource(resourceArn=repositorie['repositoryArn'])

        if not tags['Tags']:
            data.append([repositorie['repositoryName'], "Resource_Not_Tagged"])
        else:
            list = []
            for tag in tags['tags']:
                list.append(tag['Key'])
                if tag['Key'] == TAG_NAME and tag['Value'] == TAG_VALUE:
                    data.append([repositorie['repositoryName'], "Match_Found"])
            if TAG_NAME not in list:
                data.append([repositorie['repositoryName'], TAG_NAME + "_Tag_Missing"])

    creadte_report('ecr.csv', header, data)

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
    # get_ecr()

    return {
        'statusCode': 200,
        'body': json.dumps('Report generated successfully')
    }

if  __name__ == '__main__':
    lambda_handler('', '')
