# Tailscale to Cloudflare DNS Updater

This Python script retrieves IPv6 addresses from the Tailscale API and updates Cloudflare DNS records accordingly. It also includes options to format the output as a BIND zone file or a Pi-hole local.list format.

It should be noted that putting ULA (or any private addressing) into public DNS is considered bad form, the
downsides of which are well traveled, well studied, and generally it's just stupid. that said, it's pretty useful in some cases, especially for internal split-dns.
This only supports IPv6 because there is no reason to support legacy IPv4 when everything on the tailnet has a valid IPv6 address, and based on
[source address selection rules](https://datatracker.ietf.org/doc/html/rfc6724) when dual-stacked the IPv6 ULA will never be used
without [rfc6724-update](https://datatracker.ietf.org/doc/draft-ietf-6man-rfc6724-update/).

## Features

* Fetches IPv6 addresses of devices from Tailscale.
* Updates or creates corresponding AAAA DNS records in Cloudflare.
* Supports exporting data in BIND zone file or Pi-hole format.
* Allows output to a named file.

## Requirements

* Python 3.x
* A [TailScale](https://www.tailscale.com) account
* A Cloudflare account (if using Cloudflare)
* Some amount of free time and desire to do wacky stuff with your DNS
* requests module (install with pip install requests)
`pip3 install requests`

## Configuration

Set the following variables in a file called .env at the root of this directory (NOTE: No need for quotes around the values in .env):

`TS_AUTH_KEY=api_key` Your Tailscale API key. - Required

`TAILSCALE_TAILNET=fun-name.ts.net` Your Tailscale tailnet name. - Required

`TAILSCALE_IGNORE_HOSTNAMES=host1,host2,host3` A comma separated list of tailnet devices you want to ignore - Optional (NOTE: no spaces)

`CLOUDFLARE_API_KEY=api_key` Your Cloudflare API key. - Required if using cloudflare

`CLOUDFLARE_ZONE_ID=zone_id` Your Cloudflare zone ID. - Required if using cloudflare

`DNS_DOMAIN=example.com` Your domain name. - Required

Make sure to use an [Account API Token](https://developers.cloudflare.com/fundamentals/api/get-started/account-owned-tokens/) from Cloudflare if you want to push to Cloudflare.

## Usage

`chmod +x ts-cf-dns.py`

Run the script with the following options:

`python ts-cf-dns.py [-c] [-b] [-p] [-o filename]`

## Options

* -c : Perform Cloudflare migration (update DNS records).
* -b : Format output as a BIND zone file.
* -p : Format output as Pi-hole local.list format.
* -o filename : Output results to a named file.

## Example Usage

Fetch Tailscale IPv6 addresses and update Cloudflare DNS:

`./ts-cf-dns.py -c`

Export data in BIND format:

`./ts-cf-dns.py -b -o zonefile.bind`

Export data in Pi-hole format:

`./ts-cf-dns.py -p -o pihole.list`

## License

This script is provided as-is with no warranty, don't do stupid stuff with it. Or do, it's really your call and at your own risk.
