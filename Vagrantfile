# -*- mode: ruby -*-
# vi: set ft=ruby :
#
$AWX_IP = `$PWD/ip_address_by_uid.py`
$OBSERVIUM_IP = `$PWD/ip_address_by_uid.py`
$NETBOX_IP = `$PWD/ip_address_by_uid.py`
$VQFX1_IP = `$PWD/ip_address_by_uid.py`
$VQFX2_IP = `$PWD/ip_address_by_uid.py`


# On Windows, only supported if running under Linux Subsystem for Windows
if Vagrant::Util::Platform.windows?
    puts 'Linux Subsystem for Windows required on Windows hosts.  Please refer to Windows.md for further instruction.'
    abort 
end

VAGRANTFILE_API_VERSION = "2"

UUID = "POPOV"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    ######
    # AWX Server 
    ######
    config.vm.define "awx" do |awx|
        awx.vm.hostname = "awx-vqfx-lab"
        awx.vm.box = "hashicorp/bionic64"
        awx.vm.network "private_network", ip: $AWX_IP
        awx.vm.network 'private_network', ip: "10.10.66.2", virtualbox__intnet: "#{UUID}_awx_vqfx1"
        awx.vm.network 'private_network', ip: "10.10.67.2", virtualbox__intnet: "#{UUID}_awx_vqfx2"
        awx.vm.provider "virtualbox" do |v|
           v.customize ["modifyvm", :id, "--memory", "2048"]
        end
    end

    ######
    # OBSERVIUM
    ######
    config.vm.define "observium" do |observium|
        observium.vm.hostname = "observium-vqfx-lab"
        observium.vm.box = "hashicorp/bionic64"
        observium.vm.network "private_network", ip: $OBSERVIUM_IP
        observium.vm.network 'private_network', auto_config: false, nic_type: '82540EM', virtualbox__intnet: "#{UUID}_observium_vqfx1"
        observium.vm.network 'private_network', auto_config: false, nic_type: '82540EM', virtualbox__intnet: "#{UUID}_observium_vqfx2"
    end

    ######
    # NETBOX Server
    ######
    config.vm.define "netbox" do |netbox|
        netbox.vm.hostname = "netbox-vqx-lab"
        netbox.vm.box = "hashicorp/bionic64"
        netbox.vm.network "private_network", ip: $NETBOX_IP
#        netbox.vm.provision "shell", inline: <<-SHELL
#          apt-get update
#          apt-get install -y lldpd ntp
#        SHELL
    end

    config.ssh.insert_key = false

    (1..2).each do |id|
        re_name  = ( "vqfx" + id.to_s ).to_sym
        pfe_name = ( "vqfx" + id.to_s + "-pfe" ).to_sym

        ##############################
        ## Packet Forwarding Engine ##
        ##############################
        config.vm.define pfe_name do |vqfxpfe|
            vqfxpfe.ssh.insert_key = false
            vqfxpfe.vm.box = 'juniper/vqfx10k-pfe'

            # DO NOT REMOVE / NO VMtools installed
            vqfxpfe.vm.synced_folder '.', '/vagrant', disabled: true
            vqfxpfe.vm.network 'private_network', auto_config: false, nic_type: '82540EM', virtualbox__intnet: "#{UUID}_vqfx_internal_#{id}"

            # In case you have limited resources, you can limit the CPU used per vqfx-pfe VM, usually 50% is good
            #---
             vqfxpfe.vm.provider "virtualbox" do |v|
                v.customize ["modifyvm", :id, "--cpuexecutioncap", "50"]
             end
            #---
        end

        ##########################
        ## Routing Engine  #######
        ##########################
        config.vm.define re_name do |vqfx|
            vqfx.vm.hostname = "vqfx#{id}"
            vqfx.vm.box = 'juniper/vqfx10k-re'

            # VM can be really slow unless COM1 is connected to something.
            (File.exist?("/proc/version") and File.readlines("/proc/version").grep(/(Microsoft|WSL)/).size > 0) ? ( re_log = "NUL" ) : ( re_log = "/dev/null" )
            vqfx.vm.provider "virtualbox" do |v|
                v.customize ["modifyvm", :id, "--uartmode1", "file", re_log]
            end

            # DO NOT REMOVE / NO VMtools installed
            vqfx.vm.synced_folder '.', '/vagrant', disabled: true

            # Management port
            vqfx.vm.network 'private_network', auto_config: false, nic_type: '82540EM', virtualbox__intnet: "#{UUID}_vqfx_internal_#{id}"
            vqfx.vm.network 'private_network', auto_config: false, nic_type: '82540EM', virtualbox__intnet: "#{UUID}_reserved-bridge"


            #cnajar: xe-0/0/0
            vqfx.vm.network 'private_network', auto_config: false, nic_type: '82540EM', virtualbox__intnet: "#{UUID}_awx_vqfx#{id}"

            #cnajar: xe-0/0/1
            vqfx.vm.network 'private_network', ip: $VQFX1_IP

            # Dataplane ports: xe-0/0/2 xe-0/0/3
            (1..2).each do |seg_id|
               vqfx.vm.network 'private_network', auto_config: false, nic_type: '82540EM', virtualbox__intnet: "#{UUID}_seg#{seg_id}"
            end

            #cnajar: xe-0/0/4
            vqfx.vm.network 'private_network', auto_config: false, nic_type: '82540EM', virtualbox__intnet: "#{UUID}_observium_vqfx#{id}"
        end
    end

    ##############################
    ## Box provisioning        ###
    ##############################
    config.vm.provision "ansible" do |ansible|
        ansible.compatibility_mode = "2.0"
        ansible.config_file = "ansible.cfg"
        ansible.groups = {
            "srv" => ["awx", "netbox" ],
            "vqfx10k" => ["vqfx1", "vqfx2" ],
            "vqfx10kpfe"  => ["vqfx1-pfe", "vqfx2-pfe"],
            "all:children" => ["srv", "vqfx10k", "vqfx10kpfe"]
        }
	ansible.playbook = "pb.INIT-PLAYBOOK.yaml"
	# because pipenv
	#ansible.extra_vars = { ansible_python_interpreter:"`pipenv --py`"}
    end
end
