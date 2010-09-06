# Copyright(c) 2005-2007 Angelantonio Valente (y3sman@gmail.com)
# See LICENSE file for details.

"""
Data providers
"""

class DataProvider(object):
    """
    Interface to a generic sequence-based data provider
    """
    
    def __init__(self,sequence):
        self.sequence = sequence
    
    def run(self, *args, **kwargs):
        self.iterator = iter(self.sequence)
        
    def __iter__(self):
        return self.iterator
    
    def reset(self):
        self.iterator = iter(self.sequence)
    
    def next(self):
        return self.iterator.next()
        
    
class DBDataProvider(DataProvider):
    """
    dbapi2 Data Provider
    Executes a query against a dbapi2 connection and runs a query to get
    the data source
    """
    
    def __init__(self, query, **kwargs):
        self.query = query
        for arg in ("conn", "module", "conn_pars"):
            setattr(self, arg, kwargs.get(arg, None))
        
    def run(self, params = [], **kwargs):
        conn = kwargs.get("conn", self.conn)
        conn_pars = kwargs.get("conn_pars", self.conn_pars)
        module = kwargs.get("module", self.module)

        if not conn:
            connargs = []
            connkwargs = {}
            if conn_pars:
                connargs = conn_pars[0]
                if len(conn_pars) > 1:
                    connkwargs = conn_pars[1]
            
            conn = module.connect(*connargs, **connkwargs)
            
        if module.__name__ in ("sqlite", "sqlite3"):
            conn.row_factory = module.Row
                
        self.cur = conn.cursor()
        
        self.cur.execute(self.query, params)
    def __iter__(self):
        return self
    
    def next(self):
        r = self.cur.fetchone()
        if r is None:
            raise StopIteration()
        return r