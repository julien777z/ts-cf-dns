"""Create AAAA records for your Tailnet devices for different purposes."""

#!/usr/bin/env python3

import logging
import json
import requests
import argparse

from config import settings, TAILSCALE_IGNORED_HOSTNAMES_SET

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

def get_tailscale_ips():
    """Grab IPv6 address for each device on the Tailnet."""
    url = f"https://api.tailscale.com/api/v2/tailnet/{settings.TAILSCALE_TAILNET}/devices"
    headers = {
        "Authorization": f"Bearer {settings.TS_AUTH_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        devices = response.json()["devices"]
    except requests.exceptions.RequestException as e:
        logger.error("Failed to get devices from Tailscale API: %s", e)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON response from Tailscale API: %s", e)
        return {}

    ipv6_addresses = {}
    for device in devices:
        hostname = device.get("hostname")
        addresses = device.get("addresses", [])
        if not hostname:
            logger.warning("Device found with no hostname. ID: %s", device.get('id', 'N/A'))
            continue
        ipv6 = next((ip for ip in addresses if ":" in ip), None)

        if ipv6 is None:
            continue
        if hostname in TAILSCALE_IGNORED_HOSTNAMES_SET:
            logger.info("Ignoring hostname %s from the ignore list.", hostname)
            continue

        ipv6_addresses[hostname] = ipv6

    return ipv6_addresses

def update_cloudflare_dns(hostname, ipv6):
    """Update Cloudflare DNS record."""
    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{settings.CLOUDFLARE_ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_API_KEY}",
        "Content-Type": "application/json"
    }
    fqdn = f"{hostname}.{settings.DNS_DOMAIN}"
    params = {'type': 'AAAA', 'name': fqdn}

    try:
        get_response = requests.get(api_endpoint, headers=headers, params=params)
        get_response.raise_for_status()
        data = get_response.json()

        existing_records = data.get("result", [])
        record_id = None
        existing_ipv6 = None

        if existing_records:
            record = existing_records[0]
            record_id = record.get('id')
            existing_ipv6 = record.get('content')
            if record_id:
                 logger.info("Found existing record for %s with ID %s and IP %s", hostname, record_id, existing_ipv6)
            else:
                 logger.warning("Found record(s) for %s but couldn't extract ID: %s", hostname, record)
                 record_id = None

        payload = {
            "type": "AAAA", "name": hostname, "content": ipv6,
            "ttl": 60, "proxied": False
        }

        if record_id:
            if existing_ipv6 == ipv6:
                logger.info("IP for %s already correct %s. No update needed.", hostname, ipv6)
                return True
            else:
                logger.info("Updating record %s for %s to %s", record_id, hostname, ipv6)
                update_url = f"{api_endpoint}/{record_id}"
                response = requests.put(update_url, headers=headers, json=payload)
        else:
            logger.info("Creating new record for %s with IP %s", hostname, ipv6)
            response = requests.post(api_endpoint, headers=headers, json=payload)

        response.raise_for_status()
        result_data = response.json()

        if result_data.get("success"):
            logger.info("DNS record for %s processed.", hostname)
            return True
        else:
            logger.info("Cloudflare API reported failure: %s", result_data)
            return False

    except requests.exceptions.RequestException as e:
        logger.info("ERROR: Failed Cloudflare request for %s: %s", hostname, e)
        return False

def format_bind(ipv6_records):
    """Create the correct format for BIND."""
    return "\n".join(f"{hostname}. IN AAAA {ipv6}" for hostname, ipv6 in ipv6_records.items())

def format_pihole(ipv6_records):
    """Create the correct format for pihole."""
    return "\n".join(f"{ipv6} {hostname}.{settings.DNS_DOMAIN}" for hostname, ipv6 in ipv6_records.items())

def main():
    """Run the main event loop."""
    parser = argparse.ArgumentParser(description="Tailscale to Cloudflare DNS Updater")
    parser.add_argument("-c", action="store_true", help="Perform Cloudflare migration")
    parser.add_argument("-b", action="store_true", help="Format output as BIND zone file")
    parser.add_argument("-p", action="store_true", help="Format output as Pi-hole local.list format")
    parser.add_argument("-o", type=str, help="Output to a named file")
    args = parser.parse_args()

    ipv6_records = get_tailscale_ips()
    output = ""

    if args.c:
        for hostname, ipv6 in ipv6_records.items():
            update_cloudflare_dns(hostname, ipv6)

    if args.b:
        output = format_bind(ipv6_records)
    elif args.p:
        output = format_pihole(ipv6_records)

    if args.o:
        with open(args.o, "w") as f:
            f.write(output)
    else:
        logger.info(output)

if __name__ == "__main__":
    main()
