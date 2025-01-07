# Config Merger

Config Merger is a simple script which merges secrets with configuration files. It's original design is to work in init containers for Kubernetes workloads. However, you could really use this anywhere.

## Usage

As mentioned, the primary use case is for Kubernetes init  containers, so we will focus on that. However, you could use this in any environment where you need to merge secrets with configuration files.

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
        image: vo1d/config-merger:latest 
        # You could just mount the whole 'tmp' directory if you want, but this is more explicit
        args: ['-i ,'tmp/config','tmp/secrets','-o',/app/config']
        volumeMounts:
        - name: my-deployment-config
          readOnly: true
          mountPath: /tmp/config
        - name: my-deployment-secrets
          readOnly: true
          mountPath: /tmp/secrets
        - name: merged-config
          mountPath: /app/config
      containers:
      - name: my-deployment
        image: my-deployment-image
        volumeMounts:
        - name: merged-config
          readOnly: true
          mountPath: /app/config
      volumes:
      - name: my-deployment-secrets
        secret:
          secretName: my-deployment-secrets
      - name: my-deployment-config
        configMap:
          name: my-deployment-config
      - name: merged-config
        emptyDir: {}
```

Now you can mount your secrets and configMaps to the init container and it will merge them together and output the result to the merged-config volume. You can then mount that volume to your application container.

### Local

For local usage, you can just run the container and mount the directories you want to merge. Here is an example:

```bash
docker run -v /path/to/config:/tmp/config -v /path/to/secrets:/tmp/secrets -v /path/to/output:/output vo1d/config-merger:latest -i /tmp -o /output
```

Alternatively, you can use the `Makefile` which will run it for you:

```bash
make run
```

> **Note:** The Makefile is setup for development purposes and only looks at the `test` directory for the input and outputs to `output.yaml`. You can modify this for your purposes but you'll need to modify the Makefile.

