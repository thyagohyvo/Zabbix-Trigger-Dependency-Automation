# Zabbix Trigger Dependency Automation

![Python](https://img.shields.io/badge/Python-3.x-blue)
![API](https://img.shields.io/badge/API-Zabbix-green)
![Automation](https://img.shields.io/badge/Automation-Network%20Monitoring-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

Script em Python para **automatizar a criação de dependências entre triggers de indisponibilidade (ICMP/Ping) no Zabbix** utilizando a API.

Este projeto foi desenvolvido para **reduzir alertas em cascata em ambientes de monitoramento**, onde vários dispositivos dependem de um equipamento principal para conectividade.

OBS: Embora o exemplo utilize triggers de disponibilidade baseadas em ICMP/Ping, o script foi desenvolvido de forma genérica e pode ser facilmente adaptado para trabalhar com qualquer tipo de trigger definida em templates do ambiente.

---

# 📌 Objetivo

Automatizar a criação de **dependências entre triggers de disponibilidade** para evitar que o sistema de monitoramento gere múltiplos alertas quando um dispositivo central fica indisponível.

Em muitas redes monitoradas, quando um equipamento principal (como um roteador ou gateway) perde conectividade, diversos dispositivos monitorados atrás dele também deixam de responder.

Sem dependência configurada:

* O equipamento principal gera alerta
* Todos os dispositivos dependentes também geram alerta
* O monitoramento fica poluído com múltiplos eventos

Com dependência configurada:

* Apenas o dispositivo principal gera o alerta
* Os dispositivos dependentes ficam automaticamente suprimidos

---

# 🧠 Como o Script Funciona

O script executa as seguintes etapas:

1. Conecta à API do Zabbix
2. Localiza o **host principal (parent)**
3. Identifica automaticamente a **trigger de indisponibilidade**
4. Busca os hosts dentro de um **host group**
5. Para cada host encontrado:

   * Localiza a trigger de indisponibilidade
   * Verifica se já existe dependência
   * Caso não exista, cria a dependência com o host principal

A relação criada será:

```text
Trigger do Host Filho → depende da Trigger do Host Principal
```

---

# 🏗 Estrutura de Funcionamento

O script utiliza uma lógica simples baseada em topologia:

```text
Host Principal
      │
      │
Grupo de Hosts
      │
      ├── Dispositivo 1
      ├── Dispositivo 2
      ├── Dispositivo 3
      └── Dispositivo N
```

Todos os dispositivos do grupo passam a depender da trigger de indisponibilidade do host principal.

---

# 🔎 Identificação Automática da Trigger

O script tenta localizar a trigger de indisponibilidade de duas formas.

### 1. Prioridade: item `icmpping`

Busca triggers associadas ao item:

```
icmpping
```

Esse item é normalmente utilizado para monitoramento de disponibilidade via ICMP.

---

### 2. Método alternativo (fallback)

Caso não exista trigger baseada no item, o script procura triggers cujo nome contenha termos relacionados à indisponibilidade.

Expressão utilizada:

```
(ICMP|ping|unreachable|sem resposta)
```

---

# ⚙️ Configuração

Edite as variáveis no início do script.

```python
ZABBIX_URL = ""
API_TOKEN  = ""
```

Exemplo:

```python
ZABBIX_URL = "https://zabbix.seu-dominio.com/api_jsonrpc.php"
API_TOKEN  = "SEU_TOKEN_DE_API"
```

---

# 🧩 Definição da Topologia

```python
TOPOLOGY_NAME = "Nome da Topologia"
PARENT_HOST = "Nome_do_Host_Principal"
CHILD_GROUP_NAME = "Nome_do_Grupo_de_Hosts"
```

Descrição das variáveis:

| Variável         | Descrição                                             |
| ---------------- | ----------------------------------------------------- |
| TOPOLOGY_NAME    | Nome da topologia (apenas informativo)                |
| PARENT_HOST      | Host que será considerado o equipamento principal     |
| CHILD_GROUP_NAME | Grupo de hosts onde estão os dispositivos dependentes |

---

# 🔍 Filtro Opcional de Hosts

É possível aplicar um filtro para selecionar apenas hosts específicos dentro do grupo.

Exemplo:

```python
CHILD_HOST_FILTER_REGEX = r"^switch-"
```

Esse exemplo incluiria apenas hosts cujo nome começa com `switch-`.

Caso queira incluir **todos os hosts do grupo**, utilize:

```python
CHILD_HOST_FILTER_REGEX = None
```

---

# 📦 Requisitos

* Python 3.8 ou superior
* Biblioteca `requests`

Instalação:

```bash
pip install requests
```

---

# 🚀 Execução

Execute o script com:

```bash
python script.py
```

Exemplo de saída:

```
=== Topologia: Core Network ===

Parent: core-router
 - Trigger: ICMP ping is unavailable

Grupo: access-switches
Hosts no grupo: 10 | Filhos selecionados: 9

 - [ADDED] switch-01 -> depende do parent
 - [ADDED] switch-02 -> depende do parent
 - [OK]    switch-03 (dependência já existente)

=== RESUMO ===
Dependências criadas:   2
Já existentes:          1
Sem trigger ICMP:       0
Erros:                  0
```

---

# 📊 Benefícios

* Redução de alertas em cascata
* Automatização da configuração de dependências
* Menor intervenção manual
* Melhor organização do monitoramento
* Escalabilidade para ambientes com muitos dispositivos

---

# 🛠 Casos de Uso

Esse script é útil para ambientes que possuem:

* Estruturas de rede hierárquicas
* Dispositivos dependentes de um gateway ou roteador
* Monitoramento baseado em ICMP
* Ambientes com grande quantidade de hosts monitorados

---

# 📄 Licença

Este projeto pode ser utilizado livremente para automação e melhoria de ambientes de monitoramento.

---

# 👨‍💻 Autor

Script desenvolvido para automatizar a criação de dependências entre triggers em ambientes de monitoramento baseados em Zabbix.
www.linkedin.com/in/thyago-hyvo
