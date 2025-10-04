class CLI_Menu:
    """
    This module is designed to make construction of CLI menus significantly easier.

    The nesting of options as well as single bulletins screen with options to perform
    functions and tasks are available.

    The class takes dictionary with string and objects as values. Here the values can be 
    functions, methods or even classes. It's totally is allowed.

    However, to make multiple layers of options one must make multiple instances of this class.

    Each class handles a list of functions, so for multiple mini-screens (if you want that) you need
    to make that many instances of this very class.
    """
    def __init__(self, opts_lists: dict[str: object], title: str, sub_title: str|None):
        """Will initiate the presentation of the CLI menu."""
        self.opts = opts_lists
        self.title = title
        self.sub_title = sub_title
        self.calculate_lenght_title = len(title)
        self.option_maker(self.opts)
    
    def option_maker(self, opts_lists: dict[str: object]):
        """
        Responsible to set up the running menu with the operations.
        It will only take non-lambda based values! for it is a singleton connection maker.
        """
        self.title_cons(self.title)
        self.sub_title_cons(self.sub_title)
        indexing_opts = [option for option in opts_lists]
        print("\n".join(indexing_opts))
        while True:
            print("Enter your number here: ")
            usin = input()
            if usin.lower() == "q" or usin.lower() == "quit":
                print("Halting Modulated CLI... Please Wait...")
                break
            try:
                if len(indexing_opts) >= int(usin) > 0:
                    opts_lists[indexing_opts[int(usin)-1]]()
                else:
                    print("Wrong Input! Only enter number and also within the available range!\n")
            except ValueError:
                print("Type only 'q' or 'quit' to close the application, nothing else!")

    def title_cons(self, title: str):
        print("+"+"-"*(self.calculate_lenght_title+10)+"+")
        print("|"+" "*5 + title + " "*5+"|")

    def sub_title_cons(self, sub_title: str):
        calculate_length = len(sub_title)
        if self.calculate_lenght_title > calculate_length:
            remaining = self.calculate_lenght_title - calculate_length
            print("+"+"-"*(calculate_length+10)+"+"+"-"*(remaining-1)+"+")
        else:
            remaining = calculate_length - self.calculate_lenght_title
            print("+"+"-"*(self.calculate_lenght_title+10)+"+"+"-"*(remaining-1)+"+")
        print("|"+" "*5 + sub_title + " "*5+"|")
        print("+"+"-"*(calculate_length+10)+"+")


if __name__ == "__main__":
    class Exampleforusage:
        def __init__(self):
            pass

        def execute_1(self):
            print("Ran function 1")
        
        def execute_2(self):
            print("Ran function 2")
        
        def execute_3(self):
            print("Ran function 3")

    obj_example = Exampleforusage()

    opts = {
        "1. EXECUTE TASK 1" : obj_example.execute_1,
        "2. EXECUTE TASK 2" : obj_example.execute_2,
        "3. EXECUTE TASK 3" : obj_example.execute_3 
    }
    title = "Example usage 1"
    subtitle = "Written by Mirza Ishan Beg"

    obj_cli = CLI_Menu(opts_lists=opts, title=title, sub_title=subtitle)
