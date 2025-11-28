# Ledian's To-Do App

A modern Flask-based To-Do List app with:

- A clean ocean-inspired glassmorphism UI  
- SQLite backend  
- REST API (`/api/todos`)  
- Background video support  
- Full CI/CD pipeline via GitHub Actions  
- Azure Web App deployment (Docker container)  
- Monitoring endpoints (`/health`, `/metrics`)  
- Prometheus-compatible metrics (requests, latency, errors)

---

## 🚀 Run Locally

### **1. Clone the repo**
```bash
git clone https://github.com/<YOUR-REPO>.git
cd to-do-list 
```
### **2. Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# OR
.venv\Scripts\activate          # Windows
```
### **3. Install dependencies**
```bash
pip install -r requirements.txt
```
### **4. Run the app**
```bash
python server.py
```
### **5. Visit it in the browser**
```
http://localhost:5001
```
## **Testing 🧪**
### **1. Run tests**
```bash
pytest
```
### **2. Run tests with coverage**
```bash
pytest --cov=server
```
## **Docker 🐳**
### **1. Build the image**
```
docker build -t todo-app .
```
### **2. Run the container**
```
docker run -p 5001:5001 todo-app
```
## **CI/CD pipelines📈**
```
GitHub Actions automates:

+ Linting and testing

+ Docker image build

+ Docker Hub push

+ Azure Web App deployment

Any push to ```main``` triggers the full pipeline.
```
## **Health Checks and Monitoring**
```bash
GET /health
```




