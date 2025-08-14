.. _installhelm:

Installation with Helm on Kubernetes
====================================

This is the installation guide for GeoHealthCheck with Helm on Kubernetes.

Requirements
------------

* Access to a Kubernetes cluster with an officially supported version of Kubernetes
* The Helm chart in this repository
* A values file containing your customizations to the default values

Install
-------

.. code-block:: bash
  helm upgrade --install geohealthcheck -f mycustomvalues.yaml <path/to/helmchart/directory>


When everything succeeded you will get an output like the following:

.. code-block:: bash
  1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace <your-namespace> -l "app.kubernetes.io/name=geohealthcheck,app.kubernetes.io/instance=geohealthcheck" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace <your-namespace> $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace <your-namespace> port-forward $POD_NAME 8080:$CONTAINER_PORT
