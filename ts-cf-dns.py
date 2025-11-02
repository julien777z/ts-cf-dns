"""Create AAAA records for your Tailnet devices for different purposes."""

#!/usr/bin/env python3

import logging
import requests
import argparse

from config import settings

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def update_cloudflare_dns(hostname, dns_type, dns_value):
    """Update Cloudflare DNS record."""

    print(f"Updating Cloudflare DNS record for {hostname} with {dns_type}")

    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{settings.CLOUDFLARE_ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_API_KEY}",
        "Content-Type": "application/json",
    }
    params = {"type": dns_type, "name": hostname}

    try:
        get_response = requests.get(api_endpoint, headers=headers, params=params)
        get_response.raise_for_status()
        data = get_response.json()

        existing_records = data.get("result", [])
        record_id = None
        existing_dns_value = None

        if existing_records:
            record = existing_records[0]
            record_id = record.get("id")
            existing_dns_value = record.get("content")
            if record_id:
                logger.info(
                    "Found existing record for %s with ID %s and %s %s",
                    hostname,
                    record_id,
                    dns_type,
                    existing_dns_value,
                )
            else:
                logger.warning(
                    "Found record(s) for %s but couldn't extract ID: %s",
                    hostname,
                    record,
                )
                record_id = None

        payload = {
            "type": dns_type,
            "name": hostname,
            "content": dns_value,
            "ttl": 60,
            "proxied": False,
        }

        if record_id:
            if existing_dns_value == dns_value:
                logger.info(
                    "%s for %s already correct %s. No update needed.", dns_type, hostname, dns_value
                )
                return True
            else:
                logger.info(
                    "Updating record %s for %s to %s %s", record_id, hostname, dns_type, dns_value
                )
                update_url = f"{api_endpoint}/{record_id}"
                response = requests.put(update_url, headers=headers, json=payload)
        else:
            logger.info("Creating new record for %s with %s %s", hostname, dns_type, dns_value)
            response = requests.post(api_endpoint, headers=headers, json=payload)

        response.raise_for_status()
        result_data = response.json()

        if result_data.get("success"):
            logger.info("DNS record for %s processed.", hostname)
            return True
        else:
            logger.info("Cloudflare API reported failure: %s", result_data)
            return False

    except requests.exceptions.RequestException:
        logger.error(
            "ERROR: Failed Cloudflare request for %s=%s; %s",
            hostname,
            dns_value,
            response.text,
        )
        return False


def main():
    """Run the main script."""

    parser = argparse.ArgumentParser(description="Tailscale to Cloudflare DNS Updater")
    parser.add_argument(
        "-d", "--domain", type=str, help="Domain to update. Format: domain=dns_value, e.g. 'mydevice.example.com=192.168.1.1'"
    )
    parser.add_argument(
        "-t", "--dns-type", type=str, help="DNS record type", default="A", choices=["A", "AAAA", "CNAME"]
    )
    args = parser.parse_args()

    hostname, dns_value = args.domain.split("=")
    dns_type = args.dns_type

    update_cloudflare_dns(hostname, dns_type, dns_value)


if __name__ == "__main__":
    main()