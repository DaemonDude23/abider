# use k3d cluster context
allow_k8s_contexts("k3d-abider")

# apply locally rendered manifests from helm
k8s_yaml(kustomize('./dev/k3d/k8s/abider/'))

# build abider container images
# I only really enable this for Alpine before a release to test
# docker_build("abider.k3d.internal:5000/abider-alpine:latest", "./src", dockerfile='./src/Dockerfile-alpine-dev')
docker_build("abider.k3d.internal:5000/abider/debian:latest", "./src", dockerfile='./src/Dockerfile-debian-dev')

# debugpy port-forward ports
k8s_resource(workload='abider', port_forwards=['127.0.0.1:5678:5678'])
