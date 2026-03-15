class App:

    def __init__(self):
        self.hooks = {
            "before_send": [],
            "after_response": []
        }

    def register_hook(self, hook_name, func):
        if hook_name in self.hooks:
            self.hooks[hook_name].append(func)

    def run_hook(self, hook_name, data):

        if hook_name not in self.hooks:
            return data

        for func in self.hooks[hook_name]:
            try:
                result = func(data)

                if result is not None:
                    data = result

            except Exception as e:
                print("Module hook error:", e)

        return data