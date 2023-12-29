import boto3
import sys

def delete_instances(ec2,vpc_id):
    try:
        instances = ec2.instances.filter(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        for instance in instances:
            print (f"Terminating instance {instance.id}")
            instance.terminate()
            print (f"Waiting for instance {instance.id} to be terminate")
            instance.wait_until_terminated()
            print(f"Instance {instance.id} terminated")
    except Exception as e:
        print(f'No instances to be terminate. {e}')
        
def delete_internet_gateway(ec2,vpc_id):
    igws = ec2.internet_gateways.filter(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])
    try:
        for igw in igws:
            print(f"Detaching Internet Gateway: {igw.id}")
            igw.detach_from_vpc(VpcId=vpc_id)
            print(f"Deleting Internet Gateway: {igw.id}")
            igw.delete()
            print(f"Deleted Internet Gateway: {igw.id}")
    except Exception as e:
        print(f"Error deleting Internet Gateway {e}")
        
        
    

    
        
def detach_network_interface(ec2,vpc_id):
    def disassociate_and_release_elastic_ips(resource_ids):
        for resource_id in resource_ids:
            # Describe addresses to find associated Elastic IPs
            addresses = ec2.describe_addresses(Filters=[{'Name': 'network-interface-id', 'Values': [resource_id]}])

            for addr in addresses['Addresses']:
                try:
                    # Disassociate the Elastic IP address
                    ec2.disassociate_address(AssociationId=addr['AssociationId'])
                    print(f"Disassociated Elastic IP address: {addr['PublicIp']} from {resource_id}")

                    # Release the Elastic IP address
                    ec2.release_address(AllocationId=addr['AllocationId'])
                    print(f"Released Elastic IP address: {addr['PublicIp']}")

                except Exception as e:
                    print(f"Error disassociating or releasing Elastic IP address: {e}")


    
        # Finding instances in the VPC
    instances = ec2.describe_instances(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])

    instance_ids = [instance['InstanceId'] for reservation in instances['Reservations'] for instance in reservation['Instances']]

    # Finding network interfaces in the VPC
    network_interfaces = ec2.describe_network_interfaces(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])

    network_interface_ids = [ni['NetworkInterfaceId'] for ni in network_interfaces['NetworkInterfaces']]
    
    
        # Disassociate and Release Elastic IPs associated with instances
    disassociate_and_release_elastic_ips(instance_ids)

    # Disassociate and Release Elastic IPs associated with network interfaces
    disassociate_and_release_elastic_ips(network_interface_ids)


def  delete_network_interface(ec2,vpc_id,subnet_id):
    detach_network_interface(ec2,vpc_id)
    
    network_interfaces = ec2.describe_network_interfaces(Filters=[{'Name': 'subnet-id', 'Values': [subnet_id]}])
    for ni in network_interfaces['NetworkInterfaces']:
        ni_id = ni['NetworkInterfaceId']
        attachment = ni.get('Attachment')

        if attachment:
            try:
                # Detach the network interface
                ec2.detach_network_interface(AttachmentId=attachment['AttachmentId'])
                print(f"Detached network interface: {ni_id}")

                # Wait for detachment to complete
                waiter = ec2.get_waiter('network_interface_available')
                waiter.wait(NetworkInterfaceIds=[ni_id])
            except Exception as e:
                print(f"Error detaching network interface {ni_id}: {e}")
        else:
            print(f"Network interface {ni_id} is not attached")
        
        try:
        # Delete the network interface
            ec2.delete_network_interface(NetworkInterfaceId=ni_id)
            print(f"Deleted network interface: {ni_id}")
        except Exception as e:
            print(f"Error deleting network interface {ni_id}: {e}")
            
            
def  delete_subnets(ec2_client,vpc_id):
    # List subnets
    subnets = ec2_client.subnets.filter(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    try:
        for subnet in subnets:
            print(f"Deleting subnet {subnet.id}")
            subnet.delete()
            print(f"Deleted subnet {subnet.id}")
            
    except Exception as e:
        print(f"Error: Deleting subnet {e}")
        
def delete_security_groups(ec2,vpc_id):
    
    security_groups = ec2.security_groups.filter(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    try:
        for sg in security_groups:
            if sg.group_name != 'default':
                sg.delete()
    except Exception as e:
        print(f"Error: Deleting security group {e}")
        
def delete_routing_tables(ec2,vpc_id):
    route_tables = ec2.route_tables.filter(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    try:
        for rt in route_tables:
            if not rt.associations:
                rt.delete()
    except Exception as e:
        print(f"Error: Deleting route table {e}")
        

def delete_all(vpc_id):
    

    ec2_client = boto3.client('ec2')
    
    ec2 = boto3.resource('ec2')
    
    
    # List all instances    
    delete_instances(ec2,vpc_id)
    delete_subnets(ec2,vpc_id)
    delete_security_groups(ec2,vpc_id)
    
    delete_internet_gateway(ec2,vpc_id)
    
    delete_routing_tables(ec2,vpc_id)
    
    try:
        print(f"Deleting VPC: {vpc_id}")
        vpc = ec2.Vpc(vpc_id)
        print(f"VPC: {vpc.id} has the following resources: {vpc}")
        vpc.delete()
        print(f"Deleted VPC: {vpc_id}")
    except Exception as e:
        print(f"Error: Deleting VPC {e}")

 
    print(f"Deleted VPC: your-vpc-id")

if __name__ == '__main__':
    vpc_id=sys.argv[1:]
    vpc_id=f"{vpc_id[0]}".replace('[','').replace(']','').replace("'","")
    print (f"VPC {vpc_id} To Be delete")
    
    delete_all(vpc_id)