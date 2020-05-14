
# DEMO-full-2qfx-netbox-awx

This Vagrantfile will spawn 2 instances of VQFX (Full) each with 1 Routing Engine and 1 PFE VM  
Both VQFX will be connected back to back with IP address pre-configured on their interfaces
A netbox server and a awx server will be spanw too.

# Requirement

### Resources
 - RAM : 5G
 - CPU : 3 Cores

### Tools
 - Ansible for provisioning (except for windows)
 - Pipenv
 - Junos module for Ansible

# Topology

           em0|                        em0|
       =============  xe-0/0/[0-5] =============
       |           | ------------- |           |
       |   vqfx1   | ------------- |   vqfx2   |
       |           | ------------- |           |
       =============               =============
           em1|                        em1|
       =============               =============
       | vqfx1-pfe |               | vqfx1-pfe |
       =============               =============

# Provisioning / Configuration

Ansible is used to preconfigured both VQFX with an IP address on their interfaces

**1) Install Juniper vqfx10k and linux boxes**

```

vagrant box add juniper/vqfx10k-re
vagrant box add juniper/vqfx10k-pfe
vagrant box add hashicorp/bionic64
```


**2) Start pipenv**

`pipenv shell`


**3) Install python packages**

`pip install -r requirements.txt`


**4) start vagrant**

`vagrant up`


**5) Once both VMs are up and running, you can connect to them with**

```

vagrant ssh vqfx1
vagrant ssh vqfx2

vagrant ssh awx
vagrant ssh netbox
```


**6) Run some playbooks**

```

ansible-playbook deploy.bgp.yaml
ansible-playbook get.status.yaml
```

**7) Netbox**

- [x] Create API Token: [http://YOUR_NETBOX_IP/admin/users/token/add/](http://YOUR_NETBOX_IP/admin/users/token/add/).

- [x] Create **bgp_asn**  Custom Field: [http://YOUR_NETBOX_IP/admin/extras/customfield/add/](http://YOUR_NETBOX_IP/admin/extras/customfield/add/).  
This Custom Field should be an **integer** type and applies to **dcim.devices** object.


**8) Populate netbox**

- [x] Edit *script/config-netbox.py*, update url, token and other variables if needed. Then, run *populate-netbox.py*

```
python3 scripts/populate-netbox.py
```

**9) AWX**

...
