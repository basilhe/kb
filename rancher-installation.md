# Install Rancher with LetsEncrypt DNS-01 challenge

## Start K3S
<pre><code>
$ curl -sfL https://get.k3s.io | sh -
</code></pre>

## Install cert-manager
<pre><code>
$ kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.7.2/cert-manager.yaml
</code></pre>

## Install alidns-webhook for domain rancher.ltd
<pre><code>
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: alidns-webhook
  namespace: cert-manager
  labels:
    app: alidns-webhook

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: alidns-webhook
  namespace: cert-manager
  labels:
    app: alidns-webhook
rules:
  - apiGroups:
      - ''
    resources:
      - 'secrets'
    verbs:
      - 'get'

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: alidns-webhook:flowcontrol-solver
  labels:
    app: alidns-webhook
rules:
  - apiGroups:
      - "flowcontrol.apiserver.k8s.io"
    resources:
      - 'prioritylevelconfigurations'
      - 'flowschemas'
    verbs:
      - 'list'
      - 'watch'

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: alidns-webhook:flowcontrol-solver
  labels:
    app: alidns-webhook
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: alidns-webhook:flowcontrol-solver
subjects:
  - apiGroup: ""
    kind: ServiceAccount
    name: alidns-webhook
    namespace: cert-manager

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: alidns-webhook
  namespace: cert-manager
  labels:
    app: alidns-webhook
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: alidns-webhook
subjects:
  - apiGroup: ""
    kind: ServiceAccount
    name: alidns-webhook
    namespace: cert-manager

---
# Grant the webhook permission to read the ConfigMap containing the Kubernetes
# apiserver's requestheader-ca-certificate.
# This ConfigMap is automatically created by the Kubernetes apiserver.
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: alidns-webhook:webhook-authentication-reader
  namespace: kube-system
  labels:
    app: alidns-webhook
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: extension-apiserver-authentication-reader
subjects:
  - apiGroup: ""
    kind: ServiceAccount
    name: alidns-webhook
    namespace: cert-manager
---
# apiserver gets the auth-delegator role to delegate auth decisions to
# the core apiserver
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: alidns-webhook:auth-delegator
  namespace: cert-manager
  labels:
    app: alidns-webhook
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
  - apiGroup: ""
    kind: ServiceAccount
    name: alidns-webhook
    namespace: cert-manager
---
# Grant cert-manager permission to validate using our apiserver
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: alidns-webhook:domain-solver
  labels:
    app: alidns-webhook
rules:
  - apiGroups:
      - acme.rancher.ltd
    resources:
      - '*'
    verbs:
      - 'create'
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: alidns-webhook:domain-solver
  labels:
    app: alidns-webhook
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: alidns-webhook:domain-solver
subjects:
  - apiGroup: ""
    kind: ServiceAccount
    name: cert-manager
    namespace: cert-manager

---
# Source: alidns-webhook/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: alidns-webhook
  namespace: cert-manager
  labels:
    app: alidns-webhook
spec:
  type: ClusterIP
  ports:
    - port: 443
      targetPort: https
      protocol: TCP
      name: https
  selector:
    app: alidns-webhook

---
# Source: alidns-webhook/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alidns-webhook
  namespace: cert-manager
  labels:
    app: alidns-webhook
spec:
  replicas:
  selector:
    matchLabels:
      app: alidns-webhook
  template:
    metadata:
      labels:
        app: alidns-webhook
    spec:
      serviceAccountName: alidns-webhook
      containers:
        - name: alidns-webhook
          image: pragkent/alidns-webhook:0.1.1
          imagePullPolicy: IfNotPresent
          args:
            - --tls-cert-file=/tls/tls.crt
            - --tls-private-key-file=/tls/tls.key
          env:
            - name: GROUP_NAME
              value: "acme.rancher.ltd"
          ports:
            - name: https
              containerPort: 443
              protocol: TCP
          livenessProbe:
            httpGet:
              scheme: HTTPS
              path: /healthz
              port: https
          readinessProbe:
            httpGet:
              scheme: HTTPS
              path: /healthz
              port: https
          volumeMounts:
            - name: certs
              mountPath: /tls
              readOnly: true
          resources:
            {}

      volumes:
        - name: certs
          secret:
            secretName: alidns-webhook-webhook-tls

---
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1alpha1.acme.rancher.ltd
  labels:
    app: alidns-webhook
  annotations:
    cert-manager.io/inject-ca-from: "cert-manager/alidns-webhook-webhook-tls"
spec:
  group: acme.rancher.ltd
  groupPriorityMinimum: 1000
  versionPriority: 15
  service:
    name: alidns-webhook
    namespace: cert-manager
  version: v1alpha1

---
# Create a selfsigned Issuer, in order to create a root CA certificate for
# signing webhook serving certificates
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: alidns-webhook-selfsign
  namespace: cert-manager
  labels:
    app: alidns-webhook
spec:
  selfSigned: {}

---

# Generate a CA Certificate used to sign certificates for the webhook
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: alidns-webhook-ca
  namespace: cert-manager
  labels:
    app: alidns-webhook
spec:
  secretName: alidns-webhook-ca
  duration: 43800h # 5y
  issuerRef:
    name: alidns-webhook-selfsign
  commonName: "ca.alidns-webhook.cert-manager"
  isCA: true

---

# Create an Issuer that uses the above generated CA certificate to issue certs
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: alidns-webhook-ca
  namespace: cert-manager
  labels:
    app: alidns-webhook
spec:
  ca:
    secretName: alidns-webhook-ca

---

# Finally, generate a serving certificate for the webhook to use
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: alidns-webhook-webhook-tls
  namespace: cert-manager
  labels:
    app: alidns-webhook
spec:
  secretName: alidns-webhook-webhook-tls
  duration: 8760h # 1y
  issuerRef:
    name: alidns-webhook-ca
  dnsNames:
  - alidns-webhook
  - alidns-webhook.cert-manager
  - alidns-webhook.cert-manager.svc
  - alidns-webhook.cert-manager.svc.cluster.local
</code></pre>

# Install Cluster Issuer
<pre><code>
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-dns-wildcard-stag
spec:
  acme:
    # Email address used for ACME registration
    email: hans@xxxx.com
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    # production # server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      # Name of a secret used to store the ACME account private key
      name: letsencrypt-dns-wildcard-stag-pk
      # production # name: letsencrypt-dns-wildcard-prod-private-key
    # Add a single challenge solver, DNS01 using digital ocean
    solvers:
    - dns01:
        webhook:
          config:
            accessKeySecretRef:
              key: access-token
              name: ali-rancher-ltd-token
            region: ""
            secretKeySecretRef:
              key: secret-key
              name: ali-rancher-ltd-token
          groupName: acme.rancher.ltd
          solverName: alidns
      selector:
        dnsNames:
        - rancher.ltd
        - '*.rancher.ltd'

</code></pre>

# Add Secret ali-dns-token
<pre><code>
Opaque Secret
Opaque 类型的数据是一个 map 类型，要求 value 是 base64 编码格式：

$ echo -n "admin" | base64
YWRtaW4=
$ echo -n "1f2d1e2e67df" | base64
MWYyZDFlMmU2N2Rm
secrets.yml

apiVersion: v1
kind: Secret
metadata:
  name: ali-dns-token
type: Opaque
data:
  access-token: YWRtaW4=
  secret-key: MWYyZDFlMmU2N2Rm

接着，就可以创建 secret 了：kubectl create -f secrets.yml。
</code></pre>

# Create certificate
<pre><code>
# https://github.com/jetstack/cert-manager/issues/1406
---
#apiVersion: certmanager.k8s.io/v1alpha1
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: do-wildcard-certificate-staging
  namespace: default
spec:
  secretName: rancher.ltd-letsencrypt-tls-staging # ingress tls secret name
  issuerRef:
    name: letsencrypt-dns-wildcard-stag
    kind: ClusterIssuer
  commonName: 'rancher.ltd'
  dnsNames:
  - rancher.ltd
  - '*.rancher.ltd'

</code></pre>

# Install Helm
<pre><code>
$ curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
</code></pre>

# Install Rancher

https://github.com/rancher/rancher/issues/26850
<pre><code>
$ helm repo add rancher-latest https://releases.rancher.com/server-charts/latest
$ kubectl create namespace cattle-system
$ export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: tls-rancher-ingress
  namespace: cattle-system
spec:
  secretName: tls-rancher-ingress
  commonName: rancher.ltd
  dnsNames:
  - rancher.ltd
  - '*.rancher.ltd'
  issuerRef:
    name: letsencrypt-dns-wildcard-stag
    kind: ClusterIssuer

$ helm install rancher rancher-latest/rancher \
  --namespace cattle-system \
  --set hostname=rancher.rancher.ltd \
  --set bootstrapPassword=admin \
  --set ingress.tls.source=secret
</code></pre>
