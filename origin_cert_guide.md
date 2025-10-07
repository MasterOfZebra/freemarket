# Origin Certificate Generation Guide for FreeMarket

This guide explains how to generate and install an Origin Certificate for use with Cloudflare or Timeweb CDN.

## Why Origin Certificate?

Origin certificates allow you to encrypt traffic between the CDN and your origin server (web-vm), providing end-to-end encryption.

## Steps for Cloudflare

1. **Log in to Cloudflare Dashboard**
   - Go to your domain's SSL/TLS settings

2. **Generate Origin Certificate**
   - Navigate to SSL/TLS > Origin Server
   - Click "Create Certificate"
   - Choose "Generate private key and CSR with Cloudflare" or upload your own CSR
   - Select certificate validity (up to 15 years)
   - Click "Create"

3. **Download Certificate Files**
   - Download the `.pem` file (certificate + private key)
   - Or download separately: `origin.crt` and `private.key`

4. **Install on web-vm**
   ```bash
   sudo mkdir -p /etc/ssl/certs /etc/ssl/private
   sudo cp origin.crt /etc/ssl/certs/freemarket.crt
   sudo cp private.key /etc/ssl/private/freemarket.key
   sudo chmod 600 /etc/ssl/private/freemarket.key
   sudo chown www-data:www-data /etc/ssl/private/freemarket.key
   ```

## Steps for Timeweb (if using Timeweb CDN)

1. **Access Timeweb Control Panel**
   - Go to SSL Certificates section

2. **Generate Origin Certificate**
   - Create a new certificate for your domain
   - Choose "Origin Certificate" type if available
   - Generate or upload CSR

3. **Download and Install**
   - Follow similar steps as Cloudflare above

## Alternative: Let's Encrypt (Free)

If you prefer free certificates:

1. **Install Certbot**
   ```bash
   sudo apt update
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Generate Certificate**
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. **Automatic Renewal**
   - Certbot sets up automatic renewal via cron
   - Test: `sudo certbot renew --dry-run`

## Verification

After installation:

1. **Test SSL**
   ```bash
   openssl s_client -connect localhost:443 -servername yourdomain.com
   ```

2. **Check Nginx**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Test from CDN**
   - Ensure CDN is configured to use "Full (strict)" SSL mode
   - Test your site through the CDN

## Security Notes

- Keep private keys secure (chmod 600, owned by www-data)
- Rotate certificates before expiration
- Monitor certificate validity in your monitoring system
- Use HSTS header as configured in nginx.conf
