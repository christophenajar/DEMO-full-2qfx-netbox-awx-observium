import confignetbox as config
import pynetbox
import logging
from pprint import pprint

logger = logging.getLogger(__name__)
logging.basicConfig(filename=config.log_path, format='%(asctime)s %(message)s', level=logging.WARNING)

def search_dict_list(a_val, b_val, c_list):
    for line in c_list:
        if line['hostname'] == a_val:
            return line[b_val]

# Define Parent Variables that will be used to auto-generate and assign values
num_spines = config.num_spines
num_leafs = config.num_leafs
p2p_range = config.p2p_range
lo0_range = config.lo0_range
lo1_range = config.lo1_range
ibgp_range = config.ibgp_range
mgmt_range = config.mgmt_range
ibgp_vlan = config.ibgp_vlan
asn_start = config.asn_start
leaf_int_mlag_peer = config.leaf_int_mlag_peer

# Generate key/val for Leafs
leaf_list = []
asn = asn_start+1
n = 0
for i in range(num_leafs):
    id = i+1
    device = {}
    device['device_role'] = {'name': 'LEAF'}
    device['interfaces'] = []
    device['bgp_neighbors'] = []
    device['evpn_neighbors'] = []
    device['hostname'] = f'leaf{id}'
    if id%2 == 1:
        device['side'] = 'left'
        device['asn'] = asn
        asn +=1
        device['bgp_neighbors'].append({'neighbor':f'{ibgp_range}{id}', 'remote_as': device['asn'], 'state': 'present'})
        device['interfaces'].append({'interface': 'Lo1', 'address':f'{lo1_range}{id+10}', 'mask':'/32', 'description':'Loopback1 Underlay'})
    else:
        device['side'] = 'right'
        device['asn'] = asn-1
        device['bgp_neighbors'].append({'neighbor':f'{ibgp_range}{id-2}', 'remote_as': device['asn'], 'state': 'present'})
        device['interfaces'].append({'interface': 'Lo1', 'address':f'{lo1_range}{id+9}', 'mask':'/32', 'description':'Loopback1 Underlay'})
    for j in range(num_spines):
        # popov
        #device['interfaces'].append({'interface':f'xe-0/0/{j+11}', 'address':f'{p2p_range}{j+1}.{n+1}', 'mask':'/31', 'description':f'spine{j+1}'})
        #device['interfaces'].append({'interface':f'xe-0/0/{j+10}', 'address':f'{p2p_range}{j+1}.{n+1}', 'mask':'/31', 'description':f'spine{j+1}'})
        device['interfaces'].append({'interface':f'xe-0/0/{j+4}', 'address':f'{p2p_range}{j+1}.{n+1}', 'mask':'/31', 'description':f'spine{j+1}'})
        device['bgp_neighbors'].append({'neighbor':f'{p2p_range}{j+1}.{n}', 'remote_as': asn_start, 'state': 'present'})
        device['evpn_neighbors'].append({'neighbor':f'{lo0_range}{j+1}', 'remote_as': asn_start, 'state': 'present'})
    device['interfaces'].append({'interface': f'Vlan{ibgp_vlan}', 'address':f'{ibgp_range}{i}', 'mask':'/31', 'description':'IBGP Underlay SVI'})
    device['interfaces'].append({'interface': 'Lo0', 'address':f'{lo0_range}{id+10}', 'mask':'/32', 'description':'Loopback0 Underlay'})
    device['interfaces'].append({'interface': 'em0', 'address':f'{mgmt_range}{id+22}', 'mask':'/24', 'description':'OOB Management'})
    leaf_list.append(device)
    n+=2


# Generate key/val for Spines
spine_list = []
asn = asn_start
for i in range(num_spines):
    id = i+1
    device = {}
    device['device_role'] = {'name': 'SPINE'}
    device['interfaces'] = []
    device['bgp_neighbors'] = []
    device['evpn_neighbors'] = []
    device['hostname'] = f'spine{id}'
    device['asn'] = asn
    n = 0
    for j in range(num_leafs):
        leaf_asn = search_dict_list(f'leaf{j+2}','asn',leaf_list)
        # popov
        #device['interfaces'].append({'interface':f'xe-0/0/{j+1}', 'address':f'{p2p_range}{id}.{n}', 'mask':'/31', 'description':f'leaf{j+1}'})
        device['interfaces'].append({'interface':f'xe-0/0/{j}', 'address':f'{p2p_range}{id}.{n}', 'mask':'/31', 'description':f'leaf{j+1}'})
        j = j+1
        device['bgp_neighbors'].append({'neighbor':f'{p2p_range}{id}.{n+1}', 'remote_as': leaf_asn, 'state': 'present'})
        device['evpn_neighbors'].append({'neighbor':f'{lo0_range}{j+11}', 'remote_as': leaf_asn, 'state': 'present'})
        n += 2
    device['interfaces'].append({'interface': 'Lo0', 'address':f'{lo0_range}{id}', 'mask':'/32', 'description':'Loopback0 Underlay'})
    device['interfaces'].append({'interface': 'em0', 'address':f'{mgmt_range}{id+20}', 'mask':'/24', 'description':'OOB Management'})
    spine_list.append(device)

# Combine both Leaf and Spine lists into a single list
all_devices = leaf_list + spine_list



############################################################################
# NetBox Tasks
############################################################################
# Connect to NetBox
nb = pynetbox.api(config.url, token=config.token)
logger.warning("-- Connection to Netbox API success --")

# Create new Site
new_site = nb.dcim.sites.get(slug=config.dc_slug)
if not new_site:
    new_site = nb.dcim.sites.create(
        name=config.dc_name,
        slug=config.dc_slug,
    )
    logger.warning('Adding new datacenter %s ' % (config.dc_slug))

# Create Device Role 'LEAF'
new_role_leaf = nb.dcim.device_roles.get(slug=config.leaf_slug)
if not new_role_leaf:
    new_role_leaf = nb.dcim.device_roles.create(
        name=config.leaf_name,
        slug=config.leaf_slug,
        color=config.leaf_color
    )
    logger.warning("Adding new LEAF role")

# Create Device Role 'SPINE'
new_role_spine = nb.dcim.device_roles.get(slug=config.spine_slug)
if not new_role_spine:
    new_role_spine = nb.dcim.device_roles.create(
        name=config.spine_name,
        slug=config.spine_slug,
        color=config.spine_color
    )
    logger.warning("Adding new SPINE role")

# Create Manufacturer Juniper
new_manufacturer_juniper = nb.dcim.manufacturers.get(slug=config.manufacturer_slug)
if not new_manufacturer_juniper:
    new_manufacturer_juniper = nb.dcim.manufacturers.create(
        name=config.manufacturer_name,
        slug=config.manufacturer_slug
    )
    logger.warning("Adding new Manufacturer Juniper")


# Create Device Type 'vqfx10k'
new_device_type_vqfx10k = nb.dcim.device_types.get(model=config.device_type_vqfx10k)
if not new_device_type_vqfx10k:
    new_device_type_vqfx10k = nb.dcim.device_types.create(
        manufacturer=new_manufacturer_juniper.id,
        model=config.device_type_vqfx10k,
        slug=config.device_type_vqfx10k
    )
    logger.warning("Adding new device_type vqfx10k")

# Create Interfaces for vqfx10k device type
# xe-0/0/[0-11] - 10gbase-x-sfpp   ( SFP+ (10GE)  )
# em0 em1 em5 - Virtual ( Management only )
# /opt/netbox/netbox/dcim/models/__init__.py
#         if self.interface_templates.exists():
#            data['interfaces'] = [
#                {
#                    'name': c.name,
#                    'type': c.type,
#                    'mgmt_only': c.mgmt_only,
#                }
#                for c in self.interface_templates.all()
#            ]
#
#new_interfaces_vqfx10k = nb.dcim.interface_templates.get(slug=new_device_type_vqfx10k.slug)
new_interfaces_vqfx10k = nb.dcim.interface_templates.filter(slug=new_device_type_vqfx10k.slug)
if not new_interfaces_vqfx10k:
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='em0',
        type='virtual',
        mgmt_only=True
    )
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='em1',
        type='virtual',
        mgmt_only=True
    )
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='em5',
        type='virtual',
        mgmt_only=True
    )
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='xe-0/0/0',
        type='10gbase-x-sfpp'
    )
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='xe-0/0/1',
        type='10gbase-x-sfpp'
    )
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='xe-0/0/2',
        type='10gbase-x-sfpp'
    )
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='xe-0/0/3',
        type='10gbase-x-sfpp'
    )
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='xe-0/0/4',
        type='10gbase-x-sfpp'
    )
    new_interfaces_vqfx10k = nb.dcim.interface_templates.create(
        device_type=new_device_type_vqfx10k.id,
        name='xe-0/0/5',
        type='10gbase-x-sfpp'
    )
    logger.warning("Adding Interfaces Template for vqfx10k device type")

# Create Platform 'junos'
new_platform_junos = nb.dcim.platforms.get(slug=config.platform)
if not new_platform_junos:
    new_platform_junos = nb.dcim.platforms.create(
        name=config.platform,
        slug=config.platform,
        manufacturer=new_manufacturer_juniper.id
    )
    logger.warning("Adding Platform 'junos'")



# NetBox Prefixes - Underlay P2P
logger.warning("Adding NetBox Prefixes - Underlay P2P")
for j in range(num_spines):
    nb.ipam.prefixes.create(
        prefix=f'{p2p_range}{j+1}.0/24',
        description=f'spine-{j+1} P2P'
    )
    n = 0
    for h in range(num_leafs):
        nb.ipam.prefixes.create(
            prefix=f'{p2p_range}{j+1}.{n}/31',
            description=f'spine-{j+1}-leaf-{h+1} P2P'
        )
        n+=2
# NetBox Prefixes - Loopback0
logger.warning("Adding NetBox Prefixes - Loopback0")
nb.ipam.prefixes.create(
        prefix=f'{lo0_range}0/24',
        description=f'Underlay Loopbacks'
    )
# NetBox Prefixes - Loopback1
#logger.warning("Adding NetBox Prefixes - Loopback1")
#nb.ipam.prefixes.create(
#        prefix=f'{lo1_range}0/24',
#    )

# NetBox Prefixes - IBGP Underlay
logger.warning("Adding NetBox Prefixes - IBGP Underlay")
nb.ipam.prefixes.create(
        prefix=f'{ibgp_range}0/24',
        description=f'Underlay IBGP'
    )
# Iterate over each Device
for dev in all_devices:
    # Create Device in NetBox
    new_device = nb.dcim.devices.create(
        name=dev['hostname'],
        site=new_site.id,
        device_type={
            'model': 'vqfx10k'
        },
        platform={
            'name': 'junos'
        },
        device_role=dev['device_role'],
        custom_fields={
            'bgp_asn' : dev['asn']
        },
        local_context_data = {}
    )
    logger.warning('* Adding device %s ' % (dev['hostname']))

    # Assign IP Addresses to Interfaces
    for intf in dev['interfaces']:
        # popov
        #print('#1')
        #print(intf['interface'])
        # IE: create Lo1
        if 'xe-0/0/' not in intf['interface'] and 'em' not in intf['interface']:
            nbintf = nb.dcim.interfaces.create(
                name=intf['interface'],
                form_factor=0,
                description=intf['description'],
                device=new_device.id,
                type=0
            )
            logger.warning('Adding interface %s for device %s ' % (intf['interface'], dev['hostname']))
        else:
            # Get interface id from NetBox
            nbintf = nb.dcim.interfaces.get(device=dev['hostname'], name=intf['interface'])
            # popov
            #print('#2')
            #print(dev['hostname'])
            #print(intf['interface'])
            nbintf.description = intf['description']
            nbintf.save()
        # Add IP to interface to NetBox
        intip = nb.ipam.ip_addresses.create(
            address=f"{intf['address']}{intf['mask']}",
            status=1,
            interface=nbintf.id,
            )
        logger.warning('Adding IP to interface %s for device %s ' % (intf['interface'], dev['hostname']))

        # Assign Primary IP to device
        if intf['interface'] is 'Management1':
            new_device.primary_ip4 = {'address': intip.address }
            new_device.save()
    # Assign local config context data
    for k,v in dev.items():
        if 'side' in k:
            new_device.local_context_data.update({k:v})
    new_device.save()
    logger.warning('** New device %s populated in Netbox ** ' % (dev['hostname']))

print("The script passed succesfully. Well done!")
logger.warning('-- The script passed succesfully. Well done! -- ')
