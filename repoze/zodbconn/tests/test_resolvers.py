import unittest

class Base:
    def test_interpret_kwargs_noargs(self):
        resolver = self._makeOne()
        kwargs = resolver.interpret_kwargs({})
        self.assertEqual(kwargs, {})

    def test_bytesize_args(self):
        resolver = self._makeOne()
        names = list(resolver._bytesize_args)
        kwargs = {}
        for name in names:
            kwargs[name] = '10MB'
        args = resolver.interpret_kwargs(kwargs)
        keys = args.keys()
        keys.sort()
        self.assertEqual(keys, names)
        for name, value in args.items():
            self.assertEqual(value, 10*1024*1024)
    
    def test_int_args(self):
        resolver = self._makeOne()
        names = list(resolver._int_args)
        kwargs = {}
        for name in names:
            kwargs[name] = '10'
        args = resolver.interpret_kwargs(kwargs)
        keys = args.keys()
        keys.sort()
        self.assertEqual(sorted(keys), sorted(names))
        for name, value in args.items():
            self.assertEqual(value, 10)

    def test_string_args(self):
        resolver = self._makeOne()
        names = list(resolver._string_args)
        kwargs = {}
        for name in names:
            kwargs[name] = 'string'
        args = resolver.interpret_kwargs(kwargs)
        keys = args.keys()
        keys.sort()
        self.assertEqual(keys, names)
        for name, value in args.items():
            self.assertEqual(value, 'string')

    def test_bool_args(self):
        resolver = self._makeOne()
        f = resolver.interpret_kwargs
        kwargs = f({'read_only':'1'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'true'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'on'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'off'})
        self.assertEqual(kwargs, {'read_only':0})
        kwargs = f({'read_only':'no'})
        self.assertEqual(kwargs, {'read_only':0})
        kwargs = f({'read_only':'false'})
        self.assertEqual(kwargs, {'read_only':0})

class TestFileStorgeURIResolver(Base, unittest.TestCase):
    def _getTargetClass(self):
        from repoze.zodbconn.resolvers import FileStorageURIResolver
        return FileStorageURIResolver

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_call_abspath(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('file:///tmp/foo/bar?read_only=true')
        self.assertEqual(args, ('/tmp/foo/bar',))
        self.assertEqual(kw, {'read_only':1})

    def test_call_abspath_windows(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file://C:\\foo\\bar?read_only=true')
        self.assertEqual(args, ('C:\\foo\\bar',))
        self.assertEqual(kw, {'read_only':1})

    def test_call_normpath(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('file:///tmp/../foo/bar?read_only=true')
        self.assertEqual(args, ('/foo/bar',))
        self.assertEqual(kw, {'read_only':1})

    def test_invoke_factory(self):
        import os
        self.failIf(os.path.exists(os.path.join(self.tmpdir, 'db.db')))
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file://%s/db.db?quota=200' % self.tmpdir)
        self.assertEqual(k,
                         (('%s/db.db' % self.tmpdir,), (('quota', 200),),
                          (('cache_size', 10000), ('database_name', 'unnamed'),
                           ('pool_size', 7)))
                         )
        db = factory()
        self.failUnless(os.path.exists(os.path.join(self.tmpdir, 'db.db')))

    def test_demostorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            'file:///tmp/../foo/bar?demostorage=true')
        self.assertEqual(args, ('/foo/bar',))
        self.assertEqual(kw, {})

    def test_blobstorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            ('file:///tmp/../foo/bar'
             '?blobstorage_dir=/foo/bar&blobstorage_layout=bushy'))
        self.assertEqual(args, ('/foo/bar',))
        self.assertEqual(kw, {})

    def test_blobstorage_and_demostorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            ('file:///tmp/../foo/bar?demostorage=true'
             '&blobstorage_dir=/foo/bar&blobstorage_layout=bushy'))
        self.assertEqual(args, ('/foo/bar',))
        self.assertEqual(kw, {})

    def test_dbargs(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver(
            ('file:///tmp/../foo/bar?connection_pool_size=1'
             '&connection_cache_size=1&database_name=dbname'))
        self.assertEqual(k[2],
                         (('cache_size', 1), ('database_name', 'dbname'),
                          ('pool_size', 1)))
        

class TestClientStorageURIResolver(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.zodbconn.resolvers import ClientStorageURIResolver
        return ClientStorageURIResolver

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def test_call_tcp(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo://localhost:8080?debug=true')
        self.assertEqual(args, (('localhost', 8080),))
        self.assertEqual(kw, {'debug':1})
        self.assertEqual(k,
                         ((('localhost', 8080),), (('debug', 1),),
                          (('cache_size', 10000), ('database_name','unnamed'),
                           ('pool_size', 7))))

    def test_call_unix(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo:///var/sock?debug=true')
        self.assertEqual(args, ('/var/sock',))
        self.assertEqual(kw, {'debug':1})
        self.assertEqual(k,
                         (('/var/sock',),
                          (('debug', 1),),
                          (('cache_size', 10000),
                           ('database_name', 'unnamed'),
                           ('pool_size', 7))))

    def test_invoke_factory(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo:///var/nosuchfile?wait=false')
        self.assertEqual(k, (('/var/nosuchfile',),
                             (('wait', 0),),
                             (('cache_size', 10000),
                              ('database_name', 'unnamed'), ('pool_size', 7))))
        from ZEO.ClientStorage import ClientDisconnected
        self.assertRaises(ClientDisconnected, factory)

    def test_demostorage(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo:///var/sock?demostorage=true')
        self.assertEqual(args, ('/var/sock',))
        self.assertEqual(kw, {})

    def test_dbargs(self):
        resolver = self._makeOne()
        k, args, kw, factory = resolver('zeo://localhost:8080?debug=true&'
                                        'connection_pool_size=1&'
                                        'connection_cache_size=1&'
                                        'database_name=dbname')
        self.assertEqual(k[2],
                         (('cache_size', 1), ('database_name', 'dbname'),
                          ('pool_size', 1)))
