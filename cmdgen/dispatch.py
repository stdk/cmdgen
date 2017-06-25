# from types import MethodType

# class DispatchWrapper(object):
#     def __init__(self,default_func,on_arg_index):
#         self.default_func = default_func
#         self.on_arg_index = on_arg_index
#         self.options = {}
#     def __call__(self,*args,**kwargs):
#         print 'call',self,args,kwargs
#         dispatch_arg = args[self.on_arg_index]
#         func = self.options.get(type(dispatch_arg),self.default_func)
#         return func(*args,**kwargs)
#     def __get__(self, instance, owner):
#         return MethodType(self, instance, owner) if instance else self
#     def when(self,type):
#         def decorator(func):
#             self.options[type] = func
#             return self
#         return decorator

def dispatch(on_arg_index,debug=False):
    def decorator(default_func):
        options = {}
        def wrapper(*args,**kwargs):
            dispatch_arg = args[on_arg_index]
            func = options.get(type(dispatch_arg),default_func)
            result = func(*args,**kwargs)
            if debug:
                print func,args,'->',result
            return result
        def when(type):
            def when_decorator(when_func):
                options[type] = when_func
                return wrapper
            return when_decorator
        wrapper.when = when
        return wrapper
    return decorator