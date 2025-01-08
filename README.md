# Config Merger

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Config Merger is a simple script which merges secrets with configuration files. It's original design is to work in init containers for Kubernetes workloads. However, you could really use this anywhere.

## Key Concepts

Config Merger uses two types of files:

- Configurations
- Secrets

### Configurations

Configuration files are files that contain the configuration for your application. These files should be in `yaml` or `json` (You can also use both at the same time). The configuration files should contain placeholders for where you want to replace your secrets.

For example:

```yaml
password: ${MY_SECRET_PASSWORD}
```

You can have as many configuration files as you want. The script will merge all of them together.

> **Note**: If you have duplicate keys in your configuration files, by default, the first will be used. See [Merge Strategies](#merge-strategies) for more information.

### Secrets

Secrets are the files which contain the sensitive data. These much follow top-level YAML or JSON format. The keys in the secrets file should match the placeholders in the configuration files.

Following our configuration example, this would be the corresponding secret file:

```yaml
MY_SECRET_PASSWORD: mypassword
```

Secrets also follow the same merge strategy as configurations.

### Merge Strategies

There are three types of merge strategies:

- `first-wins`: This is the default strategy. It will take the first value it finds and replace the placeholder with that value.
- `last-wins`: This will take the last value it finds and replace the placeholder with that value.
- `error-on-conflict`: This will error if there are multiple values for the same placeholder.

You can set your merge strategy by using the `--merge-strategy` or `-m` flag. If no flag is set, it will just use the default.


## Usage

As mentioned, the primary use case is for Kubernetes init  containers, so we will focus on that. However, you could use this in any environment where you need to merge secrets with configuration files.

### Kubernetes

#### Configuration Example

Here is an example of how your configMap might look:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-deployment-config
data:
  config.yaml: |
    settings:
      debug: false
      logFormat: json
      database:
        host: localhost
        port: 5432
        user: ${DATABASE_USER}
        password: ${DATABASE_PASSWORD}
```

And now in your secret you would have the following:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-deployment-secrets
stringData:
  DATABASE_USER: myuser
  DATABASE_PASSWORD: mypassword
```

> **Note**: You can use `data` or `stringData` for your secrets. When you mount your secrets to the init container, they will be automatically converted to the files necessary for the script to work.

When the script runs, you will have the following for your config file in your container:

```yaml
# /app/config/config.yaml
settings:
  debug: false
  logFormat: json
  database:
    host: localhost
    port: 5432
    user: myuser
    password: mypassword
```

When using it inside of a Kubernetes init container, you simply need to mount the secrets, configMaps, and the final volume where your container will have the configuration provided to it. You want and the ensure that you have the correct inputs and output set in the flag. Here is an example of how you could use it:

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
          items:
          - key: secrets.yaml
            path: secrets.yaml
      - name: my-deployment-config
        configMap:
          name: my-deployment-config
          items:
          - key: config.yaml
            path: config.yaml
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

## Build your own image

If you want to build your own image, make sure to define the following for the `Makefile`:

- `IMAGE_NAME`: The registry, and repository name for your image.
- `TAG`: The tag for your image.

Then you can run the following command to build your image:

```bash
make build
```

> **Note**: The `build` target also tags the image with the `latest` tag.

If you have access to the registry and repository, you can also run

```bash
make push
```

This will push the image to the registry and repository you defined in the `Makefile`.

> **Note**: This pushes the `latest` tag as well.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.