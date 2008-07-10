# repoze.zodbconn middleware

class ZODBConnectionMiddleware:
    def __init__(self, app, registry, name_to_uri_map):
        self.app = app
        self.databases = []
        self.registry = registry
        for name, uri in name_to_uri_map.items():
            db = registry.from_uri(uri)
            self.databases.append((name, db))
        
    def __call__(self, environ, start_response):
        databases = self.databases
        try:
            for name, db in databases:
                conn = db.open()
                add_conn(environ, name, conn)
            result = self.app(environ, start_response)
            return result
        finally:
            for name, db in databases:
                conn = get_conn(environ, name)
                if conn is not None:
                    conn.close()
                del_conn(environ, name)

def make_middleware(app, global_conf, **kw):
    from repoze.zodbconn.manager import databases
    return ZODBConnectionMiddleware(app, databases, **kw)

_ENV_KEY = 'repoze.zodbconn.connections'

def add_conn(environ, name, conn):
    conn_d = environ.setdefault(_ENV_KEY, {})
    conn_d[name] = conn
    
def get_conn(environ, name):
    return environ.get(_ENV_KEY, {}).get(name)

def del_conn(environ, name):
    conn_d = environ.get(_ENV_KEY, {})
    try:
        del conn_d[name]
    except KeyError:
        pass

