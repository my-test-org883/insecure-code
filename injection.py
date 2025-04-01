import os

def vulnerable_echo(user_input):
    # This is insecure: it concatenates unsanitized input into a shell command.
    command = "echo " + user_input
    os.system(command)

if __name__ == "__main__":
    user_input = input("Enter text: ")
    vulnerable_echo(user_input)
