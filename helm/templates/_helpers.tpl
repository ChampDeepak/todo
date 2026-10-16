{{/*
Shared label block. Every object gets these so that `kubectl get all -l
app.kubernetes.io/instance=<release>` finds the whole application, and so
Helm can tell its own objects apart from anything else in the namespace.
*/}}
{{- define "taskr.labels" -}}
app.kubernetes.io/name: taskr
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
