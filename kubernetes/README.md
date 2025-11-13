# Kubernetes Deployment for ARK Trading Intelligence

Complete Kubernetes deployment manifests for production-ready trading intelligence backend.

## 📋 Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` CLI configured
- Docker registry access (for image storage)
- NGINX Ingress Controller (for ingress)
- cert-manager (for SSL certificates) - optional

## 🚀 Quick Start

### 1. Build and Push Docker Image

```bash
# Build image
docker build -f Dockerfile.api -t your-registry/ark-trading-api:v1.0.0 .

# Push to registry
docker push your-registry/ark-trading-api:v1.0.0
```

### 2. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 3. Create ConfigMap and Secrets

```bash
# Apply ConfigMap
kubectl apply -f configmap.yaml

# Create Secret from .env file
kubectl create secret generic ark-api-secret \
  --from-literal=TELEGRAM_BOT_TOKEN="your_bot_token" \
  --from-literal=TELEGRAM_CHAT_ID="your_chat_id" \
  --from-literal=ALPACA_API_KEY="your_alpaca_key" \
  --from-literal=ALPACA_API_SECRET="your_alpaca_secret" \
  --namespace=ark-trading

# Or from file
kubectl apply -f secret.yaml  # After editing secret.yaml.example
```

### 4. Deploy Application

```bash
# Deploy API
kubectl apply -f deployment.yaml

# Create Service
kubectl apply -f service.yaml

# Create Ingress (optional)
kubectl apply -f ingress.yaml

# Create HPA (optional)
kubectl apply -f hpa.yaml
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n ark-trading

# Check services
kubectl get svc -n ark-trading

# Check ingress
kubectl get ingress -n ark-trading

# View logs
kubectl logs -f deployment/ark-api -n ark-trading

# Check health
kubectl exec -it deployment/ark-api -n ark-trading -- curl http://localhost:8000/api/v1/health
```

## 📦 Manifest Files

### namespace.yaml
Creates `ark-trading` namespace for all resources.

### configmap.yaml
Application configuration (non-sensitive):
- Log level
- Account size
- Pattern matching thresholds
- API settings

### secret.yaml.example
Sensitive credentials (template):
- Telegram bot token
- Data provider API keys
- Database credentials

**⚠️ Never commit actual secrets to git!**

### deployment.yaml
Main API deployment:
- 2 replicas (configurable)
- Resource limits (512Mi-2Gi memory, 0.5-2 CPU)
- Health checks (liveness, readiness, startup)
- Volume mounts for config and logs

### service.yaml
Two services:
- `ark-api-service` - ClusterIP (internal)
- `ark-api-external` - LoadBalancer (external)

### ingress.yaml
HTTPS ingress with:
- SSL/TLS termination
- Rate limiting
- CORS support
- cert-manager integration

### hpa.yaml
Horizontal Pod Autoscaler:
- Min: 2 replicas
- Max: 10 replicas
- CPU target: 70%
- Memory target: 80%

## 🔧 Configuration

### Environment Variables

Set via ConfigMap and Secret:

| Variable | Source | Description | Default |
|----------|--------|-------------|---------|
| `LOG_LEVEL` | ConfigMap | Logging level | INFO |
| `ACCOUNT_SIZE` | ConfigMap | Trading account size | 100000.0 |
| `TELEGRAM_BOT_TOKEN` | Secret | Telegram bot token | - |
| `TELEGRAM_CHAT_ID` | Secret | Telegram chat ID | - |
| `ALPACA_API_KEY` | Secret | Alpaca API key | - |
| `ALPACA_API_SECRET` | Secret | Alpaca API secret | - |

### Resource Requirements

**Per Pod**:
- Memory: 512Mi request, 2Gi limit
- CPU: 500m request, 2000m limit

**Recommended Cluster**:
- Nodes: 2+ (for HA)
- Total Memory: 8Gi+
- Total CPU: 4+ cores

## 📊 Monitoring

### Health Checks

```bash
# Liveness (is pod alive?)
curl http://pod-ip:8000/api/v1/health

# Readiness (is pod ready for traffic?)
curl http://pod-ip:8000/api/v1/health
```

### Logs

```bash
# Stream logs
kubectl logs -f deployment/ark-api -n ark-trading

# Last 100 lines
kubectl logs --tail=100 deployment/ark-api -n ark-trading

# All pods
kubectl logs -l app=ark-trading-api -n ark-trading
```

### Metrics

```bash
# Pod metrics
kubectl top pods -n ark-trading

# Node metrics
kubectl top nodes
```

## 🔄 Updates

### Rolling Update

```bash
# Update image
kubectl set image deployment/ark-api \
  api=your-registry/ark-trading-api:v1.1.0 \
  -n ark-trading

# Check rollout status
kubectl rollout status deployment/ark-api -n ark-trading

# View rollout history
kubectl rollout history deployment/ark-api -n ark-trading
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/ark-api -n ark-trading

# Rollback to specific revision
kubectl rollout undo deployment/ark-api --to-revision=2 -n ark-trading
```

## 🧪 Testing

### Port Forward (Local Testing)

```bash
# Forward port 8000 to localhost
kubectl port-forward service/ark-api-service 8000:8000 -n ark-trading

# Test API
curl http://localhost:8000/api/v1/health
```

### Exec into Pod

```bash
# Get shell access
kubectl exec -it deployment/ark-api -n ark-trading -- /bin/bash

# Run Python commands
kubectl exec -it deployment/ark-api -n ark-trading -- python -c "print('Hello')"
```

## 🛡️ Security

### RBAC (Role-Based Access Control)

```yaml
# Create ServiceAccount (optional)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ark-api-sa
  namespace: ark-trading
```

### Network Policies

```yaml
# Restrict pod communication (optional)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ark-api-netpol
  namespace: ark-trading
spec:
  podSelector:
    matchLabels:
      app: ark-trading-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS for data providers
```

## 📈 Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment/ark-api --replicas=5 -n ark-trading
```

### Auto Scaling

HPA automatically scales based on CPU/memory:
- Scale up: When CPU > 70% or Memory > 80%
- Scale down: After 5 min stabilization period
- Min replicas: 2
- Max replicas: 10

## 🗑️ Cleanup

```bash
# Delete all resources
kubectl delete namespace ark-trading

# Or delete individually
kubectl delete -f .
```

## 📚 Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager](https://cert-manager.io/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## 🆘 Troubleshooting

### Pod Not Starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n ark-trading

# Check events
kubectl get events -n ark-trading --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n ark-trading --previous
```

### Health Check Failures

```bash
# Exec into pod
kubectl exec -it <pod-name> -n ark-trading -- /bin/bash

# Test health endpoint
curl http://localhost:8000/api/v1/health

# Check Python dependencies
pip list
```

### Image Pull Errors

```bash
# Check image pull secret
kubectl get secrets -n ark-trading

# Create image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<username> \
  --docker-password=<password> \
  --namespace=ark-trading

# Add to deployment
spec:
  imagePullSecrets:
  - name: regcred
```

## 📞 Support

For issues or questions:
- Check logs: `kubectl logs -f deployment/ark-api -n ark-trading`
- Review events: `kubectl get events -n ark-trading`
- Describe resources: `kubectl describe deployment/ark-api -n ark-trading`
