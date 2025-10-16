import configparser

#Function which parses the config.ini file
def parse_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)

    organisation_id = config.get('auth', 'organisation_Id', fallback=None)
    mail = config.get('auth', 'mail', fallback=None)
    password = config.get('auth', 'password', fallback=None)

    return organisation_id, mail, password