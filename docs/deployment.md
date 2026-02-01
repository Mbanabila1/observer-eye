# Observer Eye Platform - Cross-Platform Deployment Guide

## Overview

The Observer Eye Platform supports deployment across Linux, macOS, and Windows systems using Docker containerization. This guide provides platform-specific instructions for optimal deployment and configuration.

## Prerequisites by Platform

### Linux (Ubuntu/Debian/CentOS/RHEL)

**System Requirements:**
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
- 4GB RAM minimum (8GB recommended)
- 20GB free disk space
- Internet connection

**Required Software:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y curl wget git

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# CentOS/RHEL
sudo yum update -y
sudo yum install -y curl wget git

# Install Docker (CentOS/RHEL)
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### macOS

**System Requirements:**
- macOS 10.15 (Catalina) or later
- 4GB RAM minimum (8GB recommended)
- 20GB free disk space
- Internet connection

**Required Software:**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install git curl wget

# Install Docker Desktop
brew install --cask docker

# Alternative: Download from https://www.docker.com/products/docker-desktop
```

### Windows

**System Requirements:**
- Windows 10 Pro/Enterprise/Education (64-bit) or Windows 11
- WSL 2 enabled
- 4GB RAM minimum (8GB recommended)
- 20GB free disk space
- Internet connection

**Required Software:**
1. **Enable WSL 2:**
   ```powershell
   # Run as Administrator
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   
   # Restart computer, then set WSL 2 as default
   wsl --set-default-version 2
   
   # Install Ubuntu from Microsoft Store
   ```

2. **Install Docker Desktop:**
   - Download from https://www.docker.com/products/docker-desktop
   - Enable WSL 2 integration during installation

3. **Install Git:**
   - Download from https://git-scm.com/download/win
   - Or use: `winget install Git.Git`

## Platform-Specific Deployment

### Linux Deployment

#### Production Deployment on Linux

**1. System Preparation:**
```bash
# Create application user
sudo useradd -m -s /bin/bash observer-eye
sudo usermod -aG docker observer-eye

# Create application directory
sudo mkdir -p /opt/observer-eye
sudo chown observer-eye:observer-eye /opt/observer-eye

# Switch to application user
sudo su - observer-eye
cd /opt/observer-eye
```

**2. Clone and Configure:**
```bash
# Clone repository
git clone <repository-url> .

# Create environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp middleware/.env.example middleware/.env
cp dashboard/.env.example dashboard/.env

# Edit configuration files
nano .env  # Configure for production
```

**3. SSL Certificate Setup:**
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/private.key \
  -out nginx/ssl/certificate.crt

# Or copy your SSL certificates
# cp /path/to/your/certificate.crt nginx/ssl/
# cp /path/to/your/private.key nginx/ssl/
```

**4. Deploy with Docker Compose:**
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
docker-compose exec backend python manage.py createsuperuser

# Check service status
docker-compose ps
```

**5. Configure Systemd Service:**
```bash
# Create systemd service file
sudo tee /etc/systemd/system/observer-eye.service > /dev/null <<EOF
[Unit]
Description=Observer Eye Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/observer-eye
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=observer-eye
Group=observer-eye

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable observer-eye
sudo systemctl start observer-eye
```

**6. Configure Firewall:**
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

**7. Setup Log Rotation:**
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/observer-eye > /dev/null <<EOF
/opt/observer-eye/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 observer-eye observer-eye
    postrotate
        docker-compose -f /opt/observer-eye/docker-compose.prod.yml restart
    endscript
}
EOF
```

### macOS Deployment

#### Development Setup on macOS

**1. System Preparation:**
```bash
# Create project directory
mkdir -p ~/Projects/observer-eye
cd ~/Projects/observer-eye

# Clone repository
git clone <repository-url> .
```

**2. Configure Environment:**
```bash
# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp middleware/.env.example middleware/.env
cp dashboard/.env.example dashboard/.env

# Edit configuration (use your preferred editor)
code .env  # VS Code
# or
nano .env
```

**3. Start Docker Desktop:**
```bash
# Ensure Docker Desktop is running
open -a Docker

# Wait for Docker to start (check with)
docker info
```

**4. Deploy Application:**
```bash
# Start development environment
docker-compose up -d

# Initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# Check services
docker-compose ps
```

#### Production Deployment on macOS Server

**1. Install Additional Tools:**
```bash
# Install nginx for reverse proxy
brew install nginx

# Install certbot for SSL certificates
brew install certbot
```

**2. Configure Nginx:**
```bash
# Create nginx configuration
sudo tee /usr/local/etc/nginx/servers/observer-eye.conf > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /usr/local/etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /usr/local/etc/nginx/ssl/private.key;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8400/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Start nginx
sudo brew services start nginx
```

**3. Setup Launch Daemon:**
```bash
# Create launch daemon for auto-start
sudo tee /Library/LaunchDaemons/com.observer-eye.plist > /dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.observer-eye</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker-compose</string>
        <string>-f</string>
        <string>/path/to/observer-eye/docker-compose.prod.yml</string>
        <string>up</string>
        <string>-d</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/observer-eye</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load launch daemon
sudo launchctl load /Library/LaunchDaemons/com.observer-eye.plist
```

### Windows Deployment

#### Development Setup on Windows

**1. Setup WSL 2 Environment:**
```powershell
# Open PowerShell as Administrator and install Ubuntu
wsl --install -d Ubuntu

# Restart computer if required
# Open Ubuntu terminal and update
sudo apt update && sudo apt upgrade -y

# Install required tools
sudo apt install -y curl wget git
```

**2. Install Docker in WSL 2:**
```bash
# In Ubuntu WSL terminal
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Restart WSL
exit
# In PowerShell: wsl --shutdown
# Open Ubuntu terminal again
```

**3. Clone and Configure:**
```bash
# In Ubuntu WSL terminal
cd ~
git clone <repository-url> observer-eye
cd observer-eye

# Configure environment
cp .env.example .env
cp backend/.env.example backend/.env
cp middleware/.env.example middleware/.env
cp dashboard/.env.example dashboard/.env

# Edit configuration files
nano .env
```

**4. Deploy Application:**
```bash
# Start services
docker-compose up -d

# Initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# Check status
docker-compose ps
```

#### Production Deployment on Windows Server

**1. Install Windows Features:**
```powershell
# Run as Administrator
Enable-WindowsOptionalFeature -Online -FeatureName containers -All
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -All
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All

# Restart computer
```

**2. Install Docker Desktop:**
```powershell
# Download and install Docker Desktop
# Enable WSL 2 integration

# Verify installation
docker --version
docker-compose --version
```

**3. Configure Windows Service:**
```powershell
# Create PowerShell script for service management
$scriptPath = "C:\observer-eye\start-observer-eye.ps1"
@"
Set-Location "C:\observer-eye"
docker-compose -f docker-compose.prod.yml up -d
"@ | Out-File -FilePath $scriptPath -Encoding UTF8

# Create Windows Service
New-Service -Name "ObserverEye" -BinaryPathName "powershell.exe -File $scriptPath" -DisplayName "Observer Eye Platform" -StartupType Automatic
```

**4. Configure IIS Reverse Proxy (Optional):**
```powershell
# Install IIS and URL Rewrite module
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole -All
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServer -All
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpRedirect -All

# Download and install URL Rewrite module from Microsoft
# Configure reverse proxy rules in IIS Manager
```

## Platform-Specific Optimizations

### Linux Optimizations

**1. Kernel Parameters:**
```bash
# Add to /etc/sysctl.conf
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
echo "fs.file-max=65536" | sudo tee -a /etc/sysctl.conf
echo "net.core.somaxconn=65535" | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

**2. Docker Daemon Configuration:**
```bash
# Create Docker daemon configuration
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
EOF

# Restart Docker
sudo systemctl restart docker
```

### macOS Optimizations

**1. Docker Desktop Settings:**
```bash
# Increase Docker Desktop resources
# Go to Docker Desktop > Preferences > Resources
# Set Memory: 4GB+
# Set CPUs: 2+
# Set Disk: 20GB+
```

**2. File System Performance:**
```bash
# Use Docker volumes for better performance
# Avoid bind mounts for large datasets
# Use cached or delegated consistency for bind mounts
```

### Windows Optimizations

**1. WSL 2 Configuration:**
```powershell
# Create .wslconfig in user home directory
@"
[wsl2]
memory=4GB
processors=2
swap=2GB
"@ | Out-File -FilePath "$env:USERPROFILE\.wslconfig" -Encoding UTF8

# Restart WSL
wsl --shutdown
```

**2. Docker Desktop Settings:**
```powershell
# Configure Docker Desktop resources
# Enable WSL 2 based engine
# Allocate sufficient memory and CPU
# Enable file sharing for project directories
```

## Monitoring and Maintenance

### Linux Monitoring

**1. System Monitoring:**
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Monitor Docker containers
docker stats

# Monitor logs
docker-compose logs -f --tail=100

# System health check
systemctl status observer-eye
```

**2. Automated Maintenance:**
```bash
# Create maintenance script
tee ~/maintenance.sh > /dev/null <<EOF
#!/bin/bash
cd /opt/observer-eye

# Update containers
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f

# Backup database
./scripts/backup-db.sh

# Check disk space
df -h
EOF

chmod +x ~/maintenance.sh

# Add to crontab for weekly maintenance
(crontab -l 2>/dev/null; echo "0 2 * * 0 /home/observer-eye/maintenance.sh") | crontab -
```

### macOS Monitoring

**1. System Monitoring:**
```bash
# Monitor system resources
top -o cpu

# Monitor Docker containers
docker stats

# Check logs
docker-compose logs -f
```

**2. Automated Updates:**
```bash
# Create update script
tee ~/update-observer-eye.sh > /dev/null <<EOF
#!/bin/bash
cd ~/Projects/observer-eye

# Pull latest changes
git pull

# Update containers
docker-compose pull
docker-compose up -d

# Clean up
docker system prune -f
EOF

chmod +x ~/update-observer-eye.sh
```

### Windows Monitoring

**1. System Monitoring:**
```powershell
# Monitor system resources
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10

# Monitor Docker containers
docker stats

# Check Windows Event Log
Get-EventLog -LogName Application -Source "Observer Eye" -Newest 10
```

**2. Automated Maintenance:**
```powershell
# Create maintenance script
$maintenanceScript = @"
Set-Location "C:\observer-eye"
docker-compose pull
docker-compose up -d
docker system prune -f
"@

$maintenanceScript | Out-File -FilePath "C:\observer-eye\maintenance.ps1" -Encoding UTF8

# Schedule with Task Scheduler
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\observer-eye\maintenance.ps1"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "Observer Eye Maintenance"
```

## Troubleshooting by Platform

### Linux Troubleshooting

**Common Issues:**

1. **Permission Denied:**
   ```bash
   # Fix Docker permissions
   sudo usermod -aG docker $USER
   newgrp docker
   
   # Fix file permissions
   sudo chown -R $USER:$USER /opt/observer-eye
   ```

2. **Port Already in Use:**
   ```bash
   # Find process using port
   sudo netstat -tulpn | grep :80
   
   # Kill process
   sudo kill -9 <PID>
   ```

3. **Out of Disk Space:**
   ```bash
   # Clean Docker system
   docker system prune -a
   
   # Clean logs
   sudo journalctl --vacuum-time=7d
   ```

### macOS Troubleshooting

**Common Issues:**

1. **Docker Desktop Not Starting:**
   ```bash
   # Reset Docker Desktop
   # Go to Docker Desktop > Troubleshoot > Reset to factory defaults
   
   # Or restart from command line
   killall Docker\ Desktop
   open -a Docker
   ```

2. **Port Conflicts:**
   ```bash
   # Find process using port
   lsof -i :80
   
   # Kill process
   kill -9 <PID>
   ```

3. **File Permission Issues:**
   ```bash
   # Fix permissions
   chmod -R 755 ~/Projects/observer-eye
   ```

### Windows Troubleshooting

**Common Issues:**

1. **WSL 2 Issues:**
   ```powershell
   # Restart WSL
   wsl --shutdown
   wsl
   
   # Update WSL
   wsl --update
   ```

2. **Docker Desktop Issues:**
   ```powershell
   # Restart Docker Desktop
   Stop-Process -Name "Docker Desktop" -Force
   Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
   ```

3. **Network Issues:**
   ```powershell
   # Reset network
   netsh winsock reset
   netsh int ip reset
   # Restart computer
   ```

## Performance Benchmarks

### Expected Performance by Platform

**Linux (Ubuntu 20.04, 8GB RAM, 4 CPU cores):**
- Container startup time: 30-60 seconds
- API response time: < 100ms
- Database query time: < 50ms
- Memory usage: 2-4GB total
- CPU usage: 10-30% under normal load

**macOS (macOS 12, 16GB RAM, 8 CPU cores):**
- Container startup time: 45-90 seconds
- API response time: < 150ms
- Database query time: < 75ms
- Memory usage: 3-5GB total
- CPU usage: 15-35% under normal load

**Windows (Windows 11, 16GB RAM, 8 CPU cores):**
- Container startup time: 60-120 seconds
- API response time: < 200ms
- Database query time: < 100ms
- Memory usage: 4-6GB total
- CPU usage: 20-40% under normal load

## Security Considerations by Platform

### Linux Security

```bash
# Configure firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Secure SSH
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### macOS Security

```bash
# Enable firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Configure automatic updates
sudo softwareupdate --schedule on

# Secure Docker
# Ensure Docker Desktop is configured to not expose daemon
```

### Windows Security

```powershell
# Enable Windows Defender
Set-MpPreference -DisableRealtimeMonitoring $false

# Configure Windows Firewall
New-NetFirewallRule -DisplayName "Observer Eye HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "Observer Eye HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow

# Enable automatic updates
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update" -Name "AUOptions" -Value 4
```

For additional platform-specific guidance, refer to the [Installation Guide](installation.md) and [Configuration Guide](configuration.md).