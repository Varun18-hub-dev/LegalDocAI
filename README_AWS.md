# 🚀 LegalDocAI — AWS Deployment Guide

This guide details the steps to deploy `LegalDocAI` to the **AWS Cloud Platform** with 100% data persistence (preventing database wipeouts or file deletion on container restarts) and automated database self-seeding.

---

## 🏛️ Architecture Overview
LegalDocAI compiles the React frontend and runs the FastAPI backend inside a single unified Docker container. To maintain persistent contract uploads, SQLite databases, and vector stores, we mount a persistent volume at `/data` in the container.

We support two primary AWS deployment pathways:
1. **Method A: AWS EC2 (Single VM + EBS)** — *Recommended: Simple, cheap, and easiest to manage.*
2. **Method B: AWS ECS Fargate + EFS** — *Recommended for production environments requiring auto-scaling and high availability.*

---

## 💻 Method A: AWS EC2 (Recommended)

This method deploys the container to an Ubuntu EC2 instance using `docker-compose`.

### Step 1: Launch an EC2 Instance
1. Log into your **AWS Console** and go to **EC2**.
2. Click **Launch Instance**:
   * **AMI**: `Ubuntu Server 22.04 LTS` (64-bit).
   * **Instance Type**: `t3.medium` (2 vCPUs, 4GB RAM) or larger to handle document vector generation.
   * **Storage (EBS)**: 20 GB gp3 root volume.
   * **Key Pair**: Create or select a key pair for SSH access.
3. Under **Network Settings**, create a Security Group allowing:
   * `TCP port 22` (SSH from your IP)
   * `TCP port 80` (HTTP from anywhere)
   * `TCP port 443` (HTTPS from anywhere)
   * `TCP port 8000` (FastAPI backend port from anywhere)

### Step 2: Install Docker and Docker Compose on EC2
Connect to your EC2 instance via SSH and run:
```bash
sudo apt update && sudo apt upgrade -y
# Install Docker
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and log back in to apply docker group permissions
exit
```

### Step 3: Deploy the Application
1. Reconnect to the instance and clone your GitHub repository:
   ```bash
   git clone https://github.com/your-username/LegalAIDoc.git
   cd LegalAIDoc
   ```
2. Create a `.env` file at the root of the cloned directory:
   ```bash
   nano .env
   ```
   Add the following variables (replacing with your keys and IP/Domain):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   JWT_SECRET_KEY=generate_a_random_secure_hex_key
   ADMIN_EMAIL=admin@legaldocai.com
   ADMIN_PASSWORD=your_secure_admin_password
   FRONTEND_URL=http://your-ec2-public-ip:8000
   CORS_ORIGINS=http://your-ec2-public-ip:8000
   ```
3. Start the application in the background:
   ```bash
   docker-compose up -d --build
   ```

### Step 4: Persistent Volumes & Seeding
* **Persistence**: Docker Compose maps the host folder `./data` to `/data` in the container. SQLite, ChromaDB, and PDFs are saved here and will never vanish, even if you stop, rebuild, or destroy the container.
* **Automatic KB Seeding**: On the first start, the system detects that the database is blank. It automatically spawns a background thread to download and ingest BNS, BNSS, BSA, and the Constitution. Within 2–3 minutes, Global search will work out-of-the-box.

---

## 🎛️ Method B: AWS ECS Fargate + EFS (Serverless)

This method deploys the container to a serverless container environment with serverless file storage.

### Step 1: Create an EFS File System
1. Go to **AWS EFS** (Elastic File System).
2. Click **Create file system**. Set the VPC to match the one you will use for ECS.
3. Under **Access Points**, create an access point:
   * **Path**: `/data`
   * **User/Group ID**: `1000` (or root `0`).
   * **Permissions**: `0777` (full access).

### Step 2: Push your Image to AWS ECR
1. Go to **AWS ECR** (Elastic Container Registry) and create a repository named `legaldocai`.
2. Retrieve the push commands from ECR, authenticate, and push your container image:
   ```bash
   aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
   docker build -t legaldocai .
   docker tag legaldocai:latest your-account-id.dkr.ecr.your-region.amazonaws.com/legaldocai:latest
   docker push your-account-id.dkr.ecr.your-region.amazonaws.com/legaldocai:latest
   ```

### Step 3: Create an ECS Task Definition
1. Go to **AWS ECS** -> **Task Definitions** -> **Create new Task Definition with JSON**.
2. Define the container using Fargate (e.g. 1 vCPU, 2GB or 4GB memory).
3. **Volume Configuration**:
   * Add a volume named `legaldocai-efs-volume`. Select **EFS** as the volume type, pick the file system ID created in Step 1, and specify `/data` as the directory.
4. **Container Mount Point**:
   * Under Container Mount Points, map container path `/data` to the EFS volume.
5. **Environment Variables**:
   * Pass variables (`GEMINI_API_KEY`, `DATA_DIR=/data`, `JWT_SECRET_KEY`, `ADMIN_EMAIL`, etc.) under the Container definition config.

### Step 4: Run the Service
1. Create a Fargate cluster and launch an ECS service pointing to your Task Definition.
2. If running publicly, deploy it behind an **Application Load Balancer (ALB)** mapping Port 80 to container Port 8000, and configure a security group allowing traffic.

---

## 🔒 Administration and Debugging

### Running Ingestion Manually
If you ever need to manually force a database rebuild or reset the collection, you can run the builder script directly inside the active docker container:

```bash
# Get the running container ID
docker ps

# Execute the setup script inside the container
docker exec -it legaldocai-app python scripts/build_kb_v2.py --reset
```

### Checking Ingestion Logs
To monitor the background ingestion progress on your EC2 server, run:
```bash
docker logs -f legaldocai-app
```
