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
