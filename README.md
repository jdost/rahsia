# Rahsia

A small k8s service/controller that facilitates declaring requested secrets in 
public manifests and defining the secret values out of band.  This is really just
meant to be a small learning experience for my personal use as I found the need for
some of the more robust options (like Vault or the various cloud provider options)
unnecessary for my home lab.

It is made up of 3 parts:

1. The k8s CRD/manifest (the manifest is really just the permission for the service
   to access and watch the CRD and Secrets)
2. A HTTP/k8s controller service that watches the K8s resources and provides an HTTP
   interface for manipulating/reconciling the requested and actual state of secrets
3. A React based frontend for easily seeing the state and filling missing/outdated
   secrets

## Deploying

I have included some base k8s manifests defined via kustomize, if you just want to
deploy locally (with kustomize) you can add a `kustomization.yaml` file like:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- https://github.com/jdost/rahsia//manifests/?timeout=120
```

and then you can just deploy/apply via `kubectl apply -k .` and it will generate the
resources via kustomize and deploy.  (See kustomize docs for various transforms,
can include additional resources like an ingress if you want one)

## Developing

Since the k8s side is written to expect being in cluster, you should go into the
`rahsia/apis/k8s.py` file and change the `config.load_incluster_config()` call with
a manual `config.load_config` call with the target config and context.  (see the
example in the comment there)
