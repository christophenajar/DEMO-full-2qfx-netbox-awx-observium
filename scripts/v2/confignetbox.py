# confignetbox
url = 'http://192.168.33.20/'
token = 'a97a31272a2ca5f257e3af444167ed0f68c226b7'
dc_slug = 'junos-datacenter'
dc_name = 'Junos Lab Datacenter'

log_path = '/tmp/populate-netbox.log'


leaf_slug = 'leaf'
leaf_name = 'LEAF'
leaf_color = '2196f3'

spine_slug = 'spine'
spine_name = 'SPINE'
spine_color = '3f51b5'

manufacturer_slug = 'juniper'
manufacturer_name = 'Juniper Networks'

device_type_vqfx10k = 'vqfx10k'
platform = 'junos'
custom_field_bgp = 'bgp_asn'

#---
num_spines = 2
num_leafs = 1
p2p_range = '10.0.'
lo0_range = '10.0.250.'
lo1_range = '10.0.255.'
ibgp_range = '10.0.3.'
mgmt_range = '10.4.2.'
ibgp_vlan = '4091'
asn_start = 65000
leaf_int_mlag_peer = 'ae0'
#---
