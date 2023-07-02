Set up virtual environment:

```bash
virtualenv --python=python3.11.4 ./venv/
source ./venv/bin/activate
pip3 install -U -r ./src/requirements.txt
pip3 install -U -r ./docs/requirements.txt
```

```bash
pip3 install -U -r ./src/requirements-dev.txt
```

Freeze requirements for version pinning:

```bash
pip freeze -r ./src/requirements-dev.txt
```

Manually run `mypy` against code:

```bash
mypy --strict --install-types src/
```

# Compile / Create Image

## Create Cluster

- [https://hub.docker.com/r/rancher/k3s/tags](https://hub.docker.com/r/rancher/k3s/tags)

```bash
cd $HOME/abider
k3d cluster create abider -c ./dev/k3d/config.yaml
```

View kubeconfig
```bash
k3d kubeconfig get abider > ~/.kube/config
```

Use its context:
```bash
kubectl config use-context k3d-abider
```

## Install

### All in one

cd to this directory after cloning

```bash
sudo systemctl start docker && \
  k3d cluster start abider; \
  kubectl config use-context k3d-abider; \
  tilt up
```

```bash
k3d cluster stop abider; sudo systemctl stop docker.socket
```

```bash
helmizer ./dev/k3d/k8s/abider/helmizer.yaml
```

# Delete

```bash
k3d cluster delete abider
```
