#!/usr/bin/env python3
"""
Zabbix Trigger Dependency Automation

Script para criação automática de dependências entre triggers
de indisponibilidade utilizando a API do Zabbix.

Este script identifica a trigger de indisponibilidade de um host
principal (parent) e cria dependências automaticamente para todos
os hosts dentro de um host group definido.

Objetivo:
Evitar alertas em cascata no monitoramento quando um equipamento
principal fica indisponível.

Autor: Thyago Hyvo
Licença: MIT
"""

import re
import sys
from typing import Any, Dict, List, Optional, Tuple
import requests


# ========= CONFIG (PREENCHA) =========
ZABBIX_URL = ""
API_TOKEN = ""
HTTP_TIMEOUT = 60
# ====================================


# ======= TOPOLOGIA (AJUSTE AQUI) =======
TOPOLOGY_NAME = "Example Topology"
PARENT_HOST = "core-router"
CHILD_GROUP_NAME = "access-devices"

# Opcional: filtrar quais hosts do grupo entram (deixe None para pegar todos)
# Exemplo: r"^switch-"
CHILD_HOST_FILTER_REGEX = None
# =======================================


PING_ITEM_KEY = "icmpping"
FALLBACK_TRIGGER_REGEX = re.compile(r"(ICMP|ping|unreachable|sem resposta)", re.IGNORECASE)


def zbx_call(method: str, params: Dict[str, Any]) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {API_TOKEN}"
    }

    r = requests.post(ZABBIX_URL, headers=headers, json=payload, timeout=HTTP_TIMEOUT)
    r.raise_for_status()

    data = r.json()

    if "error" in data:
        raise RuntimeError(f"Zabbix API error: {data['error']}")

    return data["result"]


def get_host_by_name_exact(hostname: str) -> Dict[str, Any]:
    res = zbx_call("host.get", {
        "output": ["hostid", "host", "name", "status"],
        "filter": {"host": [hostname]}
    })

    if not res:
        raise RuntimeError(f"Host não encontrado (campo Host): {hostname}")

    return res[0]


def get_hostgroup_id_exact(group_name: str) -> str:
    res = zbx_call("hostgroup.get", {
        "output": ["groupid", "name"],
        "filter": {"name": [group_name]}
    })

    if not res:
        raise RuntimeError(f"Host group não encontrado: {group_name}")

    return res[0]["groupid"]


def get_hosts_in_group(groupid: str) -> List[Dict[str, Any]]:
    return zbx_call("host.get", {
        "output": ["hostid", "host", "name", "status"],
        "groupids": [groupid]
    })


def get_itemids_by_key(hostid: str, key_: str) -> List[str]:
    items = zbx_call("item.get", {
        "output": ["itemid", "key_"],
        "hostids": [hostid],
        "filter": {"key_": [key_]}
    })

    return [i["itemid"] for i in items]


def get_triggers_for_host(hostid: str) -> List[Dict[str, Any]]:
    return zbx_call("trigger.get", {
        "output": ["triggerid", "description", "priority", "status"],
        "hostids": [hostid],
        "selectDependencies": ["triggerid"],
        "selectFunctions": ["itemid"],
        "expandDescription": True
    })


def pick_trigger_by_itemkey(hostid: str, key_: str) -> Optional[Dict[str, Any]]:
    itemids = set(get_itemids_by_key(hostid, key_))

    if not itemids:
        return None

    triggers = get_triggers_for_host(hostid)
    candidates = []

    for t in triggers:
        functions = t.get("functions") or []
        func_itemids = {f.get("itemid") for f in functions if f.get("itemid")}

        if func_itemids & itemids:
            candidates.append(t)

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x.get("status", "0") != "0", -int(x.get("priority", "0"))))

    return candidates[0]


def pick_trigger_by_regex(hostid: str, rx: re.Pattern) -> Optional[Dict[str, Any]]:
    triggers = get_triggers_for_host(hostid)
    candidates = []

    for t in triggers:
        desc = (t.get("description") or "").strip()

        if rx.search(desc):
            candidates.append(t)

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x.get("status", "0") != "0", -int(x.get("priority", "0"))))

    return candidates[0]


def pick_unavail_trigger(hostid: str) -> Tuple[Optional[Dict[str, Any]], str]:
    t = pick_trigger_by_itemkey(hostid, PING_ITEM_KEY)

    if t:
        return t, "by_itemkey(icmpping)"

    t2 = pick_trigger_by_regex(hostid, FALLBACK_TRIGGER_REGEX)

    if t2:
        return t2, "by_regex(name)"

    return None, "none"


def ensure_dependency(child_trigger: Dict[str, Any], parent_triggerid: str) -> bool:
    child_triggerid = child_trigger["triggerid"]

    current = child_trigger.get("dependencies") or []
    current_ids = {d["triggerid"] for d in current}

    if parent_triggerid in current_ids:
        return False

    new_deps = [{"triggerid": tid} for tid in sorted(current_ids | {parent_triggerid})]

    zbx_call("trigger.update", {
        "triggerid": child_triggerid,
        "dependencies": new_deps
    })

    return True


def main():

    print(f"=== Topologia: {TOPOLOGY_NAME} ===")

    parent = get_host_by_name_exact(PARENT_HOST)

    parent_trigger, parent_method = pick_unavail_trigger(parent["hostid"])

    if not parent_trigger:
        raise RuntimeError(
            f"Não achei trigger de indisponibilidade no parent {PARENT_HOST}. "
            f"Verifique se existe item '{PING_ITEM_KEY}' e trigger ICMP nesse host/template."
        )

    parent_triggerid = parent_trigger["triggerid"]

    print(f"Parent: {PARENT_HOST}")
    print(f" - Trigger: {parent_trigger.get('description')} (id={parent_triggerid}, method={parent_method})")

    groupid = get_hostgroup_id_exact(CHILD_GROUP_NAME)

    group_hosts = get_hosts_in_group(groupid)

    rx = re.compile(CHILD_HOST_FILTER_REGEX) if CHILD_HOST_FILTER_REGEX else None

    children = []

    for h in group_hosts:

        if h["host"] == PARENT_HOST:
            continue

        if rx and not rx.search(h["host"]):
            continue

        children.append(h)

    print(f"\nGrupo: {CHILD_GROUP_NAME}")
    print(f"Hosts no grupo: {len(group_hosts)} | Filhos selecionados: {len(children)}")

    changed = 0
    skipped = 0
    missing_trigger = 0
    errors = 0

    for h in children:

        try:

            trig, method = pick_unavail_trigger(h["hostid"])

            if not trig:
                missing_trigger += 1
                print(f" - [SEM TRIGGER] {h['host']} ({h.get('name','')})")
                continue

            did = ensure_dependency(trig, parent_triggerid)

            if did:
                changed += 1
                print(f" - [ADDED] {h['host']} -> depende do parent (child_trigger={trig['triggerid']} via {method})")
            else:
                skipped += 1
                print(f" - [OK]    {h['host']} (já dependia)")

        except Exception as e:
            errors += 1
            print(f" - [ERRO]  {h['host']}: {e}")

    print("\n=== RESUMO ===")
    print(f"Dependências criadas:   {changed}")
    print(f"Já existentes (OK):     {skipped}")
    print(f"Sem trigger ICMP:       {missing_trigger}")
    print(f"Erros:                  {errors}")

    if errors:
        sys.exit(2)


if __name__ == "__main__":

    try:
        main()

    except Exception as e:
        print(f"\nERRO FATAL: {e}")
        sys.exit(1)