{{/*
Expand the name of the chart.
*/}}
{{- define "geohealthcheck.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "geohealthcheck.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "geohealthcheck.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "geohealthcheck.labels" -}}
helm.sh/chart: {{ include "geohealthcheck.chart" . | squote }}
{{ include "geohealthcheck.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | squote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service | squote }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "geohealthcheck.selectorLabels" -}}
app.kubernetes.io/name: {{ include "geohealthcheck.name" . | squote }}
app.kubernetes.io/instance: {{ .Release.Name | squote }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "geohealthcheck.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "geohealthcheck.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Set the port to expose
*/}}
{{- define "geohealthcheck.containerPort" -}}
{{- "80" }}
{{- end }}
