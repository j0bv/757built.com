# 757Built System Setup with H100 Cluster Integration

This guide provides comprehensive instructions for setting up the 757Built system on server1 (AlmaLinux 8 cPanel) and integrating it with H100 GPUs from Prime Intellect for distributed document processing.

## Important Security Notice

The server scripts have been found in the public web directory (`public_html/server1`), which poses a security risk. These scripts should be moved outside the web root to prevent unauthorized access.

## System Architecture Overview

The 757Built system consists of:

1. **Server1 (Coordinator)**: Running AlmaLinux 8 with cPanel
   - Redis queue for job distribution
   - IPFS node for document storage
   - Phi-3 model for document processing
   - API endpoints for communication

2. **H100 Nodes (Workers)**: Running Ubuntu 22.04
   - GPU-accelerated document processing
   - Distributed storage for redundancy
   - API endpoints for storage and processing

3. **Distributed Storage System**
   - Multiple storage nodes across the cluster
   - Replication of documents for redundancy
   - Temporary queue while waiting for IPFS confirmation

## Step 1: Server1 Setup (AlmaLinux 8 with cPanel)

### Preparation

1. **Move server scripts out of public_html**:
   ```bash
   # As root or with appropriate permissions
   mkdir -p /home/YOUR_CPANEL_USERNAME/757built_scripts
   cp -r /home/YOUR_CPANEL_USERNAME/public_html/server1/* /home/YOUR_CPANEL_USERNAME/757built_scripts/
   rm -rf /home/YOUR_CPANEL_USERNAME/public_html/server1
   ```

2. **Create required directories**:
   ```bash
   mkdir -p /home/YOUR_CPANEL_USERNAME/757built_data
   mkdir -p /home/YOUR_CPANEL_USERNAME/757built_models
   mkdir -p /home/YOUR_CPANEL_USERNAME/757built_data/temp_queue
   ```

3. **Download the setup script**:
   ```bash
   wget -O /home/YOUR_CPANEL_USERNAME/757built_scripts/setup-server1-h100-cpanel.sh https://raw.githubusercontent.com/your-username/757built.com/main/setup-server1-h100-cpanel.sh
   chmod +x /home/YOUR_CPANEL_USERNAME/757built_scripts/setup-server1-h100-cpanel.sh
   ```

4. **Edit the script to use your cPanel username**:
   ```bash
   # Open the script in an editor
   nano /home/YOUR_CPANEL_USERNAME/757built_scripts/setup-server1-h100-cpanel.sh
   
   # Replace YOUR_CPANEL_USERNAME with your actual cPanel username
   # Save and exit
   ```

### Run the Setup Script

Execute the setup script as root:

```bash
cd /home/YOUR_CPANEL_USERNAME/757built_scripts
sudo ./setup-server1-h100-cpanel.sh
```

This script will:
- Install required dependencies using yum (AlmaLinux package manager)
- Configure Redis for distributed job queue
- Install and configure IPFS
- Set up llama.cpp for Phi-3 model inference
- Create necessary scripts for running the services
- Configure cronjobs for IPFS pinning
- Generate startup scripts compatible with cPanel environment

### Post-Setup Tasks

1. **Download the Phi-3 model**:
   ```bash
   wget -O /home/YOUR_CPANEL_USERNAME/757built_models/phi3-q3_k_l.gguf https://huggingface.co/microsoft/phi-3-mini-4k-instruct-gguf/resolve/main/phi-3-mini-4k-instruct.Q4_K_M.gguf
   ```

2. **Configure IPFS pinning service** (optional):
   ```bash
   ipfs pin remote service add pinata https://api.pinata.cloud/psa YOUR_PINATA_JWT_TOKEN
   ```

3. **Start the services**:
   ```bash
   /home/YOUR_CPANEL_USERNAME/757built_scripts/start_services.sh
   ```

4. **Verify the setup**:
   ```bash
   # Check service status
   /home/YOUR_CPANEL_USERNAME/757built_scripts/monitor_cluster.sh
   
   # Check API status
   curl http://localhost:5000/api/storage/status
   ```

5. **Configure firewall to allow H100 nodes to connect**:
   ```bash
   # Allow Redis connections from H100 nodes
   sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="H100_NODE_IP" port protocol="tcp" port="6379" accept'
   
   # Allow API connections from H100 nodes
   sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="H100_NODE_IP" port protocol="tcp" port="5000" accept'
   
   # Reload firewall
   sudo firewall-cmd --reload
   ```

## Step 2: H100 Cluster Setup on Prime Intellect

### Provision H100 Instances

1. Log in to [Prime Intellect dashboard](https://app.primeintellect.ai/dashboard/clusters)

2. Create a new cluster with:
   - Ubuntu 22 image
   - United States location
   - H100_80GB GPU type
   - Quantity as needed (4+ recommended)

3. Take note of the IPs assigned to your H100 nodes

### Configure Each H100 Node

For each H100 node:

1. **Copy the setup script**:
   ```bash
   # From server1
   scp /home/YOUR_CPANEL_USERNAME/757built_scripts/h100-cluster/setup_h100_node.sh ubuntu@H100_NODE_IP:/tmp/
   ```

2. **SSH into the H100 node**:
   ```bash
   ssh ubuntu@H100_NODE_IP
   ```

3. **Edit the script with server1's IP**:
   ```bash
   # Replace SERVER1_IP with your actual server1 IP address
   sudo sed -i 's/REPLACE_WITH_SERVER1_IP/YOUR_SERVER1_IP/' /tmp/setup_h100_node.sh
   ```

4. **Run the setup script**:
   ```bash
   sudo bash /tmp/setup_h100_node.sh
   ```

5. **Verify the node is registered**:
   ```bash
   # On server1, check if the node is registered
   redis-cli smembers active_workers
   redis-cli hgetall storage_nodes
   ```

## Step 3: Monitoring and Scaling

### Monitoring the Cluster

1. **Use the monitoring script**:
   ```bash
   /home/YOUR_CPANEL_USERNAME/757built_scripts/monitor_cluster.sh
   ```

2. **Check the web status page**:
   ```
   https://yourdomain.com/757built_status.php
   ```

3. **Monitor individual nodes**:
   ```bash
   # Connect to a specific H100 node
   ssh ubuntu@H100_NODE_IP
   
   # Check service status
   systemctl status 757built-worker
   systemctl status 757built-storage
   
   # Check logs
   journalctl -u 757built-worker -f
   ```

### Adding More Nodes

To scale the cluster:

1. **Provision additional H100 instances** in Prime Intellect dashboard

2. **Repeat the node setup process** for each new instance

3. **Verify new nodes are registered**:
   ```bash
   # On server1
   redis-cli smembers active_workers
   redis-cli hgetall storage_nodes
   ```

## Troubleshooting

### Common Issues on Server1 (AlmaLinux 8 cPanel)

1. **Services not starting**:
   - Check if Redis is running: `redis-cli ping`
   - Check IPFS daemon status: `ps aux | grep ipfs`
   - Check process logs: `/home/YOUR_CPANEL_USERNAME/757built_scripts/run_processor.sh`

2. **Permission issues**:
   - Ensure proper ownership: `chown -R YOUR_CPANEL_USERNAME:YOUR_CPANEL_USERNAME /home/YOUR_CPANEL_USERNAME/757built_*`
   - Check SELinux: `sestatus` and adjust if needed

3. **Network connectivity**:
   - Check firewall settings: `firewall-cmd --list-all`
   - Test connectivity: `telnet H100_NODE_IP 6379`

### Common Issues on H100 Nodes

1. **Worker not connecting to server1**:
   - Check Redis connectivity: `telnet SERVER1_IP 6379`
   - Verify correct server1 IP in configuration

2. **GPU not detected**:
   - Check CUDA installation: `nvidia-smi`
   - Verify PyTorch can access GPU: `python3 -c "import torch; print(torch.cuda.is_available())"`

## Security Considerations

1. **API access control**:
   - Consider adding API key authentication
   - Use HTTPS for all API endpoints

2. **Redis security**:
   - Bind Redis to localhost when possible
   - Use Redis passwords for authentication

3. **Script security**:
   - Keep all scripts outside the web root
   - Use proper file permissions

4. **Regular updates**:
   - Keep all system packages updated
   - Update Python dependencies regularly

## Next Steps

Once your system is running:

1. **Configure CI/CD automation**:
   - Add GitHub secrets:
     - IPFS_API: `/ip4/127.0.0.1/tcp/5001`
     - GRAPH_IPNS_KEY: `757built_graph_key`

2. **Start document ingestion**:
   - Begin uploading documents to the processing queue
   - Monitor processing through the API

3. **Optimize performance**:
   - Adjust batch sizes and worker counts based on load
   - Monitor GPU utilization on H100 nodes

4. **Implement backup strategy**:
   - Regular database backups
   - IPFS pin replication