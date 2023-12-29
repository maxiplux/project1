import boto3
from botocore.config import Config
import logging
import time
from pathlib import Path
from os import path
from botocore.exceptions import ClientError
from argparse import ArgumentParser
from .myssh import validation



###### Using Local Enviroment for credentials ######

# Let's use Amazon S3


def check_credentials():
    home = path.expanduser("~")        
    return path.exists(f'{home}/.aws/credentials')
    
 
def get_client(resource=None,current_config={ "region_name":'us-east-1',"signature_version":'v4'}):     
    return boto3.client(resource, config=Config(**current_config))
     


        
    
# Print out bucket names
def is_everything_ready():
    if not(check_credentials()):        
        raise Exception("You don't have credentials in your local enviroment for AWS CLI")    
    s3 = boto3.resource('s3')
    for bucket in s3.buckets.all():        
        return True
    return False


def create_vpc(client):
    response = client.create_vpc(CidrBlock='172.16.0.0/16')
    vpc = response['Vpc']
    vpc_id = vpc['VpcId']
    client.create_tags(Resources=[vpc_id], Tags=[{'Key': 'project', 'Value': 'weclouddata'},{'Key': 'name', 'Value': 'weclouddata'}])
    print(f"VPC Created with ID: {vpc_id}")
    return vpc_id

    
def create_subnet(client,vpc_id,cidr_block='172.16.0.0/16'):
    subnet_response = client.create_subnet(VpcId=vpc_id, CidrBlock=cidr_block)
    subnet_id = subnet_response['Subnet']['SubnetId']
    client.modify_subnet_attribute(SubnetId=subnet_id,MapPublicIpOnLaunch={'Value': True})

    print(f"Subnet Created with ID: {subnet_id}")
    return subnet_id
    
def create_internet_gateway(client, vpc_id):
    igw = client.create_internet_gateway()
    print(f"Internet Gateway Created with ID: {igw['InternetGateway']['InternetGatewayId']}")
    return igw['InternetGateway']['InternetGatewayId']
    
def attach_internet_gateway(client, vpc_id, igw_id):
    client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"Internet Gateway {igw_id} attached to VPC {vpc_id}")
    
def wait_for_ip_addresses(client,instance_ids, timeout=300):
    instance_ids = [instance['InstanceId'] for instance in instance_ids]
    print(f"Waiting for IP addresses for instances: {instance_ids}")
    time.sleep(timeout)
    print(f"Done waiting for IP addresses for instances: {instance_ids}")

def create_ec2(client,security_group_id,subnet_id,key_pair_name=None,instance_type="t2.micro",worker_name='master', tags=[{'Key': 'Name', 'Value': 'master'}]):


    
    print (f"Creating {worker_name} node")
    ami_id = 'ami-06aa3f7caf3a30282'  # Replace with the AMI ID of your choice
    
    
    

    try:
        instances = client.run_instances(
            ImageId=ami_id,
            MinCount=1,
            UserData='''#!/bin/bash
sudo apt-get update
sudo apt-get install -y nginx nodejs python3.10  net-tools openjdk-11-jdk docker.io''',
            MaxCount=1,
            InstanceType=instance_type,
            KeyName=key_pair_name,
            SubnetId=subnet_id,
            
            SecurityGroupIds=[security_group_id],
            TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': tags,
            },
        ]
        )
        instances = instances['Instances']
        wait_for_ip_addresses(client,instances, timeout=300)
        
        


        print (f"Sucess  {worker_name} node")



    except Exception as e:
        print(f'Error launching EC2 instance: {e}')
        

def create_security_group(client,vpc_id, allow_ports=[22,80,443],tags=[{'Key': 'project', 'Value': 'wecloud' }]):
    security_group_id = client.create_security_group(GroupName='weclouddata',
                                            Description='Project One weclouddata',
                                            VpcId=vpc_id )
    security_group_id = security_group_id['GroupId']
    
    client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'icmp',
                    'FromPort': -1,
                    'ToPort': -1,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  
                }
            ]
        )
    for port in allow_ports:
        client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': port,
                    'ToPort': port,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  
                }
            ]
        )
    return security_group_id
    
    
    


 

def setup_route_table(client, vpc_id, igw_id, subnets, tags=[{'Key': 'project', 'Value': 'wecloud' }]):
    try:
        route_table = client.create_route_table(VpcId=vpc_id)
        route_table_id = route_table['RouteTable']['RouteTableId']
        client.create_route(
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=igw_id,
            RouteTableId=route_table_id
             
    
        )
        for subnet in subnets:
            client.associate_route_table(
                RouteTableId=route_table_id,
                SubnetId=subnet
            )
        print(f"Route table {route_table_id} created and associated with subnets: {subnets}")
    except ClientError as e:
        print(f"Error creating route table: {e}")
        


def create_key_pair(client, key_pair_name='weclouddata'):
    try:
        key_pair = client.create_key_pair(KeyName=key_pair_name)
        private_key = key_pair['KeyMaterial']
        with open(f'{key_pair_name}.pem', 'w') as file:
            file.write(private_key)
        print(f"Key Pair Created: {key_pair_name}.pem")
    except ClientError as e:
        print(f"Warning key pair: {e} The keypair already exists")
    return key_pair_name
        
    
        

def make_summary(client):
   
    include_states = ['running']
    results=[]
    try:
        response = client.describe_instances(Filters=[{'Name': 'tag:project', 'Values': ['wecloud']},{'Name': 'instance-state-name', 'Values': include_states}])
        print(f"Summary of instances: Total >> {len(response['Reservations'])}")
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                
                
                

        
                private_ip = instance.get('PrivateIpAddress')
                name=instance.get('Tags')[0].get('Value')
                public_ip = instance.get('PublicIpAddress', 'No Public IP')
                if public_ip != 'No Public IP':
                    results.append({'instance_id':instance_id,'name':name,'private_ip':private_ip,'public_ip':public_ip})
                    

                print(f'Instance ID: {instance_id} and name {name}\nPrivate IP: {private_ip}\nPublic IP: {public_ip}\n ')
        print ("The final results for the next step",results)
        return results

    except Exception as e:
        print(f'Error retrieving instance information: {e}')
        
    
        
if __name__ == '__main__':
    if (is_everything_ready()):
        t0 = time.time()
        client=get_client('ec2')
        vpc_id=create_vpc(client)
        print (f"VPC {vpc_id} created")
        igw_id=create_internet_gateway(client, vpc_id)
        sub_net_zero=create_subnet(client,vpc_id,cidr_block='172.16.0.0/24')        
        attach_internet_gateway(client, vpc_id, igw_id)
        setup_route_table(client, vpc_id, igw_id, [sub_net_zero])
        security_group_id=create_security_group(  client,vpc_id, allow_ports=[22,80,443])
        key_pair_name=create_key_pair(client)

        master_node=create_ec2(client,security_group_id,sub_net_zero,key_pair_name=key_pair_name,instance_type="t2.small",worker_name='master', tags=[{'Key': 'Name', 'Value': 'master-node-01'},{'Key': 'project', 'Value': 'wecloud' }])        
        worker_node1=create_ec2(client,security_group_id,sub_net_zero,key_pair_name=key_pair_name,worker_name='worker_node1', tags=[{'Key': 'Name', 'Value': 'worker-node-01'},{'Key': 'project', 'Value': 'wecloud' }])
        worker_node2=create_ec2(client,security_group_id,sub_net_zero,key_pair_name=key_pair_name,worker_name='worker_node2',tags=[{'Key': 'Name', 'Value': 'worker-node-02'},{'Key': 'project', 'Value': 'wecloud' }])
        
        
        results=make_summary(client)
        
        validation(results=results)
        
        t1=time.time()-t0
        print (f"Total time {t1} seconds ") 
        
    else:
        print("Something is missing in your environment")
    
         
        
     