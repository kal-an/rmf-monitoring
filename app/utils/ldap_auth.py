import ldap


class LDAPAuth:

    @staticmethod
    def get_ldap_connection(uri):
        conn = ldap.initialize(uri)
        conn.protocol_version = ldap.VERSION3
        return conn
