# geohealthcheck

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.9.0](https://img.shields.io/badge/AppVersion-0.9.0-informational?style=flat-square)

A Helm chart for GeoHealthCheck

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| additionalCertificates | object | `{}` |  |
| affinity | object | `{}` |  |
| fullnameOverride | string | `""` | This is to override the release name. |
| geohealthcheck.additionalConfigMaps | list | `[]` | additional configmaps additionalConfigMaps:   - 'foo'   - 'bar' |
| geohealthcheck.additionalEnv | object | `{}` | additional env variables additionalEnv:   name1: 'value1'   name2: 'value2' |
| geohealthcheck.additionalEnvSecrets | list | `[]` | additional envSecrets additionalEnvSecrets:   - 'foo'   - 'bar' |
| geohealthcheck.adminEmail | string | `"you@example.com"` | email address of administrator / contact- notification emails will come from this address |
| geohealthcheck.auth.secret | string | `"changeme"` | secret key to set when enabling authentication |
| geohealthcheck.basicAuthDisabled | string | `"False"` | disable Basic Authentication to access GHC webapp and APIs (default: False), |
| geohealthcheck.databaseUri | string | `"sqlite:////data/data.db"` | database connection string for SQL-Alchemy valid examples are: SQLite: 'sqlite:///data.db' PostgreSQL: 'postgresql+psycopg2://scott:tiger@localhost:5432/mydatabase' |
| geohealthcheck.largeXml | string | `"False"` | allows GeoHealthCheck to receive large XML files from the servers under test (default False). Note: setting this to True might pose a security risk |
| geohealthcheck.logLevel | string | `"30"` | logging level: 10=DEBUG 20=INFO 30=WARN(ING) 40=ERROR 50=FATAL/CRITICAL (default: 30, WARNING) |
| geohealthcheck.metadataCacheSecs | string | `"900"` | metadata, “Capabilities Docs”, cache expiry time, default 900 secs, -1 to disable |
| geohealthcheck.minimalRunFrequencyMins | int | `10` | minimal run frequency for Resource that can be set in web UI |
| geohealthcheck.notifications | string | `"False"` | turn on email and webhook notifications |
| geohealthcheck.notificationsEmail | list | `[]` | list of email addresses that notifications should come to. Use a different address to GHC_ADMIN_EMAIL if you have trouble receiving notification emails. Also, you can set separate notification emails t specific resources. Failing resource will send notification to emails from GHC_NOTIFICATIONS_EMAIL value and emails configured for that specific resource altogether. notificationsEmail:   - 'you2@example.com'   - 'you3@example.com' |
| geohealthcheck.notificationsVerbosity | string | `"True"` | receive additional email notifications than just Failing and Fixed (default True) |
| geohealthcheck.probeHttpTimeoutSecs | int | `30` | stop waiting for the first byte of a Probe response after the given number of seconds |
| geohealthcheck.requireWebappAuth | string | `"False"` | require authentication (login or Basic Auth) to access GHC webapp and APIs (default: False) |
| geohealthcheck.retentionDays | int | `30` | the number of days to keep Run history |
| geohealthcheck.runnerInWebapp | string | `"True"` | should the GHC Runner Daemon be run in webapp (default: True) |
| geohealthcheck.selfRegister | string | `"False"` | allow registrations from users on the website |
| geohealthcheck.siteTitle | string | `"GeoHealthCheck Demonstration"` | title used for installation / deployment |
| geohealthcheck.siteUrl | string | `"http://host"` | full URL of the installation / deployment |
| geohealthcheck.smtpPassword | string | `nil` | SMTP server name or IP |
| geohealthcheck.smtpPort | string | `nil` | SMTP port |
| geohealthcheck.smtpServer | string | `nil` | SMTP server name or IP |
| geohealthcheck.smtpUseTls | string | `nil` | whether or not to use StartTLS with SMTP |
| geohealthcheck.smtpUsername | string | `nil` | SMTP server name or IP |
| geohealthcheck.verifySsl | string | `"True"` | perform SSL verification for Probe HTTPS requests (default: True) |
| geohealthcheck.wwwLinkExceptionCheck | string | `"False"` | turn on checking for OGC Exceptions in WWW:LINK Resource responses (default False) |
| image.pullPolicy | string | `"IfNotPresent"` | Pull policy for the image |
| image.repository | string | `"geopython/geohealthcheck"` | image for GeoHealthCheck |
| image.tag | string | `""` | Overrides the image tag whose default is the chart appVersion. |
| imagePullSecrets | list | `[]` | This is for the secretes for pulling an image from a private repository more information can be found here: https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/ |
| ingress | object | `{"annotations":{},"className":"","enabled":false,"hosts":[{"host":"chart-example.local","paths":[{"path":"/","pathType":"ImplementationSpecific"}]}],"tls":[]}` | This block is for setting up the ingress for more information can be found here: https://kubernetes.io/docs/concepts/services-networking/ingress/ |
| ingress.annotations | object | `{}` | annotations for the ingress annotations:   kubernetes.io/ingress.class: nginx   kubernetes.io/tls-acme: "true" |
| ingress.className | string | `""` | ingress class name |
| ingress.enabled | bool | `false` | enable/disable ingress |
| initContainer.pullPolicy | string | `"IfNotPresent"` | Pull policy for the image of the init container |
| initContainer.repository | string | `"library/ubuntu"` | image for the init container |
| initContainer.resources | object | `{}` | resource definitions for the init container |
| initContainer.tag | string | `"jammy"` | tag for the init container |
| livenessProbe | object | `{"httpGet":{"path":"/","port":"http"}}` | This is to setup the liveness and readiness probes more information can be found here: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/ |
| nameOverride | string | `""` | This is to override the chart name. |
| networkPolicy.egressEnabled | bool | `true` | allow/deny external connections. This should be enabled if you want to monitor resources outside of this namespace |
| networkPolicy.enabled | bool | `true` | Enable/disable network policy generation |
| nodeSelector | object | `{}` |  |
| persistence.enabled | bool | `true` | enable persistence when using an SQLite database |
| persistence.size | string | `"1Gi"` | size of the data partition |
| persistence.storageClassName | string | `""` |  |
| podAnnotations | object | `{}` | This is for setting Kubernetes Annotations to a Pod. For more information checkout: yamllint disable-line rule:line-length https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/ |
| podLabels | object | `{}` | This is for setting Kubernetes Labels to a Pod. For more information checkout: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/ |
| podSecurityContext | object | `{}` |  |
| readinessProbe.httpGet.path | string | `"/"` |  |
| readinessProbe.httpGet.port | string | `"http"` |  |
| resources | object | `{}` | resources for the main container We usually recommend not to specify default resources and to leave this as a conscious choice for the user. This also increases chances charts run on environments with little resources, such as Minikube. If you do want to specify resources, uncomment the following lines, adjust them as necessary, and remove the curly braces after 'resources:'. limits:   cpu: 100m   memory: 128Mi requests:   cpu: 100m   memory: 128Mi |
| securityContext | object | `{}` |  |
| service | object | `{"type":"ClusterIP"}` | This is for setting up a service more information can be found here: https://kubernetes.io/docs/concepts/services-networking/service/ |
| service.type | string | `"ClusterIP"` | This sets the service type more information can be found here: https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| serviceAccount.automount | bool | `true` | Automatically mount a ServiceAccount's API credentials? |
| serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| serviceAccount.name | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| tolerations | list | `[]` |  |
| volumeMounts | list | `[]` | Additional volumeMounts on the output Deployment definition. volumeMounts:   - name: foo     mountPath: "/etc/foo"     readOnly: true |
| volumes | list | `[]` | Additional volumes on the output Deployment definition. volumes:   - name: foo     secret:       secretName: mysecret       optional: false |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
