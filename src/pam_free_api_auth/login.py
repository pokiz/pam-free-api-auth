import sys

# With ssh login (at least on Debian), python is executed with a different PYTHONPATH, securing it here.
sys.path.insert(0, "/usr/local/lib/python2.7/dist-packages/")

import site

site.main()

from fcntl import flock, LOCK_EX, LOCK_NB, LOCK_UN
import grp
import random
import threading
from uuid import uuid4
from urllib import urlencode
from urllib2 import urlopen

from pam_free_api_auth import colors
from pam_free_api_auth.consts import SECURED_GROUPS, FREE_URL, FREE_LOGIN, FREE_API_KEY, SERVER_IP, SERVER_PORT, TIMEOUT_FAILURE
from pam_free_api_auth.server import Server
from pam_free_api_auth.utils.print_utils import print_header, print_section

lockname = __file__.split("/")[-1].strip(".py")
lockfile = open("/tmp/{}.flock".format(lockname), "w")

def acquire_lock():
    flock(lockfile, LOCK_EX | LOCK_NB)

def release_lock():
    flock(lockfile, LOCK_UN)

def send_message(auth_uuid):
    message = """Tentative de connection.
Valider: https://{}:{}/{}""".format(SERVER_IP, SERVER_PORT, auth_uuid)
    data = urlencode({
        "user": FREE_LOGIN,
        "pass": FREE_API_KEY,
        "msg": message
    })
    response = urlopen("{}?{}".format(FREE_URL, data), data="")
    response.read()


def is_user_in_a_secured_group(username, secured_groups=SECURED_GROUPS):
    """
    Checks if the user inside the secured groups.

    :param (str) username: username.
    :param (set(str)) secured_groups: list of the secured group names.
    :return: returns True if the user is inside a secured groups.
    """
    return len([g.gr_name for g in grp.getgrall() if username in g.gr_mem and g.gr_name in secured_groups]) > 0

def get_user(pamh):
    """
    Returns the username that interacts with the PAM module
    :param (PamHandle) pamh: PamHandle object
    :return (str): username
    """
    try:
        user = pamh.get_user(None)
        return user
    except pamh.exception as e:
        return e.pam_result


def pam_sm_authenticate(pamh, flags, argv):
    """
    Handles the authentication of the user. Part of the auth management group.

    :param (PamHandle) pamh: PamHandle object
    :param (list) flags: list of flags passed to this script
    :param (list) argv: list of arguments passed to pam_python.so module.
    :return (int): PAM return code
    """
    try:
        acquire_lock()
    except IOError:
        print_header("Another login is in progress. Please retry later.", header_color=colors.RED)
        return pamh.PAM_AUTH_ERR

    user = get_user(pamh)
    if not is_user_in_a_secured_group(user):
        return pamh.PAM_USER_UNKNOWN

    server = None
    auth_uuid = str(uuid4())
    try:
        send_message(auth_uuid)
        server = Server(SERVER_PORT, auth_uuid)
        t1 = threading.Thread(target=server.run)
        t1.start()
        t1.join(TIMEOUT_FAILURE)
        t1.should_stop = True

        if server.auth_success:
            print_header("AUTHENTICATED!")
            return pamh.PAM_SUCCESS
    finally:
        if server is not None:
            server.close()
        release_lock()

    print_header("UNAUTHENTICATED!", header_color=colors.RED)
    return pamh.PAM_AUTH_ERR


def pam_sm_open_session(pamh, flags, argv):
    """
    Handles the opening of the user session. Part of the session management group.

    :param (PamHandle) pamh: PamHandle object
    :param (list) flags: list of flags passed to this script
    :param (list) argv: list of arguments passed to pam_python.so module.
    :return (int): PAM return code
    """
    user = get_user(pamh)

    if not is_user_in_a_secured_group(user):
        return pamh.PAM_USER_UNKNOWN

    return pamh.PAM_SUCCESS


def pam_sm_close_session(pamh, flags, argv):
    """
    Handles the closing of the user session. Part of the session management group.

    :param (PamHandle) pamh: PamHandle object
    :param (list) flags: list of flags passed to this script
    :param (list) argv: list of arguments passed to pam_python.so module.
    :return (int): PAM return code
    """
    return pamh.PAM_SUCCESS


def pam_sm_setcred(pamh, flags, argv):
    """
    Handles the credentials change of the user. Part of the passwd management group.

    :param (PamHandle) pamh: PamHandle object
    :param (list) flags: list of flags passed to this script
    :param (list) argv: list of arguments passed to pam_python.so module.
    :return (int): PAM return code
    """
    return pamh.PAM_SUCCESS


def pam_sm_acct_mgmt(pamh, flags, argv):
    """
    Handles the validation of the user. Part of the account management group.
    NOTE: I when researching the module I didn't managed to make this function to be called.

    :param (PamHandle) pamh: PamHandle object
    :param (list) flags: list of flags passed to this script
    :param (list) argv: list of arguments passed to pam_python.so module.
    :return (int): PAM return code
    """
    return pamh.PAM_SUCCESS


def pam_sm_chauthtok(pamh, flags, argv):
    return pamh.PAM_SUCCESS
