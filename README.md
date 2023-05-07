# PAM/SSH authentication via Free Mobile SMS API

This package provides a simple PAM (Pluggable Authentication Modules) module, to authenticate each request with the help of the Free Mobile SMS API (only available in France).

How does it work?

- You try to connect to an account via su or SSH
- Your password/key must succeed first
- After previous validation it sends an SMS through the Free Mobile API with a unique token to validate the request.
- Then start a temporary HTTPS server (port configurable in consts.py) to listen to the call.

It timeouts after 30 seconds by default (configurable via consts.py).

In this version, the module allows only one authentication at a time.

As of today libpam-python is limited to python2.7 with Debian Bullseye.
An update of this module will be made for Debian Bookworm around the release date (June 2023).

## Installation

### Step 1:
On Debian you must install:
- libpam-python
- python-setuptools

### Step 2:
Clone this repository into a directory on the server.

### Step 3:
Replace the values in "src/YOUR.consts.py" by your own login and key.
And rename it to "consts.py".

### Step 4:
Then go to the "src" folder and install the module with:
```commandline
sudo python -m pip install .
```

### Step 5:
Generate the certificates for the HTTPs endpoint.

For a passwordless certificate:
```commandline
openssl req -x509 -newkey rsa:4096 -keyout /etc/ssl/private/pam-free-api-auth.key -out /etc/ssl/certs/pam-free-api-auth.cert -days 365 -nodes -subj "/C=FR/ST=Paris/L=Paris/O=None/CN=your@mail.org"
```
To set a password just remove the "-nodes" option.

### Step 6 (for local session only):

Edit /etc/pam.d/common-auth and add this line to the top of the file:
```commandline
auth	[success=done user_unknown=ignore auth_err=die]	pam_python.so /usr/local/lib/python2.7/dist-packages/pam_free_api_auth/login.py
```
Edit /etc/pam.d/common-session and add this line to the top of the file:
```commandline
session	sufficient pam_python.so /usr/local/lib/python2.7/dist-packages/pam_free_api_auth/login.py
```

### Step 6 bis (to handle SSH connection too):

The following steps are designed for publickey and SMS authentication, please adapt to your usecase.

Create a file /etc/pam.d/common-auth-sshd and add this
```commandline
# /etc/pam.d/common-auth-sshd - authentication settings for SSHD
#
# This file is included from sshd service PAM config files.
# It is basically a copy of /etc/pam.d/common-auth but without pam_unix.so (password authentication)


auth	[success=done user_unknown=ignore auth_err=die]	pam_python.so /usr/local/lib/python2.7/dist-packages/pam_free_api_auth/login.py
# here's the fallback if no module succeeds
auth	requisite			pam_deny.so
# prime the stack with a positive return value if there isn't one already;
# this avoids us returning an error just because nothing sets a success code
# since the modules above will each just jump around
auth	required			pam_permit.so
```
Edit /etc/pam.d/sshd like this
```commandline
#Comment the following line (should be on top of the file)
#@include common-auth

#And add this line
@include common-auth-sshd
```

And check that /etc/ssh/sshd_config contains these:
```commandline
#This one to enable keyboard-interactive (to enable authentication with PAM modules)
ChallengeResponseAuthentication yes

#This one to specify our authentication methods (here public/private keys, then PAM modules)
AuthenticationMethods publickey,keyboard-interactive:pam
```

### Step 7
Create a group named **_free-api-auth_** (the default, if you want to use another one -> consts.py).
And simply add users to it to enable the authentication throught this module (hooked after password/key verification success).
```commandline
groupadd free-api-auth
usermod -a -G free-api-auth <test-user>
```

## Testing
You can test the module by switching users:
```commandline
su <testuser>
```

Or simply opening an SSH session.


## Credits

This project is highly inspired by the following repository for the base structure: https://gitlab.com/avirzayev/pam-minigames
Which is really fun for local sessions by the way!