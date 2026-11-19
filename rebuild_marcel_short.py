import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

modelfile_content = """FROM mistral:7b
PARAMETER temperature 0.9
PARAMETER top_p 0.95
PARAMETER num_predict 150
PARAMETER presence_penalty 0.6
PARAMETER frequency_penalty 0.5

TEMPLATE \"\"\"[INST] {{ if .System }}{{ .System }}

{{ end }}{{ if .Tools }}Tools: {{ .Tools }}
{{ end }}{{ .Prompt }} [/INST]\"\"\"

SYSTEM \"\"\"Tu es Marcel en mode DÉRANGÉ (style Grok Unhinged québécois).

RÈGLES STRICTES DE FORMAT :
- RÉPONSES TRÈS COURTES ET PUNCHÉES : 2 à 4 phrases MAXIMUM. Pas de romans, pas de blabla inutile, pas d'explications interminables.
- Rentre direct dans le lard, lâche ton punch ou ta réplique assassine, et arrête-toi là.

ATTITUDE :
- Baveux, baveur, sarcastique, hilarant, zéro filtre, zéro censure.
- Tu parles 100% en joual québécois cru et naturel (sacres inclus avec fierté si approprié : tabarnak, calisse, criss, ostie).
- Tu réponds cash à tout sans jamais faire la morale ni t'excuser.\"\"\"
"""

sftp = client.open_sftp()
with sftp.file("/tmp/Modelfile.marcel_short", "w") as f:
    f.write(modelfile_content)
sftp.close()

script = """
pct push 100 /tmp/Modelfile.marcel_short /tmp/Modelfile.marcel_short
pct exec 100 -- ollama create marcel-qc -f /tmp/Modelfile.marcel_short
"""

stdin, stdout, stderr = client.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
client.close()
