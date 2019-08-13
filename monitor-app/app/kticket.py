import subprocess
import getpass
import os
import app.mylogging as log

debug_klist=False

def exists(path):
    """Test whether a path exists.  Returns False for broken symbolic links"""
    try:
        st = os.stat(path)
    except os.error:
        return False
    return True

def check_and_reinit_kticket():
    has_kticket = has_kerberos_ticket()
    if debug_klist:
        log.info("Has k-ticket or not: {}".format(has_kticket))
    if has_kticket:
        if debug_klist:
            log.info("Renewing K-ticket")
            reinit_kticket_func()
        pass
    else:
        reinit_kticket_func()

def reinit_kticket_func():
    """
    USAGE.
        $ ktutil
        >> addent -password -p AF45008@US.AD.WELLPOINT.COM -k 1 -e aes256-cts
        >> [Enter Password]
        >> wkt /home/af45008/AF45008.keytab
        >> exit

        $ kinit AF45008 -k -t /home/af45008/AF45008.keytab
        $ klist
        >>  Ticket cache: FILE:/tmp/krb5cc_928758424
        >>  Default principal: af45008@US.AD.WELLPOINT.COM

    """
    try:
        # For service id's
        username = getpass.getuser()
        homedir = os.environ['HOME']
        # For personal id's enable below line
        user = username[:1]
        if user != 's':
            username = username.upper()
        username_lo = username.lower()
        keytab = "./" + username + ".keytab"
        command = "kinit " + username + " -kt " + keytab
        p1 = subprocess.Popen(command, shell=True) # USE THIS LINE FOR OWN UDER ID's
        p1.wait()
        log.info("Renewing Kticket (first try)")
        log.info(" - homedir : {0}".format(keytab))
        log.info(" - command : {0}".format(command))
        if not has_kerberos_ticket():
            keytab = "./" + username_lo + ".keytab"
            command = "kinit " + username + " -kt " + keytab
            p1 = subprocess.Popen(command, shell=True)  # USE THIS LINE FOR OWN UDER ID's
            p1.wait()
            log.info("Renewing Kticket (second try)")
            log.info(" - homedir : {0}".format(keytab))
            log.info(" - command : {0}".format(command))
        if not has_kerberos_ticket():
            log.info("<Err> : Kinit: Failed to reinit kticket.", level='error')
            log.info("      : Please run the following command to reinit your DS keychains.", level='error')
            log.info("      : sh /app/hca/adva/utils/ds_utils/scripts/ds_keychain.sh", level='error')
        else:
            log.info("Done. All set")

    except Exception as e:
        log.info("<Err> Kinit: {0}".format(e), level='error')

def has_kerberos_ticket():
    return True if subprocess.call(['klist', '-s']) == 0 else False

if __name__ == "__main__":
    check_and_reinit_kticket()