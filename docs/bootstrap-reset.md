# Bootstrap apos reset

## Acesso por Winbox MAC

Apos reset, abra o Winbox, use a aba Neighbors e conecte pelo MAC address do roteador. Esse caminho nao depende de IP configurado.

## Gerar script

```powershell
.\.venv\Scripts\python.exe src\main.py render-bootstrap --profile profiles\minha-rb.yaml
```

Abra o arquivo `generated/*_bootstrap_sanitized.rsc` para revisao. Se precisar criar usuario com senha real, use o arquivo `*_bootstrap_sensitive.rsc` apenas localmente e nunca commite.

## Colar no terminal

No Winbox, abra Terminal, cole o script bootstrap e acompanhe erros. O script nao executa reset, reboot ou import.

## Testar IP

Configure o PC na rede de gerenciamento ou obtenha DHCP. Teste ping no gateway LAN configurado, por exemplo `192.168.88.1`.

## Testar SSH

```powershell
.\.venv\Scripts\python.exe src\main.py ssh-check
```

## Voltar para automacao

Depois que SSH responder, rode:

```powershell
.\.venv\Scripts\python.exe src\main.py collect --execute
```

