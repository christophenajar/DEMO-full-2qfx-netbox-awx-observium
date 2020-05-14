#!/usr/bin/python3

import os
import sys
import csv
import ipaddress

#print("Effective user id: ",os.geteuid())
#print("Effective group id: ",os.getegid())
#print("Real group id: ",os.getgid())
#print("List of supplemental group ids: ",os.getgroups())

# You need to setup first a vgrant group with id 500
VAGRANT_GROUP_ID = 500
# And fill the /etc/prefix_uid.conf file. IE : 1000:192.168.10.0
PREFIX_FILE = '/etc/prefix_uid.conf'
# LOCAL_DB file will be created later if needed
LOCAL_DB = os.path.expanduser('~/tmp/vagrant_prefixes.db')

#-----------------------------------------------------------


def get_my_prefix():
    my_uid = os.geteuid()
    with open(PREFIX_FILE) as csvfile:
        data = csv.reader(csvfile, delimiter=':')
        for row in data:
            if(int(row[0]) == my_uid):
                my_prefix = row[1]

    return(my_prefix)



def provisioning(my_prefix):
    try:
        f = open(LOCAL_DB, 'r')
        f.close()
    except IOError:
        f = open(LOCAL_DB, 'w')
        f.close()

    with open(LOCAL_DB, 'r') as f:
        lines = f.read().splitlines()
        if lines:
            last_line = lines[-1]
            if last_line: #exist
                my_ip_address = ipaddress.ip_address(last_line) + 1
                #print("exist")
                #print(my_ip_address)
                file = open(LOCAL_DB, 'a')
                file.write(str(my_ip_address) + '\n')
                file.close()
            else: # do not exist
                my_ip_address = ipaddress.ip_address(my_prefix) + 2
                #print("not exist")
                #print(my_ip_address)
                file = open(LOCAL_DB, 'a')
                file.write(str(my_ip_address) + '\n')
                file.close()
        else: #lines is not defined
            my_ip_address = ipaddress.ip_address(my_prefix) + 2
            #print("no lines defined")
            #print(my_ip_address)
            file = open(LOCAL_DB, 'a')
            file.write(str(my_ip_address) + '\n')
            file.close()
        
    return(str(my_ip_address))



def main():
    
    # look for all my groups id
    my_groups = os.getgroups()
    
    if VAGRANT_GROUP_ID in my_groups:
        my_prefix = get_my_prefix()
        my_ip_address = provisioning(my_prefix)
        print(my_ip_address, end='')
    else:
        print("Error : Vagrant group NOT found for your UID")
        sys.exit()



main()
