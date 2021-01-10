import digitalocean
import CloudFlare
import time

# Fill these out
DO_API_TOKEN = "your_do_api_token"
CF_EMAIL = "you@you.com"
CF_TOKEN = "your_cloudflare_token"
CF_ZONE_NAME = "yourdomain.com"
CF_DNS_NAME = "vpntest.yourdomain.com"
SNAPSHOT_ID = "00000000"
DROPLET_NAME = "vpninstance"
REGION = "tor1"

# Specify droplet parameters and create it
droplet = digitalocean.Droplet(token=DO_API_TOKEN,
    name=DROPLET_NAME,
    region=REGION,
    image=SNAPSHOT_ID,
    size_slug='s-1vcpu-1gb',
    backups=False)
droplet.create()

# While it's spinning up, check progress
# Once the status is "completed" we can move on
actions = droplet.get_actions()
for action in actions:
    while action.status != "completed":
        action.load()
        if action.status == "in-progress":
            print(".", sep=' ', end='', flush=True)
        else:
            print(action.status)
        time.sleep(1)

# Get the new droplet IP
droplet.load()
print("droplet IP: %s\ndroplet ID: %s" % (droplet.ip_address, droplet.id))
ip_address = droplet.ip_address
ip_address_type = 'A'

# Connect to Cloudflare and get the correct zone (domain name)
cf = CloudFlare.CloudFlare(email=CF_EMAIL, token=CF_TOKEN)
zones = cf.zones.get()
for zone in zones:
    if zone['name'] == CF_ZONE_NAME:
        zone_id = zone['id']
        zone_name = zone['name']
        print(zone_id, zone_name)

# Get the existing subdomain record info so we can get the ID
try:
    params = {'name':CF_DNS_NAME, 'match':'all', 'type':ip_address_type}
    dns_records = cf.zones.dns_records.get(zone_id, params=params)
except CloudFlare.exceptions.CloudFlareAPIError as e:
    exit('/zones/dns_records %s - %d %s - api call failed' % (dns_name, e, e))

if not dns_records:
    print("No dns entry found on CloudFlare for %s" % CF_DNS_NAME)
    exit()

updated = False

# Update the record with the new IP address
for dns_record in dns_records:
    old_ip_address = dns_record['content']
    old_ip_address_type = dns_record['type']

    # Yes, we need to update this record - we know it's the same address type

    dns_record_id = dns_record['id']
    dns_record = {
        'name':CF_DNS_NAME,
        'type':ip_address_type,
        'content':ip_address
    }
    try:
        dns_record = cf.zones.dns_records.put(zone_id, dns_record_id, data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit('/zones.dns_records.put %s - %d %s - api call failed' % (CF_DNS_NAME, e, e))
    print('Updated: %s %s -> %s' % (CF_DNS_NAME, old_ip_address, ip_address))
    updated = True
