https
=====


    def foobar(python):
        python = python.upper()
        print(python)

After installing the nginx webserver, the website (although currently only one page) is only served via the unencrypted http protocol. This should be changed.

Luckily there is [let's encrypt][le] that makes issuing and renewal of certificates easy and free \o/

So let's install the client first and start the certbot. You'll get a lot of text and a few inputs

    > sudo pkg py36-certbot
    > sudo certbot-3.6 certonly
    [...]
    How would you like to authenticate with the ACME CA?
    -------------------------------------------------------------------------------
    1: Spin up a temporary webserver (standalone)
    2: Place files in webroot directory (webroot)
    -------------------------------------------------------------------------------
    Select the appropriate number [1-2] then [enter] (press 'c' to cancel): 2
    Plugins selected: Authenticator webroot, Installer None
    Enter email address (used for urgent renewal and security notices) (Enter 'c' to
    cancel): jon.doe@example.com

    -------------------------------------------------------------------------------
    Please read the Terms of Service at
    https://letsencrypt.org/documents/LE-SA-v1.2-November-15-2017.pdf. You must
    agree in order to register with the ACME server at
    https://acme-v01.api.letsencrypt.org/directory
    -------------------------------------------------------------------------------
    (A)gree/(C)ancel: a

    -------------------------------------------------------------------------------
    Would you be willing to share your email address with the Electronic Frontier
    Foundation, a founding partner of the Let's Encrypt project and the non-profit
    organization that develops Certbot? We'd like to send you email about EFF and
    our work to encrypt the web, protect its users and defend digital rights.
    -------------------------------------------------------------------------------
    (Y)es/(N)o: N
    Please enter in your domain name(s) (comma and/or space separated)  (Enter 'c'
    to cancel): www.example.com example.com
    Obtaining a new certificate
    Performing the following challenges:
    http-01 challenge for www.example.com
    http-01 challenge for example.com
    Input the webroot for www.example.com: (Enter 'c' to cancel): /usr/local/www/default 

    Select the webroot for example.com
    -------------------------------------------------------------------------------
    1: Enter a new webroot
    2: /usr/local/www/default
    -------------------------------------------------------------------------------
    Select the appropriate number [1-2] then [enter] (press 'c' to cancel): 2
    Waiting for verification...
    Cleaning up challenges

    IMPORTANT NOTES:
     - Congratulations! Your certificate and chain have been saved at:
       /usr/local/etc/letsencrypt/live/www.example.com/fullchain.pem
       Your key file has been saved at:
       /usr/local/etc/letsencrypt/live/www.example.com/privkey.pem
       Your cert will expire on 2018-05-14. To obtain a new or tweaked
       version of this certificate in the future, simply run certbot
       again. To non-interactively renew *all* of your certificates, run
       "certbot renew"
     - Your account credentials have been saved in your Certbot
       configuration directory at /usr/local/etc/letsencrypt. You should
       make a secure backup of this folder now. This configuration
       directory will also contain certificates and private keys obtained
       by Certbot so making regular backups of this folder is ideal.
     - If you like Certbot, please consider supporting our work by:

       Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
       Donating to EFF:                    https://eff.org/donate-le

To enable Diffie-Hellman key exchange, we need another key. Since the Let's Encrypt directories have the secure ownership settings, we can't use sudo directly

    > sudo zsh
    $ cd /usr/local/etc/letsencrypt/live/www.example.com
    $ openssl dhparam -out dhparam2048.pem 2048
    $ exit
    
After getting the certificates, we need to edit the nginx config of the website. First a copy of the config is created and then on the copy, the two "listen" directives are replaced and the server name set to the domains, we got the certificates for.

    > sudo vim /usr/local/etc/nginx/sites-available/example.com
    server {

        listen 443 ssl;
        listen [::]:443 ssl;
        server_name holgerfrey.de www.holgerfrey.de;

        add_header X-Clacks-Overhead "GNU Terry Pratchett";

        # ssl configuration
        # ssl key and certificate
        ssl_certificate /usr/local/etc/letsencrypt/live/www.example.com/fullchain.pem;
        ssl_certificate_key /usr/local/etc/letsencrypt/live/www.example.com/privkey.pem;

        # ssl protocols and ciphers
        ssl_protocols TLSv1.2 TLSv1.1 TLSv1;
        ssl_ciphers EECDH+AESGCM:EDH+AESGCM:EECDH:EDH:!MD5:!RC4:!LOW:!MEDIUM:!CAMELLIA:!ECDSA:!DES:!DSS:!3DES:!NULL;
        ssl_prefer_server_ciphers on;

        # use a strong diffy helman elliptic curve
        ssl_dhparam /usr/local/etc/letsencrypt/live/www.example.com/dhparam2048.pem;
        ssl_ecdh_curve secp384r1;

        # add HSTS header
        add_header Strict-Transport-Security "max-age=31536000";


        location / {
            root   /usr/local/www/default;
            index  index.html index.htm;
        }

    }

And of cause we need to link it in `sites-enabled` and reload the nginx configuration:
    
    > cd /usr/local/etc/nginx/sites-enabled
    > sudo ln -s ../sites-available/example.com
    > sudo service nginx reload

To redirect any traffic from http to http, we create a new config:

    > cd /usr/local/etc/nginx/sites-available
    > sudo rm default.conf
    > sudo vim redirects
    server {

        ##
        # redirect http to https
        ##

        listen 80;
        listen [::]:80;
    
        server_name example.com www.example.com;

        return 301 https://$host$request_uri;
    }
    
    > cd /usr/local/etc/nginx/sites-enabled
    > sudo ln -s ../sites-available/redirects
    > sudo service nginx reload


[le]: https://letsencrypt.org
