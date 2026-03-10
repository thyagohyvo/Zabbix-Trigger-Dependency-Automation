# Zabbix-Trigger-Dependency-Automation
Este script tem como finalidade automatizar a criação de dependências entre triggers de indisponibilidade (ICMP/Ping) no Zabbix, baseado em uma topologia lógica de parent/child.

Ele é especialmente útil em ambientes onde há:

Um host principal (ex: roteador, concentrador, core, POP)
Diversos hosts filhos (ex: switches de acesso, rádios, CPEs, etc.)
Monitoramento via icmpping
Necessidade de evitar alertas em cascata

Em ambientes monitorados pelo Zabbix, quando um host principal cai (por exemplo, um roteador principal), todos os hosts filhos também ficam indisponíveis.

Sem dependência configurada:

O Zabbix dispara alerta para o parent

Dispara alerta para todos os filhos

Gera múltiplos eventos desnecessários

Polui dashboards e notificações

Aumenta ruído operacional

Com dependência configurada:

Se o parent cair → apenas o alerta do parent é gerado

Os filhos ficam suprimidos automaticamente

Redução significativa de ruído

⚙️ O Que o Script Faz

Conecta à API do Zabbix usando API Token

Localiza o host principal (parent)

Identifica automaticamente a trigger de indisponibilidade:

Prioriza item icmpping

Caso não encontre, usa regex em descrições (ping, unreachable, etc.)

Busca todos os hosts dentro de um Host Group específico

Para cada host filho:

Localiza a trigger de indisponibilidade

Verifica se já existe dependência

Caso não exista, adiciona dependência via trigger.update



🏗 Estrutura de Topologia

O script trabalha com o seguinte modelo lógico:

Parent Host (Ex: TR01FAF-PRINCIPAL)
        ↓
Host Group (Ex: TRAPRINCIPAL)
        ↓
Hosts Filhos (Switches, Access, etc.)

A dependência criada será:
Trigger Filho depende da Trigger do Parent

🔎 Critérios de Identificação da Trigger

O script tenta encontrar a trigger de indisponibilidade usando:

Item key:

icmpping

Regex fallback:

(ICMP|ping|unreachable|sem resposta)

Ele sempre prioriza:

Triggers habilitadas

Maior severidade


Benefícios

🔥 Redução de alertas em cascata

⚡ Automatização via API

🧠 Inteligência na seleção de trigger

🛡 Evita erro manual na criação de dependências

🔁 Pode ser reutilizado para múltiplas topologias

🛠 Requisitos

Python 3.8+

Biblioteca requests

Token de API do Zabbix

Permissão para trigger.update

Instalação da dependência:

pip install requests
