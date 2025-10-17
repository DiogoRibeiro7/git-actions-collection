{{- define "demo.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "demo.fullname" -}}
{{- .Release.Name | default .Chart.Name -}}
{{- end -}}
