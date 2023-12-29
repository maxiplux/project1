import paramiko

def ssh_connect(username="ubuntu",  instance_ip = '54.164.57.197',key_filename='weclouddata.pem', command='ls /tmp'):
    def ssh_connect_with_retry(ssh, ip_address, retries):
        if retries > 3:
            return False
        try:
            ssh.connect(ip_address, username=username, key_filename=key_filename)
            return True
        except paramiko.ssh_exception.NoValidConnectionsError:
            sleep(10)
            return ssh_connect_with_retry(ssh, ip_address, retries + 1)


    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if ssh_connect_with_retry(ssh, instance_ip, 0):
        print("Connected successfully. Executing commands...")
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stdout.read().decode('utf-8'))
        ssh.close()
    else:
        print("Connection failed")

#ssh_connect()

def validation(results=[{'instance_id': 'i-069ea77c0a3b5c926', 'name': 'worker-node-01', 'private_ip': '172.16.0.144', 'public_ip': '44.200.28.42'}, {'instance_id': 'i-026dbce7055eb3b6d', 'name': 'wecloud', 'private_ip': '172.16.0.26', 'public_ip': '3.231.219.106'}, {'instance_id': 'i-001c7d41165200555', 'name': 'worker-node-02', 'private_ip': '172.16.0.70', 'public_ip': '18.207.137.92'}]):
    print ("We are going to validate the results / Project 1 - Linux Servers on AWS / Group 1 - WeCloud")
    for result in results:
        public_ip=result.get('public_ip')
        for sub_result in results:
            current_public_ip=sub_result.get('public_ip')
            current_private_ip=sub_result.get('private_ip')
            
            if public_ip == current_public_ip:
                continue
            
            else:
                print( "Pinging from " + public_ip + " to " + current_private_ip + " We are expecting to see a response", "This execution is because we are loggin in our local machine")
                ssh_connect(instance_ip = public_ip, command=f'ifconfig & ping -c 3  ${current_private_ip}')
                print ("@@@@@@@@@@@@@@@@@ end @@@@@@@@@@@@@ \n\n\n\n\n")
    print ("End of validation, Thanks Lara, Farius, Juan, Rakin")
    
                

