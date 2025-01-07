# Config Merger

Config Merger is a simple script which merges secrets with configuration files. It's original design is to work in init containers for Kubernetes deployments. However, you could really use this anywhere.

## Usage

### Kubernetes

If you are using it inside of a Kubernetes init container, you simply need to mount the secrets and configMaps you want and the ensure that you have the correct inputs and output set in the flag. Here is an example of how you could use it:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  template:
    spec:
      initContainers:
      - name: config-init
        image: vo1d/config-merger:v1.0.0
        command: ['/bin/sh', '-c']
        args: ['-i ,'tmp','-o',/output/config']
        volumeMounts:
        - name: config
          mountPath: /tmp/config
        - name: secrets
          mountPath: /tmp/secrets
        - name: merged-config
          mountPath: /output/config
      containers:
      - name: my-deployment
        image: my-deployment-image
        volumeMounts:
        - name: merged-config
          mountPath: /app/config
      volumes:
      - name: config
        configMap:
          name: my-deployment-config
      - name: secrets
        secret:
          secretName: my-deployment-secrets
      - name: merged-config
        emptyDir: {}
```